"""
app.py — Entrypoint chính của ứng dụng Kho nội bộ OQR
========================================================
Quản lý: Session, Auth, Sidebar navigation, Page routing.
"""

import streamlit as st
import base64
import time
from datetime import datetime

import utils_auth
from views import (
    thu_hoi_boxme, hang_nhap_kho_hcns, hang_ton_csr,
    kho_hcns_khong_chung_tu, tieu_huy, login,
    system_logs, report, template, about, user_management,
)

# ── Cấu hình trang ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kho nội bộ · OQR",
    page_icon="📦",
    layout="wide",
)

APP_VERSION = "v2.0"

# ── CSS toàn cục ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Font & Reset ── */
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif !important;
}

/* ── Bỏ padding mặc định của main block ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}

/* ── Sidebar tổng thể ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a2a1a 0%, #0d3522 60%, #0a2a1a 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * {
    color: #e8f5ee !important;
}

/* ── Radio → Nav menu ── */
div.stRadio > div[role='radiogroup'] > label > div:first-of-type {
    display: none !important;
}
div.stRadio > div[role='radiogroup'] {
    gap: 2px !important;
}
div.stRadio > div[role='radiogroup'] > label {
    background: transparent !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    margin: 0 !important;
    width: 100% !important;
    border: 1px solid transparent !important;
}
div.stRadio > div[role='radiogroup'] > label:hover {
    background: rgba(255,255,255,0.07) !important;
}
div.stRadio > div[role='radiogroup'] > label:has(input:checked) {
    background: rgba(52, 211, 153, 0.15) !important;
    border: 1px solid rgba(52, 211, 153, 0.35) !important;
}
div.stRadio > div[role='radiogroup'] > label:has(input:checked) p {
    color: #34d399 !important;
    font-weight: 600 !important;
}

/* ── Scrollbar mỏng ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #f8fffe;
    border: 1px solid #e0f2e9;
    border-radius: 10px;
    padding: 12px 16px !important;
}

/* ── Loại bỏ nền trắng của metric label ── */
[data-testid="stMetricLabel"] > div { color: #555 !important; }
[data-testid="stMetricValue"] { color: #0a2a1a !important; font-weight: 700 !important; }
/* ── Logout Button Styling ── */
section[data-testid="stSidebar"] [data-testid="stButton"] button {
    background-color: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-weight: 500 !important;
}

section[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background-color: rgba(255, 255, 255, 0.12) !important;
    border-color: rgba(255, 255, 255, 0.25) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

section[data-testid="stSidebar"] [data-testid="stButton"] button:active {
    transform: translateY(0) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Khởi tạo session state ────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def _do_logout():
    utils_auth.write_log("Đăng xuất hệ thống")
    for key in ["logged_in", "username", "full_name", "email", "is_superadmin", "permissions"]:
        st.session_state.pop(key, None)
    if "auth" in st.query_params:
        del st.query_params["auth"]
    st.rerun()


# ── Khôi phục phiên từ URL token (survive F5) ─────────────────────────────────
if not st.session_state.logged_in and "auth" in st.query_params:
    try:
        decoded_user = base64.b64decode(st.query_params["auth"]).decode("utf-8")
        user_info = utils_auth.get_user(decoded_user)
        if user_info:
            data = utils_auth.reload_user_data(decoded_user)
            st.session_state.update({
                "logged_in": True,
                "username": decoded_user,
                "full_name": str(user_info.get("full_name", decoded_user)) or decoded_user,
                "email": str(user_info.get("email", "")),
                "is_superadmin": data.get("is_superadmin", False),
                "permissions": data.get("permissions", {}),
                "session_version": data.get("session_version", 1),
            })
    except Exception:
        pass  # Token lỗi → yêu cầu đăng nhập lại


# ── Security Guard: kiểm tra phiên mỗi lần render ────────────────────────────
if st.session_state.logged_in:
    username = st.session_state.get("username")
    session_ver = st.session_state.get("session_version", 1)
    fresh_data = utils_auth.reload_user_data(username)

    user_locked = fresh_data and fresh_data.get("is_active", 1) == 0
    version_mismatch = fresh_data and fresh_data.get("session_version", 1) != session_ver
    user_missing = not fresh_data

    if user_missing or user_locked or version_mismatch:
        if user_locked:
            st.warning("⚠️ Tài khoản của bạn đã bị khoá bởi Quản trị viên.")
        else:
            st.warning("⚠️ Thông tin tài khoản đã thay đổi. Vui lòng đăng nhập lại.")
        time.sleep(2)
        _do_logout()


# ── Màn hình đăng nhập ────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    login.show()
    st.stop()


# ═════════════════════════════════════════════════════════════════════════════
# ĐỊNH NGHĨA TRANG — (label hiển thị, perm slug)
# ═════════════════════════════════════════════════════════════════════════════
ALL_PAGES = [
    ("📊 Report",               "perm_report"),
    ("📦 Thu hồi Boxme",        "perm_thu_hoi_boxme"),
    ("📥 Hàng nhập kho HCNS",  "perm_nhap_kho_hcns"),
    ("🧾 Hàng tồn CSR",        "perm_hang_ton_csr"),
    ("📋 HCNS không chứng từ", "perm_hcns_khong_ct"),
    ("🗑️ Tiêu hủy",            "perm_tieu_huy"),
    ("📄 Template",            "perm_template"),
    ("📓 Nhật ký hệ thống",    "perm_system_logs"),
    ("ℹ️ About",               "perm_about"),
    ("🔐 Quản lý người dùng",  "perm_user_mgmt"),
]

visible_pages = [
    label for label, slug in ALL_PAGES
    if utils_auth.get_perm(slug) >= 1
]

if not visible_pages:
    st.error("🚫 Tài khoản của bạn chưa được cấp quyền truy cập bất kỳ trang nào.")
    st.info("Vui lòng liên hệ quản trị viên.")
    if st.button("Đăng xuất", key="logout_no_perm"):
        _do_logout()
    st.stop()


# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Logo / Header ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding: 8px 4px 0 4px;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <span style="font-size:26px; line-height:1;">📦</span>
            <div>
                <div style="font-size:15px; font-weight:700; letter-spacing:0.5px; color:#ffffff;">KHO NỘI BỘ</div>
                <div style="font-size:11px; font-weight:400; color:#86b899; letter-spacing:1px;">OQR CO., LTD</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DB Status Badge ────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin: 6px 0 10px 0;">
        <span style="display:inline-flex; align-items:center; gap:5px;
                     background:rgba(52,211,153,0.15); border:1px solid rgba(52,211,153,0.35);
                     border-radius:20px; padding:3px 10px;
                     font-size:10px; font-weight:600; color:#34d399; letter-spacing:0.5px;">
            <span style="width:6px;height:6px;border-radius:50%;background:#34d399;display:inline-block;"></span>
            DB CONNECTED
        </span>
    </div>
    <div style="height:1px; background:rgba(255,255,255,0.08); margin-bottom:10px;"></div>
    """, unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:10px; font-weight:600; color:#6aaa82; letter-spacing:1.5px; '
        'margin-bottom:6px; padding-left:4px;">MENU</div>',
        unsafe_allow_html=True,
    )
    page = st.radio("nav", visible_pages, label_visibility="collapsed")

    # ── Divider ───────────────────────────────────────────────────────────
    st.markdown('<div style="height:1px; background:rgba(255,255,255,0.08); margin:14px 0 10px 0;"></div>', unsafe_allow_html=True)

    # ── User Info ─────────────────────────────────────────────────────────
    full_name = st.session_state.get("full_name") or st.session_state.get("username", "")
    uname = st.session_state.get("username", "")
    is_superadmin = st.session_state.get("is_superadmin", False)
    role_label = "👑 Siêu quản trị" if is_superadmin else "👤 Người dùng"
    role_color = "#f59e0b" if is_superadmin else "#86b899"

    st.markdown(f"""
    <div style="padding: 0 2px; margin-bottom:10px;">
        <div style="font-size:13px; font-weight:600; color:#ffffff;">{full_name}</div>
        <div style="font-size:11px; color:#86b899; margin-top:1px; font-family:'JetBrains Mono', monospace;">@{uname}</div>
        <div style="font-size:11px; font-weight:600; color:{role_color}; margin-top:3px;">{role_label}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⏻  Đăng xuất", use_container_width=True, key="sidebar_logout"):
        _do_logout()

    # ── Footer version ────────────────────────────────────────────────────
    now_str = datetime.now().strftime("%d/%m %H:%M")
    st.markdown(
        f'<div style="font-size:10px; color:#4a7a5e; text-align:left; margin-top:12px; '
        f'font-family:\'JetBrains Mono\', monospace;">{APP_VERSION} · {now_str}</div>',
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═════════════════════════════════════════════════════════════════════════════
PAGE_MAP = {
    "📊 Report":               (report.show,               "perm_report"),
    "📦 Thu hồi Boxme":        (thu_hoi_boxme.show,        "perm_thu_hoi_boxme"),
    "📥 Hàng nhập kho HCNS":  (hang_nhap_kho_hcns.show,  "perm_nhap_kho_hcns"),
    "🧾 Hàng tồn CSR":        (hang_ton_csr.show,         "perm_hang_ton_csr"),
    "📋 HCNS không chứng từ": (kho_hcns_khong_chung_tu.show, "perm_hcns_khong_ct"),
    "🗑️ Tiêu hủy":            (tieu_huy.show,             "perm_tieu_huy"),
    "📄 Template":            (template.show,             "perm_template"),
    "📓 Nhật ký hệ thống":    (system_logs.show,         "perm_system_logs"),
    "ℹ️ About":               (about.show,               "perm_about"),
    "🔐 Quản lý người dùng":  (user_management.show,     "perm_user_mgmt"),
}

if page in PAGE_MAP:
    show_fn, slug = PAGE_MAP[page]
    perm_level = utils_auth.get_perm(slug)

    if perm_level < 1:
        st.error("🚫 Bạn không có quyền truy cập trang này.")
        st.stop()

    st.session_state["page_readonly"] = (perm_level == 1)
    st.session_state["page_perm_level"] = perm_level
    show_fn()
