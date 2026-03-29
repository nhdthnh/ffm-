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
        
        col_widths = [1.2, 2.0, 1.0, 1.2, 1.0, 1.0, 1.0, 1.5, 0.3]
        hc1, hc2, hc3, hc4, hc5, hc6, hc7, hc8, hc9 = st.columns(col_widths)
        hc1.markdown("**BARCODE**")
        hc2.markdown("**DESCRIPTION**")
        hc3.markdown("**HSD**")
        hc4.markdown("**TÌNH TRẠNG**")
        hc5.markdown("**SỐ LƯỢNG**")
        hc6.markdown("**ĐÃ XUẤT**")
        hc7.markdown("**CÒN LẠI**")
        hc8.markdown("**GHI CHÚ**")
        hc9.markdown("")
        
        total_qty = 0
        for idx, item in enumerate(st.session_state.cart):
            with st.container():
                 c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(col_widths)
                 c1.write(str(item.get('SKU', '')))
                 c2.write(str(item.get('Tên SP', '')))
                 c3.write(str(item.get('Hạn sử dụng', '')))
                 c4.write(str(item.get('Tình trạng sản phẩm', '')))
                 
                 thuc_nhan = int(item.get('Số lượng', 0))
                 c5.write(str(thuc_nhan))
                 
                 da_xuat = int(item.get('custom_da_xuat', 0))
                 new_da_xuat = c6.number_input("Đã xuất", value=da_xuat, step=1, label_visibility="collapsed", key=f"da_xuat_{idx}")
                 st.session_state.cart[idx]['custom_da_xuat'] = int(new_da_xuat)
                 
                 con_lai = thuc_nhan - int(new_da_xuat)
                 c7.write(str(con_lai))
                 total_qty += int(new_da_xuat)
                 
                 new_note = c8.text_input("Ghi chú", value=item.get('custom_note', ''), label_visibility="collapsed", key=f"note_{idx}")
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
                            UPDATE nhap_kho_hcns 
                            SET so_luong = :p_so_luong, ghi_chu = :p_note 
                            WHERE id = :p_id
                        """), {
                            "p_so_luong": con_lai_cap_nhat,
                            "p_note": item.get('custom_note'),
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