"""
Import dữ liệu từ OQR_TỔN KHO HCNS.xlsx → MySQL (oqr_kho)

Mapping 4 sheet → 3 bảng (khớp cấu trúc cột trong DB):
  Sheet 1  DANH SÁCH HÀNG NHẬP KHO HCNS_17  → nhap_kho
  Sheet 2  DANH SÁCH TIÊU HỦY               → tieu_huy
  Sheet 3  DANH SÁCH HÀNG TỒN CSR           → ton_kho  (co_chung_tu=1)
  Sheet 4  DANH SÁCH KHO HCNS KHÔNG CHỨNG   → ton_kho  (co_chung_tu=0)

Cài: pip install pandas pymysql openpyxl
"""

import re
import warnings
import pandas as pd
import pymysql
from datetime import datetime

warnings.filterwarnings("ignore")

# ─── CẤU HÌNH ────────────────────────────────────────────────
LOCAL_FILE = r"C:\Users\OQR\Desktop\ffm\OQR_TỔN KHO HCNS.xlsx"

DB = dict(
    host        = "192.168.1.119",
    port        = 3306,
    user        = "root",
    password    = "Oqr@18009413",
    database    = "oqr_kho",
    charset     = "utf8mb4",
    cursorclass = pymysql.cursors.DictCursor,
)
# ─────────────────────────────────────────────────────────────


# ════════════════════════════════════════════════════════════
# HELPER
# ════════════════════════════════════════════════════════════
def clean_barcode(val) -> str | None:
    """Chuẩn hoá barcode: float 8.8e12 → '8809820741566'"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if 'e' in s.lower():
        try:
            return str(int(float(s)))
        except Exception:
            return None
    return re.sub(r'\.0$', '', s)


def parse_date(val) -> str | None:
    """Chuyển nhiều định dạng ngày về YYYY-MM-DD"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip().replace('\n', ' ').split()[0]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def clean(val) -> str | None:
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s or None


# ════════════════════════════════════════════════════════════
# PARSE SHEET 1 → nhap_kho
# Cột DB: id | ma_barcode | ten_san_pham | don_vi_tinh | so_luong | han_su_dung | ngay_nhap
# ════════════════════════════════════════════════════════════
def parse_nhap_kho(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get('MÃ BARCODE'))
        if not bc:
            continue
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': clean(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM')) or '',
            'don_vi_tinh' : clean(r.get('ĐƠN VỊ TÍNH')) or 'Hộp',
            'so_luong'    : int(r.get('SL') or 0),
            'han_su_dung' : parse_date(r.get('HSD')),
            'ngay_nhap'   : parse_date(r.get('Ngày nhập')),
        })
    return rows


# ════════════════════════════════════════════════════════════
# PARSE SHEET 2 → tieu_huy
# Cột DB: id | ma_barcode | ten_san_pham | so_luong | han_su_dung | phan_loai
# ════════════════════════════════════════════════════════════
def parse_tieu_huy(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        sl = r.get('SL')
        if pd.isna(sl):
            continue
        bc = clean_barcode(r.get('MÃ BARCODE'))
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': clean(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM')) or '',
            'so_luong'    : int(float(sl)),
            'han_su_dung' : parse_date(r.get('HSD')),
            'phan_loai'   : clean(r.get('Phân loại')),   # 'Có chứng từ' / 'Không chứng từ'
        })
    return rows


# ════════════════════════════════════════════════════════════
# PARSE SHEET 3 → ton_kho (CSR có chứng từ)
# Cột DB: id | ma_barcode | ten_san_pham | so_luong | han_su_dung | ghi_chu
# ════════════════════════════════════════════════════════════
def parse_ton_kho_csr(df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in df.iterrows():
        bc  = clean_barcode(r.get('MÃ BARCODE'))
        ten = clean(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM'))
        if not bc and not ten:
            continue
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'so_luong'    : int(r.get('SL') or 0),
            'han_su_dung' : parse_date(r.get('HSD')),
            'ghi_chu'     : clean(r.get('Ghi chú')),
        })
    return rows


# ════════════════════════════════════════════════════════════
# PARSE SHEET 4 → ton_kho (HCNS không chứng từ)
# Cột gốc: MÃ\nBARCODE | TÊN SẢN PHẨM | TỔNG \nSỐ LƯỢNG | HẠN \nSỬ DỤNG
# ════════════════════════════════════════════════════════════
def parse_ton_kho_hcns(df: pd.DataFrame) -> list[dict]:
    # Chuẩn hoá tên cột (có newline)
    df = df.rename(columns={
        'MÃ\nBARCODE'      : 'MÃ BARCODE',
        'TỔNG \nSỐ LƯỢNG'  : 'SL',
        'HẠN \nSỬ DỤNG'    : 'HSD',
        'TÊN SẢN PHẨM'     : 'TÊN SẢN PHẨM',
    })
    rows = []
    for _, r in df.iterrows():
        bc  = clean_barcode(r.get('MÃ BARCODE'))
        ten = clean(r.get('TÊN SẢN PHẨM'))
        if not bc and not ten:
            continue
        sl_raw = r.get('SL')
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'so_luong'    : int(float(sl_raw)) if not pd.isna(sl_raw) else 0,
            'han_su_dung' : parse_date(r.get('HSD')),
            'ghi_chu'     : None,
        })
    return rows


# ════════════════════════════════════════════════════════════
# INSERT VÀO DB
# ════════════════════════════════════════════════════════════
def insert_nhap_kho(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO nhap_kho
            (ma_barcode, ten_san_pham, don_vi_tinh, so_luong, han_su_dung, ngay_nhap)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'],
            r['so_luong'], r['han_su_dung'], r['ngay_nhap'],
        ))
    return len(rows)


def insert_tieu_huy(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO tieu_huy
            (ma_barcode, ten_san_pham, so_luong, han_su_dung, phan_loai)
        VALUES (%s, %s, %s, %s, %s)
    """
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'],
            r['so_luong'], r['han_su_dung'], r['phan_loai'],
        ))
    return len(rows)


def insert_ton_kho(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO ton_kho
            (ma_barcode, ten_san_pham, so_luong, han_su_dung, ghi_chu)
        VALUES (%s, %s, %s, %s, %s)
    """
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'],
            r['so_luong'], r['han_su_dung'], r['ghi_chu'],
        ))
    return len(rows)


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  OQR KHO — Import Excel → MySQL")
    print("=" * 60)

    # Đọc Excel
    print(f"\n📂 Đọc: {LOCAL_FILE}")
    all_sheets = pd.read_excel(LOCAL_FILE, sheet_name=None, header=0)
    sheets     = list(all_sheets.values())
    names      = list(all_sheets.keys())
    print(f"   {len(names)} sheets: {names}")

    # Parse
    rows_nhap = parse_nhap_kho(sheets[0])
    rows_tieu = parse_tieu_huy(sheets[1])
    rows_csr  = parse_ton_kho_csr(sheets[2])
    rows_hcns = parse_ton_kho_hcns(sheets[3])
    rows_ton  = rows_csr + rows_hcns

    print(f"\n📊 Dữ liệu đã parse:")
    print(f"   nhap_kho  : {len(rows_nhap):>4} dòng  ← {names[0]}")
    print(f"   tieu_huy  : {len(rows_tieu):>4} dòng  ← {names[1]}")
    print(f"   ton_kho   : {len(rows_ton):>4} dòng  ← {names[2]} ({len(rows_csr)}) + {names[3]} ({len(rows_hcns)})")

    # Kết nối MySQL
    print(f"\n🔌 Kết nối MySQL {DB['host']}:{DB['port']} / {DB['database']} ...")
    conn = pymysql.connect(**DB)
    print("   ✅ OK!")

    try:
        with conn.cursor() as cur:
            print("\n📥 Import...")
            n1 = insert_nhap_kho(cur, rows_nhap)
            print(f"   nhap_kho : {n1} dòng ✓")
            n2 = insert_tieu_huy(cur, rows_tieu)
            print(f"   tieu_huy : {n2} dòng ✓")
            n3 = insert_ton_kho(cur, rows_ton)
            print(f"   ton_kho  : {n3} dòng ✓")
        conn.commit()
        print("\n✅ Commit thành công!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi — đã rollback!\n   {e}")
        raise
    finally:
        conn.close()

    # Kiểm tra
    print("\n📋 Số dòng trong DB:")
    conn2 = pymysql.connect(**DB)
    with conn2.cursor() as cur:
        for tbl in ['nhap_kho', 'tieu_huy', 'ton_kho']:
            cur.execute(f"SELECT COUNT(*) as n FROM {tbl}")
            n = cur.fetchone()['n']
            print(f"   {tbl:<12}: {n} dòng")
    conn2.close()
    print("\n🎉 Hoàn tất!")


if __name__ == "__main__":
    main()
