"""
views/hang_nhap_kho_hcns.py — Trang quản lý Hàng nhập kho HCNS
"""

import streamlit as st
import utils_auth
from views.components.nhap_kho_hcns import filters, grid, cart, import_excel


def show():
    if "cart" not in st.session_state:
        st.session_state.cart = []

    st.markdown("## 📥 Hàng nhập kho HCNS")

    utils_auth.require_perm("perm_nhap_kho_hcns", required=1)
    readonly = st.session_state.get("page_readonly", False)
    if readonly:
        utils_auth.show_readonly_banner()

    try:
        if not readonly:
            import_excel.render_import_section()

        selected_date, selected_skus = filters.render_filters()
        grid.render_data_grid(selected_date, selected_skus)

        if not readonly:
            cart.render_cart()

    except Exception as e:
        st.error(f"❌ Lỗi tải dữ liệu: {e}")
