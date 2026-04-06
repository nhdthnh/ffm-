"""
views/hang_ton_csr.py — Trang quản lý Hàng tồn CSR
"""

import streamlit as st
import utils_auth
from views.components.ton_csr import filters, grid, import_excel, cart


def show():
    st.markdown("## 🧾 Hàng tồn CSR")

    utils_auth.require_perm("perm_hang_ton_csr", required=1)
    readonly = st.session_state.get("page_readonly", False)
    if readonly:
        utils_auth.show_readonly_banner()

    try:
        if not readonly:
            import_excel.render_import_section()

        selected_ngay, selected_skus = filters.render_filters()
        grid.render_data_grid(selected_ngay, selected_skus)

        if not readonly:
            cart.render_cart()

    except Exception as e:
        st.error(f"❌ Lỗi tải dữ liệu: {e}")
