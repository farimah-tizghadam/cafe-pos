
import tkinter as tk
from tkinter import ttk, messagebox

from database import (
    get_product,
    get_open_cashier_session,
    open_cashier_session,
    close_cashier_session,
    get_current_session_orders,
    save_order,
)

from product_management import ProductManagement


class CafePOS:
    def __init__(self, root):
        self.root = root
        self.root.title("صندوق فروش کافه")
        self.root.geometry("1050x680")
        self.root.minsize(850, 550)

        self.products = []
        self.cart = []

        self.setup_style()
        self.build_interface()
        self.update_status()
        self.load_products()

    def setup_style(self):
        self.root.configure(bg="#f4f5f7")

        style = ttk.Style()
        style.configure(
            "TButton",
            font=("Tahoma", 11),
            padding=8
        )
        style.configure(
            "TLabel",
            font=("Tahoma", 11)
        )

    def build_interface(self):
        # Header
        header = tk.Frame(
            self.root,
            bg="#172554",
            height=90
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="صندوق فروش کافه",
            bg="#172554",
            fg="white",
            font=("Tahoma", 20, "bold")
        ).pack(side="right", padx=25, pady=20)

        self.status_label = tk.Label(
            header,
            bg="#172554",
            fg="#bbf7d0",
            font=("Tahoma", 11)
        )
        self.status_label.pack(
            side="left", padx=25, pady=25
        )

        # Cashier controls
        controls = tk.Frame(
            self.root,
            bg="#f4f5f7"
        )
        controls.pack(fill="x", padx=20, pady=15)

        ttk.Button(
            controls,
            text="باز کردن صندوق",
            command=self.open_cashier
        ).pack(side="right", padx=5)

        ttk.Button(
            controls,
            text="بستن صندوق",
            command=self.close_cashier
        ).pack(side="right", padx=5)

        ttk.Button(
            controls,
            text="مدیریت محصولات",
            command=self.open_product_management
        ).pack(side="right", padx=5)

        # Main content
        content = tk.Frame(
            self.root,
            bg="#f4f5f7"
        )
        content.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        # Products on the right
        products_panel = tk.LabelFrame(
            content,
            text="محصولات",
            font=("Tahoma", 13, "bold"),
            bg="white",
            padx=15,
            pady=15
        )
        products_panel.pack(
            side="right",
            fill="both",
            expand=True,
            padx=8
        )

        self.products_frame = tk.Frame(
            products_panel,
            bg="white"
        )
        self.products_frame.pack(
            fill="both",
            expand=True
        )

        # Cart on the left
        cart_panel = tk.LabelFrame(
            content,
            text="سبد خرید",
            font=("Tahoma", 13, "bold"),
            bg="white",
            padx=15,
            pady=15
        )
        cart_panel.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8
        )

        self.cart_list = tk.Listbox(
            cart_panel,
            font=("Tahoma", 12),
            justify="right",
            height=14
        )
        self.cart_list.pack(
            fill="both",
            expand=True,
            pady=10
        )

        ttk.Button(
            cart_panel,
            text="حذف محصول انتخاب‌شده",
            command=self.remove_from_cart
        ).pack(fill="x", pady=5)

        self.total_label = tk.Label(
            cart_panel,
            text="مبلغ کل: ۰ تومان",
            bg="white",
            fg="#172554",
            font=("Tahoma", 15, "bold")
        )
        self.total_label.pack(pady=15)

        tk.Button(
            cart_panel,
            text="ثبت سفارش",
            command=self.checkout,
            bg="#15803d",
            fg="white",
            activebackground="#166534",
            activeforeground="white",
            font=("Tahoma", 13, "bold"),
            relief="flat",
            pady=12
        ).pack(fill="x")

    def update_status(self):
        session_id = get_open_cashier_session()

        if session_id is None:
            self.status_label.config(
                text="صندوق بسته است",
                fg="#fecaca"
            )
        else:
            self.status_label.config(
                text=f"صندوق باز است | شیفت {session_id}",
                fg="#bbf7d0"
            )

    def load_products(self):
        self.products = get_product()

        for widget in self.products_frame.winfo_children():
            widget.destroy()

        for index, product in enumerate(self.products):
            product_id, name, price = product

            button = tk.Button(
                self.products_frame,
                text=f"{name}\n{price:,} تومان",
                font=("Tahoma", 12),
                bg="#e2e8f0",
                fg="#172554",
                relief="flat",
                height=3,
                command=lambda p=product: self.add_to_cart(p)
            )

            row = index // 3
            column = 2 - (index % 3)

            button.grid(
                row=row,
                column=column,
                padx=6,
                pady=6,
                sticky="nsew"
            )

        for column in range(3):
            self.products_frame.grid_columnconfigure(
                column,
                weight=1
            )

    def add_to_cart(self, product):
        if get_open_cashier_session() is None:
            messagebox.showwarning(
                "صندوق",
                "ابتدا صندوق را باز کنید."
            )
            return

        product_id, name, price = product

        # Increase quantity if product is already in cart.
        for item in self.cart:
            if item["product_id"] == product_id:
                item["quantity"] += 1
                self.refresh_cart()
                return

        self.cart.append({
            "product_id": product_id,
            "name": name,
            "price": price,
            "quantity": 1
        })

        self.refresh_cart()

    def refresh_cart(self):
        self.cart_list.delete(0, tk.END)

        total = 0

        for item in self.cart:
            item_total = item["price"] * item["quantity"]
            total += item_total

            self.cart_list.insert(
                tk.END,
                f'{item["name"]} × {item["quantity"]}'
                f'  |  {item_total:,} تومان'
            )

        self.total_label.config(
            text=f"مبلغ کل: {total:,} تومان"
        )

    def remove_from_cart(self):
        selected = self.cart_list.curselection()

        if not selected:
            messagebox.showwarning(
                "سبد خرید",
                "ابتدا یک محصول انتخاب کنید."
            )
            return

        self.cart.pop(selected[0])
        self.refresh_cart()

    def checkout(self):
        session_id = get_open_cashier_session()

        if session_id is None:
            messagebox.showwarning(
                "صندوق",
                "ابتدا صندوق را باز کنید."
            )
            return

        if not self.cart:
            messagebox.showwarning(
                "سبد خرید",
                "سبد خرید خالی است."
            )
            return

        total = sum(
            item["price"] * item["quantity"]
            for item in self.cart
        )

        confirmed = messagebox.askyesno(
            "تأیید سفارش",
            f"مبلغ سفارش: {total:,} تومان\n\n"
            "آیا سفارش ثبت شود؟"
        )

        if not confirmed:
            return

        try:
            save_order(session_id, total, self.cart)
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"سفارش ثبت نشد:\n{error}"
            )
            return

        self.cart.clear()
        self.refresh_cart()

        messagebox.showinfo(
            "ثبت موفق",
            f"سفارش با موفقیت ثبت شد.\n"
            f"مبلغ: {total:,} تومان"
        )

    def open_cashier(self):
        if get_open_cashier_session() is not None:
            messagebox.showwarning(
                "صندوق",
                "صندوق از قبل باز است."
            )
            return

        open_cashier_session()
        self.update_status()

    def close_cashier(self):
        session_id = get_open_cashier_session()

        if session_id is None:
            messagebox.showwarning(
                "صندوق",
                "هیچ صندوق بازی وجود ندارد."
            )
            return

        if self.cart:
            messagebox.showwarning(
                "سبد خرید",
                "ابتدا سفارش فعلی را ثبت یا حذف کنید."
            )
            return

        orders = get_current_session_orders()
        total = sum(order[1] for order in orders)

        confirmed = messagebox.askyesno(
            "گزارش پایان شیفت",
            f"شماره شیفت: {session_id}\n"
            f"تعداد سفارش‌ها: {len(orders)}\n"
            f"مجموع فروش: {total:,} تومان\n\n"
            "آیا صندوق بسته شود؟"
        )

        if confirmed:
            close_cashier_session()
            self.update_status()

    def open_product_management(self):
        ProductManagement(
            self.root,
            on_close=self.load_products
    )        


if __name__ == "__main__":
    root = tk.Tk()
    app = CafePOS(root)
    root.mainloop()