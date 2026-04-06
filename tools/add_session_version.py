"""
tools/add_session_version.py
============================
Thêm cột session_version vào sheet users nếu chưa có.
Chạy một lần: python tools/add_session_version.py
"""

import os
import pandas as pd

LOG_FILE = os.path.join("log", "db_log.xlsx")

try:
    with pd.ExcelFile(LOG_FILE) as xls:
        df_log   = pd.read_excel(xls, sheet_name="log")
        df_users = pd.read_excel(xls, sheet_name="users")

    if "session_version" not in df_users.columns:
        df_users["session_version"] = "1"
        print("Đã thêm cột 'session_version'.")
    else:
        print("Cột 'session_version' đã tồn tại.")

    with pd.ExcelWriter(LOG_FILE, engine="openpyxl") as writer:
        df_users.to_excel(writer, sheet_name="users", index=False)
        df_log.to_excel(writer, sheet_name="log", index=False)

    print("Hoàn tất.")

except Exception as e:
    print(f"Lỗi: {e}")
