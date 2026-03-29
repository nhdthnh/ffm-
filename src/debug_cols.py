import pandas as pd
import sys
import os

print("--- DEBUG SCRIPT START ---")

LOCAL_FILE = r"C:\Users\OQR\Desktop\ffm\(ALL) FFM_Tổng hợp hàng xuất kho Boxme về văn phòng.xlsx"

if not os.path.exists(LOCAL_FILE):
    print(f"Error: File not found at {LOCAL_FILE}")
    sys.exit(1)

print(f"File exists: {LOCAL_FILE}")
print(f"File size: {os.path.getsize(LOCAL_FILE)} bytes")

try:
    print("Loading Excel File...")
    xl = pd.ExcelFile(LOCAL_FILE)
    print("Sheet names:", xl.sheet_names)
    
    sheet_name = "Tổng hợp thu hồi"
    if sheet_name not in xl.sheet_names:
        print(f"Error: Sheet '{sheet_name}' not found.")
        sys.exit(1)
        
    print("\n--- Trying header=None (nrows=10) ---")
    df = pd.read_excel(LOCAL_FILE, sheet_name=sheet_name, header=None, nrows=10)
    print("First 10 rows:")
    print(df.to_string())
    
    print("\n--- Trying header=0 (nrows=5) ---")
    df0 = pd.read_excel(LOCAL_FILE, sheet_name=sheet_name, header=0, nrows=5)
    print("Columns header=0:", df0.columns.tolist())
    
    print("\n--- Trying header=1 (nrows=5) ---")
    df1 = pd.read_excel(LOCAL_FILE, sheet_name=sheet_name, header=1, nrows=5)
    print("Columns header=1:", df1.columns.tolist())
    
    print("\n--- Trying header=2 (nrows=5) ---")
    df2 = pd.read_excel(LOCAL_FILE, sheet_name=sheet_name, header=2, nrows=5)
    print("Columns header=2:", df2.columns.tolist())

except Exception as e:
    print("Error:", e)

print("--- DEBUG SCRIPT END ---")
