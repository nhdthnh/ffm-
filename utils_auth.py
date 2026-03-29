import os
import pandas as pd
from datetime import datetime

LOG_FILE = os.path.join("log", "db_log.xlsx")

def authenticate_user(username, password):
    try:
        df_user = pd.read_excel(LOG_FILE, sheet_name='user')
        # Check against 'user' and 'password' columns
        user_row = df_user[(df_user['user'] == username) & (df_user['password'].astype(str) == str(password))]
        
        if not user_row.empty:
            return True, username
        return False, None
    except Exception as e:
        print(f"Auth error: {e}")
        return False, None

def write_log(log_message):
    try:
        df_log = pd.read_excel(LOG_FILE, sheet_name='log')
        new_row = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "log": log_message
        }
        df_log = pd.concat([df_log, pd.DataFrame([new_row])], ignore_index=True)
        
        # We need to preserve the user sheet when writing back
        df_user = pd.read_excel(LOG_FILE, sheet_name='user')
        
        with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
            df_user.to_excel(writer, sheet_name='user', index=False)
            df_log.to_excel(writer, sheet_name='log', index=False)
    except Exception as e:
        print(f"Log write error: {e}")

def get_logs():
    try:
        return pd.read_excel(LOG_FILE, sheet_name='log')
    except Exception:
        return pd.DataFrame()
