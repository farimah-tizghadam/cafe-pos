import sqlite3
from datetime import datetime

def connect():
    connection = sqlite3.connect("cafe.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection



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



def save_order(
        session_id,
        total,
        items,
        bill_id=None,
        payment_method=None
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
        calculated_total = 0

        for item in items:
            quantity = item["quantity"]
            price = item["price"]

            if quantity <= 0 or price < 0:
                raise ValueError("Invalid quantity or price.")

            calculated_total += quantity * price

        if calculated_total != total:
            raise ValueError("Order total does not match.")

        # Save the order.
        cursor.execute(
            """
            INSERT INTO orders (
                session_id, 
                total, 
                created_at,
                bill_id,
                payment_method
            )
            VALUES (?, ?, datetime('now', 'localtime'), ?, ?)
            """,
            (
                session_id,
                total,
                bill_id,
                payment_method
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
                COALESCE(SUM(o.total), 0) AS total,
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
                COALESCE(SUM(o.total), 0) AS total,
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



def close_table_bill(bill_id, session_id, payment_method):
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

        # Close the bill and record payment information.
        cursor.execute(
            """
            UPDATE table_bills
            SET status = 'closed',
                closed_at = datetime('now', 'localtime'),
                paid_at = datetime('now', 'localtime'),
                paid_session_id = ?,
                payment_method = ?
            WHERE id = ?
            AND status = 'open'
            """,
            (session_id, payment_method, bill_id)
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "این صورتحساب وجود ندارد یا قبلاً بسته شده است."
            )

        conn.commit()

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



create_products_table()
create_cashier_sessions_table()
create_order_table()
create_order_items_table()
create_cafe_tables()

add_bill_id_to_orders()
add_payment_fields_to_table_bills()
add_payment_method_to_orders()
add_payment_method_to_table_bills()