import streamlit as st
from views.components.thu_hoi_boxme import boxme_import, boxme_filters, boxme_grid, boxme_cart

def show():
    if "cart" not in st.session_state:
        st.session_state.cart = []
        
    st.title("📦 Thu hồi Boxme")
    
    try:
        # Khối Component 1: Giao diện Import Excel an toàn.
        boxme_import.render_import_section()
        
        # Khối Component 2: Các cụm Filters (Ngày, Thể loại, SKU)
        selected_date, selected_phan_loai, selected_skus = boxme_filters.render_filters()
        
        # Khối Component 3: Bảng dữ liệu Grid Ag-Grid / Dataframe natively
        boxme_grid.render_data_grid(selected_date, selected_phan_loai, selected_skus)
        
        # Khối Component 4: Giỏ hàng và cập nhật database
        boxme_cart.render_cart()
        
    except Exception as e:
        st.error(f"Failed to load data components: {e}")
