import streamlit as st
from views.components.tieu_huy import filters, grid

def show():
    st.title("🗑 Tiêu hủy")
    
    try:
        # Khối Component 1: Các cụm Filters (Ngày, Thể loại, SKU)
        selected_phan_loai, selected_skus = filters.render_filters()
        
        # Khối Component 2: Bảng dữ liệu Grid Ag-Grid / Dataframe natively
        # grid.render_data_grid(selected_phan_loai, selected_skus)
        
    except Exception as e:
        st.error(f"Failed to load data components: {e}")
