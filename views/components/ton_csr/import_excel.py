"""
views/components/ton_csr/import_excel.py
Import Excel → bảng ton_csr_co_chung_tu (TRUNCATE + INSERT)
"""

import re
import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, safe_str, safe_int, safe_date, safe_barcode
import utils_auth


def _norm(c) -> str:
    return re.sub(r"\s+", " ", str(c).upper().strip())


def render_import_section():
    engine = get_engine()
    with st.expander("⬆️ Import Data từ file Excel", expanded=False):
        uploaded_file = st.file_uploader("Chọn file Excel", type=["xlsx", "xls"])
        if uploaded_file is None:
            return

        if not st.button("⬆️ Tiến hành Import", type="primary"):
            return

        with st.spinner("Đang import dữ liệu..."):
            try:
                # Tìm sheet CSR
                xls = pd.ExcelFile(uploaded_file)
                sheet = next((s for s in xls.sheet_names if "CSR" in s.upper()), "DANH SÁCH HÀNG TỒN CSR_CÓ CT")

                # Phát hiện header row
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None, nrows=15)
                header_idx = 0
                for i, row in df_raw.iterrows():
                    vals = [_norm(v) for v in row if pd.notna(v)]
                    if any("MÃ BARC" in v or "TÊN GỌI" in v or "MÃ SP" in v for v in vals):
                        header_idx = i
                        break

                df = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)

                # Map cột
                barcode_col  = next((c for c in df.columns if "MÃ BARC" in _norm(c)), None)
                masp_col     = next((c for c in df.columns if "MÃ SP" in _norm(c) and "BARCODE" not in _norm(c)), None)
                ten_col      = next((c for c in df.columns if "TÊN GỌI" in _norm(c) or "TÊN SẢN PHẨM" in _norm(c)), None)
                sl_col       = next((c for c in df.columns if _norm(c) == "SL" or "SỐ LƯỢNG" in _norm(c)), None)
                hsd_col      = next((c for c in df.columns if _norm(c) == "HSD" or "HẠN SỬ DỤNG" in _norm(c)), None)
                ghi_chu_col  = next((c for c in df.columns if "GHI CHÚ" in _norm(c)), None)

                if not (barcode_col or ten_col or masp_col):
                    st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    return

                filter_cols = [c for c in [barcode_col, ten_col, masp_col] if c]
                df = df.dropna(subset=filter_cols, how="all").copy()

                count, skip = 0, 0
                with engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE ton_csr_co_chung_tu"))
                    for _, r in df.iterrows():
                        sku = safe_barcode(r.get(barcode_col)) if barcode_col else ""
                        ten = safe_str(r.get(ten_col))        if ten_col    else ""
                        msp = safe_str(r.get(masp_col))       if masp_col   else ""

                        if not sku and not ten and not msp:
                            skip += 1
                            continue

                        conn.execute(text("""
                            INSERT INTO ton_csr_co_chung_tu
                                (ma_sp, ma_barcode, ten_san_pham,
                                 so_luong, han_su_dung, ghi_chu, ngay_cap_nhap)
                            VALUES
                                (:msp, :sku, :ten, :sl, :hsd, :gc, CURRENT_TIMESTAMP())
                        """), {
                            "msp": msp,
                            "sku": sku,
                            "ten": ten,
                            "sl":  safe_int(r.get(sl_col))      if sl_col      else 0,
                            "hsd": safe_date(r.get(hsd_col))    if hsd_col     else None,
                            "gc":  safe_str(r.get(ghi_chu_col)) if ghi_chu_col else "",
                        })
                        count += 1

                utils_auth.write_log(f"Import {count} SP → ton_csr_co_chung_tu (bỏ qua {skip})")
                st.success(f"✅ Đã import {count} dòng! (Bỏ qua {skip} dòng thiếu dữ liệu)")

            except Exception as e:
                st.error(f"❌ Lỗi khi import: {e}")
