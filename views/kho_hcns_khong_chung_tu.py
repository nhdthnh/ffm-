"""
views/kho_hcns_khong_chung_tu.py — Trang HCNS không chứng từ
"""

import streamlit as st
import utils_auth
from views.components.kho_hcns_khong_chung_tu import filters, grid, cart, import_excel


def show():
    if "cart" not in st.session_state:
        st.session_state.cart = []

    st.markdown("## 📋 HCNS không chứng từ")

    utils_auth.require_perm("perm_hcns_khong_ct", required=1)
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
