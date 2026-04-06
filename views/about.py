"""
views/about.py — Thông tin phiên bản & nhật ký cập nhật
"""

import streamlit as st
from datetime import date


def show():
    st.markdown("## ℹ️ About · Thông tin hệ thống")
    st.markdown("---")

    # ── Thông tin chung ──────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Ứng dụng", "Kho nội bộ OQR")
    c2.metric("🔢 Phiên bản", "v2.0")
    c3.metric("🗓️ Cập nhật", "06/04/2026")

    st.markdown("---")

    # ── Tech stack ───────────────────────────────────────────────────────────
    st.markdown("### 🛠️ Công nghệ sử dụng")

    tech = {
        "Python 3.11+": "Ngôn ngữ lập trình chính",
        "Streamlit": "Framework giao diện web",
        "SQLAlchemy + PyMySQL": "Kết nối & tương tác cơ sở dữ liệu",
        "MariaDB / MySQL": "Cơ sở dữ liệu chính (192.168.1.119)",
        "Pandas + OpenPyXL": "Xử lý & import dữ liệu Excel",
        "openpyxl": "Đọc/ghi file .xlsx",
    }
    cols = st.columns(2)
    for i, (k, v) in enumerate(tech.items()):
        cols[i % 2].markdown(f"- **{k}** — {v}")

    st.markdown("---")

    # ── Nhật ký cập nhật ─────────────────────────────────────────────────────
    st.markdown("### 📋 Nhật ký cập nhật (Changelog)")

    with st.expander("**v2.0** — 06/04/2026  *(Hiện tại)*", expanded=True):
        st.markdown("""
        - 🎨 **Giao diện toàn bộ** được thiết kế lại: sidebar tối gradient xanh lá, login screen immersive, font *Be Vietnam Pro*.
        - 🔐 **Login page** mới hoàn toàn: nền gradient tối, form glassmorphism, animation hover nút.
        - 📊 **Metric cards** được định kiểu nhất quán trên toàn app.
        - 🧹 **Clean code**: xóa các file test/debug thừa (`test.py`, `src/test.py`, `src/debug_cols.py`), gom import, loại bỏ comment thừa.
        - 📖 **README.md** — tài liệu hướng dẫn đầy đủ được tạo mới.
        - ⚡ Tối ưu session guard: logic gọn hơn, `st.stop()` sau login để tránh re-render.
        - 🔢 Cập nhật version `v2.0` trên toàn app.
        """)

    with st.expander("**v1.1** — 03/04/2026"):
        st.markdown("""
        - Hoàn thiện hệ thống đăng nhập / xác thực SHA256.
        - Quản lý session version — tự động đăng xuất khi admin sửa tài khoản.
        - Thêm trang Quản lý người dùng & phân quyền RBAC đầy đủ (0/1/2/9).
        - Thêm trang Nhật ký hệ thống.
        - Token URL để survive F5 reload.
        """)

    with st.expander("**v1.0** — 28/03/2026"):
        st.markdown("""
        - Ra mắt lần đầu hệ thống Kho nội bộ OQR.
        - Import Excel vào các module: Thu hồi Boxme, Nhập kho HCNS, Tồn CSR, Tiêu hủy, HCNS không chứng từ.
        - Sidebar navigation với phân quyền theo trang.
        - Kết nối MySQL/MariaDB nội bộ (192.168.1.119).
        - Tải template Excel.
        - Tích hợp báo cáo Google Looker Studio.
        """)

    st.markdown("---")

    # ── Liên hệ / Thông tin ──────────────────────────────────────────────────
    st.markdown("### 📬 Thông tin dự án")
    st.markdown("""
    | Mục | Chi tiết |
    |-----|----------|
    | **Đơn vị** | OQR Co., Ltd |
    | **Database** | MariaDB tại `192.168.1.119:3306` · schema `oqr_kho` |
    | **Log file** | `log/db_log.xlsx` (sheet `log` + sheet `users`) |
    | **Templates** | `templates/` — file Excel mẫu để import |
    """)
