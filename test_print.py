from printer import create_professional_receipt, print_receipt_image

receipt = {
    "cafe_name": "کافه حیات",
    "address": "تهران",
    "phone": "02166081622",
    "receipt_number": 1001,
    "date": "2026-10-22",
    "table_name": "",
    "items": [
        ("کاپوچینو", 2, 120000),
        ("کیک شکلاتی", 1, 95000),
    ],
    "subtotal": 335000,
    "discount": 35000,
    "total": 300000,
    "payment_method": "card",
}

image = create_professional_receipt(receipt, paper_width=80)

print("Sending test receipt to Microsoft Print to PDF...")

print_receipt_image(image, "Microsoft Print to PDF")

print("Print job completed.")