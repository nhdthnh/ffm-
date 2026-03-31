import streamlit as st
from sqlalchemy import text
from utils import get_engine
import utils_auth

def render_cart():
    engine = get_engine()
    st.markdown("---")
    st.subheader("📋 DANH SÁCH SẢN PHẨM XUẤT")
    
    if st.session_state.cart:
        # UI Styling cho Icon xoá gỡ bỏ CSS dư thừa
        st.markdown("""
            <style>
            div[data-testid="column"]:last-child div.stButton > button,
            div[data-testid="stColumn"]:last-child div.stButton > button {
                margin: 0 auto !important;
                margin-top: 4px !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                width: 32px !important;
                height: 32px !important;
                padding: 0px !important;
                border: none !important;
                background-color: transparent !important;
                box-shadow: none !important;
                outline: none !important;
                font-size: 14px !important;
                line-height: 1 !important;
            }
            div[data-testid="column"]:last-child div.stButton > button p,
            div[data-testid="stColumn"]:last-child div.stButton > button p {
                font-size: 14px !important;
                margin: 0 !important;
            }
            div[data-testid="column"]:last-child div.stButton > button:hover,
            div[data-testid="stColumn"]:last-child div.stButton > button:hover {
                background-color: #f0f2f6 !important;
                border-radius: 4px !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        col_widths = [1.5, 2.5, 1.5, 1.5, 2.0, 0.5]
        hc1, hc2, hc3, hc4, hc5, hc6 = st.columns(col_widths)
        hc1.markdown("**MÃ SP/BARCODE**")
        hc2.markdown("**TÊN SẢN PHẨM**")
        hc3.markdown("**HSD**")
        hc4.markdown("**SỐ LƯỢNG**")
        hc5.markdown("**GHI CHÚ**")
        hc6.markdown("")
        
        total_qty = 0
        for idx, item in enumerate(st.session_state.cart):
            with st.container():
                 c1, c2, c3, c4, c5, c6 = st.columns(col_widths)
                 ma_sp = str(item.get('Mã SP', ''))
                 barcode = str(item.get('Mã Barcode', ''))
                 c1.markdown(f"{ma_sp}<br><small>{barcode}</small>", unsafe_allow_html=True)
                 c2.write(str(item.get('Tên SP', '')))
                 
                 # Allow editing HSD
                 new_hsd = c3.text_input("HSD", value=str(item.get('HSD', '')), label_visibility="collapsed", key=f"hsd_{idx}")
                 st.session_state.cart[idx]['HSD'] = new_hsd
                 
                 # Allow editing Số lượng
                 new_sl = c4.number_input("Số lượng", value=int(item.get('Số lượng', 0)), step=1, label_visibility="collapsed", key=f"sl_{idx}")
                 st.session_state.cart[idx]['Số lượng'] = new_sl
                 total_qty += int(new_sl)
                 
                 # Allow editing Ghi chú
                 new_note = c5.text_input("Ghi chú", value=str(item.get('Ghi chú', '') if item.get('Ghi chú') is not None else ''), label_visibility="collapsed", key=f"note_{idx}")
                 st.session_state.cart[idx]['Ghi chú'] = new_note
                 
                 if c6.button("🗑️", key=f"del_{idx}"):
                     st.session_state.cart.pop(idx)
                     st.rerun()
                     
        st.markdown("---")
        st.markdown(f"**Tổng Số Lượng Cập Nhật: {total_qty:,}**")
        
        if st.button("💾 Cập nhật Database", type="secondary"):
            with engine.begin() as update_conn:
                updated_count = 0
                for item in st.session_state.cart:
                    row_id = item.get('Mã SP')
                    if row_id:
                        update_conn.execute(text("""
                            UPDATE ton_csr_co_chung_tu 
                            SET so_luong = :p_so_luong, han_su_dung = :p_hsd, ghi_chu = :p_note 
                            WHERE ma_sp = :p_id
                        """), {
                            "p_so_luong": int(item.get('Số lượng', 0)),
                            "p_hsd": item.get('HSD', ''),
                            "p_note": item.get('Ghi chú', ''),
                            "p_id": row_id
                        })
                        updated_count += 1
                if updated_count > 0:
                    detail_logs = []
                    for item in st.session_state.cart:
                        if item.get('Mã SP'):
                            barcode = item.get('Mã Barcode', '')
                            sl = int(item.get('Số lượng', 0))
                            hsd = item.get('HSD', '')
                            note = item.get('Ghi chú', '')
                            detail_logs.append(f"[{barcode} | SL: {sl} | HSD: {hsd} | Note: {note}]")
                            
                    detail_str = ", ".join(detail_logs)
                    uname = st.session_state.get('username', 'Unknown')
                    utils_auth.write_log(
                        f"Người dùng {uname} cập nhật {updated_count} SP (Tồn CSR có chứng từ): {detail_str}"
                    )
                    # Xoá cart sau khi xuất thành công
                    st.session_state.cart.clear()
                    st.success(f"✅ Đã cập nhật thành công {updated_count} dòng trong Database!")
                    st.rerun()
                else:
                    st.warning("⚠ Không tìm thấy Mã SP để cập nhật.")
    else:
        st.info("Chưa có sản phẩm nào được chọn.")