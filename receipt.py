import tkinter as tk
from tkinter import ttk, messagebox
from database import get_cafe_settings
from printer import (
    create_professional_receipt,
    show_printer_selection,
    print_receipt_image
)
from PIL import Image, ImageTk



def show_receipt_preview(parent, receipt_text, receipt_data=None):
    window = tk.Toplevel(parent)
    window.title("پیش‌نمایش رسید")
    window.geometry("400x550")
    window.minsize(320, 400)
    window.transient(parent)

    settings = get_cafe_settings()
    
    if receipt_data is not None:
        details = get_receipt_details(receipt_data)
        image = create_professional_receipt(
            details,
            paper_width=settings["receipt_paper_width"]
        )
    # Show the separate café heading only for the old text preview
    if receipt_data is None:
        tk.Label(
            window,
            text=settings["cafe_name"],
            font=("Tahoma", 18, "bold")
        ).pack(pady=15)

    # Container for receipt and scrollbar
    receipt_frame = ttk.Frame(window)
    receipt_frame.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    scrollbar = ttk.Scrollbar(
        receipt_frame,
        orient="vertical"
    )
    scrollbar.pack(side="right", fill="y")

    
    if receipt_data is not None:
        # Resize the professional receipt to fit the preview window
        preview_width = 340

        if image.width > preview_width:
            preview_height = round(
                image.height * preview_width / image.width
            )

            image = image.resize(
                (preview_width, preview_height),
                Image.Resampling.LANCZOS
            )

        receipt_box = tk.Canvas(
            receipt_frame,
            bg="white",
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )

        receipt_box.pack(
            side="left",
            fill="both",
            expand=True
        )

        photo = ImageTk.PhotoImage(image)

        receipt_box.create_image(
            0, 0,
            image=photo,
            anchor="nw"
        )

        receipt_box.configure(
            scrollregion=(0, 0, image.width, image.height)
        )

        # Keep the image visible in Tkinter
        receipt_box.image = photo

    else:
        # Keep the original text preview as a fallback
        receipt_box = tk.Text(
            receipt_frame,
            font=("Tahoma", 11),
            wrap="word",
            padx=15,
            pady=15,
            yscrollcommand=scrollbar.set
        )

        receipt_box.pack(
            side="left",
            fill="both",
            expand=True
        )

        receipt_box.tag_configure(
            "right",
            justify="right",
            spacing1=3,
            spacing3=3
        )

        receipt_box.insert("1.0", receipt_text, "right")
        receipt_box.config(state="disabled")
        
    scrollbar.config(command=receipt_box.yview)
    def print_receipt():
        if receipt_data is None:
            messagebox.showwarning(
                "چاپ رسید",
                "اطلاعات لازم برای چاپ رسید موجود نیست.",
                parent=window
            )
            return

        printer_name = show_printer_selection(window)

        if printer_name is None:
            return

        try:
            # Create a full-resolution image for printing.
            # Do not print the smaller preview image.
            print_image = create_professional_receipt(
                details,
                paper_width=settings["receipt_paper_width"]
            )

            print_receipt_image(print_image, printer_name)

            messagebox.showinfo(
                "چاپ رسید",
                "رسید به چاپگر ارسال شد.",
                parent=window
            )

        except Exception as error:
            messagebox.showerror(
                "خطای چاپ",
                str(error),
                parent=window
            )
        
    # Buttons below the receipt preview
    button_frame = ttk.Frame(window)
    button_frame.pack(pady=15)

    ttk.Button(
        button_frame,
        text="چاپ رسید",
        command=print_receipt
    ).pack(side="right", padx=5)

    ttk.Button(
        button_frame,
        text="بستن",
        command=window.destroy
    ).pack(side="left", padx=5)

    return window



def format_receipt(receipt):
    settings = get_cafe_settings()
    def money(amount):
        return f"{amount:,}"

    payment_names = {
        "cash": "نقدی",
        "card": "کارت"
    }

    lines = [
        settings["cafe_name"],
    ]

    if settings["address"]:
        lines.append(settings["address"])

    if settings["phone"]:
        lines.append(f'تلفن: {settings["phone"]}')

    lines.extend([
        "────────────────────",
        f"شماره رسید: {receipt['receipt_number']}",
        f"تاریخ: {receipt['date']}"
    ])


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



def get_receipt_details(receipt):
    settings = get_cafe_settings()

    return {
        "cafe_name": settings["cafe_name"],
        "address": settings["address"],
        "phone": settings["phone"],
        "receipt_number": receipt["receipt_number"],
        "date": receipt["date"],
        "table_name": receipt.get("table_name", ""),
        "items": receipt["items"],
        "subtotal": receipt["subtotal"],
        "discount": receipt["discount"],
        "total": receipt["total"],
        "payment_method": receipt["payment_method"],
    }