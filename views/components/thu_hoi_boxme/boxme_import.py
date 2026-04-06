"""
views/components/thu_hoi_boxme/boxme_import.py
Import Excel → bảng thu_hoi_boxme (APPEND, không TRUNCATE)
"""

import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, safe_str, safe_int, safe_float, safe_date, safe_barcode
import utils_auth


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
                SHEET = "Tổng hợp thu hồi"

                # Phát hiện header row
                df_raw = pd.read_excel(uploaded_file, sheet_name=SHEET, header=None, nrows=10)
                header_idx = 0
                for i, row in df_raw.iterrows():
                    vals = [str(v).upper().strip() for v in row if pd.notna(v)]
                    if "SKU" in vals or any("ĐỐI TÁC" in v for v in vals):
                        header_idx = i
                        break

                df = pd.read_excel(uploaded_file, sheet_name=SHEET, header=header_idx)

                # Tìm cột SKU
                sku_col = next(
                    (c for c in df.columns if str(c).strip().upper() == "SKU"),
                    next((c for c in df.columns if "SKU" in str(c).upper()), None),
                )

                if not sku_col:
                    st.error("❌ File Excel không hợp lệ: Không tìm thấy cột 'SKU'.")
                    return

                df = df[df[sku_col].notna()].copy()
                df = df[df[sku_col].astype(str).str.strip() != ""].copy()

                count, skip = 0, 0
                with engine.begin() as conn:
                    for _, r in df.iterrows():
                        sku = safe_barcode(r.get(sku_col))
                        if not sku:
                            skip += 1
                            continue

                        conn.execute(text("""
                            INSERT INTO thu_hoi_boxme (
                                doi_tac, phan_loai, thang_phat_sinh,
                                sku, ten_sp, brand,
                                sl_thuc_nhan, sl_da_xuat,
                                tinh_trang_san_pham, han_su_dung,
                                hsd_tieu_chuan_thang,
                                ma_tham_chieu, ghi_chu, ngay_cap_nhat
                            ) VALUES (
                                :dt, :pl, :thang,
                                :sku, :ten, :brand,
                                :nhan, :xuat,
                                :tt, :hsd, :tc,
                                :ma, :gc, :ncn
                            )
                        """), {
                            "dt":   safe_str(r.get("Đối tác/Đơn phát sinh")),
                            "pl":   safe_str(r.get("Phân loại")),
                            "thang": safe_str(r.get("Tháng phát sinh")),
                            "sku":  sku,
                            "ten":  safe_str(r.get("Tên SP")),
                            "brand": safe_str(r.get("Brand")),
                            "nhan": safe_int(r.get("SL thực nhận")),
                            "xuat": safe_int(r.get("SL đã xuất")),
                            "tt":   safe_str(r.get("Tình trạng sản phẩm")),
                            "hsd":  safe_date(r.get("Hạn sử dụng sản phẩm")),
                            "tc":   safe_float(r.get("HSD tiêu chuẩn (tháng)")),
                            "ma":   safe_str(r.get("Mã tham chiếu")),
                            "gc":   safe_str(r.get("Ghi chú")),
                            "ncn":  safe_date(r.get("Ngày cập nhật") or r.get("Ngày cập nhập")),
                        })
                        count += 1

                utils_auth.write_log(f"Import {count} SP → thu_hoi_boxme (bỏ qua {skip})")
                st.success(f"✅ Đã import {count} dòng! (Bỏ qua {skip} dòng thiếu SKU)")

            except Exception as e:
                st.error(f"❌ Lỗi khi import: {e}")
