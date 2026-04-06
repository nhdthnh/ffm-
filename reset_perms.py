import pandas as pd
import os

LOG_FILE = os.path.join("log", "db_log.xlsx")
PERM_SLUGS = [
    "perm_report", "perm_thu_hoi_boxme", "perm_nhap_kho_hcns",
    "perm_hang_ton_csr", "perm_hcns_khong_ct", "perm_tieu_huy",
    "perm_template", "perm_system_logs", "perm_about", "perm_user_mgmt"
]

try:
    with pd.ExcelFile(LOG_FILE) as xls:
        sheets = xls.sheet_names
        df_log = pd.read_excel(xls, sheet_name='log')
        if 'users' in sheets:
            df = pd.read_excel(xls, sheet_name='users')
        elif 'user' in sheets:
            df = pd.read_excel(xls, sheet_name='user')
        else:
            print("No user sheet found.")
            exit(1)

    # Force reset all perms to 2 (write) and superadmin to 1 for the first user
    for slug in PERM_SLUGS:
        df[slug] = 2
    
    # Ensure columns exist
    df['is_superadmin'] = 0
    df.loc[0, 'is_superadmin'] = 1
    df['is_active'] = 1
    
    with pd.ExcelWriter(LOG_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='users', index=False)
        df_log.to_excel(writer, sheet_name='log', index=False)
    
    print("Successfully reset all user permissions to 2 and set first user as superadmin.")

except Exception as e:
    print(f"Error: {e}")
