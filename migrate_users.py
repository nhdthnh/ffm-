"""
migrate_users.py
================
Script chuyển đổi sheet 'user' cũ → sheet 'users' mới với phân quyền đầy đủ.
Chạy một lần: python migrate_users.py

Mức quyền:
  0 = Không có quyền (ẩn trang)
  1 = Xem (Read-only)
  2 = Ghi (Write/CRUD)
  9 = Quản trị (Admin full)
"""

import os
import pandas as pd
import openpyxl
from openpyxl import load_workbook

LOG_FILE = os.path.join("log", "db_log.xlsx")
BACKUP_FILE = os.path.join("log", "db_log_backup.xlsx")

PERM_COLS = [
    "perm_report",
    "perm_thu_hoi_boxme",
    "perm_nhap_kho_hcns",
    "perm_hang_ton_csr",
    "perm_hcns_khong_ct",
    "perm_tieu_huy",
    "perm_template",
    "perm_system_logs",
    "perm_about",
    "perm_user_mgmt",
]

USER_COLS = ["user", "password", "full_name", "email", "is_active", "is_superadmin"] + PERM_COLS


def migrate():
    if not os.path.exists(LOG_FILE):
        print(f"[ERROR] Không tìm thấy file: {LOG_FILE}")
        return

    # Backup
    import shutil
    shutil.copy2(LOG_FILE, BACKUP_FILE)
    print(f"[OK] Đã backup → {BACKUP_FILE}")

    # Đọc file cũ
    all_sheets = pd.read_excel(LOG_FILE, sheet_name=None)
    print(f"[INFO] Sheets hiện tại: {list(all_sheets.keys())}")

    # Xác định sheet user
    user_sheet_name = None
    for name in ["users", "user"]:
        if name in all_sheets:
            user_sheet_name = name
            break

    if user_sheet_name is None:
        print("[ERROR] Không tìm thấy sheet 'user' hoặc 'users'")
        return

    df_old = all_sheets[user_sheet_name]
    print(f"[INFO] Sheet user cũ ({user_sheet_name}), columns: {df_old.columns.tolist()}")
    print(df_old.to_string())

    # Xây dựng DataFrame mới
    rows = []
    for _, row in df_old.iterrows():
        new_row = {
            "user": row.get("user", ""),
            "password": row.get("password", ""),
            "full_name": row.get("full_name", row.get("user", "")),
            "email": row.get("email", ""),
            "is_active": int(row.get("is_active", 1)),
            "is_superadmin": int(row.get("is_superadmin", 0)),
        }
        # Copy quyền hiện có hoặc gán mặc định
        for col in PERM_COLS:
            if col in df_old.columns:
                new_row[col] = int(row.get(col, 2))
            else:
                # Mặc định: gán write cho tất cả trang trừ user_mgmt
                if col == "perm_user_mgmt":
                    new_row[col] = 0
                else:
                    new_row[col] = 2  # write mặc định

        rows.append(new_row)

    df_users = pd.DataFrame(rows, columns=USER_COLS)

    # === Đặt tài khoản đầu tiên là superadmin nếu chưa có ===
    if df_users["is_superadmin"].sum() == 0 and len(df_users) > 0:
        # Thử match username 'admin' hoặc dùng user đầu tiên
        admin_candidates = df_users[df_users["user"].str.lower().str.contains("admin|oqr|manager", na=False)]
        if not admin_candidates.empty:
            idx = admin_candidates.index[0]
        else:
            idx = df_users.index[0]
        df_users.loc[idx, "is_superadmin"] = 1
        df_users.loc[idx, "perm_user_mgmt"] = 9
        print(f"[INFO] Đã set is_superadmin=1 cho user: {df_users.loc[idx, 'user']}")

    print(f"\n[INFO] DataFrame users mới:")
    print(df_users.to_string())

    # Đọc sheet log
    df_log = all_sheets.get("log", pd.DataFrame(columns=["time", "log"]))

    # Ghi lại file
    with pd.ExcelWriter(LOG_FILE, engine="openpyxl") as writer:
        df_users.to_excel(writer, sheet_name="users", index=False)
        df_log.to_excel(writer, sheet_name="log", index=False)

    print(f"\n[SUCCESS] Đã migrate xong! File: {LOG_FILE}")
    print("  - Sheet 'users' với đầy đủ cột quyền hạn")
    print("  - Sheet 'log' giữ nguyên")


if __name__ == "__main__":
    migrate()
