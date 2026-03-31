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
                            vals = [str(v).upper().replace('\n', ' ').replace('\r', ' ').strip() for v in row if pd.notna(v)]
                            if any('MÃ BARCODE' in v for v in vals) or any('MÃ BARC' in v for v in vals) or any('TÊN SẢN PHẨM' in v for v in vals) or any('TỔNG SỐ LƯỢNG' in v for v in vals):
                                header_idx = i
                                break
                        
                        df = pd.read_excel(uploaded_file, sheet_name="DANH SÁCH KHO HCNS KHÔNG CT", header=header_idx)
                        
                        import re
                        def norm_col(c):
                            return re.sub(r'\s+', ' ', str(c).upper().strip())
                        
                        barcode_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['MÃ BARC', 'SKU'])), None)
                        masp_col = next((c for c in df.columns if 'MÃ SP' in norm_col(c) and 'BARCODE' not in norm_col(c)), None)
                        ten_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['TÊN SẢN PHẨM', 'TÊN GỌI', 'TÊN SP'])), None)
                        sl_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['SỐ LƯỢNG', 'SL'])), None)
                        hsd_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['HẠN SỬ DỤNG', 'HSD', 'HẠN', 'DATE'])), None)
                        ghi_chu_col = next((c for c in df.columns if any(k in norm_col(c) for k in ['GHI CHÚ', 'NOTE'])), None)
                        
                        if barcode_col or ten_col or masp_col:
                            filter_cols = [c for c in [barcode_col, ten_col, masp_col] if c]
                            if filter_cols:
                                df = df.dropna(subset=filter_cols, how='all').copy()
                            
                            count = 0
                            skip = 0
                            
                            with engine.begin() as conn:
                                # Xoá dữ liệu cũ trước khi nạp sheet tồn kho mới
                                conn.execute(text("TRUNCATE TABLE kho_hcns_khong_chung_tu"))
                                
                                for _, r in df.iterrows():
                                    sku = safe_barcode(r.get(barcode_col)) if barcode_col else ""
                                    ten = safe_str(r.get(ten_col)) if ten_col else ""
                                    msp = safe_str(r.get(masp_col)) if masp_col else ""
                                    
                                    if not sku and not ten and not msp:
                                        skip += 1
                                        continue
                                    
                                    conn.execute(text("""
                                        INSERT INTO kho_hcns_khong_chung_tu (
                                            ma_sp, ma_barcode, ten_san_pham, 
                                            so_luong, han_su_dung, ghi_chu,
                                            ngay_cap_nhap
                                        ) VALUES (
                                            :msp, :sku, :ten, 
                                            :sl, :hsd, :gc,
                                            CURRENT_TIMESTAMP()
                                        )
                                    """), {
                                        "msp"  : msp,
                                        "sku"  : sku,
                                        "ten"  : ten,
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
