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
    st.subheader("📋 DANH SÁCH SẢN PHẨM XUẤT")
    
    if st.session_state.cart:
        inject_cart_css()
        
        col_widths = [1.2, 2.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.5, 0.3]
        hc1, hc2, hc3, hc4, hc5, hc6, hc7, hc8, hc9 = st.columns(col_widths)
        hc1.markdown("**BARCODE**")
        hc2.markdown("**DESCRIPTION**")
        hc3.markdown("**HSD**")
        hc5.markdown("**SỐ LƯỢNG**")
        hc6.markdown("**ĐÃ XUẤT**")
        hc7.markdown("**CÒN LẠI**")
        hc8.markdown("**GHI CHÚ**")
        hc9.markdown("")
        
        total_qty = 0
        for idx, item in enumerate(st.session_state.cart):
            with st.container():
                 c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(col_widths)
                 
                 new_sku = c1.text_input("SKU", value=str(item.get('SKU', '')), label_visibility="collapsed", key=f"sku_{idx}")
                 st.session_state.cart[idx]['SKU'] = new_sku
                 
                 new_ten = c2.text_input("Tên SP", value=str(item.get('Tên SP', '')), label_visibility="collapsed", key=f"ten_{idx}")
                 st.session_state.cart[idx]['Tên SP'] = new_ten
                 
                 hsd_val = item.get('Hạn sử dụng')
                 hsd_str = str(hsd_val) if hsd_val is not None and str(hsd_val).strip().lower() != 'none' else ""
                 new_hsd = c3.text_input("HSD", value=hsd_str, label_visibility="collapsed", key=f"hsd_{idx}")
                 st.session_state.cart[idx]['Hạn sử dụng'] = new_hsd if new_hsd.strip() else None
                 
                 thuc_nhan = int(item.get('Số lượng') or 0)
                 new_sl = c5.number_input("Số lượng", value=thuc_nhan, step=1, label_visibility="collapsed", key=f"sl_{idx}")
                 st.session_state.cart[idx]['Số lượng'] = new_sl
                 
                 da_xuat = int(item.get('custom_da_xuat', 0))
                 new_da_xuat = c6.number_input("Đã xuất", value=da_xuat, step=1, label_visibility="collapsed", key=f"da_xuat_{idx}")
                 st.session_state.cart[idx]['custom_da_xuat'] = int(new_da_xuat)
                 
                 con_lai = int(new_sl) - int(new_da_xuat)
                 c7.write(str(con_lai))
                 total_qty += int(new_da_xuat)
                 
                 new_note = c8.text_input("Ghi chú", value=str(item.get('custom_note', '')), label_visibility="collapsed", key=f"note_{idx}")
                 st.session_state.cart[idx]['custom_note'] = new_note
                 
                 if c9.button("🗑️", key=f"del_{idx}"):
                     st.session_state.cart.pop(idx)
                     st.rerun()
                     
        st.markdown("---")
        st.markdown(f"**Tổng Số lượng Đã Xuất: {total_qty:,}**")
        
        if st.button("💾 Cập nhật Database", type="secondary"):
            with engine.begin() as update_conn:
                updated_count = 0
                for item in st.session_state.cart:
                    row_id = item.get('id')
                    if row_id:
                        thuc_nhan = int(item.get('Số lượng', 0))
                        da_xuat = int(item.get('custom_da_xuat', 0))
                        con_lai_cap_nhat = thuc_nhan - da_xuat
                        
                        update_conn.execute(text("""
                            UPDATE kho_hcns_khong_chung_tu 
                            SET ma_barcode = :p_sku,
                                ten_san_pham = :p_ten,
                                han_su_dung = :p_hsd,
                                so_luong = :p_so_luong, 
                                ghi_chu = :p_note,
                                ngay_cap_nhap = CURRENT_TIMESTAMP()
                            WHERE id = :p_id
                        """), {
                            "p_sku": item.get('SKU', ''),
                            "p_ten": item.get('Tên SP', ''),
                            "p_hsd": item.get('Hạn sử dụng') if item.get('Hạn sử dụng') and str(item.get('Hạn sử dụng')).strip() else None,
                            "p_so_luong": con_lai_cap_nhat,
                            "p_note": item.get('custom_note', ''),
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
                            thuc_nhan = int(item.get('Số lượng', 0))
                            con_lai = thuc_nhan - da_xuat
                            detail_logs.append(f"[{sku} | {phan_loai} | Nhập xuất: {da_xuat} | Tồn Cập nhật: {con_lai}]")
                            
                    detail_str = ", ".join(detail_logs)
                    uname = st.session_state.get('username', 'Unknown')
                    utils_auth.write_log(
                        f"Người dùng {uname} cập nhật {updated_count} SP (Nhập kho HCNS): {detail_str}"
                    )
                    st.success(f"✅ Đã cập nhật thành công {updated_count} dòng trong Database!")
                else:
                    st.warning("⚠ Không tìm thấy ID để cập nhật.")
    else:
        st.info("Chưa có sản phẩm nào được chọn.")