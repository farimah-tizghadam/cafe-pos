from database import (
    get_product, 
    add_products, 
    delete_product, 
    update_product_price,
    open_cashier_session,
    close_cashier_session,
    get_open_cashier_session,
    save_order
    )


def show_menu(products):
    product_list= {}

    print("\n----- menu -----")

    for product in products:
        product_id = product[0]
        name = product[1]
        price = product[2]

        product_list[name] = {
            "id": product_id,
            "price": price
        }

        print(f"{name}: {price:,} Toman")

    return product_list



def calculate_total(price, quantity):
    return price * quantity



def print_receipt(grand_total_price, orders):
    print("\n----- Receipt -----")
    for order in orders:
        print(
            f"Product: {order['product']}\n"
            f"Price: {order['price']:,}\n"
            f"Quantity: {order['quantity']}\n"
            f"Total={order['total']:,}\n"
        )
    print("-----------------")
    print(f"Grand Total: {grand_total_price:,} Toman")



def get_positive_integer(message):
    while True:
        try:
            user_input = int(input(message))
            if user_input <= 0:
                print("input can't be 0 or less")
                continue

            return user_input

        except ValueError:
            print("please enter a valid number")



def cafe_management():
    print("====== cafe management ======")
    print(
            f"1. Show Products\n"
            f"2. Add Product\n"
            f"3. Update Product Price\n"
            f"4. Delete Product\n"
            f"5. Open Cashier\n"
            f"6. Close Cashier\n"
            f"7. Exit\n"
        )



def find_product_id(products, user_product_input):
    for product in products:
        if product[1].strip().lower() == user_product_input:
            return product[0]
            
    return None



def get_yes_no(message):

    while True:

        user_answer = input(message).strip().lower()

        if user_answer in ('yes', 'no'):
            return user_answer

        print("answer should be yes/no!")




def create_order():
    grand_total_price = 0
    orders = []
    session_id = get_open_cashier_session()

    if session_id is None:
        print("Please open the cashier before creating an order.")
        return

    products = get_product()
    product_list = show_menu(products)
    
    while True:
        product_name = input("choose a product: ").strip().lower()
        if product_name not in product_list:
            print("please choose a product from list")
            continue

        quantity = get_positive_integer("Enter quantity: ")
        price = product_list[product_name]["price"]
        product_id = product_list[product_name]["id"]

        total_price = calculate_total(price, quantity)
        grand_total_price += total_price


        print("\n----- Order -----")
        print(f"product name: {product_name}")
        print(f"price: {price:,}")
        print(f"quantity: {quantity}")
        print(f"Total: {total_price:,}")

        orders.append({
            "product_id": product_id,
            "product": product_name,
            "quantity": quantity,
            "price": price,
            "total": total_price,
        })

        another_product = get_yes_no("add another product? (yes/no): ")
        if another_product == "no":
            break
    save_order(session_id, grand_total_price, orders)
    print_receipt(grand_total_price,  orders)





def add_new_product():
    products = get_product()
    new_product = input("enter new product: ").strip().lower()
    duplicated_product = find_product_id(products, new_product)
    if duplicated_product is not None:
        print("Duplicate product")
    else:
        price = get_positive_integer("Enter price: ")
        add_products(new_product, price)
        print("new product added successfully.")


    
def update_existed_product():
    user_input = input("enter product name: ").strip().lower()
    products = get_product()
    product_id = find_product_id(products, user_input)

    if product_id is None:
        print("product doesn't exist!")
    else:
        validated_price = get_positive_integer(f"Enter new price for {user_input}: ")
        update_product_price(product_id, validated_price)
        print(f"price updated successfully for {user_input}")



def delete_existed_product():
    user_product_input = input("enter product: ").strip().lower()
    products = get_product()
    product_id = find_product_id(products, user_product_input)
    if product_id is None:
        print("product doesn't exist")
    else:
        delete_confirm = get_yes_no(f"Are you sure you want to delete {user_product_input}? yes/no: ")
        if delete_confirm == "yes":
            delete_product(product_id)
            print("product deleted successfully")
        elif delete_confirm == "no":
            print("Delete cancelled")


def main():

    while True:   
        cafe_management()
        option = input("choose: ")
        

        if option == "1":
           
           create_order()

        elif option == "2":
           
           add_new_product() 

        elif option == "3":
           
           update_existed_product()     
        
        elif option == "4":
            delete_existed_product()

        elif option == "5":
            open_cashier_session()

        elif option == "6":
            close_cashier_session()

        elif option == "7":
            print("exit")
            break

        else:
            print("invalid option")


if __name__ == "__main__":
    main()

