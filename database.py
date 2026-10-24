import sqlite3
from datetime import datetime

def connect():
    connection = sqlite3.connect("cafe.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_session_refunds_by_method(session_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT payment_method, COALESCE(SUM(amount), 0)
            FROM refunds
            WHERE session_id = ?
            GROUP BY payment_method
        """, (session_id,))

        totals = {
            "cash": 0,
            "card": 0,
            "unknown": 0
        }

        for payment_method, amount in cursor.fetchall():
            if payment_method == "cash":
                totals["cash"] = amount
            elif payment_method == "card":
                totals["card"] = amount
            else:
                totals["unknown"] += amount

        return totals

    finally:
        conn.close()


def get_session_refund_total(session_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM refunds
            WHERE session_id = ?
        """, (session_id,))

        return cursor.fetchone()[0]

    finally:
        conn.close()



def get_refunds_by_method_and_date(start_date, end_date):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT payment_method, COALESCE(SUM(amount), 0)
            FROM refunds
            WHERE refunded_at >= ?
              AND refunded_at < date(?, '+1 day')
            GROUP BY payment_method
        """, (start_date, end_date))

        totals = {
            "cash": 0,
            "card": 0,
            "unknown": 0
        }

        for method, amount in cursor.fetchall():
            if method == "cash":
                totals["cash"] += amount
            elif method == "card":
                totals["card"] += amount
            else:
                totals["unknown"] += amount

        return totals

    finally:
        conn.close()


def get_refund_total_by_date(start_date, end_date):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM refunds
            WHERE refunded_at >= ?
              AND refunded_at < date(?, '+1 day')
        """, (start_date, end_date))

        return cursor.fetchone()[0]

    finally:
        conn.close()



def add_payment_method_to_refunds():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(refunds)")
        columns = [row[1] for row in cursor.fetchall()]

        if "payment_method" not in columns:
            cursor.execute("""
                ALTER TABLE refunds
                ADD COLUMN payment_method TEXT
                    CHECK (
                        payment_method IN ('cash', 'card')
                        OR payment_method IS NULL
                    )
            """)

        conn.commit()

    finally:
        conn.close()



def create_refunds_table():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_id INTEGER,
                bill_id INTEGER,

                session_id INTEGER NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0),

                reason TEXT NOT NULL,
                refunded_at TEXT NOT NULL,

                FOREIGN KEY (order_id)
                    REFERENCES orders(id),

                FOREIGN KEY (bill_id)
                    REFERENCES table_bills(id),

                FOREIGN KEY (session_id)
                    REFERENCES cashier_sessions(id),

                CHECK (
                    (order_id IS NOT NULL AND bill_id IS NULL)
                    OR
                    (order_id IS NULL AND bill_id IS NOT NULL)
                )
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                one_refund_per_direct_sale
            ON refunds(order_id)
            WHERE order_id IS NOT NULL
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                one_refund_per_table_bill
            ON refunds(bill_id)
            WHERE bill_id IS NOT NULL
        """)

        conn.commit()

    finally:
        conn.close()



def add_discount_fields():
    conn = connect()

    try:
        cursor = conn.cursor()

        # Direct sales: orders table
        cursor.execute("PRAGMA table_info(orders)")
        order_columns = {
            row[1] for row in cursor.fetchall()
        }

        if "subtotal" not in order_columns:
            cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN subtotal INTEGER
            """)

        if "discount_amount" not in order_columns:
            cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN discount_amount INTEGER NOT NULL DEFAULT 0
            """)

        # Existing orders had no discounts.
        cursor.execute("""
            UPDATE orders
            SET subtotal = total
            WHERE subtotal IS NULL
        """)

        # Table discounts belong to the final bill.
        cursor.execute("PRAGMA table_info(table_bills)")
        bill_columns = {
            row[1] for row in cursor.fetchall()
        }

        if "subtotal" not in bill_columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN subtotal INTEGER
            """)

        if "discount_amount" not in bill_columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN discount_amount INTEGER NOT NULL DEFAULT 0
            """)

        # Existing paid table bills had no discounts.
        cursor.execute("""
            UPDATE table_bills
            SET subtotal = (
                SELECT COALESCE(SUM(o.total), 0)
                FROM orders AS o
                WHERE o.bill_id = table_bills.id
            )
            WHERE subtotal IS NULL
              AND status = 'closed'
        """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def create_products_table():
    connection = connect()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1))

        )
    """)

    connection.commit()
    connection.close()



def get_direct_sale_receipt(order_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                created_at,
                subtotal,
                discount_amount,
                total,
                payment_method
            FROM orders
            WHERE id = ?
              AND bill_id IS NULL
        """, (order_id,))

        order = cursor.fetchone()

        if order is None:
            raise ValueError("فروش مستقیم پیدا نشد.")

        cursor.execute("""
            SELECT
                p.name,
                oi.quantity,
                oi.price
            FROM order_items AS oi
            JOIN products AS p
                ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.id
        """, (order_id,))

        return {
            "receipt_number": order[0],
            "date": order[1],
            "subtotal": order[2],
            "discount": order[3],
            "total": order[4],
            "payment_method": order[5],
            "items": cursor.fetchall()
        }

    finally:
        conn.close()



def get_table_receipt(bill_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                b.id,
                t.name,
                b.paid_at,
                b.subtotal,
                b.discount_amount,
                b.payment_method
            FROM table_bills AS b
            JOIN cafe_tables AS t
                ON t.id = b.table_id
            WHERE b.id = ?
              AND b.status = 'closed'
              AND b.paid_at IS NOT NULL
        """, (bill_id,))

        bill = cursor.fetchone()

        if bill is None:
            raise ValueError("صورتحساب پرداخت‌شده پیدا نشد.")

        cursor.execute("""
            SELECT
                p.name,
                oi.quantity,
                oi.price
            FROM orders AS o
            JOIN order_items AS oi
                ON oi.order_id = o.id
            JOIN products AS p
                ON p.id = oi.product_id
            WHERE o.bill_id = ?
            ORDER BY o.id, oi.id
        """, (bill_id,))

        items = cursor.fetchall()

        subtotal = bill[3]
        discount = bill[4]

        return {
            "receipt_number": bill[0],
            "table_name": bill[1],
            "date": bill[2],
            "subtotal": subtotal,
            "discount": discount,
            "total": subtotal - discount,
            "payment_method": bill[5],
            "items": items
        }
    
    finally:
        conn.close()




def add_products(name, price):
    name = name.strip()

    if not name:
        raise ValueError("نام محصول نمی‌تواند خالی باشد.")

    if price <= 0:
        raise ValueError("قیمت باید بیشتر از صفر باشد.")

    conn = connect()

    try:
        cursor = conn.cursor()

        # Check active products for the same name.
        cursor.execute(
            """
            SELECT id
            FROM products
            WHERE LOWER(TRIM(name)) = LOWER(?)
              AND is_active = 1
            """,
            (name,)
        )

        if cursor.fetchone() is not None:
            raise ValueError("محصولی با این نام از قبل وجود دارد.")

        cursor.execute(
            """
            INSERT INTO products (name, price)
            VALUES (?, ?)
            """,
            (name, price)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def get_product():
    connection = connect()
    cursor = connection.cursor()


    cursor.execute("SELECT id, name, price FROM products WHERE is_active = 1")

    products = cursor.fetchall()

    connection.close()

    return products

def update_product_price(product_id, new_price):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE products SET price = ? WHERE id = ?",
        (new_price, product_id)
    )

    connection.commit()
    connection.close()


def delete_product(product_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE products SET is_active = 0 where id = ?",
        (product_id,)
    )

    connection.commit()
    connection.close()


def create_order_table():
    connection = connect()
    cursor = connection.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            total INTEGER NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (session_id)
                REFERENCES cashier_sessions(id)
        )
        """
    )

    connection.commit()
    connection.close()


def calculate_discount(subtotal, discount_type="none", discount_value=0):
    if type(subtotal) is not int or subtotal <= 0:
        raise ValueError("مبلغ اولیه باید بیشتر از صفر باشد.")

    if type(discount_value) is not int or discount_value < 0:
        raise ValueError("مقدار تخفیف نامعتبر است.")

    if discount_type == "none":
        if discount_value != 0:
            raise ValueError("برای بدون تخفیف، مقدار باید صفر باشد.")
        discount_amount = 0

    elif discount_type == "percent":
        if discount_value > 100:
            raise ValueError("درصد تخفیف نباید بیشتر از ۱۰۰ باشد.")

        discount_amount = (
            subtotal * discount_value + 50
        ) // 100

    elif discount_type == "amount":
        if discount_value > subtotal:
            raise ValueError("تخفیف نباید بیشتر از مبلغ کل باشد.")

        discount_amount = discount_value

    else:
        raise ValueError("نوع تخفیف نامعتبر است.")

    final_total = subtotal - discount_amount

    return discount_amount, final_total


def save_order(
        session_id,
        total,
        items,
        bill_id=None,
        payment_method=None,
        discount_type="none",
        discount_value=0
    ):
    conn = connect()

    try:
        cursor = conn.cursor()

        # Start a database transaction.
        cursor.execute("BEGIN")

        # Check that the cashier session is still open.
        cursor.execute(
            """
            SELECT id
            FROM cashier_sessions
            WHERE id = ? AND status = 1
            """,
            (session_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError("Cashier session is closed.")

        if bill_id is not None:
            cursor.execute(
                """
                SELECT id 
                FROM table_bills
                WHERE id = ?
                    AND status = 'open'
                """, 
                (bill_id,)
            )

            if cursor.fetchone() is None:
                raise ValueError(
                    "این صورتحساب وجود ندارد یا بسته شده است."
                )

        if bill_id is None:
            if payment_method not in ("cash", "card"):
                raise ValueError(
                    "روش پرداخت فروش مستقیم باید نقدی یا کارت باشد."
                )
        else:
            if payment_method is not None:
                raise ValueError(
                     "روش پرداخت میز هنگام تسویه صورتحساب ثبت می‌شود."
                )

        if not items:
            raise ValueError("Cannot save an empty order.")

        # Calculate the total on the backend.
                # Calculate the total on the backend.
        calculated_total = 0

        for item in items:
            quantity = item["quantity"]
            price = item["price"]

            if quantity <= 0 or price < 0:
                raise ValueError("Invalid quantity or price.")

            calculated_total += quantity * price

        # Check the total only AFTER all items are added.
        subtotal = calculated_total

        if bill_id is None:
            discount_amount, final_total = calculate_discount(
                subtotal,
                discount_type,
                discount_value
            )

            if total != final_total:
                raise ValueError("مبلغ نهایی سفارش صحیح نیست.")

        else:
            if discount_type != "none" or discount_value != 0:
                raise ValueError(
                    "تخفیف میز فقط هنگام تسویه صورتحساب اعمال می‌شود."
                )

            discount_amount = 0

            if total != subtotal:
                raise ValueError("مبلغ سفارش میز صحیح نیست.")
            
        # Save the order.
        cursor.execute(
            """
            INSERT INTO orders (
                session_id, 
                total, 
                created_at,
                bill_id,
                payment_method,
                subtotal,
                discount_amount
            )
            VALUES (?, ?, datetime('now', 'localtime'), ?, ?, ?, ?)
            """,
            (
                session_id,
                total,
                bill_id,
                payment_method,
                subtotal,
                discount_amount
            )
        )

        order_id = cursor.lastrowid

        # Save every item belonging to this order.
        for item in items:
            cursor.execute(
                """
                INSERT INTO order_items
                    (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["quantity"],
                    item["price"]
                )
            )

        # Save everything only after all operations succeed.
        conn.commit()

        return order_id

    except Exception:
        # Undo every change made during this transaction.
        conn.rollback()
        raise

    finally:
        # Close the connection whether saving succeeds or fails.
        conn.close()

def create_order_items_table():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,

            FOREIGN KEY (order_id)
                REFERENCES orders(id),

            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
        """
    )


    connection.commit()
    connection.close()



def  get_order_items(order_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 
            products.name,
            order_items.quantity,
            order_items.price
        FROM order_items
        JOIN products 
            ON order_items.product_id = products.id
        JOIN orders
            ON order_items.order_id = orders.id
        WHERE orders.id = ?

        """,
        (order_id,)
    )

    items = cursor.fetchall()
    connection.close()

    return items



def get_table_bill_items(bill_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                p.name,
                SUM(oi.quantity) AS quantity,
                oi.price
            FROM orders AS o
            JOIN order_items AS oi
                ON oi.order_id = o.id
            JOIN products AS p
                ON p.id = oi.product_id
            WHERE o.bill_id = ?
            GROUP BY
                p.id,
                p.name,
                oi.price
            ORDER BY p.name
            """,
            (bill_id,)
        )

        return cursor.fetchall()

    finally:
        conn.close()


def create_cashier_sessions_table():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cashier_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status INTEGER NOT NULL CHECK (status IN (0, 1)),
            opened_at TEXT NOT NULL,
            closed_at TEXT 
        )
    """)

    connection.commit()
    connection.close()


def open_cashier_session():
    connection = connect()
    cursor = connection.cursor()


    # check if a session is already open
    cursor.execute(
        "SELECT id FROM cashier_sessions WHERE status = 1"
    )
    open_session = cursor.fetchone()

    if open_session is not None:
        print("Cashier session is already open")
        connection.close()
        return

    # open a new session
    opened_at = datetime.now()

    cursor.execute(
        """
        INSERT INTO cashier_sessions (status, opened_at, closed_at) values (?, ?, ?)
        """,
        (1, opened_at, None)

    )

    connection.commit()
    connection.close()

    print("Cashier session opened successfully")


def get_open_cashier_session():
    connection = connect()
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT id FROM cashier_sessions where status = 1"
    )

    open_session = cursor.fetchone()

    connection.close()

    if open_session is None:
        return None

    return open_session[0]


def close_cashier_session():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id FROM cashier_sessions WHERE status = 1
        """
    )

    open_session = cursor.fetchone()

    if open_session is None:
        print("No open cashier session")
        connection.close()
        return

    session_id = open_session[0]
    closed_at = datetime.now()

    cursor.execute(
        """
        UPDATE cashier_sessions
        SET status = ?, closed_at = ?
        WHERE id = ?
        """,
        (0, closed_at, session_id)
    )

    connection.commit()
    connection.close()

    print("cashier session closed successfully")


def get_current_session_orders():
    session_id = get_open_cashier_session()

    if session_id is None:
        return None

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT o.id, o.total, o.created_at 
        FROM orders AS o
        LEFT JOIN table_bills AS b
            ON o.bill_id = b.id
        WHERE o.session_id = ?
          AND (
                o.bill_id IS NULL
                OR b.status = 'closed'
              )
        ORDER BY o.id
        """,
        (session_id,)
    )

    orders = cursor.fetchall()
    connection.close()

    return orders


def get_cashier_sessions():
    conn = connect()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, status, opened_at, closed_at
            FROM cashier_sessions
            ORDER BY id DESC
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_session_orders(session_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                'order' AS sale_type,
                o.id AS sale_id,
                NULL AS table_name,
                o.total AS total,
                o.created_at AS sale_time,
                o.payment_method AS payment_method
            FROM orders AS o
            WHERE o.session_id = ?
              AND o.bill_id IS NULL

            UNION ALL

            SELECT
                'table' AS sale_type,
                b.id AS sale_id,
                t.name AS table_name,
                COALESCE(
                    b.subtotal - b.discount_amount,
                    SUM(o.total),
                    0
                ) AS total,
                b.paid_at AS sale_time,
                b.payment_method AS payment_method
            FROM table_bills AS b
            JOIN cafe_tables AS t
                ON t.id = b.table_id
            JOIN orders AS o
                ON o.bill_id = b.id
            WHERE b.status = 'closed'
              AND b.paid_session_id = ?
              AND b.paid_at IS NOT NULL
            GROUP BY
                b.id,
                t.name,
                b.paid_at

            ORDER BY sale_time DESC
            """,
            (session_id, session_id)
        )

        return cursor.fetchall()

    finally:
        conn.close()


def get_orders_by_date(start_date, end_date):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                'order' AS sale_type,
                o.id AS sale_id,
                NULL AS table_name,
                o.total AS total,
                o.created_at AS sale_time,
                o.payment_method AS payment_method
            FROM orders AS o
            WHERE o.bill_id IS NULL
              AND o.created_at >= ?
              AND o.created_at < date(?, '+1 day')

            UNION ALL

            SELECT
                'table' AS sale_type,
                b.id AS sale_id,
                t.name AS table_name,
                COALESCE(
                    b.subtotal - b.discount_amount,
                    SUM(o.total),
                    0
                ) AS total,
                b.paid_at AS sale_time,
                b.payment_method AS payment_method
            FROM table_bills AS b
            JOIN cafe_tables AS t
                ON t.id = b.table_id
            JOIN orders AS o
                ON o.bill_id = b.id
            WHERE b.status = 'closed'
              AND b.paid_at IS NOT NULL
              AND b.paid_at >= ?
              AND b.paid_at < date(?, '+1 day')
            GROUP BY
                b.id,
                t.name,
                b.paid_at

            ORDER BY sale_time DESC
            """,
            (
                start_date,
                end_date,
                start_date,
                end_date
            )
        )

        return cursor.fetchall()

    finally:
        conn.close()


def create_cafe_tables():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cafe_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK (is_active IN (0, 1))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
                    CHECK (status IN ('open', 'closed')),
                opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                FOREIGN KEY (table_id) REFERENCES cafe_tables(id)
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS one_open_bill_per_table
            ON table_bills(table_id)
            WHERE status = 'open'
        """)

        conn.commit()

    finally:
        conn.close()




def add_cafe_table(name):
    name = name.strip()

    if not name:
        raise ValueError("نام میز نمی‌تواند خالی باشد.")

    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cafe_tables (name)
            VALUES (?)
        """, (name,))

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()



def rename_cafe_table(table_id, new_name):
    new_name = new_name.strip()

    if not new_name:
        raise ValueError("نام میز نمی‌تواند خالی باشد.")

    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE cafe_tables
            SET name = ?
            WHERE id = ?
              AND is_active = 1
        """, (new_name, table_id))

        if cursor.rowcount != 1:
            raise ValueError("میز پیدا نشد یا غیرفعال است.")

        conn.commit()

    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("میزی با این نام از قبل وجود دارد.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def get_all_cafe_tables():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                t.id,
                t.name,
                t.is_active,
                b.id AS open_bill_id
            FROM cafe_tables AS t
            LEFT JOIN table_bills AS b
                ON b.table_id = t.id
                AND b.status = 'open'
            ORDER BY t.id
        """)

        return cursor.fetchall()

    finally:
        conn.close()


def set_cafe_table_active(table_id, is_active):
    if is_active not in (0, 1):
        raise ValueError("وضعیت میز نامعتبر است.")

    conn = connect()

    try:
        cursor = conn.cursor()

        if is_active == 0:
            cursor.execute("""
                SELECT id
                FROM table_bills
                WHERE table_id = ?
                  AND status = 'open'
            """, (table_id,))

            if cursor.fetchone() is not None:
                raise ValueError(
                    "این میز صورتحساب باز دارد و نمی‌توان آن را غیرفعال کرد."
                )

        cursor.execute("""
            UPDATE cafe_tables
            SET is_active = ?
            WHERE id = ?
        """, (is_active, table_id))

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT id FROM cafe_tables WHERE id = ?",
                (table_id,)
            )

            if cursor.fetchone() is None:
                raise ValueError("میز پیدا نشد.")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def get_cafe_tables():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                t.id,
                t.name,
                b.id AS open_bill_id
            FROM cafe_tables AS t
            LEFT JOIN table_bills AS b
                ON b.table_id = t.id
                AND b.status = 'open'
            WHERE t.is_active = 1
            ORDER BY t.id
        """)

        return cursor.fetchall()

    finally:
        conn.close()



def open_table_bill(table_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("BEGIN")

        cursor.execute("""
            SELECT id
            FROM cafe_tables
            WHERE id = ? AND is_active = 1
        """, (table_id,))

        if cursor.fetchone() is None:
            raise ValueError("این میز وجود ندارد یا غیرفعال است.")

        cursor.execute("""
            INSERT INTO table_bills (table_id)
            VALUES (?)
        """, (table_id,))

        bill_id = cursor.lastrowid
        conn.commit()

        return bill_id

    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("این میز در حال حاضر صورتحساب باز دارد.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def cancel_empty_table_bill(bill_id):
    conn = connect()

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN")

        # Make sure the bill exists and is still open.
        cursor.execute(
            """
            SELECT id
            FROM table_bills
            WHERE id = ?
              AND status = 'open'
            """,
            (bill_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError(
                "صورتحساب وجود ندارد یا قبلاً بسته شده است."
            )

        # Never allow cancellation if an order was already added.
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE bill_id = ?
            """,
            (bill_id,)
        )

        order_count = cursor.fetchone()[0]

        if order_count > 0:
            raise ValueError(
                "صورتحساب دارای سفارش است و قابل لغو نیست."
            )

        cursor.execute(
            """
            DELETE FROM table_bills
            WHERE id = ?
              AND status = 'open'
            """,
            (bill_id,)
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "لغو صورتحساب ناموفق بود."
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def close_table_bill(
        bill_id,
        session_id,
        payment_method,
        discount_type="none",
        discount_value=0
    ):
    conn = connect()

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN")

        if payment_method not in ("cash", "card"):
            raise ValueError("روش پرداخت باید نقدی یا کارت باشد.")

        # Make sure the cashier session is still open.
        cursor.execute(
            """
            SELECT id
            FROM cashier_sessions
            WHERE id = ?
              AND status = 1
            """,
            (session_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError(
                "برای ثبت پرداخت، صندوق باید باز باشد."
            )

        # Verify that the table bill is open.
        cursor.execute(
            """
            SELECT id
            FROM table_bills
            WHERE id = ?
              AND status = 'open'
            """,
            (bill_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError(
                "این صورتحساب وجود ندارد یا قبلاً بسته شده است."
            )

        # Calculate the original bill amount.
        cursor.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM orders
            WHERE bill_id = ?
            """,
            (bill_id,)
        )

        subtotal = cursor.fetchone()[0]

        if subtotal <= 0:
            raise ValueError("صورتحساب میز خالی است.")

        # Calculate discount and final payment.
        discount_amount, final_total = calculate_discount(
            subtotal,
            discount_type,
            discount_value
        )

        # Close the bill and save the discount.
        cursor.execute(
            """
            UPDATE table_bills
            SET status = 'closed',
                closed_at = datetime('now', 'localtime'),
                paid_at = datetime('now', 'localtime'),
                paid_session_id = ?,
                payment_method = ?,
                subtotal = ?,
                discount_amount = ?
            WHERE id = ?
              AND status = 'open'
            """,
            (
                session_id,
                payment_method,
                subtotal,
                discount_amount,
                bill_id
            )
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "بستن صورتحساب ناموفق بود."
            )

        conn.commit()

        return final_total

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()




def add_bill_id_to_orders():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in cursor.fetchall()]

        if "bill_id" not in columns:
            cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN bill_id INTEGER
                    REFERENCES table_bills(id)
            """)

        conn.commit()

    finally:
        conn.close()



def add_payment_fields_to_table_bills():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(table_bills)")
        columns = [row[1] for row in cursor.fetchall()]

        if "paid_at" not in columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN paid_at TEXT
            """)

        if "paid_session_id" not in columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN paid_session_id INTEGER
                    REFERENCES cashier_sessions(id)
            """)

        conn.commit()

    finally:
        conn.close()



def add_payment_method_to_table_bills():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(table_bills)")
        columns = [row[1] for row in cursor.fetchall()]

        if "payment_method" not in columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN payment_method TEXT
            """)

        conn.commit()

    finally:
        conn.close()


def get_table_bill_details(bill_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        # Check that the bill exists.
        cursor.execute("""
            SELECT
                b.id,
                t.name,
                b.status,
                b.opened_at
            FROM table_bills AS b
            JOIN cafe_tables AS t
                ON t.id = b.table_id
            WHERE b.id = ?
        """, (bill_id,))

        bill = cursor.fetchone()

        if bill is None:
            raise ValueError("صورتحساب پیدا نشد.")

        # Retrieve every order belonging to this bill.
        cursor.execute("""
            SELECT id, total, created_at
            FROM orders
            WHERE bill_id = ?
            ORDER BY id
        """, (bill_id,))

        orders = cursor.fetchall()

        total = sum(order[1] for order in orders)

        return {
            "bill_id": bill[0],
            "table_name": bill[1],
            "status": bill[2],
            "opened_at": bill[3],
            "orders": orders,
            "total": total
        }

    finally:
        conn.close()


def add_payment_method_to_orders():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in cursor.fetchall()]

        if "payment_method" not in columns:
            cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN payment_method TEXT
            """)

        conn.commit()

    finally:
        conn.close()



def is_sale_refunded(sale_type, sale_id):
    conn = connect()

    try:
        cursor = conn.cursor()

        if sale_type == "order":
            cursor.execute("""
                SELECT 1
                FROM refunds
                WHERE order_id = ?
            """, (sale_id,))

        elif sale_type == "table":
            cursor.execute("""
                SELECT 1
                FROM refunds
                WHERE bill_id = ?
            """, (sale_id,))

        else:
            raise ValueError("نوع فروش نامعتبر است.")

        return cursor.fetchone() is not None

    finally:
        conn.close()


def refund_direct_sale(order_id, reason, payment_method):
    reason = reason.strip()
    
    if payment_method not in ("cash", "card"):
        raise ValueError("روش بازپرداخت باید نقدی یا کارت باشد.")

    if not reason:
        raise ValueError("دلیل بازپرداخت نمی‌تواند خالی باشد.")

    conn = connect()

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        # Find the original direct sale.
        cursor.execute("""
            SELECT id, total, cancelled_at
            FROM orders
            WHERE id = ?
              AND bill_id IS NULL
        """, (order_id,))

        sale = cursor.fetchone()

        if sale is None:
            raise ValueError("فروش مستقیم پیدا نشد.")

        sale_id, amount, cancelled_at = sale

        if cancelled_at is not None:
            raise ValueError("این فروش قبلاً بازپرداخت شده است.")

        # Find the currently open cashier shift.
        cursor.execute("""
            SELECT id
            FROM cashier_sessions
            WHERE status = 1
        """)

        session = cursor.fetchone()

        if session is None:
            raise ValueError(
                "برای ثبت بازپرداخت، صندوق باید باز باشد."
            )

        refund_session_id = session[0]

        # Record the refund in the current shift.
        cursor.execute("""
            INSERT INTO refunds (
                order_id,
                bill_id,
                session_id,
                amount,
                reason,
                refunded_at,
                payment_method
            )
            VALUES (
                ?, NULL, ?, ?, ?,
                datetime('now', 'localtime'), ?
            )
        """, (
            sale_id,
            refund_session_id,
            amount,
            reason,
            payment_method
        ))

        # Mark the original sale as refunded.
        cursor.execute("""
            UPDATE orders
            SET cancelled_at = datetime('now', 'localtime'),
                cancellation_reason = ?
            WHERE id = ?
              AND cancelled_at IS NULL
        """, (reason, sale_id))

        if cursor.rowcount != 1:
            raise ValueError("ثبت بازپرداخت ناموفق بود.")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def refund_table_bill(bill_id, reason, payment_method):
    reason = reason.strip()

    if payment_method not in ("cash", "card"):
        raise ValueError("روش بازپرداخت باید نقدی یا کارت باشد.")

    if not reason:
        raise ValueError("دلیل بازپرداخت نمی‌تواند خالی باشد.")

    conn = connect()

    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE")

        # Only completed, paid table bills can be refunded.
        cursor.execute("""
            SELECT id, cancelled_at
            FROM table_bills
            WHERE id = ?
              AND status = 'closed'
              AND paid_at IS NOT NULL
        """, (bill_id,))

        bill = cursor.fetchone()

        if bill is None:
            raise ValueError("صورتحساب پرداخت‌شده پیدا نشد.")

        if bill[1] is not None:
            raise ValueError("این صورتحساب قبلاً بازپرداخت شده است.")

                # Refund the amount actually paid after discount.
        cursor.execute("""
            SELECT COALESCE(
                b.subtotal - b.discount_amount,
                (
                    SELECT SUM(o.total)
                    FROM orders AS o
                    WHERE o.bill_id = b.id
                ),
                0
            )
            FROM table_bills AS b
            WHERE b.id = ?
        """, (bill_id,))

        amount = cursor.fetchone()[0]

        # Refunds belong to the currently open cashier shift.
        cursor.execute("""
            SELECT id
            FROM cashier_sessions
            WHERE status = 1
        """)

        session = cursor.fetchone()

        if session is None:
            raise ValueError(
                "برای ثبت بازپرداخت، صندوق باید باز باشد."
            )

        refund_session_id = session[0]

        cursor.execute("""
            INSERT INTO refunds (
                order_id,
                bill_id,
                session_id,
                amount,
                reason,
                refunded_at,
                payment_method
            )
            VALUES (
                NULL, ?, ?, ?, ?,
                datetime('now', 'localtime'), ?
            )
        """, (
            bill_id,
            refund_session_id,
            amount,
            reason,
            payment_method
        ))

        cursor.execute("""
            UPDATE table_bills
            SET cancelled_at = datetime('now', 'localtime'),
                cancellation_reason = ?
            WHERE id = ?
              AND cancelled_at IS NULL
        """, (reason, bill_id))

        if cursor.rowcount != 1:
            raise ValueError("ثبت بازپرداخت ناموفق بود.")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()



def add_cancellation_fields_to_orders():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in cursor.fetchall()]

        if "cancelled_at" not in columns:
            cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN cancelled_at TEXT
            """)

        if "cancellation_reason" not in columns:
            cursor.execute("""
                ALTER TABLE orders
                ADD COLUMN cancellation_reason TEXT
            """)

        conn.commit()

    finally:
        conn.close()



def add_cancellation_fields_to_table_bills():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(table_bills)")
        columns = [row[1] for row in cursor.fetchall()]

        if "cancelled_at" not in columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN cancelled_at TEXT
            """)

        if "cancellation_reason" not in columns:
            cursor.execute("""
                ALTER TABLE table_bills
                ADD COLUMN cancellation_reason TEXT
            """)

        conn.commit()

    finally:
        conn.close()


def create_cafe_settings_table():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cafe_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cafe_name TEXT NOT NULL DEFAULT 'کافه',
                address TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT ''
            )
        """)

        cursor.execute("""
            INSERT OR IGNORE INTO cafe_settings
                (id, cafe_name, address, phone)
            VALUES (1, 'کافه', '', '')
        """)

        conn.commit()

    finally:
        conn.close()



def add_receipt_paper_width():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(cafe_settings)")
        columns = [row[1] for row in cursor.fetchall()]

        if "receipt_paper_width" not in columns:
            cursor.execute("""
                ALTER TABLE cafe_settings
                ADD COLUMN receipt_paper_width INTEGER
                NOT NULL DEFAULT 80
                CHECK (receipt_paper_width IN (58, 80))
            """)

        conn.commit()

    finally:
        conn.close()
        


def get_cafe_settings():
    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cafe_name, address, phone, receipt_paper_width
            FROM cafe_settings
            WHERE id = 1
        """)

        row = cursor.fetchone()

        if row is None:
            raise ValueError("تنظیمات کافه پیدا نشد.")

        return {
            "cafe_name": row[0],
            "address": row[1],
            "phone": row[2],
            "receipt_paper_width": row[3]
        }

    finally:
        conn.close()



def update_cafe_settings(cafe_name, address, phone, receipt_paper_width=80):
    cafe_name = cafe_name.strip()
    address = address.strip()
    phone = phone.strip()

    receipt_paper_width = int(receipt_paper_width)

    if not cafe_name:
        raise ValueError("نام کافه نمی‌تواند خالی باشد.")

    if receipt_paper_width not in (58, 80):
        raise ValueError("عرض کاغذ باید ۵۸ یا ۸۰ میلی‌متر باشد.")

    conn = connect()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE cafe_settings
            SET cafe_name = ?,
                address = ?,
                phone = ?,
                receipt_paper_width = ?
            WHERE id = 1
        """, (cafe_name, address, phone, receipt_paper_width))

        if cursor.rowcount != 1:
            raise ValueError("تنظیمات کافه پیدا نشد.")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
        

create_products_table()
create_cashier_sessions_table()
create_order_table()
create_order_items_table()
create_cafe_tables()

add_bill_id_to_orders()
add_payment_fields_to_table_bills()
add_payment_method_to_orders()
add_payment_method_to_table_bills()
add_cancellation_fields_to_orders()
add_cancellation_fields_to_table_bills()

create_refunds_table()
add_payment_method_to_refunds()
add_discount_fields()

create_cafe_settings_table()
add_receipt_paper_width()