import streamlit as st
import base64
from views import thu_hoi_boxme, hang_nhap_kho_hcns, hang_ton_csr, kho_hcns_khong_chung_tu, tieu_huy, login, system_logs, report, template, about
import utils_auth

# Page configuration
st.set_page_config(page_title="Kho nội bộ · OQR", page_icon="📦", layout="wide")

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
        # Title
        st.markdown("## 📦 KHO NỘI BỘ")
        st.markdown('<p style="font-size: 14px; font-weight: bold; margin-top: -15px; margin-bottom: 5px;">OQR Co.LTd</p>', unsafe_allow_html=True)
        st.markdown('<hr style="margin: 5px 0 10px 0; border: none; border-top: 1px solid #e6e6e6;">', unsafe_allow_html=True)
        
        # DB status
        st.markdown("""
        <div style='background-color: #e6fced; padding: 4px 10px; border-radius: 6px; color: #02381f; font-weight: 600; font-size: 0.8rem; width: fit-content; margin-bottom: 5px; border: 1px solid #bdf2cc'>
            ● DB CONNECTED
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<hr style="margin: 0px 0 10px 0; border: none; border-top: 1px solid #e6e6e6;">', unsafe_allow_html=True)
        
        # Custom CSS to beautifully hack Streamlit radio buttons into a modern blocky Navbar
        st.markdown("""
        <style>
        /* Ẩn dấu chấm tròn mặc định của Radio */
        div.stRadio > div[role='radiogroup'] > label > div:first-of-type {
            display: none !important;
        }
        /* Style khối bao của từng mục chọn */
        div.stRadio > div[role='radiogroup'] {
            gap: 0.1rem;
        }
        div.stRadio > div[role='radiogroup'] > label {
            background-color: transparent;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            margin: 0;
            width: 100%;
            border: 1px solid transparent;
        }
        /* Hiệu ứng trỏ chuột */
        div.stRadio > div[role='radiogroup'] > label:hover {
            background-color: rgba(3, 102, 54, 0.05);
        }
        /* Thay đổi màu văn bản khi được chọn để tạo nền trong suốt, viền xám xanh nhẹ */
        div.stRadio > div[role='radiogroup'] > label:has(input:checked) {
            background-color: rgba(3, 102, 54, 0.15) !important;
            border: 1px solid rgba(3, 102, 54, 0.3) !important;
        }
        div.stRadio > div[role='radiogroup'] > label:has(input:checked) div, 
        div.stRadio > div[role='radiogroup'] > label:has(input:checked) p {
            color: #036636 !important;
            font-weight: 700 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "Điều hướng",
            [
                "📊 Report",
                "📦 Thu hồi Boxme",
                "📥 Hàng nhập kho HCNS",
                "🧾 Hàng tồn CSR",
                "📋 HCNS không chứng từ",
                "🗑️ Tiêu hủy",
                "📄 Template",
                "📓 Nhật ký hệ thống",
                "ℹ️ About"
            ],
            label_visibility="visible"
        )
        
        st.markdown('<hr style="margin: 15px 0 10px 0; border: none; border-top: 1px solid #e6e6e6;">', unsafe_allow_html=True)
        st.markdown(f"**Người dùng:** {st.session_state.get('username', '')} 👤")
        if st.button("Đăng xuất", use_container_width=True):
            utils_auth.write_log(f"Người dùng {st.session_state.get('username', '')} đã Đăng xuất hệ thống")
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            if "auth" in st.query_params:
                del st.query_params["auth"]
            st.rerun()
            
        from datetime import datetime
        now_str = datetime.now().strftime("%d/%m %H:%M")
        st.markdown(f"<p style='font-size: 11px; color: #888; text-align: left; margin-top: 15px;'>v1.0 · {now_str}</p>", unsafe_allow_html=True)

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
    elif page == "📄 Template":
        template.show()
    elif page == "📓 Nhật ký hệ thống":
        system_logs.show()
    elif page == "ℹ️ About":
        about.show()
    elif page == "📊 Report":
        report.show()