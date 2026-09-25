import tkinter as tk
from tkinter import ttk, messagebox

from database import (
    get_open_cashier_session,
    get_current_session_orders,
    get_order_items
)


class SalesReport(tk.Toplevel):
    
    def __init__(self, parent):
        super().__init__(parent)

        self.title("گزارش فروش")
        self.geometry("900x650")
        self.minsize(750, 550)
        self.configure(bg="#f4f5f7")

        self.transient(parent)
        self.grab_set()

        self.build_interface()
        self.refresh_report()


    def build_interface(self):
        # Title
        tk.Label(
            self,
            text="گزارش فروش شیفت جاری",
            font=("Tahoma", 19, "bold"),
            bg="#f4f5f7",
            fg="#172554"
        ).pack(pady=15)

        self.session_label = tk.Label(
            self,
            text="",
            font=("Tahoma", 11),
            bg="#f4f5f7"
        )
        self.session_label.pack()

        self.summary_label = tk.Label(
            self,
            text="",
            font=("Tahoma", 13, "bold"),
            bg="#f4f5f7",
            fg="#15803d"
        )
        self.summary_label.pack(pady=10)

        # Orders table
        orders_frame = ttk.LabelFrame(
            self,
            text="سفارش‌ها",
            padding=10
        )
        orders_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=8
        )

        self.orders_table = ttk.Treeview(
            orders_frame,
            columns=("id", "total", "created"),
            show="headings",
            selectmode="browse",
            height=7
        )

        self.orders_table.heading(
            "id", text="شماره سفارش"
        )
        self.orders_table.heading(
            "total", text="مبلغ (تومان)"
        )
        self.orders_table.heading(
            "created", text="زمان ثبت"
        )

        self.orders_table.column(
            "id", width=120, anchor="center"
        )
        self.orders_table.column(
            "total", width=180, anchor="center"
        )
        self.orders_table.column(
            "created", width=200, anchor="center"
        )

        self.orders_table.pack(
            fill="both",
            expand=True
        )

        self.orders_table.bind(
            "<<TreeviewSelect>>",
            self.show_order_items
        )

        # Order details
        details_frame = ttk.LabelFrame(
            self,
            text="جزئیات سفارش انتخاب‌شده",
            padding=10
        )
        details_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=8
        )

        self.details_table = ttk.Treeview(
            details_frame,
            columns=(
                "name",
                "quantity",
                "price",
                "subtotal"
            ),
            show="headings",
            height=6
        )

        for key, title, width in (
            ("name", "نام محصول", 220),
            ("quantity", "تعداد", 90),
            ("price", "قیمت واحد", 150),
            ("subtotal", "مبلغ", 150),
        ):
            self.details_table.heading(
                key, text=title
            )
            self.details_table.column(
                key,
                width=width,
                anchor="center"
            )

        self.details_table.pack(
            fill="both",
            expand=True
        )

        ttk.Button(
            self,
            text="به‌روزرسانی گزارش",
            command=self.refresh_report
        ).pack(pady=12)

    def refresh_report(self):
        # Clear old information.
        self.orders_table.delete(
            *self.orders_table.get_children()
        )
        self.details_table.delete(
            *self.details_table.get_children()
        )

        session_id = get_open_cashier_session()

        if session_id is None:
            self.session_label.config(
                text="در حال حاضر صندوق باز نیست."
            )
            self.summary_label.config(
                text="تعداد سفارش‌ها: ۰ | مجموع فروش: ۰ تومان"
            )
            return

        try:
            orders = get_current_session_orders()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت گزارش ناموفق بود:\n{error}",
                parent=self
            )
            return

        total_sales = sum(
            order[1] for order in orders
        )

        self.session_label.config(
            text=f"شماره شیفت: {session_id}"
        )
        self.summary_label.config(
            text=(
                f"تعداد سفارش‌ها: {len(orders)}"
                f" | مجموع فروش: {total_sales:,} تومان"
            )
        )

        for order_id, total, created_at in orders:
            self.orders_table.insert(
                "",
                tk.END,
                iid=str(order_id),
                values=(
                    order_id,
                    f"{total:,}",
                    created_at
                )
            )

    def show_order_items(self, event=None):
        selected = self.orders_table.selection()

        self.details_table.delete(
            *self.details_table.get_children()
        )

        if not selected:
            return

        order_id = int(selected[0])

        try:
            items = get_order_items(order_id)
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت جزئیات ناموفق بود:\n{error}",
                parent=self
            )
            return

        for name, quantity, price in items:
            self.details_table.insert(
                "",
                tk.END,
                values=(
                    name,
                    quantity,
                    f"{price:,}",
                    f"{quantity * price:,}"
                )
            )