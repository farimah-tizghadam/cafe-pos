import tkinter as tk
from tkinter import ttk


def show_receipt_preview(parent, receipt_text):
    window = tk.Toplevel(parent)
    window.title("پیش‌نمایش رسید")
    window.geometry("400x550")
    window.minsize(320, 400)
    window.transient(parent)

    tk.Label(
        window,
        text="رسید فروش کافه",
        font=("Tahoma", 17, "bold")
    ).pack(pady=15)

    receipt_box = tk.Text(
        window,
        font=("Tahoma", 11),
        wrap="word",
        padx=15,
        pady=15,
        state="normal"
    )
    receipt_box.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    receipt_box.tag_configure(
    "right",
    justify="right",
    spacing1=3,
    spacing3=3

    )

    receipt_box.insert("1.0", receipt_text, "right")
    receipt_box.config(state="disabled")

    ttk.Button(
        window,
        text="بستن",
        command=window.destroy
    ).pack(pady=15)

    return window



def format_receipt(receipt):
    def money(amount):
        return f"{amount:,}"

    payment_names = {
        "cash": "نقدی",
        "card": "کارت"
    }

    lines = [
        "رسید فروش کافه",
        "────────────────────",
        f"شماره رسید: {receipt['receipt_number']}",
        f"تاریخ: {receipt['date']}"
    ]

    if receipt.get("table_name"):
        lines.append(f"میز: {receipt['table_name']}")

    lines.extend([
        "────────────────────",
        "اقلام سفارش"
    ])

    for name, quantity, price in receipt["items"]:
        item_total = quantity * price

        lines.extend([
            "",
            f"{name}",
            f"تعداد: {quantity}",
            f"قیمت واحد: {money(price)}",
            f"جمع کالا: {money(item_total)}"
        ])

    lines.extend([
        "",
        "────────────────────",
        f"جمع اولیه: {money(receipt['subtotal'])}",
        f"تخفیف: {money(receipt['discount'])}",
        f"مبلغ پرداختی: {money(receipt['total'])}",
        "واحد مبالغ: تومان",
        f"روش پرداخت: {payment_names.get(receipt['payment_method'], 'نامشخص')}",
        "────────────────────",
        "از خرید شما سپاسگزاریم"
    ])

    return "\n".join(lines)