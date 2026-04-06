"""
views/components/nhap_kho_hcns/import_excel.py
Import Excel → bảng nhap_kho_hcns (TRUNCATE + INSERT)
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
                SHEET = "DANH SÁCH HÀNG NHẬP KHO HCNS"

                # Phát hiện header row
                df_raw = pd.read_excel(uploaded_file, sheet_name=SHEET, header=None, nrows=15)
                header_idx = 0
                for i, row in df_raw.iterrows():
                    vals = [_norm(v) for v in row if pd.notna(v)]
                    if any("MÃ BARC" in v or "TÊN GỌI" in v or "TÊN SẢN PHẨM" in v for v in vals):
                        header_idx = i
                        break

                df = pd.read_excel(uploaded_file, sheet_name=SHEET, header=header_idx)

                # Map cột
                barcode_col   = next((c for c in df.columns if any(k in _norm(c) for k in ["MÃ BARC", "SKU"])), None)
                masp_col      = next((c for c in df.columns if "MÃ SP" in _norm(c) and "BARCODE" not in _norm(c)), None)
                ten_col       = next((c for c in df.columns if any(k in _norm(c) for k in ["TÊN SẢN PHẨM", "TÊN GỌI", "TÊN SP"])), None)
                dvt_col       = next((c for c in df.columns if "ĐƠN VỊ" in _norm(c)), None)
                sl_col        = next((c for c in df.columns if any(k in _norm(c) for k in ["SỐ LƯỢNG", "SL"])), None)
                hsd_col       = next((c for c in df.columns if any(k in _norm(c) for k in ["HẠN SỬ DỤNG", "HSD", "HẠN", "DATE"])), None)
                ngaynhap_col  = next((c for c in df.columns if "NGÀY NHẬP" in _norm(c)), None)
                ghi_chu_col   = next((c for c in df.columns if any(k in _norm(c) for k in ["GHI CHÚ", "NOTE"])), None)

                if not (barcode_col or ten_col or masp_col):
                    st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'Mã Barcode'.")
                    return

                # Lọc dòng trống
                filter_cols = [c for c in [barcode_col, ten_col, masp_col] if c]
                df = df.dropna(subset=filter_cols, how="all").copy()

                count, skip = 0, 0
                with engine.begin() as conn:
                    conn.execute(text("TRUNCATE TABLE nhap_kho_hcns"))
                    for _, r in df.iterrows():
                        sku = safe_barcode(r.get(barcode_col)) if barcode_col else ""
                        ten = safe_str(r.get(ten_col))        if ten_col    else ""
                        msp = safe_str(r.get(masp_col))       if masp_col   else ""

                        if not sku and not ten and not msp:
                            skip += 1
                            continue

                        conn.execute(text("""
                            INSERT INTO nhap_kho_hcns
                                (ma_barcode, ten_san_pham, don_vi_tinh,
                                 han_su_dung, so_luong, ngay_nhap, ghi_chu, ma_sp)
                            VALUES
                                (:sku, :ten, :dvt, :hsd, :sl, :nnk, :gc, :msp)
                        """), {
                            "sku": sku,
                            "ten": ten,
                            "dvt": safe_str(r.get(dvt_col))       if dvt_col      else "",
                            "hsd": safe_date(r.get(hsd_col))      if hsd_col      else None,
                            "sl":  safe_int(r.get(sl_col))        if sl_col       else 0,
                            "nnk": safe_date(r.get(ngaynhap_col)) if ngaynhap_col else None,
                            "gc":  safe_str(r.get(ghi_chu_col))   if ghi_chu_col  else "",
                            "msp": msp,
                        })
                        count += 1

                utils_auth.write_log(f"Import {count} SP → nhap_kho_hcns (bỏ qua {skip})")
                st.success(f"✅ Đã import {count} dòng! (Bỏ qua {skip} dòng thiếu dữ liệu)")

            except Exception as e:
                st.error(f"❌ Lỗi khi import: {e}")
