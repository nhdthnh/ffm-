import streamlit as st
from views.components.kho_hcns_khong_chung_tu import filters, grid, cart, import_excel

def show():
    if "cart" not in st.session_state:
        st.session_state.cart = []
        
    st.title("📦 Hàng nhập kho HCNS - Không chứng từ")
    
    try:
        # Khối Component 1: Giao diện Import Excel an toàn.
        import_excel.render_import_section()
        
        # Khối Component 2: Các cụm Filters (Ngày, Thể loại, SKU)
        selected_skus = filters.render_filters()
        
        # Khối Component 3: Bảng dữ liệu Grid Ag-Grid / Dataframe natively
        grid.render_data_grid(selected_skus)
        
        # Khối Component 4: Giỏ hàng và cập nhật database
        cart.render_cart()
        
    except Exception as e:
        st.error(f"Failed to load data components: {e}")