"""
views/login.py — Màn hình đăng nhập OQR Kho nội bộ
"""

import base64
import streamlit as st
import utils_auth


def show():
    # ── CSS toàn màn hình login ──────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');

    /* Nền tổng */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a2a1a 0%, #0d3d26 50%, #061a10 100%) !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    /* Form container */
    .login-card {
        background: rgba(255,255,255,0.04);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        max-width: 420px;
        margin: 0 auto;
    }

    /* ── Zero White Strategy: Unified Dark Inputs ───────────────────── */
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-testid="stTextInput"] [role="textbox"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] > div {
        background-color: #0c3d26 !important; /* Solid Dark Green */
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        transition: all 0.2s ease !important;
    }

    /* Focus & Active State: Even more specific for Solid Dark Green */
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:active {
        background-color: #08291a !important; 
        border-color: #34d399 !important;
        box-shadow: 0 0 0 2px rgba(52,211,153,0.2) !important;
    }

    div[data-testid="stTextInput"] label {
        color: #a7c4b2 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        margin-bottom: 6px !important;
    }

    /* Aggressive Autofill Overrides - Forced Dark Inset */
    input:-webkit-autofill,
    input:-webkit-autofill:hover, 
    input:-webkit-autofill:focus,
    input:-internal-autofill-selected {
        -webkit-box-shadow: 0 0 0px 1000px #0c3d26 inset !important;
        -webkit-text-fill-color: #ffffff !important;
        caret-color: #ffffff !important;
        transition: background-color 5000s ease-in-out 0s !important;
    }

    /* Submit button */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #34d399 0%, #059669 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px !important;
        transition: all 0.2s ease !important;
        font-family: 'Be Vietnam Pro', sans-serif !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(52,211,153,0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Layout ───────────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        # Logo & tiêu đề
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-size:52px; margin-bottom:8px;">📦</div>
            <div style="font-size:24px; font-weight:700; color:#ffffff; letter-spacing:0.5px;">Kho nội bộ OQR</div>
            <div style="font-size:13px; color:#6aaa82; margin-top:4px; letter-spacing:1px;">OQR CO., LTD · WAREHOUSE MANAGEMENT</div>
        </div>
        """, unsafe_allow_html=True)

        # Form đăng nhập
        with st.form("login_form", clear_on_submit=False):
            st.markdown('<div style="color:#c8e6d6; font-size:13px; margin-bottom:12px;">Vui lòng nhập thông tin đăng nhập</div>', unsafe_allow_html=True)

            username = st.text_input("Tên đăng nhập", placeholder="username")
            password = st.text_input("Mật khẩu", type="password", placeholder="••••••••")

            submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.warning("⚠️ Vui lòng điền đầy đủ thông tin.")
                else:
                    success, user_info = utils_auth.authenticate_user(username, password)
                    if success and user_info:
                        if user_info.get("locked"):
                            st.error("🔒 Tài khoản đã bị khoá. Liên hệ quản trị viên.")
                        else:
                            st.session_state.update({
                                "logged_in": True,
                                "username": user_info["username"],
                                "full_name": user_info["full_name"],
                                "email": user_info.get("email", ""),
                                "is_superadmin": user_info.get("is_superadmin", False),
                                "permissions": user_info.get("permissions", {}),
                                "session_version": user_info.get("session_version", 1),
                            })
                            utils_auth.write_log("Đăng nhập hệ thống thành công")
                            st.query_params["auth"] = base64.b64encode(
                                user_info["username"].encode("utf-8")
                            ).decode("utf-8")
                            st.success("✅ Đăng nhập thành công!")
                            st.rerun()
                    else:
                        st.error("❌ Tên đăng nhập hoặc mật khẩu không đúng.")

        st.markdown("""
        <div style="text-align:center; margin-top:2rem; color:#4a7a5e; font-size:11px;">
            v2.0 · OQR Co., Ltd · Hệ thống quản lý kho nội bộ
        </div>
        """, unsafe_allow_html=True)
