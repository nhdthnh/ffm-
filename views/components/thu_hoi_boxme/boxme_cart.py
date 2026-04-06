import streamlit as st
from sqlalchemy import text
from utils import get_engine
import utils_auth
from views.components._shared import inject_cart_css

def render_cart():
    engine = get_engine()
    st.markdown("---")
    st.subheader("📋 DANH SÁCH SẢN PHẨM XUẤT")
    
    if st.session_state.cart:
        inject_cart_css()
        
        col_widths = [1.2, 1.8, 1.0, 1.2, 1.2, 0.7, 0.7, 0.7, 1.1, 1.2, 0.2]
        hc1, hc2, hc3, hc4, hc5, hc6, hc7, hc8, hc9, hc10, hc11 = st.columns(col_widths)
        hc1.markdown("**BARCODE**")
        hc2.markdown("**DESCRIPTION**")
        hc3.markdown("**HSD**")
        hc4.markdown("**TÌNH TRẠNG**")
        hc5.markdown("**PHÂN LOẠI**")
        hc6.markdown("**THỰC NHẬN**")
        hc7.markdown("**ĐÃ XUẤT**")
        hc8.markdown("**CÒN LẠI**")
        hc9.markdown("**MÃ THAM CHIẾU**")
        hc10.markdown("**GHI CHÚ**")
        
        total_qty = 0
        for idx, item in enumerate(st.session_state.cart):
            with st.container():
                 c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 = st.columns(col_widths)
                 c1.write(str(item.get('SKU', '')))
                 c2.write(str(item.get('Tên SP', '')))
                 c3.write(str(item.get('Hạn sử dụng', '')))
                 c4.write(str(item.get('Tình trạng sản phẩm', '')))
                 c5.write(str(item.get('Phân loại', '')))
                 
                 thuc_nhan = int(item.get('SL Thực nhận', 0))
                 c6.write(str(thuc_nhan))
                 
                 da_xuat = int(item.get('custom_da_xuat', item.get('SL Đã xuất', 0)))
                 new_da_xuat = c7.number_input("Đã xuất", value=da_xuat, step=1, label_visibility="collapsed", key=f"da_xuat_{idx}")
                 st.session_state.cart[idx]['custom_da_xuat'] = int(new_da_xuat)
                 
                 con_lai = thuc_nhan - int(new_da_xuat)
                 c8.write(str(con_lai))
                 total_qty += int(new_da_xuat)
                 
                 cur_ref = item.get('custom_ma_tham_chieu', item.get('Mã tham chiếu', ''))
                 new_ref = c9.text_input("Mã tham chiếu", value=cur_ref if cur_ref is not None and cur_ref != 'None' else '', label_visibility="collapsed", key=f"ref_{idx}")
                 st.session_state.cart[idx]['custom_ma_tham_chieu'] = new_ref
                 
                 new_note = c10.text_input("Ghi chú", value=item.get('custom_note', ''), label_visibility="collapsed", key=f"note_{idx}")
                 st.session_state.cart[idx]['custom_note'] = new_note
                 
                 if c11.button("🗑️", key=f"del_{idx}"):
                     st.session_state.cart.pop(idx)
                     st.rerun()
                     
        st.markdown("---")
        st.markdown(f"**Tổng QTY: {total_qty:,}**")
        
        if st.button("💾 Cập nhật Database", type="secondary"):
            with engine.begin() as update_conn:
                updated_count = 0
                for item in st.session_state.cart:
                    row_id = item.get('id')
                    if row_id:
                        update_conn.execute(text("""
                            UPDATE thu_hoi_boxme 
                            SET sl_da_xuat = :p_da_xuat, ghi_chu = :p_note, ma_tham_chieu = :p_ref 
                            WHERE id = :p_id
                        """), {
                            "p_da_xuat": item.get('custom_da_xuat'),
                            "p_note": item.get('custom_note'),
                            "p_ref": item.get('custom_ma_tham_chieu'),
                            "p_id": row_id
                        })
                        updated_count += 1
                if updated_count > 0:
                    detail_logs = []
                    for item in st.session_state.cart:
                        if item.get('id'):
                            sku = item.get('SKU', '')
                            phan_loai = item.get('Phân loại', '')
                            da_xuat = int(item.get('custom_da_xuat', 0))
                            thuc_nhan = int(item.get('SL Thực nhận', 0))
                            con_lai = thuc_nhan - da_xuat
                            detail_logs.append(f"[{sku} | {phan_loai} | Xuất: {da_xuat} | Còn: {con_lai}]")
                            
                    detail_str = ", ".join(detail_logs)
                    uname = st.session_state.get('username', 'Unknown')
                    utils_auth.write_log(
                        f"Người dùng {uname} cập nhật {updated_count} SP (Thu hồi Boxme): {detail_str}"
                    )
                    st.success(f"✅ Đã cập nhật thành công {updated_count} dòng trong Database!")
                else:
                    st.warning("⚠ Không tìm thấy ID để cập nhật.")
    else:
        st.info("Chưa có sản phẩm nào được chọn.")
