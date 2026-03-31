import streamlit as st
from views.components.ton_csr import filters, grid, import_excel, cart

def show():
    st.title("📦 Hàng tồn CSR")
    
    # Khu vực Import Excel
    import_excel.render_import_section()
    
    try:
        # Khối Component 1: Các cụm Filters (Ngày, Thể loại, SKU)
        selected_ngay, selected_skus = filters.render_filters()
        
        # Khối Component 2: Bảng dữ liệu Grid Ag-Grid / Dataframe natively
        grid.render_data_grid(selected_ngay, selected_skus)
        
        # Khối Component 3: Giỏ hàng (Cart)
        cart.render_cart()
        
    except Exception as e:
        st.error(f"Failed to load data components: {e}")
