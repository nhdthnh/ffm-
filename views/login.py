import streamlit as st
import utils_auth

def show():
    # Thêm chút CSS cho giao diện đăng nhập đẹp hơn
    st.markdown("""
        <style>
        .login-box {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>🔒 Đăng Nhập Hệ Thống</h1>", unsafe_allow_html=True)
    
    # Tạo layout căn giữa
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### Vui lòng nhập thông tin")
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            
            submit = st.form_submit_button("Đăng nhập", use_container_width=True)
            
            if submit:
                if username and password:
                    success, user = utils_auth.authenticate_user(username, password)
                    if success:
                        import base64
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = user
                        st.session_state["role"] = "user" # default role placeholder
                        utils_auth.write_log(f"Người dùng {user} đã Đăng nhập hệ thống thành công")
                        
                        # Lưu token vào URL parameter để giữ đăng nhập khi F5
                        st.query_params["auth"] = base64.b64encode(user.encode("utf-8")).decode("utf-8")
                        
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Tên đăng nhập hoặc mật khẩu không chính xác.")
                else:
                    st.warning("Vui lòng điền đầy đủ thông tin.")
