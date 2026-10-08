from database import (
    get_open_cashier_session,
    get_product,
    save_order,
    get_table_bill_details,
)

session_id = get_open_cashier_session()

if session_id is None:
    print("No cashier shift is open.")
    raise SystemExit

products = get_product()

if not products:
    print("No products found.")
    raise SystemExit

product_id, product_name, product_price = products[0]

print("Using product:")
print(product_id, product_name, product_price)

# First order for Table 1 / Bill 2
first_order_id = save_order(
    session_id,
    product_price,
    [
        {
            "product_id": product_id,
            "quantity": 1,
            "price": product_price,
        }
    ],
    bill_id=2,
)

print("First order ID:", first_order_id)
print("Bill after first order:")
print(get_table_bill_details(2))

# Customer orders the same product again later.
second_order_id = save_order(
    session_id,
    product_price,
    [
        {
            "product_id": product_id,
            "quantity": 1,
            "price": product_price,
        }
    ],
    bill_id=2,
)

print("Second order ID:", second_order_id)
print("Bill after second order:")
print(get_table_bill_details(2))