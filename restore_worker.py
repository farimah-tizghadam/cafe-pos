import os
import sqlite3
import sys
import time
from pathlib import Path
import ctypes
from ctypes import wintypes


def main():
    if len(sys.argv) != 4:
        raise ValueError("Invalid restore arguments.")

    backup_path = Path(sys.argv[1]).resolve()
    database_path = Path(sys.argv[2]).resolve()
    pos_pid = int(sys.argv[3])

    if not backup_path.is_file():
        raise ValueError("Backup file not found.")

    # Wait for the POS process to exit (Windows).
    SYNCHRONIZE = 0x00100000
    WAIT_OBJECT_0 = 0x00000000
    WAIT_TIMEOUT = 0x00000102

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel32.OpenProcess.restype = wintypes.HANDLE

    kernel32.WaitForSingleObject.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
    ]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    process_handle = kernel32.OpenProcess(SYNCHRONIZE, False, pos_pid)

    if process_handle:
        try:
            result = kernel32.WaitForSingleObject(process_handle, 30000)

            if result == WAIT_TIMEOUT:
                raise RuntimeError("POS did not close within 30 seconds.")

            if result != WAIT_OBJECT_0:
                raise RuntimeError("Failed while waiting for POS to close.")
        finally:
            kernel32.CloseHandle(process_handle)

    else:
        # The POS may have closed before this worker started.
        # The database lock check below provides another safeguard.
        print("POS process is already closed or unavailable.")
        
    # Check that SQLite is not currently locked.
    connection = sqlite3.connect(database_path, timeout=2)

    try:
        connection.execute("BEGIN EXCLUSIVE")
        connection.rollback()
    finally:
        connection.close()

    # Restore using SQLite's backup API.
    import database

    original_get_database_path = database.get_database_path

    try:
        database.get_database_path = lambda: database_path

        # Validate the selected backup before changing anything.
        with sqlite3.connect(
            backup_path.as_uri() + "?mode=ro",
            uri=True
        ) as source:

            result = source.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            if result is None or result[0] != "ok":
                raise ValueError("Backup database is damaged.")
            
            
            required_tables = {
                "products",
                "orders",
                "order_items",
                "cashier_sessions",
                "cafe_tables",
                "table_bills",
                "refunds",
                "cafe_settings",
            }

            existing_tables = {
                row[0]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

            if not required_tables.issubset(existing_tables):
                raise ValueError(
                    "این فایل پشتیبان مربوط به صندوق کافه نیست."
                )

            foreign_key_errors = source.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

            if foreign_key_errors:
                raise ValueError(
                    "اطلاعات فایل پشتیبان ناسازگار است."
                )

        # Save the current database before restoring.
        from datetime import datetime

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        safety_backup = database_path.with_name(
            f"cafe_before_restore_{timestamp}.db"
        )

        database.backup_database(safety_backup)

        # Restore into the existing database through SQLite.
        with sqlite3.connect(
            backup_path.as_uri() + "?mode=ro",
            uri=True
        ) as source:
            with sqlite3.connect(database_path) as destination:
                source.backup(destination)

    finally:
        database.get_database_path = original_get_database_path

    print("Database restored successfully.")


if __name__ == "__main__":
    from datetime import datetime
    import traceback

    log_path = Path(sys.executable).resolve().parent / "restore_log.txt"

    try:
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(
                f"\n--- Restore started: {datetime.now()} ---\n"
            )

        main()

        with open(log_path, "a", encoding="utf-8") as log:
            log.write("SUCCESS: Database restored.\n")
        
        
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        messagebox.showinfo(
            "بازیابی اطلاعات",
            "اطلاعات با موفقیت بازیابی شد.\n\n"
            "اکنون می‌توانید برنامه صندوق را دوباره باز کنید."
        )

        root.destroy()

    except Exception:
        with open(log_path, "a", encoding="utf-8") as log:
            log.write("FAILED:\n")
            log.write(traceback.format_exc())
            log.write("\n")

        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        messagebox.showerror(
            "خطای بازیابی اطلاعات",
            "بازیابی اطلاعات انجام نشد.\n\n"
            "فایل پشتیبان ممکن است نامعتبر یا خراب باشد.\n\n"
            "برای اطلاعات بیشتر فایل restore_log.txt را بررسی کنید."
        )

        root.destroy()