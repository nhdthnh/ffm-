import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, safe_str, safe_int, safe_float, safe_date, safe_barcode
import utils_auth

def render_import_section():
    engine = get_engine()
    with st.expander("⬆️ Import Data từ file Excel", expanded=False):
        uploaded_file = st.file_uploader("Tải lên file Excel tổng hợp", type=['xlsx', 'xls'])
        if uploaded_file is not None:
            if st.button("Tiến hành Import Dữ liệu", type="primary"):
                with st.spinner("Đang đọc luồng dữ liệu..."):
                    try:
                        xls = pd.ExcelFile(uploaded_file)
                        target_sheet = None
                        for s in xls.sheet_names:
                            if "CSR" in s.upper():
                                target_sheet = s
                                break
                        if not target_sheet:
                            target_sheet = "DANH SÁCH HÀNG TỒN CSR_CÓ CT"

                        df_raw = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=None, nrows=15)
                        header_idx = 0
                        for i, row in df_raw.iterrows():
                            vals = [str(v).upper().strip() for v in row if pd.notna(v)]
                            if any('MÃ BARC' in v for v in vals) or any('TÊN GỌI' in v for v in vals) or any('MÃ SP' in v for v in vals):
                                header_idx = i
                                break
                        
                        df = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=header_idx)
                        
                        barcode_col = next((c for c in df.columns if 'MÃ BARC' in str(c).upper()), None)
                        masp_col = next((c for c in df.columns if 'MÃ SP' in str(c).upper() and 'BARCODE' not in str(c).upper()), None)
                        ten_col = next((c for c in df.columns if 'TÊN GỌI' in str(c).upper() or 'TÊN SẢN PHẨM' in str(c).upper()), None)
                        sl_col = next((c for c in df.columns if str(c).upper().strip() == 'SL' or 'SỐ LƯỢNG' in str(c).upper()), None)
                        hsd_col = next((c for c in df.columns if str(c).upper().strip() == 'HSD' or 'HẠN SỬ DỤNG' in str(c).upper()), None)
                        ghi_chu_col = next((c for c in df.columns if 'GHI CHÚ' in str(c).upper()), None)

                        if barcode_col or ten_col or masp_col:
                            filter_cols = [c for c in [barcode_col, ten_col, masp_col] if c]
                            if filter_cols:
                                df = df.dropna(subset=filter_cols, how='all').copy()

                            count = 0
                            skip = 0
                            
                            with engine.begin() as conn:
                                # Xoá dữ liệu cũ trước khi nạp sheet tồn kho mới
                                conn.execute(text("TRUNCATE TABLE ton_csr_co_chung_tu"))

                                for _, r in df.iterrows():
                                    sku = safe_barcode(r.get(barcode_col)) if barcode_col else ""
                                    ten = safe_str(r.get(ten_col)) if ten_col else ""
                                    msp = safe_str(r.get(masp_col)) if masp_col else ""

                                    if not sku and not ten and not msp:
                                        skip += 1
                                        continue
                                    
                                    conn.execute(text("""
                                        INSERT INTO ton_csr_co_chung_tu (
                                            ma_sp, ma_barcode, ten_san_pham,
                                            so_luong, han_su_dung, ghi_chu,
                                            ngay_cap_nhap
                                        ) VALUES (
                                            :msp,  :sku,   :ten,
                                            :sl,   :hsd,   :gc,
                                            CURRENT_TIMESTAMP()
                                        )
                                    """), {
                                        "msp"  : safe_str(r.get(masp_col)) if masp_col else "",
                                        "sku"  : safe_barcode(r.get(barcode_col)),
                                        "ten"  : safe_str(r.get(ten_col)) if ten_col else "",
                                        "sl"   : safe_int(r.get(sl_col)) if sl_col else 0,
                                        "hsd"  : safe_date(r.get(hsd_col)) if hsd_col else None,
                                        "gc"   : safe_str(r.get(ghi_chu_col)) if ghi_chu_col else ""
                                    })
                                    count += 1
                            
                            utils_auth.write_log(f"Người dùng {st.session_state.get('username', 'Unknown')} đã Import {count} sản phẩm vào Tồn CSR Có chứng từ")
                            st.success(f"✅ Đã tải lên và lưu vào cơ sở dữ liệu {count} dòng! (Bỏ qua {skip} dòng thiếu Mã Barcode)")
                        else:
                            st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    except Exception as e:
                        st.error(f"❌ Xảy ra lỗi khi phân tích File Excel: {str(e)}")
