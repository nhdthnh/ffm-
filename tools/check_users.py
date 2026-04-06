"""
tools/check_users.py
====================
Kiểm tra nhanh nội dung sheet users trong db_log.xlsx.
Chạy: python tools/check_users.py
"""

import os
import pandas as pd

LOG_FILE = os.path.join("log", "db_log.xlsx")

try:
    with pd.ExcelFile(LOG_FILE) as xls:
        print(f"Sheets: {xls.sheet_names}")
        sheet = "users" if "users" in xls.sheet_names else "user"
        df = pd.read_excel(xls, sheet_name=sheet)
        print(f"Cols: {df.columns.tolist()}\n")
        for _, r in df.iterrows():
            print(f"  User: {r.get('user')} | Super: {r.get('is_superadmin')} | Active: {r.get('is_active')}")
except Exception as e:
    print(f"Lỗi: {e}")
