
import tkinter as tk
from tkinter import ttk, messagebox

from database import (
    get_product,
    get_open_cashier_session,
    open_cashier_session,
    close_cashier_session,
    get_session_orders,
    get_session_refund_total,
    get_session_refunds_by_method,
    save_order,
    get_cafe_tables,
    get_table_bill_details,
    open_table_bill,
    close_table_bill,
    get_order_items,
    get_table_bill_items,
    cancel_empty_table_bill,
)

from product_management import ProductManagement
from sales_report import SalesReport


class CafePOS:
    def __init__(self, root):
        self.root = root
        self.root.title("صندوق فروش کافه")
        self.root.geometry("1050x680")
        self.root.minsize(850, 550)

        self.products = []
        self.cart = []

        self.selected_table_id = None
        self.selected_table_name = None
        self.selected_bill_id = None

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

        self.table_status_label = tk.Label(
            controls,
            text="نوع فروش: مستقیم",
            bg="#f4f5f7",
            fg="#172554",
            font=("Tahoma", 11, "bold")
        )

        self.table_status_label.pack(side="left", padx=10)

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

        ttk.Button(
            controls,
            text="گزارش فروش",
            command=self.open_sales_report
        ).pack(side="right", padx=5)


        ttk.Button(
            controls,
            text="میزها",
            command=self.open_tables_window
        ).pack(side="right", padx=5)


        ttk.Button(
            controls,
            text="فروش مستقیم",
            command=self.select_direct_sale
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

        if self.selected_bill_id is None:
            sale_destination = "فروش مستقیم"
        else:
            sale_destination = f"میز: {self.selected_table_name}"

        confirmed = messagebox.askyesno(
            "تأیید سفارش",
            f"نوع فروش: {sale_destination}\n"
            f"مبلغ سفارش: {total:,} تومان\n\n"
            "آیا سفارش ثبت شود؟"
        )

        if not confirmed:
            return


        payment_method = None
                    
        if self.selected_bill_id is None:
            payment_window = tk.Toplevel(self.root)
            payment_window.title("روش پرداخت")
            payment_window.geometry("300x170")
            payment_window.transient(self.root)
            payment_window.grab_set()

            selected_method = tk.StringVar(value="card")

            tk.Label(
                payment_window,
                text="روش پرداخت را انتخاب کنید:",
                font=("Tahoma", 11)
            ).pack(pady=10)

            tk.Radiobutton(
            payment_window,
            text="کارت",
            variable=selected_method,
            value="card"
            ).pack()

            tk.Radiobutton(
                payment_window,
                text="نقدی",
                variable=selected_method,
                value="cash"
            ).pack()

            confirmed = {"value": False}

            def confirm_payment():
                confirmed["value"] = True
                payment_window.destroy()

            tk.Button(
                payment_window,
                text="تأیید",
                command=confirm_payment
            ).pack(pady=10)

            self.root.wait_window(payment_window)

            if not confirmed["value"]:
                return

            payment_method = selected_method.get()
        
        try:
            save_order(
                session_id,
                total,
                self.cart,
                bill_id=self.selected_bill_id,
                payment_method=payment_method
            )
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"سفارش ثبت نشد:\n{error}"
            )
            return

        self.cart.clear()
        self.refresh_cart()

        if self.selected_bill_id is not None:
            table_name = self.selected_table_name

            self.selected_table_id = None
            self.selected_table_name = None
            self.selected_bill_id = None

            self.table_status_label.config(
                text="نوع فروش: مستقیم"
            )

            messagebox.showinfo(
                "ثبت موفق",
                f"سفارش {table_name} با موفقیت ثبت شد.\n"
                f"مبلغ: {total:,} تومان\n\n"
                "نوع فروش به فروش مستقیم تغییر کرد."
            )
        else:
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

        try:
            sales = get_session_orders(session_id)
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"محاسبه فروش شیفت ناموفق بود:\n{error}"
            )
            return

        total = sum(sale[3] for sale in sales)

        refund_total = get_session_refund_total(session_id)
        net_total = total - refund_total   

        refund_methods = get_session_refunds_by_method(session_id)

        cash_refunds = refund_methods["cash"]
        card_refunds = refund_methods["card"]
        unknown_refunds = refund_methods["unknown"]

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

        # Find tables that still have an open bill.
        tables = get_cafe_tables()

        open_tables = [
            table_name
            for table_id, table_name, open_bill_id in tables
            if open_bill_id is not None
        ]

        # Build the shift-closing message.
        message = (
            f"شماره شیفت: {session_id}\n"
            f"تعداد فروش‌ها: {len(sales)}\n\n"

            f"فروش ناخالص: {total:,} تومان\n"
            f"فروش نقدی: {cash_total:,} تومان\n"
            f"فروش کارت: {card_total:,} تومان\n"
            f"فروش نامشخص: {unknown_total:,} تومان\n\n"

            f"بازپرداخت نقدی: {cash_refunds:,} تومان\n"
            f"بازپرداخت کارت: {card_refunds:,} تومان\n"
            f"بازپرداخت نامشخص: {unknown_refunds:,} تومان\n"
            f"مجموع بازپرداخت‌ها: {refund_total:,} تومان\n\n"

            f"خالص نقدی: {cash_total - cash_refunds:,} تومان\n"
            f"خالص کارت: {card_total - card_refunds:,} تومان\n"
            f"خالص نامشخص: {unknown_total - unknown_refunds:,} تومان\n\n"

            f"فروش خالص کل: {net_total:,} تومان"
        )

        # Warn about unpaid table bills.
        if open_tables:
            table_names = "، ".join(open_tables)

            message += (
                f"\n\nصورتحساب باز: {len(open_tables)}"
                f"\nمیزها: {table_names}"
                "\nاین صورتحساب‌ها باز می‌مانند و به شیفت بعد منتقل می‌شوند."
            )

        message += "\n\nآیا صندوق بسته شود؟"

        confirmed = messagebox.askyesno(
            "گزارش پایان شیفت",
            message
        )

        if not confirmed:
            return

        try:
            close_cashier_session()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"بستن صندوق ناموفق بود:\n{error}"
            )
            return

        self.update_status()

    def open_product_management(self):
        ProductManagement(
            self.root,
            on_close=self.load_products
    )        

    def open_sales_report(self):
        SalesReport(self.root)



    def open_bill_details(self, table_id, table_name, bill_id, tables_window):
        bill = get_table_bill_details(bill_id)

        bill_window = tk.Toplevel(self.root)
        bill_window.title(f"صورتحساب {table_name}")
        bill_window.geometry("550x550")

        tk.Label(
            bill_window,
            text=f"صورتحساب {table_name}",
            font=("Tahoma", 18, "bold")
        ).pack(pady=15)

        orders_frame = tk.Frame(bill_window)
        orders_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        items = get_table_bill_items(bill_id)

        for product_name, quantity, price in items:
            item_total = quantity * price

            tk.Label(
                orders_frame,
                text=(
                    f"{product_name} × {quantity}"
                    f"   |   {item_total:,} تومان"
                ),
                font=("Tahoma", 12),
                anchor="e"
            ).pack(
                fill="x",
                pady=5
            )

        tk.Label(
            bill_window,
            text=f"مبلغ کل: {bill['total']:,} تومان",
            font=("Tahoma", 15, "bold")
        ).pack(pady=15)

        ttk.Button(
            bill_window,
            text="انتخاب میز و افزودن سفارش",
            command=lambda: self.select_table_from_bill(
                table_id,
                table_name,
                bill_id,
                bill_window,
                tables_window
            )
        ).pack(
            fill="x",
            padx=20,
            pady=5
        )

        ttk.Button(
            bill_window,
            text="پرداخت و بستن صورتحساب",
            command=lambda: self.pay_bill_from_window(
                bill_id,
                bill_window,
                tables_window
            )
        ).pack(
            fill="x",
            padx=20,
            pady=5
        )


        if not bill["orders"]:
            ttk.Button(
                bill_window,
                text="لغو صورتحساب خالی",
                command=lambda: self.cancel_empty_bill_from_window(
                    bill_id,
                    bill_window,
                    tables_window
                )
            ).pack(
                fill="x",
                padx=20,
                pady=5
            )
    def cancel_empty_bill_from_window(
        self,
        bill_id,
        bill_window,
        tables_window
    ):
        confirmed = messagebox.askyesno(
            "لغو صورتحساب",
            "این صورتحساب خالی است.\n"
            "آیا صورتحساب لغو و میز آزاد شود؟",
            parent=bill_window
        )

        if not confirmed:
            return

        try:
            cancel_empty_table_bill(bill_id)
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"لغو صورتحساب ناموفق بود:\n{error}",
                parent=bill_window
            )
            return

        # If this bill is currently selected on the POS,
        # return the POS to direct-sale mode.
        if self.selected_bill_id == bill_id:
            self.selected_table_id = None
            self.selected_table_name = None
            self.selected_bill_id = None

            self.table_status_label.config(
                text="نوع فروش: مستقیم"
            )

        bill_window.destroy()
        tables_window.destroy()

        messagebox.showinfo(
            "لغو صورتحساب",
            "صورتحساب خالی لغو شد و میز آزاد شد."
        )
            

    def pay_bill_from_window(
            self,
            bill_id,
            bill_window,
            tables_window
        ):
            try:
                bill = get_table_bill_details(bill_id)
            except Exception as error:
                messagebox.showerror(
                    "خطا",
                    f"دریافت صورتحساب ناموفق بود:\n{error}",
                    parent=bill_window
                )
                return

            if bill["status"] != "open":
                messagebox.showwarning(
                    "پرداخت",
                    "این صورتحساب قبلاً بسته شده است.",
                    parent=bill_window
                )
                return

            if bill["total"] <= 0:
                messagebox.showwarning(
                    "پرداخت",
                    "صورتحساب این میز خالی است.",
                    parent=bill_window
                )
                return

            confirmed = messagebox.askyesno(
                "تأیید پرداخت",
                f"میز: {bill['table_name']}\n"
                f"مبلغ قابل پرداخت: {bill['total']:,} تومان\n\n"
                "آیا پرداخت انجام شد؟",
                parent=bill_window
            )

            if not confirmed:
                return

            session_id = get_open_cashier_session()

            if session_id is None:
                messagebox.showwarning(
                    "پرداخت",
                    "برای ثبت پرداخت ابتدا صندوق را باز کنید.",
                    parent=bill_window
                )
                return

            payment_window = tk.Toplevel(bill_window)
            payment_window.title("روش پرداخت")
            payment_window.geometry("300x170")
            payment_window.transient(bill_window)
            payment_window.grab_set()

            selected_method = tk.StringVar(value="card")

            tk.Label(
                payment_window,
                text="روش پرداخت صورتحساب:",
                font=("Tahoma", 11)
            ).pack(pady=10)

            tk.Radiobutton(
                payment_window,
                text="کارت",
                variable=selected_method,
                value="card"
            ).pack()

            tk.Radiobutton(
                payment_window,
                text="نقدی",
                variable=selected_method,
                value="cash"
            ).pack()

            confirmed_payment = {"value": False}

            def confirm_payment_method():
                confirmed_payment["value"] = True
                payment_window.destroy()

            tk.Button(
                payment_window,
                text="تأیید",
                command=confirm_payment_method
            ).pack(pady=10)

            bill_window.wait_window(payment_window)

            if not confirmed_payment["value"]:
                return

            payment_method = selected_method.get()

            try:
                close_table_bill(
                    bill_id,
                    session_id,
                    payment_method
                )
            except Exception as error:
                messagebox.showerror(
                    "خطا",
                    f"بستن صورتحساب ناموفق بود:\n{error}",
                    parent=bill_window
                )
                return

            # Clear the selected table if this is the currently selected bill.
            if self.selected_bill_id == bill_id:
                self.selected_table_id = None
                self.selected_table_name = None
                self.selected_bill_id = None

                self.table_status_label.config(
                    text="نوع فروش: مستقیم"
                )

            total = bill["total"]
            table_name = bill["table_name"]

            bill_window.destroy()
            tables_window.destroy()

            messagebox.showinfo(
                "پرداخت موفق",
                f"صورتحساب {table_name} بسته شد.\n"
                f"مبلغ پرداخت‌شده: {total:,} تومان"
            )


    def select_table_from_bill(
        self,
        table_id,
        table_name,
        bill_id,
        bill_window,
        tables_window
    ):
        # Select the existing open bill.
        self.selected_table_id = table_id
        self.selected_table_name = table_name
        self.selected_bill_id = bill_id

        # Update the main POS screen.
        self.table_status_label.config(
            text=f"نوع فروش: میز | {table_name}"
        )

        # Close both table-related windows.
        bill_window.destroy()
        tables_window.destroy()


    def select_table(self, table_id, table_name, bill_id, window):
        # If the table is free, start a new bill for this customer group.
        if bill_id is None:
            try:
                bill_id = open_table_bill(table_id)
            except Exception as error:
                messagebox.showerror(
                    "خطا",
                    f"صورتحساب میز باز نشد:\n{error}",
                    parent=window
                )
                return

        self.selected_table_id = table_id
        self.selected_table_name = table_name
        self.selected_bill_id = bill_id

        self.table_status_label.config(
            text=f"نوع فروش: میز | {table_name}"
        )

        window.destroy()



    def select_direct_sale(self):
        if self.cart:
            messagebox.showwarning(
                "سبد خرید",
                "ابتدا سفارش فعلی را ثبت یا حذف کنید."
            )
            return

        self.selected_table_id = None
        self.selected_table_name = None
        self.selected_bill_id = None

        self.table_status_label.config(
            text="نوع فروش: مستقیم"
        )


    def open_tables_window(self):
        window = tk.Toplevel(self.root)
        window.title("مدیریت میزها")
        window.geometry("500x500")

        title = tk.Label(
            window,
            text="میزهای کافه",
            font=("Tahoma", 18, "bold")
        )
        title.pack(pady=15)

        tables_frame = tk.Frame(window)
        tables_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        tables = get_cafe_tables()

        for table_id, table_name, open_bill_id in tables:

            if open_bill_id is None:
                status_text = "آزاد"

                button_command = lambda tid=table_id, tname=table_name: (
                    self.select_table(
                        tid,
                        tname,
                        None,
                        window
                    )
                )

            else:
                bill = get_table_bill_details(open_bill_id)
                total = bill["total"]

                if not bill["orders"]:
                    status_text = "صورتحساب خالی"

                else:
                    status_text = (
                        f"در حال استفاده\n"
                        f"{total:,} تومان"
                    )

                button_command = lambda tid=table_id, tname=table_name, bid=open_bill_id: (
                    self.open_bill_details(
                        tid,
                        tname,
                        bid,
                        window
                    )
                )

            table_button = tk.Button(
                tables_frame,
                text=f"{table_name}\n{status_text}",
                font=("Tahoma", 14),
                width=18,
                height=4,
                command=button_command
            )

            table_button.pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    app = CafePOS(root)
    root.mainloop()