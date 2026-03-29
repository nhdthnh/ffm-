import streamlit as st
import base64
from views import thu_hoi_boxme, hang_nhap_kho_hcns, hang_ton_csr, kho_hcns_khong_chung_tu, tieu_huy, login, system_logs
import utils_auth

# Page configuration
st.set_page_config(page_title="Boxme Management", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Tính năng khôi phục phiên (Survive F5): Đọc token từ URL
if not st.session_state.logged_in and "auth" in st.query_params:
    try:
        encoded_token = st.query_params["auth"]
        decoded_user = base64.b64decode(encoded_token).decode("utf-8")
        st.session_state.logged_in = True
        st.session_state.username = decoded_user
        st.session_state.role = "user"
    except Exception:
        pass

if not st.session_state.logged_in:
    login.show()
else:
    # Sidebar Setup
    with st.sidebar:
        st.markdown(f"**Xin chào, {st.session_state.get('username', '')}** 👤")
        if st.button("Đăng xuất"):
            utils_auth.write_log(f"Người dùng {st.session_state.get('username', '')} đã Đăng xuất hệ thống")
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            # Xoá token khỏi thanh URL khi bấm đăng xuất
            if "auth" in st.query_params:
                del st.query_params["auth"]
            st.rerun()
            
        st.markdown("---")
        
        # Custom CSS to beautifully hack Streamlit radio buttons into a modern blocky Navbar
        st.markdown("""
        <style>
        /* Ẩn dấu chấm tròn mặc định của Radio */
        div.stRadio > div[role='radiogroup'] > label > div:first-of-type {
            display: none !important;
        }
        /* Style khối bao của từng mục chọn */
        div.stRadio > div[role='radiogroup'] {
            gap: 0.2rem;
        }
        div.stRadio > div[role='radiogroup'] > label {
            background-color: transparent;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            margin: 0;
            width: 100%;
        }
        /* Hiệu ứng trỏ chuột */
        div.stRadio > div[role='radiogroup'] > label:hover {
            background-color: #f0f2f6;
        }
        /* Thay đổi màu văn bản khi được chọn để tạo nền */
        div.stRadio > div[role='radiogroup'] > label:has(input:checked) {
            background-color: #c4f08c !important;
        }
        div.stRadio > div[role='radiogroup'] > label:has(input:checked) div, 
        div.stRadio > div[role='radiogroup'] > label:has(input:checked) p {
            color: #1a1a1a !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "Điều hướng",
            [
                "📦 Thu hồi Boxme",
                "📥 Hàng nhập kho HCNS",
                "🧾 Hàng tồn CSR",
                "📋 HCNS không chứng từ",
                "🗑️ Tiêu hủy",
                "📓 Nhật ký hệ thống",
                "📊 Report"
            ],
            label_visibility="collapsed"
        )

    # Routing
    if page == "📦 Thu hồi Boxme":
        thu_hoi_boxme.show()
    elif page == "📥 Hàng nhập kho HCNS":
        hang_nhap_kho_hcns.show()
    elif page == "🧾 Hàng tồn CSR":
        hang_ton_csr.show()
    elif page == "📋 HCNS không chứng từ":
        kho_hcns_khong_chung_tu.show()
    elif page == "🗑️ Tiêu hủy":
        tieu_huy.show()
    elif page == "📓 Nhật ký hệ thống":
        system_logs.show()