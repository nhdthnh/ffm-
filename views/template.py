import streamlit as st
import os

def show():
    st.title("📄 Tải Xuống Template")
    st.markdown("---")
    
    templates_dir = "templates"
    
    files = [
        "(ALL) FFM_Tổng hợp hàng xuất kho Boxme về văn phòng.xlsx",
        "OQR_TỔN KHO HCNS.xlsx"
    ]
    
    st.info("Vui lòng chọn mẫu báo cáo bên dưới để tải về phiên bản Excel gốc. Lưu ý chỉ nhập dữ liệu cần import, các dữ liệu cũ cần xóa đi")
    
    col1, col2 = st.columns(2)
    
    for idx, filename in enumerate(files):
        filepath = os.path.join(templates_dir, filename)
        
        # Select column
        col = col1 if idx % 2 == 0 else col2
        
        with col:
            st.markdown(f"### 📎 Mẫu {idx + 1}")
            st.write(f"**{filename}**")
            
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    file_data = f.read()
                    
                st.download_button(
                    label=f"📥 Tải xuống (Mẫu {idx +1})",
                    data=file_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.error(f"❌ Không tìm thấy file: {filename}")
                
            st.markdown("---")
