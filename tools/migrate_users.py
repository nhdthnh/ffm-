"""
tools/migrate_users.py
======================
Script chuyển đổi sheet 'user' cũ → sheet 'users' mới với phân quyền RBAC đầy đủ.
Chạy một lần duy nhất: python tools/migrate_users.py

Mức quyền:
  0 = Không có quyền (ẩn trang)
  1 = Xem (Read-only)
  2 = Ghi (Write/CRUD)
  9 = Quản trị (Admin full)
"""

import os
import shutil
import pandas as pd

LOG_FILE    = os.path.join("log", "db_log.xlsx")
BACKUP_FILE = os.path.join("log", "db_log_backup.xlsx")

PERM_COLS = [
    "perm_report", "perm_thu_hoi_boxme", "perm_nhap_kho_hcns",
    "perm_hang_ton_csr", "perm_hcns_khong_ct", "perm_tieu_huy",
    "perm_template", "perm_system_logs", "perm_about", "perm_user_mgmt",
]

USER_COLS = ["user", "password", "full_name", "email", "is_active", "is_superadmin"] + PERM_COLS


def migrate():
    if not os.path.exists(LOG_FILE):
        print(f"[ERROR] Không tìm thấy file: {LOG_FILE}")
        return

    shutil.copy2(LOG_FILE, BACKUP_FILE)
    print(f"[OK] Đã backup → {BACKUP_FILE}")

    all_sheets = pd.read_excel(LOG_FILE, sheet_name=None)
    print(f"[INFO] Sheets hiện tại: {list(all_sheets.keys())}")

    user_sheet_name = next((n for n in ["users", "user"] if n in all_sheets), None)
    if user_sheet_name is None:
        print("[ERROR] Không tìm thấy sheet 'user' hoặc 'users'")
        return

    df_old = all_sheets[user_sheet_name]
    rows = []
    for _, row in df_old.iterrows():
        new_row = {
            "user":         row.get("user", ""),
            "password":     row.get("password", ""),
            "full_name":    row.get("full_name", row.get("user", "")),
            "email":        row.get("email", ""),
            "is_active":    int(row.get("is_active", 1)),
            "is_superadmin": int(row.get("is_superadmin", 0)),
        }
        for col in PERM_COLS:
            new_row[col] = int(row.get(col, 2)) if col in df_old.columns else (
                9 if col == "perm_user_mgmt" and new_row["is_superadmin"] else
                0 if col == "perm_user_mgmt" else 2
            )
        rows.append(new_row)

    df_users = pd.DataFrame(rows, columns=USER_COLS)

    # Đặt superadmin cho user đầu tiên nếu chưa có
    if df_users["is_superadmin"].sum() == 0 and len(df_users) > 0:
        candidates = df_users[df_users["user"].str.lower().str.contains("admin|oqr|manager", na=False)]
        idx = candidates.index[0] if not candidates.empty else df_users.index[0]
        df_users.loc[idx, "is_superadmin"] = 1
        df_users.loc[idx, "perm_user_mgmt"] = 9
        print(f"[INFO] Đã set superadmin cho: {df_users.loc[idx, 'user']}")

    df_log = all_sheets.get("log", pd.DataFrame(columns=["time", "log"]))

    with pd.ExcelWriter(LOG_FILE, engine="openpyxl") as writer:
        df_users.to_excel(writer, sheet_name="users", index=False)
        df_log.to_excel(writer, sheet_name="log", index=False)

    print("[SUCCESS] Migration hoàn tất!")


if __name__ == "__main__":
    migrate()
