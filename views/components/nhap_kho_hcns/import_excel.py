import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, safe_str, safe_int, safe_float, safe_date, safe_barcode
import utils_auth

def render_import_section():
    engine = get_engine()
    with st.expander("⬆️ Import Data từ file Excel", expanded=False):
        uploaded_file = st.file_uploader("Tải lên file Excel Tổng hợp (nhấn Browse)", type=['xlsx', 'xls'])
        if uploaded_file is not None:
            if st.button("Tiến hành Import Dữ liệu", type="primary"):
                with st.spinner("Đang đọc luồng dữ liệu..."):
                    try:
                        df_raw = pd.read_excel(uploaded_file, sheet_name="DANH SÁCH HÀNG NHẬP KHO HCNS", header=None, nrows=15)
                        header_idx = 0
                        for i, row in df_raw.iterrows():
                            vals = [str(v).upper().strip() for v in row if pd.notna(v)]
                            if any('MÃ BARCODE' in v for v in vals) or any('TÊN GỌI' in v for v in vals) or any('MÃ SP' in v for v in vals):
                                header_idx = i
                                break
                        
                        df = pd.read_excel(uploaded_file, sheet_name="DANH SÁCH HÀNG NHẬP KHO HCNS", header=header_idx)
                        
                        barcode_col = next((c for c in df.columns if 'MÃ BARCODE' in str(c).upper()), None)
                        masp_col = next((c for c in df.columns if 'MÃ SP' in str(c).upper() and 'BARCODE' not in str(c).upper()), None)
                        ten_col = next((c for c in df.columns if 'TÊN GỌI' in str(c).upper() or 'TÊN SẢN PHẨM' in str(c).upper()), None)
                        dvt_col = next((c for c in df.columns if 'ĐƠN VỊ' in str(c).upper()), None)
                        sl_col = next((c for c in df.columns if str(c).upper().strip() in ['SL', 'SỐ LƯỢNG']), None)
                        hsd_col = next((c for c in df.columns if str(c).upper().strip() in ['HSD', 'HẠN SỬ DỤNG']), None)
                        ngaynhap_col = next((c for c in df.columns if 'NGÀY NHẬP' in str(c).upper()), None)
                        ghi_chu_col = next((c for c in df.columns if 'GHI CHÚ' in str(c).upper()), None)

                        if barcode_col:
                            df = df[df[barcode_col].notna()].copy()
                            df = df[df[barcode_col].astype(str).str.strip() != ""].copy()
                            
                            count = 0
                            skip = 0
                            
                            with engine.begin() as conn:
                                for _, r in df.iterrows():
                                    sku = safe_barcode(r.get(barcode_col))
                                    if not sku:
                                        skip += 1
                                        continue
                                    
                                    conn.execute(text("""
                                        INSERT INTO nhap_kho_hcns (
                                            ma_barcode, ten_san_pham, don_vi_tinh,
                                            han_su_dung, so_luong,
                                            ngay_nhap, ghi_chu,
                                            ma_sp
                                        ) VALUES (
                                            :sku,  :ten,   :dvt,
                                            :hsd,  :sl,
                                            :nnk,  :gc,
                                            :msp
                                        )
                                    """), {
                                        "sku"  : sku,
                                        "ten"  : safe_str(r.get(ten_col)) if ten_col else "",
                                        "dvt"  : safe_str(r.get(dvt_col)) if dvt_col else "",
                                        "hsd"  : safe_date(r.get(hsd_col)) if hsd_col else None,
                                        "sl"   : safe_int(r.get(sl_col)) if sl_col else 0,
                                        "nnk"  : safe_date(r.get(ngaynhap_col)) if ngaynhap_col else None,
                                        "gc"   : safe_str(r.get(ghi_chu_col)) if ghi_chu_col else "",
                                        "msp"  : safe_barcode(r.get(masp_col)) if masp_col else ""
                                    })
                                    count += 1
                            
                            utils_auth.write_log(f"Người dùng {st.session_state.get('username', 'Unknown')} đã Import {count} sản phẩm vào danh sách Nhập kho HCNS")
                            st.success(f"✅ Đã tải lên và lưu vào cơ sở dữ liệu {count} dòng! (Bỏ qua {skip} dòng thiếu Mã Barcode)")
                        else:
                            st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    except Exception as e:
                        st.error(f"❌ Xảy ra lỗi khi phân tích File Excel: {str(e)}")
