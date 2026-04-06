"""
views/components/tieu_huy/import_excel.py
Import Excel → bảng tieu_huy (TRUNCATE + INSERT)
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
                # Tìm sheet tiêu hủy
                xls = pd.ExcelFile(uploaded_file)
                sheet = next(
                    (s for s in xls.sheet_names if "TIÊU HỦY" in s.upper()),
                    "DANH SÁCH TIÊU HỦY",
                )

                # Phát hiện header row
                df_raw = pd.read_excel(uploaded_file, sheet_name=sheet, header=None, nrows=15)
                header_idx = 0
                for i, row in df_raw.iterrows():
                    vals = [_norm(v) for v in row if pd.notna(v)]
                    if any("MÃ BARC" in v or "TÊN SẢN PHẨM" in v or "SL" in v for v in vals):
                        header_idx = i
                        break

                df = pd.read_excel(uploaded_file, sheet_name=sheet, header=header_idx)

                # Map cột
                barcode_col = next((c for c in df.columns if any(k in _norm(c) for k in ["MÃ BARC", "SKU"])), None)
                masp_col    = next((c for c in df.columns if "MÃ SP" in _norm(c) and "BARCODE" not in _norm(c)), None)
                ten_col     = next((c for c in df.columns if any(k in _norm(c) for k in ["TÊN SẢN PHẨM", "TÊN GỌI", "TÊN SP"])), None)
                sl_col      = next((c for c in df.columns if any(k in _norm(c) for k in ["SỐ LƯỢNG", "SL"])), None)
                hsd_col     = next((c for c in df.columns if any(k in _norm(c) for k in ["HẠN SỬ DỤNG", "HSD", "HẠN", "DATE"])), None)
                pl_col      = next((c for c in df.columns if "PHÂN LOẠI" in _norm(c)), None)

                if not (barcode_col or ten_col or masp_col):
                    st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    return

                filter_cols = [c for c in [barcode_col, ten_col, masp_col] if c]
                df = df.dropna(subset=filter_cols, how="all").copy()

                count, skip = 0, 0
                with engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE tieu_huy"))
                    for _, r in df.iterrows():
                        sku = safe_barcode(r.get(barcode_col)) if barcode_col else ""
                        ten = safe_str(r.get(ten_col))        if ten_col    else ""
                        msp = safe_str(r.get(masp_col))       if masp_col   else ""

                        if not sku and not ten and not msp:
                            skip += 1
                            continue

                        conn.execute(text("""
                            INSERT INTO tieu_huy
                                (ma_sp, ma_barcode, ten_san_pham,
                                 so_luong, han_su_dung, phan_loai, ngay_cap_nhap)
                            VALUES
                                (:msp, :sku, :ten, :sl, :hsd, :pl, CURRENT_TIMESTAMP())
                        """), {
                            "msp": msp,
                            "sku": sku,
                            "ten": ten,
                            "hsd": safe_date(r.get(hsd_col)) if hsd_col else None,
                            "sl":  safe_int(r.get(sl_col))   if sl_col  else 0,
                            "pl":  safe_str(r.get(pl_col))   if pl_col  else "",
                        })
                        count += 1

                utils_auth.write_log(f"Import {count} SP → tieu_huy (bỏ qua {skip})")
                st.success(f"✅ Đã import {count} dòng! (Bỏ qua {skip} dòng thiếu dữ liệu)")

            except Exception as e:
                st.error(f"❌ Lỗi khi import: {e}")
