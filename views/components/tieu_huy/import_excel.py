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
                            if "TIÊU HỦY" in s.upper():
                                target_sheet = s
                                break
                        if not target_sheet:
                            target_sheet = "DANH SÁCH TIÊU HỦY"

                        df_raw = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=None, nrows=15)
                        header_idx = 0
                        for i, row in df_raw.iterrows():
                            vals = [str(v).upper().replace('\n', ' ').replace('\r', ' ').strip() for v in row if pd.notna(v)]
                            if any('MÃ BARC' in v for v in vals) or any('TÊN SẢN PHẨM' in v for v in vals) or any('SL' in v for v in vals):
                                header_idx = i
                                break
                        
                        df = pd.read_excel(uploaded_file, sheet_name=target_sheet, header=header_idx)
                        
                        import re
                        def norm_col(c):
                            return re.sub(r'\s+', ' ', str(c).upper().strip())

                        barcode_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['MÃ BARC', 'SKU'])), None)
                        masp_col = next((c for c in df.columns if 'MÃ SP' in norm_col(c) and 'BARCODE' not in norm_col(c)), None)
                        ten_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['TÊN SẢN PHẨM', 'TÊN GỌI', 'TÊN SP'])), None)
                        sl_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['SỐ LƯỢNG', 'SL'])), None)
                        hsd_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['HẠN SỬ DỤNG', 'HSD', 'HẠN', 'DATE'])), None)
                        pl_col = next((c for c in df.columns if 'PHÂN LOẠI' in norm_col(c)), None)

                        if barcode_col or ten_col or masp_col:
                            filter_cols = [c for c in [barcode_col, ten_col, masp_col] if c]
                            if filter_cols:
                                df = df.dropna(subset=filter_cols, how='all').copy()
                            
                            count = 0
                            skip = 0
                            
                            with engine.begin() as conn:
                                # Xoá dữ liệu cũ trước khi nạp sheet tồn kho mới
                                conn.execute(text("TRUNCATE TABLE tieu_huy"))
                                
                                for _, r in df.iterrows():
                                    sku = safe_barcode(r.get(barcode_col)) if barcode_col else ""
                                    ten = safe_str(r.get(ten_col)) if ten_col else ""
                                    msp = safe_str(r.get(masp_col)) if masp_col else ""
                                    
                                    if not sku and not ten and not msp:
                                        skip += 1
                                        continue
                                    
                                    conn.execute(text("""
                                        INSERT INTO tieu_huy (
                                            ma_sp, ma_barcode, ten_san_pham, 
                                            so_luong, han_su_dung, phan_loai,
                                            ngay_cap_nhap
                                        ) VALUES (
                                            :msp, :sku, :ten, 
                                            :sl, :hsd, :pl,
                                            CURRENT_TIMESTAMP()
                                        )
                                    """), {
                                        "msp"  : msp,
                                        "sku"  : sku,
                                        "ten"  : ten,
                                        "hsd"  : safe_date(r.get(hsd_col)) if hsd_col else None,
                                        "sl"   : safe_int(r.get(sl_col)) if sl_col else 0,
                                        "pl"   : safe_str(r.get(pl_col)) if pl_col else ""
                                    })
                                    count += 1
                            
                            utils_auth.write_log(f"Người dùng {st.session_state.get('username', 'Unknown')} đã Import {count} sản phẩm vào danh sách Tiêu Hủy")
                            st.success(f"✅ Đã tải lên và lưu vào cơ sở dữ liệu {count} dòng! (Bỏ qua {skip} dòng thiếu Mã Barcode)")
                        else:
                            st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    except Exception as e:
                        st.error(f"❌ Xảy ra lỗi khi phân tích File Excel: {str(e)}")
