"""
CSS dùng chung cho toàn bộ cart components.
Import bằng: from views.components._shared import inject_cart_css
"""

import streamlit as st

_CART_BUTTON_CSS = """
<style>
/* Nút xóa hàng trong cart — nhỏ, trong suốt */
div[data-testid="stColumn"]:last-child div.stButton > button {
    margin: 4px auto 0 auto !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    font-size: 14px !important;
    line-height: 1 !important;
}
div[data-testid="stColumn"]:last-child div.stButton > button p {
    font-size: 14px !important;
    margin: 0 !important;
}
div[data-testid="stColumn"]:last-child div.stButton > button:hover {
    background: #f0f2f6 !important;
    border-radius: 4px !important;
}
</style>
"""


def inject_cart_css():
    """Inject CSS chuẩn cho nút xóa trong cart."""
    st.markdown(_CART_BUTTON_CSS, unsafe_allow_html=True)
