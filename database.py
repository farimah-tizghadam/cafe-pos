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
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        (name, price)
    )

    connection.commit()
    connection.close()




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



def save_order(session_id, total, items):
    connection = connect()
    cursor = connection.cursor()

    created_at = datetime.now()

    cursor.execute(
        """
        INSERT INTO orders (session_id, total, created_at) VALUES (?, ?, ?)

        """,
        (session_id, total, created_at)
    )

    order_id = cursor.lastrowid

    for item in items:
        cursor.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
            """,
            (
                order_id,
                item["product_id"],
                item["quantity"],
                item["price"]
            )
        )


    connection.commit()
    connection.close()

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



create_products_table()
create_cashier_sessions_table()
create_order_table()
create_order_items_table()
