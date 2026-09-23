
import tkinter as tk
from tkinter import ttk, messagebox

from database import (
    get_product,
    add_products,
    update_product_price,
    delete_product,
)


class ProductManagement(tk.Toplevel):
    def __init__(self, parent, on_close=None):
        super().__init__(parent)

        self.title("مدیریت محصولات")
        self.geometry("850x700")
        self.minsize(750, 650)
        self.configure(bg="#f4f5f7")

        self.on_close = on_close
        self.products = []

        # Keep this window above the main POS window.
        self.transient(parent)
        self.grab_set()

        self.build_interface()
        self.refresh_products()

        self.protocol("WM_DELETE_WINDOW", self.close_window)

    def build_interface(self):
        # Page title
        tk.Label(
            self,
            text="مدیریت محصولات کافه",
            font=("Tahoma", 18, "bold"),
            bg="#f4f5f7",
            fg="#172554"
        ).pack(pady=20)

        # Product form
        form = tk.LabelFrame(
            self,
            text="افزودن محصول جدید",
            font=("Tahoma", 12, "bold"),
            bg="white",
            padx=15,
            pady=15
        )
        form.pack(fill="x", padx=20, pady=10)

        tk.Label(
            form,
            text="نام محصول:",
            font=("Tahoma", 11),
            bg="white"
        ).grid(row=0, column=3, padx=8, pady=8)

        self.name_entry = ttk.Entry(
            form,
            font=("Tahoma", 11),
            justify="right",
            width=25
        )
        self.name_entry.grid(
            row=0, column=2, padx=8, pady=8
        )

        tk.Label(
            form,
            text="قیمت (تومان):",
            font=("Tahoma", 11),
            bg="white"
        ).grid(row=1, column=3, padx=8, pady=8)

        self.price_entry = ttk.Entry(
            form,
            font=("Tahoma", 11),
            justify="right",
            width=25
        )
        self.price_entry.grid(
            row=1, column=2, padx=8, pady=8
        )

        ttk.Button(
            form,
            text="افزودن محصول",
            command=self.add_product
        ).grid(
            row=2,
            column=2,
            pady=12,
            sticky="e"
        )

        # Existing products
        list_frame = tk.LabelFrame(
            self,
            text="محصولات فعال",
            font=("Tahoma", 12, "bold"),
            bg="white",
            padx=15,
            pady=15
        )
        list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        self.product_list = tk.Listbox(
            list_frame,
            font=("Tahoma", 12),
            justify="right",
            height=8
        )
        self.product_list.pack(
            fill="both",
            expand=True
        )

        # Edit selected product
        edit_frame = tk.Frame(
            self,
            bg="#f4f5f7"
        )
        edit_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(
            edit_frame,
            text="قیمت جدید:",
            font=("Tahoma", 11),
            bg="#f4f5f7"
        ).pack(side="right", padx=5)

        self.new_price_entry = ttk.Entry(
            edit_frame,
            font=("Tahoma", 11),
            justify="right",
            width=15
        )
        self.new_price_entry.pack(
            side="right", padx=5
        )

        ttk.Button(
            edit_frame,
            text="تغییر قیمت",
            command=self.change_price
        ).pack(side="right", padx=5)

        ttk.Button(
            edit_frame,
            text="غیرفعال کردن محصول",
            command=self.deactivate_product
        ).pack(side="left", padx=5)

    def refresh_products(self):
        self.products = get_product()

        self.product_list.delete(0, tk.END)

        for product_id, name, price in self.products:
            self.product_list.insert(
                tk.END,
                f"{name} | {price:,} تومان"
            )

    def get_selected_product(self):
        selected = self.product_list.curselection()

        if not selected:
            messagebox.showwarning(
                "انتخاب محصول",
                "لطفاً ابتدا یک محصول انتخاب کنید.",
                parent=self
            )
            return None

        return self.products[selected[0]]

    def parse_price(self, entry):
        text = entry.get().strip().replace(",", "")

        try:
            price = int(text)
        except ValueError:
            messagebox.showerror(
                "قیمت نامعتبر",
                "قیمت باید یک عدد صحیح باشد.",
                parent=self
            )
            return None

        if price <= 0:
            messagebox.showerror(
                "قیمت نامعتبر",
                "قیمت باید بیشتر از صفر باشد.",
                parent=self
            )
            return None

        return price

    def add_product(self):
        name = self.name_entry.get().strip()
        price = self.parse_price(self.price_entry)

        if not name:
            messagebox.showwarning(
                "نام محصول",
                "نام محصول را وارد کنید.",
                parent=self
            )
            return

        if price is None:
            return

        try:
            add_products(name, price)
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"محصول اضافه نشد:\n{error}",
                parent=self
            )
            return

        self.name_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)

        self.refresh_products()

        messagebox.showinfo(
            "موفقیت",
            "محصول جدید اضافه شد.",
            parent=self
        )

    def change_price(self):
        product = self.get_selected_product()

        if product is None:
            return

        product_id, name, old_price = product
        new_price = self.parse_price(
            self.new_price_entry
        )

        if new_price is None:
            return

        confirmed = messagebox.askyesno(
            "تأیید تغییر قیمت",
            f"محصول: {name}\n"
            f"قیمت قبلی: {old_price:,} تومان\n"
            f"قیمت جدید: {new_price:,} تومان\n\n"
            "آیا قیمت تغییر کند؟",
            parent=self
        )

        if not confirmed:
            return

        try:
            update_product_price(
                product_id,
                new_price
            )
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"قیمت تغییر نکرد:\n{error}",
                parent=self
            )
            return

        self.new_price_entry.delete(0, tk.END)
        self.refresh_products()

        messagebox.showinfo(
            "موفقیت",
            "قیمت محصول تغییر کرد.",
            parent=self
        )

    def deactivate_product(self):
        product = self.get_selected_product()

        if product is None:
            return

        product_id, name, price = product

        confirmed = messagebox.askyesno(
            "غیرفعال کردن محصول",
            f"آیا محصول «{name}» غیرفعال شود؟\n\n"
            "سوابق فروش قبلی حفظ خواهند شد.",
            parent=self
        )

        if not confirmed:
            return

        try:
            delete_product(product_id)
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"محصول غیرفعال نشد:\n{error}",
                parent=self
            )
            return

        self.refresh_products()

        messagebox.showinfo(
            "موفقیت",
            "محصول غیرفعال شد.",
            parent=self
        )

    def close_window(self):
        if self.on_close is not None:
            self.on_close()

        self.destroy()