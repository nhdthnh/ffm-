import streamlit as st

def show():
    st.title("ℹ️ Thông tin phiên bản (About)")
    st.markdown("---")
    
    st.subheader("Nhật ký cập nhật (Changelogs)")
    
    st.markdown("""
    **v1.0 - 03/04/2026**
    - Cập nhật giao diện Sidebar mới: tối ưu các padding, gap, giao diện Menu xanh biển đậm trong suốt hiện đại.
    - Sắp xếp vị trí Title "Kho nội bộ OQR" và "DB Connected" lên đầu. Tách User và Đăng xuất cố định dưới cùng.
    - Áp dụng phân loại sản phẩm linh hoạt kết hợp tình trạng hiển thị bảng dữ liệu.
    - Điều chỉnh màu sắc giao diện cảnh báo 'Hết hạn' nổi bật hơn.
    """)
