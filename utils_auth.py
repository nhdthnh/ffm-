"""
utils_auth.py — RBAC Authentication & Permission Engine
=========================================================
Mức quyền:
  0 = Không có quyền (trang bị ẩn)
  1 = Xem (Read-only, không thể thêm/sửa/xóa)
  2 = Ghi (Write / CRUD đầy đủ)
  9 = Quản trị (Admin, toàn quyền kể cả xóa hàng loạt)
"""

import os
import pandas as pd
from datetime import datetime
import streamlit as st

LOG_FILE = os.path.join("log", "db_log.xlsx")

# Tên cột quyền hạn và nhãn hiển thị
PERM_SLUGS = [
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

PERM_LABELS = {
    "perm_report": "📊 Report",
    "perm_thu_hoi_boxme": "📦 Thu hồi Boxme",
    "perm_nhap_kho_hcns": "📥 Hàng nhập kho HCNS",
    "perm_hang_ton_csr": "🧾 Hàng tồn CSR",
    "perm_hcns_khong_ct": "📋 HCNS không chứng từ",
    "perm_tieu_huy": "🗑️ Tiêu hủy",
    "perm_template": "📄 Template",
    "perm_system_logs": "📓 Nhật ký hệ thống",
    "perm_about": "ℹ️ About",
    "perm_user_mgmt": "🔐 Quản lý người dùng",
}

PERM_LEVEL_LABELS = {0: "❌ Không có", 1: "👁 Xem", 2: "✏️ Ghi", 9: "👑 Quản trị"}

USER_COLS = [
    "user", "password", "full_name", "email",
    "is_active", "is_superadmin", "session_version",
] + PERM_SLUGS


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _read_users() -> pd.DataFrame:
    """Đọc sheet 'users' từ Excel, tạo mới nếu chưa có."""
    try:
        df = pd.read_excel(LOG_FILE, sheet_name="users", dtype=str)
        # Đảm bảo đủ cột
        for col in USER_COLS:
            if col not in df.columns:
                if col in PERM_SLUGS or col in ("is_active", "is_superadmin") or col == "session_version":
                    df[col] = "0" if col != "is_active" else "1"
                    if col == "session_version":
                        df[col] = "1"
                else:
                    df[col] = ""
        return df
    except Exception:
        # Thử sheet cũ tên 'user'
        try:
            df_old = pd.read_excel(LOG_FILE, sheet_name="user", dtype=str)
            # build minimal df
            df = pd.DataFrame(columns=USER_COLS)
            df["user"] = df_old.get("user", pd.Series(dtype=str))
            df["password"] = df_old.get("password", pd.Series(dtype=str))
            df["full_name"] = df_old.get("user", pd.Series(dtype=str))
            df["is_active"] = "1"
            df["is_superadmin"] = "0"
            for p in PERM_SLUGS:
                df[p] = "2" if p != "perm_user_mgmt" else "0"
            return df
        except Exception:
            return pd.DataFrame(columns=USER_COLS)


def _write_users(df_users: pd.DataFrame):
    """Ghi sheet 'users' trở lại file, giữ nguyên sheet 'log'."""
    try:
        # Kiểm tra file có đang mở không (chỉ Windows)
        if os.path.exists(LOG_FILE):
            try:
                os.rename(LOG_FILE, LOG_FILE)
            except OSError:
                raise PermissionError(f"File '{LOG_FILE}' đang được mở bởi chương trình khác (Excel?). Vui lòng đóng lại.")

        try:
            df_log = pd.read_excel(LOG_FILE, sheet_name="log")
        except Exception:
            df_log = pd.DataFrame(columns=["time", "log"])

        with pd.ExcelWriter(LOG_FILE, engine="openpyxl") as writer:
            df_users.to_excel(writer, sheet_name="users", index=False)
            df_log.to_excel(writer, sheet_name="log", index=False)
    except Exception as e:
        st.error(f"❌ Không thể ghi vào Database: {e}")
        raise e


def _safe_int(val, default=0) -> int:
    try:
        return int(float(str(val)))
    except Exception:
        return default


# ─────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────

def authenticate_user(username: str, password: str):
    """
    Xác thực người dùng.
    Returns:
        (success: bool, user_info: dict | None)
        user_info gồm: username, full_name, email, is_superadmin, permissions
    """
    try:
        df = _read_users()
        mask = (df["user"].astype(str) == str(username)) & \
               (df["password"].astype(str) == str(password))
        row = df[mask]

        if row.empty:
            return False, None

        r = row.iloc[0]

        # Kiểm tra tài khoản có bị khoá không
        if _safe_int(r.get("is_active", 1), 1) == 0:
            return False, {"locked": True}

        permissions = {}
        for slug in PERM_SLUGS:
            permissions[slug] = _safe_int(r.get(slug, 0), 0)

        user_info = {
            "username": str(r.get("user", username)),
            "full_name": str(r.get("full_name", username)) if str(r.get("full_name", "")).strip() else username,
            "email": str(r.get("email", "")),
            "is_superadmin": _safe_int(r.get("is_superadmin", 0), 0) == 1,
            "session_version": _safe_int(r.get("session_version", 1), 1),
            "permissions": permissions,
        }
        return True, user_info

    except Exception as e:
        print(f"[Auth Error] {e}")
        return False, None


def reload_user_data(username: str) -> dict:
    """Tải lại toàn bộ thông tin người dùng (dùng để kiểm tra session version)."""
    try:
        df = _read_users()
        row = df[df["user"].astype(str) == str(username)]
        if row.empty:
            return {}
        r = row.iloc[0]
        
        permissions = {slug: _safe_int(r.get(slug, 0), 0) for slug in PERM_SLUGS}
        return {
            "session_version": _safe_int(r.get("session_version", 1), 1),
            "is_active": _safe_int(r.get("is_active", 1), 1),
            "is_superadmin": _safe_int(r.get("is_superadmin", 0), 0) == 1,
            "permissions": permissions,
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────
# Permission checking (sử dụng st.session_state)
# ─────────────────────────────────────────────

def get_perm(slug: str) -> int:
    """
    Lấy mức quyền của user hiện tại cho một trang.
    Superadmin luôn trả về 9.
    """
    if st.session_state.get("is_superadmin", False):
        return 9
    perms = st.session_state.get("permissions", {})
    return perms.get(slug, 0)


def require_perm(slug: str, required: int = 1) -> bool:
    """
    Kiểm tra user có đủ quyền không.
    Nếu không, hiển thị thông báo lỗi và trả về False.
    """
    level = get_perm(slug)
    if level < required:
        st.error("🚫 Bạn không có quyền truy cập trang này.")
        st.info("Vui lòng liên hệ quản trị viên để được cấp quyền.")
        st.stop()
        return False
    return True


def can_write(slug: str) -> bool:
    """Kiểm tra user có quyền ghi không (>= 2)."""
    return get_perm(slug) >= 2


def can_admin(slug: str) -> bool:
    """Kiểm tra user có quyền quản trị không (== 9 hoặc superadmin)."""
    return get_perm(slug) >= 9


def show_readonly_banner():
    """Hiển thị banner thông báo chế độ chỉ xem."""
    st.info("👁 **Chế độ Chỉ xem** — Bạn không có quyền thêm, sửa hoặc xóa dữ liệu trên trang này.")


# ─────────────────────────────────────────────
# User Management (CRUD)
# ─────────────────────────────────────────────

def get_all_users() -> pd.DataFrame:
    """Trả về toàn bộ danh sách người dùng (không có cột password)."""
    df = _read_users()
    return df.drop(columns=["password"], errors="ignore")


def get_user(username: str) -> dict | None:
    """Lấy thông tin đầy đủ 1 user (có password)."""
    df = _read_users()
    row = df[df["user"].astype(str) == str(username)]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def user_exists(username: str) -> bool:
    df = _read_users()
    return not df[df["user"].astype(str) == str(username)].empty


def create_user(user_data: dict) -> tuple[bool, str]:
    """
    Tạo người dùng mới.
    user_data: dict với các key của USER_COLS
    Returns (success, message)
    """
    try:
        df = _read_users()
        username = str(user_data.get("user", "")).strip()
        if not username:
            return False, "Tên đăng nhập không được để trống."
        if user_exists(username):
            return False, f"Tên đăng nhập '{username}' đã tồn tại."
        if not user_data.get("password", "").strip():
            return False, "Mật khẩu không được để trống."

        new_row = {col: "" for col in USER_COLS}
        new_row.update({k: str(v) for k, v in user_data.items() if k in USER_COLS})
        new_row.setdefault("is_active", "1")
        new_row.setdefault("is_superadmin", "0")
        new_row["session_version"] = "1"
        for slug in PERM_SLUGS:
            new_row.setdefault(slug, "0")

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        _write_users(df)
        write_log(f"Tạo tài khoản mới: {username}")
        return True, f"Đã tạo tài khoản '{username}' thành công."
    except Exception as e:
        return False, f"Lỗi tạo user: {str(e)}"


def update_user(username: str, user_data: dict, change_password: bool = False) -> tuple[bool, str]:
    """
    Cập nhật thông tin người dùng.
    Nếu change_password=False, giữ nguyên mật khẩu cũ.
    """
    try:
        df = _read_users()
        idx = df[df["user"].astype(str) == str(username)].index
        if idx.empty:
            return False, f"Không tìm thấy user '{username}'."

        i = idx[0]
        for key, val in user_data.items():
            if key == "password" and not change_password:
                continue
            if key in USER_COLS:
                df.at[i, key] = str(val)

        # Tăng version để logout session hiện tại
        current_ver = _safe_int(df.at[i, "session_version"], 1)
        df.at[i, "session_version"] = str(current_ver + 1)

        _write_users(df)
        write_log(f"Cập nhật tài khoản: {username}")
        return True, f"Đã cập nhật tài khoản '{username}'."
    except Exception as e:
        return False, f"Lỗi cập nhật user: {str(e)}"


def delete_user(username: str) -> tuple[bool, str]:
    """Xóa người dùng. Không thể xóa chính mình."""
    current = st.session_state.get("username", "")
    if str(username) == str(current):
        return False, "Không thể xóa chính tài khoản đang đăng nhập."

    df = _read_users()
    mask = df["user"].astype(str) == str(username)
    if not mask.any():
        return False, f"Không tìm thấy user '{username}'."

    df = df[~mask].reset_index(drop=True)
    _write_users(df)
    write_log(f"Xóa tài khoản: {username}")
    return True, f"Đã xóa tài khoản '{username}'."


def toggle_user_lock(username: str) -> tuple[bool, str]:
    """Khoá / Mở khoá tài khoản."""
    df = _read_users()
    idx = df[df["user"].astype(str) == str(username)].index
    if idx.empty:
        return False, f"Không tìm thấy user '{username}'."

    i = idx[0]
    current_active = _safe_int(df.at[i, "is_active"], 1)
    new_val = 0 if current_active == 1 else 1
    df.at[i, "is_active"] = str(new_val)
    
    # Tăng version để văng session
    current_ver = _safe_int(df.at[i, "session_version"], 1)
    df.at[i, "session_version"] = str(current_ver + 1)
    
    _write_users(df)
    action = "Khoá" if new_val == 0 else "Mở khoá"
    write_log(f"{action} tài khoản: {username}")
    return True, f"Đã {action.lower()} tài khoản '{username}'."


# ─────────────────────────────────────────────
# Log management
# ─────────────────────────────────────────────

def write_log(log_message: str):
    """Ghi log vào sheet 'log', giữ nguyên sheet 'users'."""
    try:
        df_users = _read_users()
        try:
            df_log = pd.read_excel(LOG_FILE, sheet_name="log")
        except Exception:
            df_log = pd.DataFrame(columns=["time", "log"])

        # Thêm username vào message nếu đang đăng nhập
        actor = st.session_state.get("username", "system") if hasattr(st, "session_state") else "system"
        full_msg = f"[{actor}] {log_message}"

        new_row = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "log": full_msg,
        }
        df_log = pd.concat([df_log, pd.DataFrame([new_row])], ignore_index=True)

        with pd.ExcelWriter(LOG_FILE, engine="openpyxl") as writer:
            df_users.to_excel(writer, sheet_name="users", index=False)
            df_log.to_excel(writer, sheet_name="log", index=False)

    except Exception as e:
        print(f"[Log Write Error] {e}")


def get_logs() -> pd.DataFrame:
    """Đọc toàn bộ log."""
    try:
        return pd.read_excel(LOG_FILE, sheet_name="log")
    except Exception:
        return pd.DataFrame(columns=["time", "log"])
