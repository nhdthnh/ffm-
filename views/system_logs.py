import streamlit as st
import utils_auth

def show():
    st.title("🛡️ Nhật ký Hệ thống")
    st.markdown("Xem lịch sử thao tác của các tài khoản.")
    
    # Tải dữ liệu log
    df_logs = utils_auth.get_logs()
    
    if not df_logs.empty:
        # Sort logs by timestamp descending (mới nhất lên trên)
        if 'time' in df_logs.columns:
            df_logs = df_logs.sort_values(by="time", ascending=False)
        
        # Áp dụng bộ lọc cơ bản
        search_query = st.text_input("🔍 Tìm kiếm nội dung Log", placeholder="Nhập từ khóa...")
        
        if search_query:
            # Lọc nếu log chứa chuỗi cần tìm kiếm (không phân biệt hoa/thường)
            df_logs = df_logs[df_logs["log"].astype(str).str.contains(search_query, case=False, na=False)]
            
        st.dataframe(
            df_logs, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "time": st.column_config.DatetimeColumn("Thời gian", format="DD/MM/YYYY HH:mm:ss"),
                "log": st.column_config.TextColumn("Ghi chú thao tác")
            }
        )
    else:
        st.info("Chưa có dữ liệu nhật ký nào.")
