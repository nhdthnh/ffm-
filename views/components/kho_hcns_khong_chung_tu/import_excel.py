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
                        df_raw = pd.read_excel(uploaded_file, sheet_name="DANH SÁCH KHO HCNS KHÔNG CT", header=None, nrows=15)
                        header_idx = 0
                        for i, row in df_raw.iterrows():
                            vals = [str(v).upper().strip() for v in row if pd.notna(v)]
                            if any('MÃ BARCODE' in v for v in vals) or any('TÊN SẢN PHẨM' in v for v in vals) or any('TỔNG SỐ LƯỢNG' in v for v in vals):
                                header_idx = i
                                break
                        
                        df = pd.read_excel(uploaded_file, sheet_name="DANH SÁCH KHO HCNS KHÔNG CT", header=header_idx)
                        
                        barcode_col = next((c for c in df.columns if 'MÃ BARCODE' in str(c).upper()), None)
                        ten_col = next((c for c in df.columns if 'TÊN SẢN PHẨM' in str(c).upper() or 'TÊN GỌI' in str(c).upper()), None)
                        sl_col = next((c for c in df.columns if 'SỐ LƯỢNG' in str(c).upper() or 'SL' == str(c).upper().strip()), None)
                        hsd_col = next((c for c in df.columns if 'HẠN SỬ DỤNG' in str(c).upper() or 'HSD' == str(c).upper().strip()), None)
                        ghi_chu_col = next((c for c in df.columns if 'GHI CHÚ' in str(c).upper()), None)
                        
                        if barcode_col:
                            df = df[df[barcode_col].notna()].copy()
                            df = df[df[barcode_col].astype(str).str.strip() != ""].copy()
                            
                            count = 0
                            skip = 0
                            
                            with engine.begin() as conn:
                                # Xoá dữ liệu cũ (tuỳ logic, nếu là tồn kho thì thường truncate/delete all trước)
                                # conn.execute(text("TRUNCATE TABLE kho_hcns_khong_chung_tu"))
                                
                                for _, r in df.iterrows():
                                    sku = safe_barcode(r.get(barcode_col))
                                    if not sku:
                                        skip += 1
                                        continue
                                    
                                    conn.execute(text("""
                                        INSERT INTO kho_hcns_khong_chung_tu (
                                            ma_barcode, ten_san_pham, han_su_dung, so_luong, ghi_chu
                                        ) VALUES (
                                            :sku, :ten, :hsd, :sl, :gc
                                        )
                                    """), {
                                        "sku"  : sku,
                                        "ten"  : safe_str(r.get(ten_col)) if ten_col else "",
                                        "hsd"  : safe_date(r.get(hsd_col)) if hsd_col else None,
                                        "sl"   : safe_int(r.get(sl_col)) if sl_col else 0,
                                        "gc"   : safe_str(r.get(ghi_chu_col)) if ghi_chu_col else ""
                                    })
                                    count += 1
                            
                            utils_auth.write_log(f"Người dùng {st.session_state.get('username', 'Unknown')} đã Import {count} sản phẩm vào danh sách Hàng Không Chứng Từ")
                            st.success(f"✅ Đã tải lên và lưu vào cơ sở dữ liệu {count} dòng! (Bỏ qua {skip} dòng thiếu Mã Barcode)")
                        else:
                            st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    except Exception as e:
                        st.error(f"❌ Xảy ra lỗi khi phân tích File Excel: {str(e)}")
