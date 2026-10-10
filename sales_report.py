import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import csv

from database import (
    get_open_cashier_session,
    get_current_session_orders,
    get_order_items,
    get_cashier_sessions,
    get_session_orders,
    get_orders_by_date,
    get_table_bill_items,
    get_session_refund_total,
    get_refund_total_by_date,
    refund_direct_sale,
    refund_table_bill,
)

from datetime import date


class SalesReport(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("گزارش فروش")
        self.geometry("950x850")
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
        
        action_frame = tk.Frame(
            self,
            bg="#f4f5f7"
        )
        action_frame.pack(pady=8)

        self.refund_button = tk.Button(
            action_frame,
            text="بازپرداخت فروش",
            command=self.refund_selected_sale,
            font=("Tahoma", 11, "bold"),
            bg="#fee2e2",
            fg="#991b1b",
            padx=15,
            pady=6
        )

        self.refund_button.pack(side="right", pady=8)

        tk.Button(
            action_frame,
            text="به‌روزرسانی گزارش",
            command=self.refresh_report,
            font=("Tahoma", 11),
            bg="#e2e8f0",
            fg="#172554",
            padx=15,
            pady=6
        ).pack(side="right", padx=8)

        tk.Button(
            action_frame,
            text="خروجی اکسل (CSV)",
            command=self.export_csv,
            font=("Tahoma", 11),
            padx=15,
            pady=6
        ).pack(side="right", padx=8)

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
            pady=4
        )

        self.orders_table = ttk.Treeview(
            orders_frame,
            columns=("id", "total", "created", "payment_method"),
            show="headings",
            selectmode="browse",
            height=5
        )

        self.orders_table.heading(
            "id", text="فروش"
        )
        self.orders_table.heading(
            "total", text="مبلغ (تومان)"
        )
        self.orders_table.heading(
            "created", text="زمان ثبت"
        )
        self.orders_table.heading(
            "payment_method", text="روش پرداخت"
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
        self.orders_table.column(
            "payment_method", width=110, anchor="center"
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
            pady=4
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
            height=4
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

        self.report_total_label = tk.Label(
            details_frame,
            text="مجموع فروش شیفت: ۰ تومان",
            font=("Tahoma", 12, "bold"),
            fg="#15803d"
        )

        self.report_total_label.pack(
            pady=(10, 0)
        )

        buttons_frame = tk.Frame(
            self,
            bg="#f4f5f7"
        )

        buttons_frame.pack(pady=8)


        

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
                text="تعداد فروش‌ها: ۰ | مجموع فروش: ۰ تومان"
            )
            return

        try:
            sales = get_session_orders(
                self.selected_session_id
            )
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت فروش‌ها ناموفق بود:\n{error}",
                parent=self
            )
            return

        # New database result:
        # sale_type, sale_id, table_name, total, sale_time, payment_method
        total_sales = sum(sale[3] for sale in sales)

        refund_total = get_session_refund_total(
            self.selected_session_id
        )
        net_sales = total_sales - refund_total

        cash_total = sum(
            sale[3] for sale in sales
            if sale[5] == "cash"
        )

        card_total = sum(
            sale[3] for sale in sales
            if sale[5] == "card"
        )

        unknown_total = sum(
            sale[3] for sale in sales
            if sale[5] not in ("cash", "card")
        )

        self.report_total_label.config(
            text=(
                f"فروش ناخالص: {total_sales:,} تومان\n"
                f"نقدی: {cash_total:,} | "
                f"کارت: {card_total:,} | "
                f"نامشخص: {unknown_total:,} تومان\n"
                f"بازپرداخت‌ها: {refund_total:,} تومان\n"
                f"فروش خالص: {net_sales:,} تومان"
            )
        )

        if not sales:
            self.session_label.config(
                text=f"شیفت {self.selected_session_id} - فروشی ثبت نشده است"
            )
        else:
            self.session_label.config(
                text=f"شماره شیفت: {self.selected_session_id}"
            )

        self.summary_label.config(
            text=(
                f"تعداد فروش‌ها: {len(sales)}"
                f" | مجموع فروش: {total_sales:,} تومان"
            )
        )

        for sale_type, sale_id, table_name, total, sale_time, payment_method in sales:

            if payment_method == "cash":
                payment_text = "نقدی"
            elif payment_method == "card":
                payment_text = "کارت"
            else:
                payment_text = "نامشخص"

            if sale_type == "table":
                display_id = f"{table_name} - صورتحساب {sale_id}"
                row_id = f"table:{sale_id}"
            else:
                display_id = f"سفارش {sale_id}"
                row_id = f"order:{sale_id}"

            self.orders_table.insert(
                "",
                tk.END,
                iid=row_id,
                values=(
                    display_id,
                    f"{total:,}",
                    sale_time,
                    payment_text,
                )
            )



    def show_order_items(self, event=None):
        selected = self.orders_table.selection()

        self.details_table.delete(
            *self.details_table.get_children()
        )

        if not selected:
            return

        row_id = selected[0]

        try:
            sale_type, sale_id_text = row_id.split(":", 1)
            sale_id = int(sale_id_text)

            if sale_type == "table":
                items = get_table_bill_items(sale_id)
            else:
                items = get_order_items(sale_id)

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
            sales = get_orders_by_date(
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

        total_sales = sum(sale[3] for sale in sales)

        refund_total = get_refund_total_by_date(
            start.isoformat(),
            end.isoformat()
        )
        net_sales = total_sales - refund_total

        cash_total = sum(
            sale[3] for sale in sales
            if sale[5] == "cash"
        )

        card_total = sum(
            sale[3] for sale in sales
            if sale[5] == "card"
        )

        unknown_total = sum(
            sale[3] for sale in sales
            if sale[5] not in ("cash", "card")
        )

        self.report_total_label.config(
        text=(
            f"فروش ناخالص: {total_sales:,} تومان\n"
            f"نقدی: {cash_total:,} | "
            f"کارت: {card_total:,} | "
            f"نامشخص: {unknown_total:,} تومان\n"
            f"بازپرداخت‌ها: {refund_total:,} تومان\n"
            f"فروش خالص: {net_sales:,} تومان"
        )
    )

        self.session_label.config(
            text=f"گزارش از {start} تا {end}"
        )

        self.summary_label.config(
            text=(
                f"تعداد فروش‌ها: {len(sales)} | "
                f"مجموع فروش: {total_sales:,} تومان"
            )
        )

        for sale_type, sale_id, table_name, total, sale_time, payment_method in sales:

            if payment_method == "cash":
                payment_text = "نقدی"
            elif payment_method == "card":
                payment_text = "کارت"
            else:
                payment_text = "نامشخص"
            
            if sale_type == "table":
                display_id = f"{table_name} - صورتحساب {sale_id}"
                row_id = f"table:{sale_id}"
            else:
                display_id = f"سفارش {sale_id}"
                row_id = f"order:{sale_id}"

            self.orders_table.insert(
                "",
                tk.END,
                iid=row_id,
                values=(
                    display_id,
                    f"{total:,}",
                    sale_time,
                    payment_text,
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


    def export_csv(self):
        sale_rows = self.orders_table.get_children()

        if not sale_rows:
            messagebox.showinfo(
                "خروجی گزارش",
                "فروشی برای خروجی گرفتن وجود ندارد.",
                parent=self
            )
            return

        export_rows = []

        try:
            for row_id in sale_rows:
                display_name, formatted_total, sale_time, payment_text = (
                    self.orders_table.item(row_id, "values")
                )

                sale_total = int(
                    str(formatted_total).replace(",", "")
                )

                sale_type, sale_id_text = row_id.split(":", 1)
                sale_id = int(sale_id_text)

                if sale_type == "table":
                    items = get_table_bill_items(sale_id)
                else:
                    items = get_order_items(sale_id)

                if not items:
                    export_rows.append([
                        display_name,
                        sale_time,
                        payment_text,
                        "",
                        "",
                        "",
                        "",
                        sale_total
                    ])
                    continue

                for index, (name, quantity, price) in enumerate(items):
                    export_rows.append([
                        display_name,
                        sale_time,
                        payment_text,
                        name,
                        quantity,
                        price,
                        quantity * price,
                        sale_total if index == 0 else ""
                    ])

        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"آماده‌سازی گزارش ناموفق بود:\n{error}",
                parent=self
            )
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="ذخیره گزارش فروش",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="sales_report.csv"
        )

        if not file_path:
            return

        try:
            with open(
                file_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)

                writer.writerow([
                    "فروش",
                    "زمان فروش",
                    "روش پرداخت",
                    "نام محصول",
                    "تعداد",
                    "قیمت واحد (تومان)",
                    "مبلغ ردیف (تومان)",
                    "جمع فروش (تومان)"
                ])

                writer.writerows(export_rows)

        except OSError as error:
            messagebox.showerror(
                "خطا",
                f"ذخیره فایل ناموفق بود:\n{error}",
                parent=self
            )
            return

        messagebox.showinfo(
            "خروجی گزارش",
            "فایل گزارش با موفقیت ذخیره شد.",
            parent=self
        )


    def refund_selected_sale(self):
        selected = self.orders_table.selection()

        if not selected:
            messagebox.showwarning(
                "انتخاب فروش",
                "لطفاً ابتدا یک فروش را انتخاب کنید.",
                parent=self
            )
            return

        # A refund must belong to an open cashier shift.
        try:
            session = get_open_cashier_session()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"بررسی وضعیت صندوق ناموفق بود:\n{error}",
                parent=self
            )
            return

        if session is None:
            messagebox.showwarning(
                "صندوق بسته است",
                "برای بازپرداخت، ابتدا صندوق را باز کنید.",
                parent=self
            )
            return

        row_id = selected[0]
        sale_type, sale_id_text = row_id.split(":", 1)
        sale_id = int(sale_id_text)

        values = self.orders_table.item(row_id, "values")
        sale_name = values[0]
        sale_amount = values[1]

        reason = simpledialog.askstring(
            "دلیل بازپرداخت",
            (
                f"فروش: {sale_name}\n"
                f"مبلغ: {sale_amount} تومان\n\n"
                "دلیل بازپرداخت را وارد کنید:"
            ),
            parent=self
        )

        # Cancel was pressed.
        if reason is None:
            return

        reason = reason.strip()

        if not reason:
            messagebox.showwarning(
                "دلیل بازپرداخت",
                "وارد کردن دلیل بازپرداخت الزامی است.",
                parent=self
            )
            return

        confirmed = messagebox.askyesno(
            "تأیید بازپرداخت",
            (
                f"آیا از بازپرداخت کامل این فروش مطمئن هستید؟\n\n"
                f"فروش: {sale_name}\n"
                f"مبلغ: {sale_amount} تومان\n"
                f"دلیل: {reason}\n\n"
                "این عملیات قابل بازگشت نیست."
            ),
            icon="warning",
            parent=self
        )

        if not confirmed:
            return

        try:
            if sale_type == "table":
                refund_table_bill(sale_id, reason)
            elif sale_type == "order":
                refund_direct_sale(sale_id, reason)
            else:
                raise ValueError("نوع فروش نامعتبر است.")

        except Exception as error:
            messagebox.showerror(
                "خطای بازپرداخت",
                f"ثبت بازپرداخت ناموفق بود:\n{error}",
                parent=self
            )
            return

        self.refresh_report()

        messagebox.showinfo(
            "بازپرداخت موفق",
            "بازپرداخت با موفقیت ثبت شد.",
            parent=self
        )

        
    def refresh_report(self):
        if self.report_mode == "date":
            self.show_date_report()
        else:
            self.refresh_shifts()