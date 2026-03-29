"""
Import sheet "Tổng hợp thu hồi" vào bảng thu_hoi_boxme
pip install pandas pymysql sqlalchemy openpyxl
"""

import os
import re
import warnings
from datetime import date
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote

warnings.filterwarnings("ignore")

# ============================================================
# CẤU HÌNH
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_FILE = os.path.join(SCRIPT_DIR, "(ALL) FFM_Tổng hợp hàng xuất kho Boxme về văn phòng.xlsx")

DB_HOST = "192.168.1.119"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "Oqr@18009413"
DB_NAME = "oqr_kho"
# ============================================================


def safe_str(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s and s not in ('-', 'nan', 'NaN') else None


def safe_int(val, default=0):
    try:
        f = float(val)
        return int(f) if not pd.isna(f) else default
    except (TypeError, ValueError):
        return default


def safe_float(val):
    try:
        f = float(val)
        return None if pd.isna(f) else round(f, 6)
    except (TypeError, ValueError):
        return None


def safe_date(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = re.sub(r'\s*00:00:00$', '', str(val).strip())
    if s in ('', '-', 'nan', 'NaN'):
        return None
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    if re.match(r'^\d{4}-\d{2}-\d{2}', s):
        return s[:10]
    return None


def safe_barcode(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return str(int(float(val)))
    except (TypeError, ValueError):
        return safe_str(val)


def main():
    # ── Đọc file ─────────────────────────────────────────────
    print(f"📂 Đọc file:\n   {LOCAL_FILE}")
    # Tìm dòng tiêu đề (header)
    df_raw = pd.read_excel(LOCAL_FILE, sheet_name="Tổng hợp thu hồi", header=None, nrows=10)
    header_idx = 0
    for i, row in df_raw.iterrows():
        vals = [str(v).upper().strip() for v in row if pd.notna(v)]
        if 'SKU' in vals or any('ĐỐI TÁC' in v for v in vals):
            header_idx = i
            break
            
    print(f"   → Sử dụng header row: {header_idx}")
    df = pd.read_excel(LOCAL_FILE, sheet_name="Tổng hợp thu hồi", header=header_idx)
    print(f"   → {df.shape[0]} dòng x {df.shape[1]} cột")

    # Tìm cột SKU
    sku_col = None
    for c in df.columns:
        c_str = str(c).strip()
        if c_str.upper() == 'SKU':
            sku_col = c
            break
            
    if not sku_col:
        for c in df.columns:
            if 'SKU' in str(c).upper():
                sku_col = c
                break
                
    if not sku_col:
        print("❌ Không tìm thấy cột 'SKU' trong file Excel!")
        print(f"📋 Các cột có sẵn: {df.columns.tolist()}")
        import sys; sys.exit(1)
        
    print(f"✅ Tìm thấy cột SKU: '{sku_col}'")

    # Lọc bỏ dòng không có SKU
    df = df[df[sku_col].notna()].copy()
    df = df[df[sku_col].astype(str).str.strip() != ""].copy()
    print(f"   → {df.shape[0]} dòng hợp lệ (có SKU)")

    # ── Kết nối DB ───────────────────────────────────────────
    db_pass_quoted = quote(DB_PASS)
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{db_pass_quoted}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )

    # ── Import ───────────────────────────────────────────────
    # Không truyền: con_lai, ngay_lam_chuan, hsd_con_lai_thang, pct_hsd_con_lai
    # → trigger tự động tính
    print("\n📥 Đang import...")
    count = 0
    skip  = 0

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
                    :dt,   :pl,    :thang,
                    :sku,  :ten,   :brand,
                    :nhan, :xuat,
                    :tt,   :hsd,
                    :tc,
                    :ma,   :gc,    :ncn
                )
            """), {
                "dt"   : safe_str(r.get("Đối tác/Đơn phát sinh")),
                "pl"   : safe_str(r.get("Phân loại")),
                "thang": safe_str(r.get("Tháng phát sinh")),
                "sku"  : sku,
                "ten"  : safe_str(r.get("Tên SP")),
                "brand": safe_str(r.get("Brand")),
                "nhan" : safe_int(r.get("SL thực nhận")),
                "xuat" : safe_int(r.get("SL đã xuất")),
                "tt"   : safe_str(r.get("Tình trạng sản phẩm")),
                "hsd"  : safe_date(r.get("Hạn sử dụng sản phẩm")),
                "tc"   : safe_float(r.get("HSD tiêu chuẩn (tháng)")),
                "ma"   : safe_str(r.get("Mã tham chiếu")),
                "gc"   : safe_str(r.get("Ghi chú")),
                "ncn"  : safe_date(r.get("Ngày cập nhật") or r.get("Ngày cập nhập")),
            })
            count += 1

    print(f"   ✅ Import: {count} dòng")
    if skip:
        print(f"   ⚠  Bỏ qua: {skip} dòng (không có SKU)")

    # ── Thống kê ─────────────────────────────────────────────
    print("\n📈 Kết quả trong DB:")
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM thu_hoi_boxme")).fetchone()[0]
        print(f"   Tổng: {total} dòng\n")

        rows = conn.execute(text("""
            SELECT phan_loai,
                   COUNT(*)          AS so_dong,
                   SUM(sl_thuc_nhan) AS tong_nhan,
                   SUM(con_lai)      AS tong_con_lai
            FROM thu_hoi_boxme
            GROUP BY phan_loai
            ORDER BY so_dong DESC
        """)).fetchall()

        print(f"   {'Phân loại':<25} {'Dòng':>6} {'SL nhận':>10} {'Còn lại':>10}")
        print("   " + "-" * 55)
        for row in rows:
            print(f"   {str(row[0] or ''):<25} {row[1]:>6} "
                  f"{int(row[2] or 0):>10} {int(row[3] or 0):>10}")

    print("\n✅ Xong!")


if __name__ == "__main__":
    main()
