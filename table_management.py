import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from database import (
    add_cafe_table,
    get_all_cafe_tables,
    rename_cafe_table,
    set_cafe_table_active,
)


def show_table_management(parent):
    window = tk.Toplevel(parent)
    window.title("تنظیمات میزها")
    window.geometry("540x470")
    window.minsize(450, 350)
    window.transient(parent)

    frame = ttk.Frame(window, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="مدیریت میزهای کافه",
        font=("Tahoma", 16, "bold")
    ).pack(pady=(0, 15))

    columns = ("name", "status", "bill")

    tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings",
        selectmode="browse"
    )

    tree.heading("name", text="نام میز")
    tree.heading("status", text="وضعیت")
    tree.heading("bill", text="صورتحساب")

    tree.column("name", width=180, anchor="center")
    tree.column("status", width=110, anchor="center")
    tree.column("bill", width=120, anchor="center")

    tree.pack(fill="both", expand=True)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)

        for table_id, name, is_active, open_bill_id in get_all_cafe_tables():
            status = "فعال" if is_active else "غیرفعال"
            bill = "باز" if open_bill_id is not None else "ندارد"

            tree.insert(
                "",
                "end",
                iid=str(table_id),
                values=(name, status, bill)
            )

    def selected_table():
        selection = tree.selection()

        if not selection:
            messagebox.showwarning(
                "انتخاب میز",
                "ابتدا یک میز را انتخاب کنید.",
                parent=window
            )
            return None

        return int(selection[0])

    def add_table():
        name = simpledialog.askstring(
            "افزودن میز",
            "نام میز جدید:",
            parent=window
        )

        if name is None:
            return

        try:
            add_cafe_table(name)
            refresh()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                str(error),
                parent=window
            )

    def rename_table():
        table_id = selected_table()

        if table_id is None:
            return

        old_name = tree.item(str(table_id), "values")[0]

        new_name = simpledialog.askstring(
            "تغییر نام میز",
            "نام جدید میز:",
            initialvalue=old_name,
            parent=window
        )

        if new_name is None:
            return

        try:
            rename_cafe_table(table_id, new_name)
            refresh()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                str(error),
                parent=window
            )

    def change_status(is_active):
        table_id = selected_table()

        if table_id is None:
            return

        try:
            set_cafe_table_active(table_id, is_active)
            refresh()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                str(error),
                parent=window
            )

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=15)

    ttk.Button(
        buttons,
        text="افزودن میز",
        command=add_table
    ).pack(side="right", padx=4)

    ttk.Button(
        buttons,
        text="تغییر نام",
        command=rename_table
    ).pack(side="right", padx=4)

    ttk.Button(
        buttons,
        text="غیرفعال کردن",
        command=lambda: change_status(0)
    ).pack(side="right", padx=4)

    ttk.Button(
        buttons,
        text="فعال کردن",
        command=lambda: change_status(1)
    ).pack(side="right", padx=4)

    ttk.Button(
        frame,
        text="بستن",
        command=window.destroy
    ).pack(pady=5)

    refresh()

    return window