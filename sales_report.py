import tkinter as tk
from tkinter import ttk, messagebox

from database import (
    get_open_cashier_session,
    get_current_session_orders,
    get_order_items,
    get_cashier_sessions,
    get_session_orders,
    get_orders_by_date,
)

from datetime import date


class SalesReport(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("گزارش فروش")
        self.geometry("900x750")
        self.minsize(750, 550)
        self.configure(bg="#f4f5f7")

        self.transient(parent)
        self.grab_set()

        self.session_options = {}
        self.selected_session_id = None
        self.report_mode = "shift"

        self.build_interface()
        self.refresh_report()
         

    def build_interface(self):
        # Title
        tk.Label(
            self,
            text="گزارش فروش کافه",
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


        # shift selector
        selector_frame = tk.Frame(
            self,
            bg="#f4f5f7"
        )
        selector_frame.pack(pady=10)

        tk.Label(
            selector_frame,
            text="انتخاب شیفت:",
            font=("Tahoma", 11),
            bg="#f4f5f7"
        ).pack(side="right", padx=8)

        self.session_combo = ttk.Combobox(
            selector_frame,
            state="readonly",
            font=("Tahoma", 11),
            width=45,
            justify="right"
        )
        self.session_combo.pack(side="right")

        self.session_combo.bind(
            "<<ComboboxSelected>>",
            self.on_session_selected
        )

        #sort by date
        
        date_frame = tk.Frame(self, bg='#f4f5f7')
        date_frame.pack(pady=10)

        tk.Label(
            date_frame,
            text="از تاریخ:",
            bg="#f4f5f7"
        ).pack(side="right", padx=5)


        self.start_date_entry = ttk.Entry(
            date_frame,
            width=14,
            justify="center"
        )

        self.start_date_entry.pack(side="right", padx=5)
        self.start_date_entry.insert(0, date.today().isoformat())

        tk.Label(
            date_frame,
            text="تا تاریخ:",
            bg="#f4f5f7"
        ).pack(side="right", padx=5)

        self.end_date_entry = ttk.Entry(
            date_frame,
            width=14,
            justify="center"
        )

        self.end_date_entry.pack(side="right", padx=5)
        self.end_date_entry.insert(0, date.today().isoformat())

        ttk.Button(
            date_frame,
            text="نمایش گزارش تاریخ",
            command=self.show_date_report
        ).pack(side="right", padx=10)


        ttk.Button(
            date_frame,
            text="نمایش گزارش شیفت",
            command=self.show_selected_shift
        ).pack(side="right", padx=10)
        

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

        tk.Button(
            self,
            text="به‌روزرسانی گزارش",
            command=self.refresh_report,
            font=("Tahoma", 11),
            bg="#e2e8f0",
            fg="#172554",
            padx=15,
            pady=6
        ).pack(pady=12)

        

    def refresh_shifts(self):
        try:
            sessions = get_cashier_sessions()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت شیفت‌ها ناموفق بود:\n{error}",
                parent=self
            )
            return

        self.session_options = {}
        labels = []

        for session_id, status, opened_at, closed_at in sessions:
            state = "باز" if status == 1 else "بسته"

            label = (
                f"شیفت {session_id} | {state}"
                f" | شروع: {opened_at}"
            )

            labels.append(label)
            self.session_options[label] = session_id

        self.session_combo["values"] = labels

        if not labels:
            self.session_combo.set("")
            self.selected_session_id = None
            self.show_session_orders()
            return

        # Keep the selected shift when refreshing.
        selected_label = next(
            (
                label
                for label, session_id in self.session_options.items()
                if session_id == self.selected_session_id
            ),
            labels[0]
        )

        self.session_combo.set(selected_label)
        self.selected_session_id = self.session_options[selected_label]

        self.show_session_orders()


    def on_session_selected(self, event=None):
        self.report_mode = "shift"
        label = self.session_combo.get()

        self.selected_session_id = self.session_options.get(label)

        self.show_session_orders()


    def show_session_orders(self):
        self.orders_table.delete(
            *self.orders_table.get_children()
        )
        self.details_table.delete(
            *self.details_table.get_children()
        )

        if self.selected_session_id is None:
            self.session_label.config(
                text="هیچ شیفتی ثبت نشده است."
            )
            self.summary_label.config(
                text="تعداد سفارش‌ها: ۰ | مجموع فروش: ۰ تومان"
            )
            return

        try:
            orders = get_session_orders(
                self.selected_session_id
            )
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت سفارش‌ها ناموفق بود:\n{error}",
                parent=self
            )
            return

        total_sales = sum(order[1] for order in orders)

        if not orders:
            self.session_label.config(
                text=f"شیفت {self.selected_session_id} - سفارشی ثبت نشده است"
            )
        else:
            self.session_label.config(
                text=f"شماره شیفت: {self.selected_session_id}"
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


    def show_date_report(self):
        start_text = self.start_date_entry.get().strip()
        end_text = self.end_date_entry.get().strip()

        try:
            start = date.fromisoformat(start_text)
            end = date.fromisoformat(end_text)

        except ValueError:
            messagebox.showerror(
                "خطا",
                "تاریخ را به صورت YYYY-MM-DD وارد کنید.",
                parent=self
            )
            return

        if start > end:
            messagebox.showerror(
                "خطا",
                "تاریخ شروع نباید بعد از تاریخ پایان باشد.",
                parent=self
            )
            return

        try:
            orders = get_orders_by_date(
                start.isoformat(),
                end.isoformat()
            )

        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت گزارش ناموفق بود:\n{error}",
                parent=self
            )
            return

        self.report_mode = "date"

        self.orders_table.delete(
            *self.orders_table.get_children()
        )

        self.details_table.delete(
            *self.details_table.get_children()
        )

        total_sales = sum(order[1] for order in orders)

        self.session_label.config(
            text=f"گزارش از {start} تا {end}"
        )

        self.summary_label.config(
            text=(
                f"تعداد سفارش‌ها: {len(orders)} | "
                f"مجموع فروش: {total_sales:,} تومان"
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
             


    def show_selected_shift(self):
        label = self.session_combo.get()
        session_id = self.session_options.get(label)

        if session_id is None:
            messagebox.showwarning(
                "انتخاب شیفت",
                "لطفاً ابتدا یک شیفت انتخاب کنید.",
                parent=self
            )
            return

        self.selected_session_id = session_id
        self.report_mode = "shift"
        self.show_session_orders()

        
    def refresh_report(self):
        if self.report_mode == "date":
            self.show_date_report()
        else:
            self.refresh_shifts()