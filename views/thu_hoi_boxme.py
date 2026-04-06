"""
views/thu_hoi_boxme.py — Trang quản lý Thu hồi Boxme
"""

import streamlit as st
import utils_auth
from views.components.thu_hoi_boxme import boxme_import, boxme_filters, boxme_grid, boxme_cart


def show():
    if "cart" not in st.session_state:
        st.session_state.cart = []

    st.markdown("## 📦 Thu hồi Boxme")

    utils_auth.require_perm("perm_thu_hoi_boxme", required=1)
    readonly = st.session_state.get("page_readonly", False)
    if readonly:
        utils_auth.show_readonly_banner()

    try:
        if not readonly:
            boxme_import.render_import_section()

        selected_date, selected_phan_loai, selected_skus = boxme_filters.render_filters()
        boxme_grid.render_data_grid(selected_date, selected_phan_loai, selected_skus)

        if not readonly:
            boxme_cart.render_cart()

    except Exception as e:
        st.error(f"❌ Lỗi tải dữ liệu: {e}")
