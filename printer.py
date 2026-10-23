import win32print


def get_installed_printers():
    flags = (
        win32print.PRINTER_ENUM_LOCAL
        | win32print.PRINTER_ENUM_CONNECTIONS
    )

    printers = win32print.EnumPrinters(flags)

    return sorted(
        {printer[2] for printer in printers}
    )


def get_default_printer():
    try:
        return win32print.GetDefaultPrinter()
    except Exception:
        return None


def show_printer_selection(parent):
    import tkinter as tk
    from tkinter import ttk, messagebox

    printers = get_installed_printers()

    if not printers:
        messagebox.showwarning(
            "چاپگر",
            "هیچ چاپگری در ویندوز پیدا نشد.",
            parent=parent
        )
        return None

    window = tk.Toplevel(parent)
    window.title("انتخاب چاپگر")
    window.geometry("400x180")
    window.transient(parent)
    window.grab_set()

    selected_printer = tk.StringVar(
        value=get_default_printer()
        if get_default_printer() in printers
        else printers[0]
    )

    ttk.Label(
        window,
        text="چاپگر مورد نظر را انتخاب کنید:"
    ).pack(pady=12)

    printer_combo = ttk.Combobox(
        window,
        textvariable=selected_printer,
        values=printers,
        state="readonly",
        width=45
    )
    printer_combo.pack(padx=15, pady=5)

    result = {"printer": None}

    def confirm():
        result["printer"] = selected_printer.get()
        window.destroy()

    ttk.Button(
        window,
        text="تأیید",
        command=confirm
    ).pack(pady=15)

    window.protocol("WM_DELETE_WINDOW", window.destroy)
    parent.wait_window(window)

    return result["printer"]



def create_receipt_image(receipt_text, paper_width=80):
    from PIL import Image, ImageDraw, ImageFont
    import arabic_reshaper
    from bidi.algorithm import get_display

    widths = {
        58: 384,
        80: 576,
        210: 1600
    }

    if paper_width not in widths:
        raise ValueError("اندازه کاغذ نامعتبر است.")

    width = widths[paper_width]

    font_size = 24 if paper_width != 210 else 40

    font = ImageFont.truetype(
        "C:/Windows/Fonts/tahoma.ttf",
        font_size
    )

    lines = receipt_text.splitlines()

    margin = 25
    line_height = font_size + 18

    height = max(
        200,
        len(lines) * line_height + margin * 2
    )

    image = Image.new(
        "RGB",
        (width, height),
        "white"
    )

    draw = ImageDraw.Draw(image)

    y = margin

    for line in lines:
        reshaped_text = arabic_reshaper.reshape(line)
        display_text = get_display(reshaped_text)

        draw.text(
            (width - margin, y),
            display_text,
            font=font,
            fill="black",
            anchor="ra"
        )

        y += line_height

    return image



def create_professional_receipt(details, paper_width=80):
    from PIL import Image, ImageDraw, ImageFont
    import arabic_reshaper
    from bidi.algorithm import get_display

    widths = {58: 384, 80: 576, 210: 1600}

    if paper_width not in widths:
        raise ValueError("اندازه کاغذ نامعتبر است.")

    width = widths[paper_width]
    margin = 25

    estimated_height = (
        950
        + len(details["items"]) * (150 if paper_width == 58 else 42)
        + (40 if details.get("address") else 0)
        + (40 if details.get("phone") else 0)
        + (38 if details.get("table_name") else 0)
    )

    image = Image.new("RGB", (width, estimated_height), "white")
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.truetype(
        "C:/Windows/Fonts/tahomabd.ttf", 36
    )
    normal_font = ImageFont.truetype(
        "C:/Windows/Fonts/tahoma.ttf", 23
    )

    def persian(text):
        return get_display(arabic_reshaper.reshape(str(text)))

    y = 30

    # Centered café name
    draw.text(
        (width // 2, y),
        persian(details["cafe_name"]),
        font=title_font,
        fill="black",
        anchor="mt"
    )
    y += 65

    # Centered address and phone
    for value in (details["address"], details["phone"]):
        if value:
            draw.text(
                (width // 2, y),
                persian(value),
                font=normal_font,
                fill="black",
                anchor="mt"
            )
            y += 40

       # Separator
    y += 15
    draw.line(
        (margin, y, width - margin, y),
        fill="black",
        width=2
    )

    y += 20

    # Receipt number and date
    info_lines = [
        f"شماره رسید: {details['receipt_number']}",
        f"تاریخ: {details['date']}"
    ]

    if details.get("table_name"):
        info_lines.append(f"میز: {details['table_name']}")

    for line in info_lines:
        draw.text(
            (width - margin, y),
            persian(line),
            font=normal_font,
            fill="black",
            anchor="ra"
        )
        y += 38

        # Product table
    y += 15
    draw.line(
        (margin, y, width - margin, y),
        fill="black",
        width=2
    )
    y += 18

    name_x = width - margin
    quantity_x = width // 2
    total_x = margin

    draw.text(
        (name_x, y),
        persian("نام محصول"),
        font=normal_font,
        fill="black",
        anchor="ra"
    )

    draw.text(
        (quantity_x, y),
        persian("تعداد"),
        font=normal_font,
        fill="black",
        anchor="ma"
    )

    draw.text(
        (total_x, y),
        persian("مبلغ کل"),
        font=normal_font,
        fill="black",
        anchor="la"
    )

    y += 40

    draw.line(
        (margin, y, width - margin, y),
        fill="black",
        width=1
    )
    y += 15

    def fit_product_font(name):
        max_width = name_x - quantity_x - 45

        for size in range(23, 13, -1):
            font = ImageFont.truetype(
                "C:/Windows/Fonts/tahoma.ttf",
                size
            )

            text = persian(name)

            if draw.textlength(text, font=font) <= max_width:
                return font

        return ImageFont.truetype(
            "C:/Windows/Fonts/tahoma.ttf",
            14
        )

    for name, quantity, price in details["items"]:
        item_total = quantity * price
        name_text = persian(name)

        if paper_width == 58:
            # Show the product name on a separate line.
            # Split long names into lines that fit the paper.
            words = str(name).split()
            lines = []
            current_line = ""

            for word in words:
                candidate = f"{current_line} {word}".strip()

                if (
                    current_line
                    and draw.textlength(
                        persian(candidate), font=normal_font
                    ) > width - 2 * margin
                ):
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = candidate

            if current_line:
                lines.append(current_line)

            for line in lines:
                draw.text(
                    (name_x, y),
                    persian(line),
                    font=normal_font,
                    fill="black",
                    anchor="ra"
                )
                y += 35

            draw.text(
                (quantity_x, y),
                str(quantity),
                font=normal_font,
                fill="black",
                anchor="ma"
            )

            draw.text(
                (total_x, y),
                f"{item_total:,}",
                font=normal_font,
                fill="black",
                anchor="la"
            )

            y += 42

        else:
            draw.text(
                (name_x, y),
                name_text,
                font=fit_product_font(name),
                fill="black",
                anchor="ra"
            )

            draw.text(
                (quantity_x, y),
                str(quantity),
                font=normal_font,
                fill="black",
                anchor="ma"
            )

            draw.text(
                (total_x, y),
                f"{item_total:,}",
                font=normal_font,
                fill="black",
                anchor="la"
            )

            y += 42

        # Payment summary
    y += 15

    draw.line(
        (margin, y, width - margin, y),
        fill="black",
        width=2
    )
    y += 20

    payment_names = {
        "cash": "نقدی",
        "card": "کارت"
    }

    summary_lines = [
        ("جمع اولیه", details["subtotal"]),
        ("تخفیف", details["discount"]),
        ("مبلغ پرداختی", details["total"])
    ]

    for label, amount in summary_lines:
        is_total = label == "مبلغ پرداختی"

        if is_total and paper_width == 58:
            font = ImageFont.truetype(
                "C:/Windows/Fonts/tahomabd.ttf",
                23
            )
        else:
            font = title_font if is_total else normal_font


        draw.text(
            (width - margin, y),
            persian(label),
            font=font,
            fill="black",
            anchor="ra"
        )

        draw.text(
            (margin, y),
            f"{amount:,}",
            font=font,
            fill="black",
            anchor="la"
        )

        y += 55 if is_total else 40

    draw.text(
        (width - margin, y),
        persian("واحد مبالغ: تومان"),
        font=normal_font,
        fill="black",
        anchor="ra"
    )
    y += 40

    payment_method = payment_names.get(
        details["payment_method"],
        "نامشخص"
    )

    draw.text(
        (width - margin, y),
        persian(f"روش پرداخت: {payment_method}"),
        font=normal_font,
        fill="black",
        anchor="ra"
    )

    y += 50

    draw.line(
        (margin, y, width - margin, y),
        fill="black",
        width=2
    )

    y += 20

    draw.text(
        (width // 2, y),
        persian("از خرید شما سپاسگزاریم"),
        font=normal_font,
        fill="black",
        anchor="mt"
    )


    final_height = min(image.height, y + 65)

    return image.crop((0, 0, width, final_height))



def print_receipt_image(image, printer_name):
    import win32ui
    from PIL import ImageWin

    printer_dc = win32ui.CreateDC()
    printer_dc.CreatePrinterDC(printer_name)

    try:
        printer_dc.StartDoc("Cafe POS Receipt")
        printer_dc.StartPage()

        # Get the printable area in printer pixels
        printable_width = printer_dc.GetDeviceCaps(8)
        printable_height = printer_dc.GetDeviceCaps(10)

        # Scale the image to fit the printable page width
        scale = min(
            printable_width / image.width,
            printable_height / image.height
        )

        output_width = round(image.width * scale)
        output_height = round(image.height * scale)
        dib = ImageWin.Dib(image.convert("RGB"))

        dib.draw(
            printer_dc.GetHandleOutput(),
            (0, 0, printable_width, output_height)
        )

        printer_dc.EndPage()
        printer_dc.EndDoc()

    finally:
        printer_dc.DeleteDC()