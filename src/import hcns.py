"""
Import dữ liệu từ OQR_TỔN KHO HCNS.xlsx → MySQL oqr_kho
4 sheets → 4 bảng:
  Sheet 1: HÀNG NHẬP KHO  → nhap_kho        (barcode, ten, don_vi_tinh, sl, hsd, ngay_nhap)
  Sheet 2: TIÊU HỦY       → tieu_huy         (barcode, ten, sl, hsd, phan_loai)
  Sheet 3: TỒN KHO CSR    → ton_kho_csr      (barcode, ten, sl, hsd, ghi_chu)
  Sheet 4: HCNS KG CT     → kho_hcns_khong_ct (barcode, ten, sl, hsd, ghi_chu)
"""

import re
import warnings
import pandas as pd
import pymysql
from datetime import datetime

warnings.filterwarnings("ignore")

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

# ════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════

def clean_barcode(val) -> str | None:
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
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip().split('\n')[0].strip().split()[0]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def s(val) -> str | None:
    """Chuỗi sạch hoặc None"""
    if pd.isna(val):
        return None
    v = str(val).strip()
    return v if v else None


# ════════════════════════════════════════════════════════
# PARSE TỪNG SHEET
# ════════════════════════════════════════════════════════

def parse_nhap_kho(df: pd.DataFrame, sheet_name: str) -> list[dict]:
    df = df.rename(columns=lambda c: str(c).replace('\n', ' ').strip() if pd.notna(c) else '')

    col_bc  = next((c for c in df.columns if 'BARCODE' in c.upper()), None)
    col_ten = next((c for c in df.columns if 'TÊN' in c.upper() or 'TEN' in c.upper()), None)
    col_dvt = next((c for c in df.columns if 'ĐƠN VỊ' in c.upper() or 'DON VI' in c.upper()), None)
    col_sl  = next((c for c in df.columns if 'SL' == c.upper() or 'LƯỢNG' in c.upper()), None)
    col_hsd = next((c for c in df.columns if 'HSD' == c.upper() or 'HẠN' in c.upper()), None)
    col_ngay_nhap = next((c for c in df.columns if 'NGÀY' in c.upper() and 'NHẬP' in c.upper()), None)

    m = re.search(r'_(\d+)$', sheet_name)
    dot = int(m.group(1)) if m else None
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get(col_bc)) if col_bc else None
        if not bc:
            continue
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': s(r.get(col_ten)) if col_ten else '',
            'don_vi_tinh' : s(r.get(col_dvt)) if col_dvt else 'Hộp',
            'so_luong'    : int(r.get(col_sl) or 0) if col_sl else 0,
            'han_su_dung' : parse_date(r.get(col_hsd)) if col_hsd else None,
            'ngay_nhap'   : parse_date(r.get(col_ngay_nhap)) if col_ngay_nhap else None,
        })
    return rows


def parse_tieu_huy(df: pd.DataFrame) -> list[dict]:
    df = df.rename(columns=lambda c: str(c).replace('\n', ' ').strip() if pd.notna(c) else '')

    col_bc  = next((c for c in df.columns if 'BARCODE' in c.upper()), None)
    col_ten = next((c for c in df.columns if 'TÊN' in c.upper() or 'TEN' in c.upper()), None)
    col_sl  = next((c for c in df.columns if 'SL' == c.upper() or 'LƯỢNG' in c.upper()), None)
    col_hsd = next((c for c in df.columns if 'HSD' == c.upper() or 'HẠN' in c.upper()), None)
    col_pl  = next((c for c in df.columns if 'PHÂN LOẠI' in c.upper() or 'PHAN LOAI' in c.upper()), None)

    rows = []
    for _, r in df.iterrows():
        bc  = clean_barcode(r.get(col_bc)) if col_bc else None
        ten = s(r.get(col_ten)) if col_ten else None
        sl  = r.get(col_sl) if col_sl else None
        if pd.isna(sl) or (not bc and not ten):
            continue
        phan_loai = s(r.get(col_pl)) if col_pl else 'Có chứng từ'
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'so_luong'    : int(float(sl)),
            'han_su_dung' : parse_date(r.get(col_hsd)) if col_hsd else None,
            'phan_loai'   : phan_loai,
        })
    return rows


def parse_ton_kho_csr(df: pd.DataFrame) -> list[dict]:
    df = df.rename(columns=lambda c: str(c).replace('\n', ' ').strip() if pd.notna(c) else '')

    col_bc  = next((c for c in df.columns if 'BARCODE' in c.upper()), None)
    col_ten = next((c for c in df.columns if 'TÊN' in c.upper() or 'TEN' in c.upper()), None)
    col_sl  = next((c for c in df.columns if 'SL' == c.upper() or 'LƯỢNG' in c.upper()), None)
    col_hsd = next((c for c in df.columns if 'HSD' == c.upper() or 'HẠN' in c.upper()), None)
    col_gc  = next((c for c in df.columns if 'GHI CHÚ' in c.upper() or 'GHI CHU' in c.upper()), None)

    rows = []
    for _, r in df.iterrows():
        bc  = clean_barcode(r.get(col_bc)) if col_bc else None
        ten = s(r.get(col_ten)) if col_ten else None
        if not bc and not ten:
            continue
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'so_luong'    : int(r.get(col_sl) or 0) if col_sl else 0,
            'han_su_dung' : parse_date(r.get(col_hsd)) if col_hsd else None,
            'ghi_chu'     : s(r.get(col_gc)) if col_gc else None,
        })
    return rows


def parse_kho_hcns(df: pd.DataFrame) -> list[dict]:
    """
    Sheet 4: DANH SÁCH KHO HCNS KHÔNG CHỨNG TỪ
    Columns: MÃ BARCODE | TÊN SẢN PHẨM | TỔNG SỐ LƯỢNG | HẠN SỬ DỤNG
    → kho_hcns_khong_ct: ma_barcode, ten_san_pham, so_luong, han_su_dung, ghi_chu (NULL)
    """
    # Chuẩn hóa tên cột (có \n)
    df = df.rename(columns=lambda c: c.replace('\n', ' ').strip())

    col_bc  = next((c for c in df.columns if 'BARCODE' in c.upper()), None)
    col_ten = next((c for c in df.columns if 'TÊN' in c.upper() or 'TEN' in c.upper()), None)
    col_sl  = next((c for c in df.columns if 'LƯỢNG' in c.upper() or 'LUONG' in c.upper()), None)
    col_hsd = next((c for c in df.columns if 'DỤNG' in c.upper() or 'DUNG' in c.upper()), None)

    rows = []
    for _, r in df.iterrows():
        bc  = clean_barcode(r.get(col_bc)) if col_bc else None
        ten = s(r.get(col_ten)) if col_ten else None
        if not bc and not ten:
            continue
        sl_raw = r.get(col_sl) if col_sl else None
        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'so_luong'    : int(float(sl_raw)) if sl_raw and not pd.isna(sl_raw) else 0,
            'han_su_dung' : parse_date(r.get(col_hsd)) if col_hsd else None,
            'ghi_chu'     : None,
        })
    return rows


# ════════════════════════════════════════════════════════
# IMPORT VÀO MYSQL
# ════════════════════════════════════════════════════════

def import_nhap_kho(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO nhap_kho_hcns
            (ma_barcode, ten_san_pham, don_vi_tinh, so_luong, han_su_dung, ngay_nhap)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'],
            r['so_luong'], r['han_su_dung'], r['ngay_nhap'],
        ))
    return len(rows)


def import_tieu_huy(cur, rows: list[dict]) -> int:
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


def import_ton_kho_csr(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO ton_csr_co_chung_tu
            (ma_barcode, ten_san_pham, so_luong, han_su_dung, ghi_chu)
        VALUES (%s, %s, %s, %s, %s)
    """
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'],
            r['so_luong'], r['han_su_dung'], r['ghi_chu'],
        ))
    return len(rows)


def import_kho_hcns(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO kho_hcns_khong_chung_tu
            (ma_barcode, ten_san_pham, so_luong, han_su_dung, ghi_chu)
        VALUES (%s, %s, %s, %s, %s)
    """
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'],
            r['so_luong'], r['han_su_dung'], r['ghi_chu'],
        ))
    return len(rows)


# ════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  OQR KHO — Import Excel → MySQL")
    print("=" * 60)

    # Đọc Excel
    print(f"\n📂 Đọc: {LOCAL_FILE}")
    all_sheets = pd.read_excel(LOCAL_FILE, sheet_name=None, header=0)
    names = list(all_sheets.keys())
    print(f"   Số sheets: {len(names)}")
    for i, n in enumerate(names):
        print(f"   [{i+1}] {n}")

    # Parse
    s1 = parse_nhap_kho  (all_sheets[names[0]], names[0])
    s2 = parse_tieu_huy  (all_sheets[names[1]])
    s3 = parse_ton_kho_csr(all_sheets[names[2]])
    s4 = parse_kho_hcns  (all_sheets[names[3]])

    print(f"\n📊 Dữ liệu đã parse:")
    print(f"   nhap_kho          : {len(s1):>4} dòng")
    print(f"   tieu_huy          : {len(s2):>4} dòng")
    print(f"   ton_kho_csr       : {len(s3):>4} dòng")
    print(f"   kho_hcns_khong_ct : {len(s4):>4} dòng")

    # Kết nối
    print(f"\n🔌 Kết nối MySQL {DB['host']} / {DB['database']} ...")
    conn = pymysql.connect(**DB)
    print("   ✅ Thành công!")

    try:
        with conn.cursor() as cur:
            print("\n📥 Đang import...")
            n1 = import_nhap_kho   (cur, s1)  ; print(f"   nhap_kho_hcns     : {n1} dòng ✓")
            n2 = import_tieu_huy   (cur, s2)  ; print(f"   tieu_huy          : {n2} dòng ✓")
            n3 = import_ton_kho_csr(cur, s3)  ; print(f"   ton_csr_co_chung_tu: {n3} dòng ✓")
            n4 = import_kho_hcns   (cur, s4)  ; print(f"   kho_hcns_khong_chung_tu: {n4} dòng ✓")
        conn.commit()
        print("\n✅ Commit thành công!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi — đã rollback!\n   {e}")
        raise
    finally:
        conn.close()

    # Kiểm tra
    print("\n📋 Kiểm tra số dòng trong DB:")
    conn2 = pymysql.connect(**DB)
    with conn2.cursor() as cur:
        for tbl in ['nhap_kho_hcns', 'tieu_huy', 'ton_csr_co_chung_tu', 'kho_hcns_khong_chung_tu']:
            cur.execute(f"SELECT COUNT(*) as n FROM `{tbl}`")
            n = cur.fetchone()['n']
            print(f"   {tbl:<22}: {n} dòng")
    conn2.close()
    print("\n🎉 Hoàn tất!")


if __name__ == "__main__":
    main()
