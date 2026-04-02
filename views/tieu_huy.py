import streamlit as st
from views.components.tieu_huy import filters, grid

def show():
    st.title("🗑 Tiêu hủy")
    
    # Khu vực Import Excel
    from views.components.tieu_huy import import_excel
    import_excel.render_import_section()
    
    try:
        # Khối Component 1: Các cụm Filters (Ngày, Phân loại, SKU)
        selected_ngay, selected_phan_loai, selected_skus = filters.render_filters()
        
        # Khối Component 2: Bảng dữ liệu Grid Ag-Grid / Dataframe natively
        grid.render_data_grid(selected_ngay, selected_phan_loai, selected_skus)

        # Khối Component 3: Giỏ hàng
        from views.components.tieu_huy import cart
        cart.render_cart()
        
    except Exception as e:
        st.error(f"Failed to load data components: {e}")
