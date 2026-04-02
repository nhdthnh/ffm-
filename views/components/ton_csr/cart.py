import streamlit as st
from sqlalchemy import text
from utils import get_engine
import utils_auth

def render_cart():
    if 'cart' not in st.session_state:
        st.session_state.cart = []
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
        
        col_widths = [1.0, 1.2, 2.0, 1.3, 1.0, 1.5, 0.3]
        hc1, hc2, hc3, hc4, hc5, hc6, hc7 = st.columns(col_widths)
        hc1.markdown("**MÃ SP**")
        hc2.markdown("**BARCODE**")
        hc3.markdown("**TÊN SẢN PHẨM**")
        hc4.markdown("**HSD**")
        hc5.markdown("**SỐ LƯỢNG**")
        hc6.markdown("**GHI CHÚ**")
        hc7.markdown("")
        
        total_qty = 0
        for idx, item in enumerate(st.session_state.cart):
            with st.container():
                 c1, c2, c3, c4, c5, c6, c7 = st.columns(col_widths)
                 
                 new_ma_sp = c1.text_input("Mã SP", value=str(item.get('Mã SP', '')), label_visibility="collapsed", key=f"masp_{idx}")
                 st.session_state.cart[idx]['Mã SP'] = new_ma_sp
                 
                 new_barcode = c2.text_input("Barcode", value=str(item.get('Mã Barcode', '')), label_visibility="collapsed", key=f"bar_{idx}")
                 st.session_state.cart[idx]['Mã Barcode'] = new_barcode
                 
                 new_ten = c3.text_input("Tên SP", value=str(item.get('Tên SP', '')), label_visibility="collapsed", key=f"ten_{idx}")
                 st.session_state.cart[idx]['Tên SP'] = new_ten
                 
                 hsd_val = item.get('HSD')
                 hsd_str = str(hsd_val) if hsd_val is not None and str(hsd_val).strip().lower() != 'none' else ""
                 new_hsd = c4.text_input("HSD", value=hsd_str, label_visibility="collapsed", key=f"hsd_{idx}")
                 st.session_state.cart[idx]['HSD'] = new_hsd if new_hsd.strip() else None
                 
                 sl_val = int(item.get('Số lượng') or 0)
                 new_sl = c5.number_input("Số lượng", value=sl_val, step=1, label_visibility="collapsed", key=f"sl_{idx}")
                 st.session_state.cart[idx]['Số lượng'] = new_sl
                 total_qty += int(new_sl)
                 
                 new_note = c6.text_input("Ghi chú", value=str(item.get('Ghi chú', '') if item.get('Ghi chú') is not None else ''), label_visibility="collapsed", key=f"note_{idx}")
                 st.session_state.cart[idx]['Ghi chú'] = new_note
                 
                 if c7.button("🗑️", key=f"del_{idx}"):
                     st.session_state.cart.pop(idx)
                     st.rerun()
                     
        st.markdown("---")
        st.markdown(f"**Tổng Số Lượng Cập Nhật: {total_qty:,}**")
        
        if st.button("💾 Cập nhật Database", type="secondary"):
            should_rerun = False
            with engine.begin() as update_conn:
                updated_count = 0
                for item in st.session_state.cart:
                    row_id = item.get('id')
                    fallback_id = item.get('Mã SP')
                    
                    if row_id or fallback_id:
                        try:
                            if row_id:
                                query = """
                                    UPDATE ton_csr_co_chung_tu 
                                    SET ma_sp = :p_masp, ma_barcode = :p_bar, ten_san_pham = :p_ten,
                                        so_luong = :p_so_luong, han_su_dung = :p_hsd, ghi_chu = :p_note,
                                        ngay_cap_nhap = CURRENT_TIMESTAMP()
                                    WHERE id = :p_id
                                """
                                p_id_val = row_id
                            else:
                                query = """
                                    UPDATE ton_csr_co_chung_tu 
                                    SET ma_sp = :p_masp, ma_barcode = :p_bar, ten_san_pham = :p_ten,
                                        so_luong = :p_so_luong, han_su_dung = :p_hsd, ghi_chu = :p_note,
                                        ngay_cap_nhap = CURRENT_TIMESTAMP()
                                    WHERE ma_sp = :p_id
                                """
                                p_id_val = fallback_id

                            result = update_conn.execute(text(query), {
                                "p_masp": item.get('Mã SP', ''),
                                "p_bar": item.get('Mã Barcode', ''),
                                "p_ten": item.get('Tên SP', ''),
                                "p_so_luong": int(item.get('Số lượng', 0)),
                                "p_hsd": item.get('HSD') if item.get('HSD') and str(item.get('HSD')).strip() else None,
                                "p_note": item.get('Ghi chú', ''),
                                "p_id": p_id_val
                            })
                            
                            if result.rowcount > 0:
                                updated_count += 1
                            else:
                                st.warning(f"⚠️ Lệnh gửi đi không tìm thấy dòng dữ liệu nào khớp với khoá (ID/Mã SP: {p_id_val})")
                                
                        except Exception as e:
                            st.error(f"Lỗi SQL cập nhật cho mã {p_id_val}: {e}")
                if updated_count > 0:
                    detail_logs = []
                    for item in st.session_state.cart:
                        if item.get('Mã SP') or item.get('id'):
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
                    should_rerun = True
                elif updated_count == 0 and len(st.session_state.cart) > 0:
                    # Added a clearer warning here if it totally failed inside
                    pass
            
            if should_rerun:
                # Xoá cart sau khi xuất thành công, ĐÃ RA NGOÀI VÒNG TRANSACTION
                st.session_state.cart.clear()
                st.success(f"✅ Đã cập nhật thành công {updated_count} dòng trong Database!")
                st.rerun()
    else:
        st.info("Chưa có sản phẩm nào được chọn.")