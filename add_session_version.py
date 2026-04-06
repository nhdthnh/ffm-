import pandas as pd
import os

LOG_FILE = os.path.join("log", "db_log.xlsx")

try:
    with pd.ExcelFile(LOG_FILE) as xls:
        sheets = xls.sheet_names
        df_log = pd.read_excel(xls, sheet_name='log')
        df_users = pd.read_excel(xls, sheet_name='users')

    if 'session_version' not in df_users.columns:
        df_users['session_version'] = "1"
        print("Added 'session_version' column to 'users' sheet.")
    else:
        print("'session_version' column already exists.")

    with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
        df_users.to_excel(writer, sheet_name='users', index=False)
        df_log.to_excel(writer, sheet_name='log', index=False)
    
    print("Migration successful.")

except Exception as e:
    print(f"Error: {e}")
