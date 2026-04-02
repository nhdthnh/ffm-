import streamlit as st
from sqlalchemy import text
from utils import get_engine
import utils_auth

def render_cart():
    if 'cart' not in st.session_state:
        st.session_state.cart = []
        
    engine = get_engine()
    st.markdown("---")
    st.subheader("📋 DANH SÁCH NHẬP KHO HCNS & XUẤT HÀNG")
    
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
        
        col_widths = [1.2, 2.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.5, 0.3]
        hc1, hc2, hc3, hc4, hc5, hc6, hc7, hc8, hc9 = st.columns(col_widths)
        hc1.markdown("**SKU**")
        hc2.markdown("**TÊN SP**")
        hc3.markdown("**ĐVT**")
        hc4.markdown("**HSD**")
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
                 
                 new_dvt = c3.text_input("ĐVT", value=str(item.get('Đơn vị tính', '')), label_visibility="collapsed", key=f"dvt_{idx}")
                 st.session_state.cart[idx]['Đơn vị tính'] = new_dvt
                 
                 hsd_val = item.get('Hạn sử dụng')
                 hsd_str = str(hsd_val) if hsd_val is not None and str(hsd_val).strip().lower() != 'none' else ""
                 new_hsd = c4.text_input("HSD", value=hsd_str, label_visibility="collapsed", key=f"hsd_{idx}")
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
            should_rerun = False
            with engine.begin() as update_conn:
                updated_count = 0
                for item in st.session_state.cart:
                    row_id = item.get('id')
                    fallback_id = item.get('SKU')
                    
                    if row_id or fallback_id:
                        try:
                            thuc_nhan = int(item.get('Số lượng', 0))
                            da_xuat = int(item.get('custom_da_xuat', 0))
                            con_lai_cap_nhat = thuc_nhan - da_xuat
                            
                            if row_id:
                                query = """
                                    UPDATE nhap_kho_hcns 
                                    SET ma_barcode = :p_sku,
                                        ten_san_pham = :p_ten,
                                        don_vi_tinh = :p_dvt,
                                        han_su_dung = :p_hsd,
                                        so_luong = :p_so_luong, 
                                        ghi_chu = :p_note
                                    WHERE id = :p_id
                                """
                                p_id_val = row_id
                            else:
                                query = """
                                    UPDATE nhap_kho_hcns 
                                    SET ten_san_pham = :p_ten,
                                        don_vi_tinh = :p_dvt,
                                        han_su_dung = :p_hsd,
                                        so_luong = :p_so_luong, 
                                        ghi_chu = :p_note
                                    WHERE ma_barcode = :p_id
                                """
                                p_id_val = fallback_id

                            result = update_conn.execute(text(query), {
                                "p_sku": item.get('SKU', ''),
                                "p_ten": item.get('Tên SP', ''),
                                "p_dvt": item.get('Đơn vị tính', ''),
                                "p_hsd": item.get('Hạn sử dụng') if item.get('Hạn sử dụng') and str(item.get('Hạn sử dụng')).strip() else None,
                                "p_so_luong": con_lai_cap_nhat,
                                "p_note": item.get('custom_note', ''),
                                "p_id": p_id_val
                            })
                            
                            if result.rowcount > 0:
                                updated_count += 1
                            else:
                                st.warning(f"⚠️ Không tìm thấy dòng dữ liệu nào khớp với khoá (ID/SKU: {p_id_val})")
                                
                        except Exception as e:
                            st.error(f"Lỗi SQL cập nhật cho ID/SKU {p_id_val}: {e}")
                            
                if updated_count > 0:
                    detail_logs = []
                    for item in st.session_state.cart:
                        if item.get('id') or item.get('SKU'):
                            sku = item.get('SKU', '')
                            da_xuat = int(item.get('custom_da_xuat', 0))
                            thuc_nhan = int(item.get('Số lượng', 0))
                            con_lai = thuc_nhan - da_xuat
                            detail_logs.append(f"[{sku} | Nhập xuất: {da_xuat} | Tồn: {con_lai}]")
                            
                    detail_str = ", ".join(detail_logs)
                    uname = st.session_state.get('username', 'Unknown')
                    utils_auth.write_log(
                        f"Người dùng {uname} cập nhật {updated_count} SP (Nhập kho HCNS): {detail_str}"
                    )
                    should_rerun = True
            
            if should_rerun:
                st.session_state.cart.clear()
                st.success(f"✅ Đã cập nhật thành công {updated_count} dòng trong Database!")
                st.rerun()
    else:
        st.info("Chưa có sản phẩm nào được chọn.")