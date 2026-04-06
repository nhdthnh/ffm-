import streamlit as st
from sqlalchemy import text
from utils import get_engine
import utils_auth
from views.components._shared import inject_cart_css

def render_cart():
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    engine = get_engine()
    st.markdown("---")
    st.subheader("📋 QUẢN LÝ DANH SÁCH TIÊU HUỶ")
    
    if st.session_state.cart:
        inject_cart_css()
        
        col_widths = [1.5, 2.5, 1.2, 1.5, 1.0, 0.4]
        hc1, hc2, hc3, hc4, hc5, hc6 = st.columns(col_widths)
        hc1.markdown("**MÃ BARCODE**")
        hc2.markdown("**TÊN SẢN PHẨM**")
        hc3.markdown("**PHÂN LOẠI**")
        hc4.markdown("**HSD**")
        hc5.markdown("**SỐ LƯỢNG**")
        hc6.markdown("")
        
        total_qty = 0
        for idx, item in enumerate(st.session_state.cart):
            with st.container():
                 c1, c2, c3, c4, c5, c6 = st.columns(col_widths)
                 
                 new_barcode = c1.text_input("Barcode", value=str(item.get('Mã Barcode', '')), label_visibility="collapsed", key=f"bar_{idx}")
                 st.session_state.cart[idx]['Mã Barcode'] = new_barcode
                 
                 new_ten = c2.text_input("Tên SP", value=str(item.get('Tên SP', '')), label_visibility="collapsed", key=f"ten_{idx}")
                 st.session_state.cart[idx]['Tên SP'] = new_ten
                 
                 new_pl = c3.text_input("Phân loại", value=str(item.get('Phân loại', '')), label_visibility="collapsed", key=f"pl_{idx}")
                 st.session_state.cart[idx]['Phân loại'] = new_pl
                 
                 hsd_val = item.get('HSD')
                 hsd_str = str(hsd_val) if hsd_val is not None and str(hsd_val).strip().lower() != 'none' else ""
                 new_hsd = c4.text_input("HSD", value=hsd_str, label_visibility="collapsed", key=f"hsd_{idx}")
                 st.session_state.cart[idx]['HSD'] = new_hsd if new_hsd.strip() else None
                 
                 sl_val = int(item.get('Số lượng') or 0)
                 new_sl = c5.number_input("Số lượng", value=sl_val, step=1, label_visibility="collapsed", key=f"sl_{idx}")
                 st.session_state.cart[idx]['Số lượng'] = new_sl
                 total_qty += int(new_sl)
                 
                 if c6.button("🗑️", key=f"del_{idx}"):
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
                    fallback_id = item.get('Mã Barcode')
                    
                    if row_id or fallback_id:
                        try:
                            if row_id:
                                query = """
                                    UPDATE tieu_huy 
                                    SET ma_barcode = :p_bar,
                                        ten_san_pham = :p_ten,
                                        phan_loai = :p_pl,
                                        han_su_dung = :p_hsd,
                                        so_luong = :p_so_luong,
                                        ngay_cap_nhap = CURRENT_TIMESTAMP()
                                    WHERE id = :p_id
                                """
                                p_id_val = row_id
                            else:
                                query = """
                                    UPDATE tieu_huy 
                                    SET ten_san_pham = :p_ten,
                                        phan_loai = :p_pl,
                                        han_su_dung = :p_hsd,
                                        so_luong = :p_so_luong,
                                        ngay_cap_nhap = CURRENT_TIMESTAMP()
                                    WHERE ma_barcode = :p_id
                                """
                                p_id_val = fallback_id

                            result = update_conn.execute(text(query), {
                                "p_bar": item.get('Mã Barcode', ''),
                                "p_ten": item.get('Tên SP', ''),
                                "p_pl": item.get('Phân loại', ''),
                                "p_so_luong": int(item.get('Số lượng', 0)),
                                "p_hsd": item.get('HSD') if item.get('HSD') and str(item.get('HSD')).strip() else None,
                                "p_id": p_id_val
                            })
                            
                            if result.rowcount > 0:
                                updated_count += 1
                            else:
                                st.warning(f"⚠️ Lệnh gửi đi không tìm thấy dòng dữ liệu nào khớp với khoá (ID/Barcode: {p_id_val})")
                                
                        except Exception as e:
                            st.error(f"Lỗi SQL cập nhật cho mã {p_id_val}: {e}")
                            
                if updated_count > 0:
                    detail_logs = []
                    for item in st.session_state.cart:
                        if item.get('Mã Barcode') or item.get('id'):
                            barcode = item.get('Mã Barcode', '')
                            sl = int(item.get('Số lượng', 0))
                            hsd = item.get('HSD', '')
                            detail_logs.append(f"[{barcode} | SL: {sl} | HSD: {hsd}]")
                            
                    detail_str = ", ".join(detail_logs)
                    uname = st.session_state.get('username', 'Unknown')
                    utils_auth.write_log(
                        f"Người dùng {uname} cập nhật {updated_count} SP (Tiêu Huỷ): {detail_str}"
                    )
                    should_rerun = True
                    
            if should_rerun:
                st.session_state.cart.clear()
                st.success(f"✅ Đã cập nhật thành công {updated_count} dòng trong Database!")
                st.rerun()
    else:
        st.info("Chưa có sản phẩm nào được chọn.")