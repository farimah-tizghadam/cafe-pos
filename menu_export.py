from database import get_products_with_categories
import json
from pathlib import Path

def get_menu_data():
    products = get_products_with_categories()

    menu_products = []

    for product_id, name, price, category in products:
        menu_products.append({
            "id": product_id,
            "name": name,
            "price": price,
            "category": category,
            "available": True
        })

    return {"products": menu_products}




def export_menu_json():
    menu_data = get_menu_data()

    output_path = Path(__file__).resolve().parent / "menu.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            menu_data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return output_path