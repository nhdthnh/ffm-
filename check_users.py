import pandas as pd
import os

LOG_FILE = os.path.join("log", "db_log.xlsx")
try:
    with pd.ExcelFile(LOG_FILE) as xls:
        print(f"Sheets: {xls.sheet_names}")
        if 'users' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='users')
            print(f"Cols: {df.columns.tolist()}")
            for idx, r in df.iterrows():
                p = r.get('perm_report', 'N/A')
                s = r.get('is_superadmin', 'N/A')
                print(f"User: {r['user']} | Super: {s} | Report: {p}")
        elif 'user' in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name='user')
            print(f"Sheet 'user' persists. Migration failed or skipped? Cols: {df.columns.tolist()}")
except Exception as e:
    print(f"Error: {e}")
