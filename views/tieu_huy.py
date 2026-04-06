"""
views/tieu_huy.py — Trang quản lý Tiêu hủy
"""

import streamlit as st
import utils_auth
from views.components.tieu_huy import filters, grid


def show():
    st.markdown("## 🗑️ Tiêu hủy")

    utils_auth.require_perm("perm_tieu_huy", required=1)
    readonly = st.session_state.get("page_readonly", False)
    if readonly:
        utils_auth.show_readonly_banner()

    try:
        if not readonly:
            from views.components.tieu_huy import import_excel
            import_excel.render_import_section()

        selected_ngay, selected_phan_loai, selected_skus = filters.render_filters()
        grid.render_data_grid(selected_ngay, selected_phan_loai, selected_skus)

        if not readonly:
            from views.components.tieu_huy import cart
            cart.render_cart()

    except Exception as e:
        st.error(f"❌ Lỗi tải dữ liệu: {e}")
