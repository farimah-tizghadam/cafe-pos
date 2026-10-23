import tkinter as tk
from tkinter import ttk, messagebox

from database import get_cafe_settings, update_cafe_settings


def show_cafe_settings(parent):
    settings = get_cafe_settings()

    window = tk.Toplevel(parent)
    window.title("تنظیمات کافه")
    window.geometry("450x430")
    window.resizable(False, False)
    window.transient(parent)
    window.grab_set()

    frame = ttk.Frame(window, padding=25)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="تنظیمات کافه",
        font=("Tahoma", 16, "bold")
    ).pack(pady=(0, 20))

    ttk.Label(
        frame,
        text="نام کافه:"
    ).pack(anchor="e")

    cafe_name_entry = ttk.Entry(
        frame,
        font=("Tahoma", 11),
        justify="right"
    )
    cafe_name_entry.pack(fill="x", pady=(5, 12))
    cafe_name_entry.insert(0, settings["cafe_name"])

    ttk.Label(
        frame,
        text="آدرس:"
    ).pack(anchor="e")

    address_entry = ttk.Entry(
        frame,
        font=("Tahoma", 11),
        justify="right"
    )
    address_entry.pack(fill="x", pady=(5, 12))
    address_entry.insert(0, settings["address"])

    ttk.Label(
        frame,
        text="شماره تماس:"
    ).pack(anchor="e")

    phone_entry = ttk.Entry(
        frame,
        font=("Tahoma", 11),
        justify="right"
    )
    phone_entry.pack(fill="x", pady=(5, 20))
    phone_entry.insert(0, settings["phone"])
    ttk.Label(
        frame,
        text="عرض کاغذ رسید:"
    ).pack(anchor="e")

    paper_width_var = tk.StringVar(
        value=str(settings["receipt_paper_width"])
    )

    paper_width_combo = ttk.Combobox(
        frame,
        textvariable=paper_width_var,
        values=["58", "80"],
        state="readonly",
        font=("Tahoma", 11),
        justify="right"
    )
    paper_width_combo.pack(fill="x", pady=(5, 20))

    def save_settings():
        try:
            update_cafe_settings(
                cafe_name_entry.get(),
                address_entry.get(),
                phone_entry.get(),
                int(paper_width_var.get())

            )

            messagebox.showinfo(
                "ذخیره موفق",
                "تنظیمات کافه با موفقیت ذخیره شد.",
                parent=window
            )

            window.destroy()

        except Exception as error:
            messagebox.showerror(
                "خطا",
                str(error),
                parent=window
            )

    ttk.Button(
        frame,
        text="ذخیره تنظیمات",
        command=save_settings
    ).pack(fill="x")

    cafe_name_entry.focus_set()

    return window