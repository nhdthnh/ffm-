"""
Import OQR_TỒN KHO HCNS.osheet từ NAS Synology → MySQL
Cài đặt: pip install synology-drive-api pandas pymysql openpyxl
"""

import io
import re
import warnings
import pandas as pd
import pymysql
from datetime import datetime

warnings.filterwarnings("ignore")

# ─── CẤU HÌNH ────────────────────────────────────────────────
NAS_IP    = "192.168.1.119"
USERNAME  = "thanhnhu"
PASSWORD  = "Nhdthnh10102002"
FILE_PATH = "/team-folders/OQR/HCNS/TRUYỀN THÔNG NỘI BỘ OQR/CSR/OQR_TỔN KHO HCNS.osheet"

DB = dict(
    host     = "192.168.1.119",
    port     = 3306,
    user     = "root",
    password = "Oqr@18009413",
    database = "oqr_kho",
    charset  = "utf8mb4",
    cursorclass = pymysql.cursors.DictCursor,
)
# ─────────────────────────────────────────────────────────────


# ════════════════════════════════════════════════════════════
# 1. TẢI FILE TỪ NAS
# ════════════════════════════════════════════════════════════
def load_from_nas() -> io.BytesIO:
    from synology_drive_api.drive import SynologyDrive
    for port, https in [(5000, False), (5001, True)]:
        try:
            with SynologyDrive(USERNAME, PASSWORD, NAS_IP, port,
                               https=https, dsm_version='7') as synd:
                bio = synd.download_synology_office_file(FILE_PATH)
                print(f"✅ Kết nối NAS thành công (port {port})")
                return bio
        except Exception as e:
            print(f"⚠️  Port {port} thất bại: {e}")
    raise RuntimeError("❌ Không kết nối được NAS!")


# ════════════════════════════════════════════════════════════
# 2. PARSE TỪNG SHEET
# ════════════════════════════════════════════════════════════

def clean_barcode(val) -> str | None:
    """Chuẩn hoá barcode: float 8.8e12 → '8809820741566'"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    # dạng khoa học: 8.809545e+12
    if 'e' in s.lower():
        try:
            return str(int(float(s)))
        except Exception:
            return None
    return re.sub(r'\.0$', '', s)  # bỏ .0 cuối


def parse_date(val) -> str | None:
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip().split()[0]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def base_ffill(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill cột BRAND (ô merged → NaN)"""
    df = df.copy()
    if 'BRAND' in df.columns:
        df['BRAND'] = df['BRAND'].ffill()
    return df


def is_section_header(row: pd.Series) -> bool:
    """Phát hiện dòng tiêu đề phân mục (CÓ CHỨNG TỪ / KHÔNG CHỨNG TỪ)"""
    barcode_col = next((c for c in row.index if 'BARCODE' in str(c).upper()), None)
    ten_col     = next((c for c in row.index if 'TÊN' in str(c).upper()), None)
    if barcode_col and pd.isna(row[barcode_col]):
        if ten_col and pd.isna(row[ten_col]):
            return True
    return False


# ── Sheet 1: Nhập kho ──────────────────────────────────────
def parse_nhap_kho(df: pd.DataFrame, sheet_name: str) -> list[dict]:
    # Trích dot_nhap từ tên sheet (VD: "HCNS_17" → 17)
    m = re.search(r'_(\d+)$', sheet_name)
    dot = int(m.group(1)) if m else None

    df = base_ffill(df)
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get('MÃ BARCODE'))
        if not bc:
            continue
        rows.append({
            'brand'       : str(r.get('BRAND', '') or '').strip() or None,
            'ma_barcode'  : bc,
            'ten_san_pham': str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM', '') or '').strip(),
            'don_vi_tinh' : str(r.get('ĐƠN VỊ TÍNH', '') or 'Hộp').strip(),
            'ma_sp'       : str(r.get('MÃ SP', '') or '').strip() or None,
            'so_luong'    : int(r.get('SL') or 0),
            'han_su_dung' : parse_date(r.get('HSD')),
            'dot_nhap'    : dot,
        })
    return rows


# ── Sheet 2: Tiêu huỷ ──────────────────────────────────────
def parse_tieu_huy(df: pd.DataFrame) -> list[dict]:
    df = base_ffill(df)
    co_chung_tu = True
    rows = []
    for _, r in df.iterrows():
        if is_section_header(r):
            brand_val = str(r.get('BRAND', '') or '').strip().upper()
            co_chung_tu = 'KHÔNG' not in brand_val
            continue
        bc = clean_barcode(r.get('MÃ BARCODE'))
        if not bc:
            continue
        sl = r.get('SL')
        if pd.isna(sl):
            continue
        rows.append({
            'brand'       : str(r.get('BRAND', '') or '').strip() or None,
            'ma_barcode'  : bc,
            'ten_san_pham': str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM', '') or '').strip(),
            'don_vi_tinh' : str(r.get('ĐƠN VỊ TÍNH', '') or 'Hộp').strip(),
            'so_luong'    : int(float(sl)),
            'han_su_dung' : parse_date(r.get('HSD')),
            'co_chung_tu' : co_chung_tu,
        })
    return rows


# ── Sheet 3: Tồn kho CSR ───────────────────────────────────
def parse_ton_kho_csr(df: pd.DataFrame) -> list[dict]:
    df = base_ffill(df)
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get('MÃ BARCODE'))
        if not bc:
            continue
        rows.append({
            'brand'       : str(r.get('BRAND', '') or '').strip() or None,
            'ma_barcode'  : bc,
            'ten_san_pham': str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM', '') or '').strip(),
            'don_vi_tinh' : str(r.get('ĐƠN VỊ TÍNH', '') or 'Hộp').strip(),
            'ma_sp'       : str(r.get('MÃ SP', '') or '').strip() or None,
            'so_luong'    : int(r.get('SL') or 0),
            # HSD dạng text nhiều ngày → giữ nguyên
            'han_su_dung' : str(r.get('HSD', '') or '').strip() or None,
            'ghi_chu'     : str(r.get('Unnamed: 7', '') or '').strip() or None,
        })
    return rows


# ── Sheet 4: Xuất kho FFM ──────────────────────────────────
def parse_xuat_kho(df: pd.DataFrame) -> list[dict]:
    df = base_ffill(df)
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get('MÃ BARCODE'))
        if not bc:
            continue
        rows.append({
            'brand'       : str(r.get('BRAND', '') or '').strip() or None,
            'ma_barcode'  : bc,
            'ten_san_pham': str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM', '') or '').strip(),
            'don_vi_tinh' : str(r.get('ĐƠN VỊ TÍNH', '') or 'Hộp').strip(),
            'ma_sp'       : str(r.get('MÃ SP', '') or '').strip() or None,
            'sl_de_xuat'  : int(r.get('SL ĐỀ XUẤT') or 0),
            'han_su_dung' : parse_date(r.get('HSD')),
        })
    return rows


# ── Sheet 5: Kho HCNS không chứng từ ──────────────────────
def parse_kho_khong_ct(df: pd.DataFrame) -> list[dict]:
    # Đổi tên cột (có newline)
    df = df.rename(columns={
        'MÃ\nBARCODE'       : 'MÃ BARCODE',
        'TỔNG \nSỐ LƯỢNG'  : 'SL',
        'HẠN \nSỬ DỤNG'    : 'HSD',
    })
    df['BRAND'] = df['BRAND'].ffill()
    rows = []
    for _, r in df.iterrows():
        brand_val = str(r.get('BRAND', '') or '').strip()
        bc = clean_barcode(r.get('MÃ BARCODE'))
        ten = str(r.get('TÊN SẢN PHẨM', '') or '').strip()
        if not bc and not ten:
            continue
        rows.append({
            'brand'       : brand_val or None,
            'ma_barcode'  : bc,
            'ten_san_pham': ten,
            'so_luong'    : int(r.get('SL') or 0),
            'han_su_dung' : parse_date(r.get('HSD')),
        })
    return rows


# ════════════════════════════════════════════════════════════
# 3. IMPORT VÀO MYSQL
# ════════════════════════════════════════════════════════════

def upsert_brand(cur, ten_brand: str | None) -> int | None:
    if not ten_brand:
        return None
    cur.execute(
        "INSERT INTO brands (ten_brand) VALUES (%s) "
        "ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)",
        (ten_brand,)
    )
    return cur.lastrowid


def upsert_product(cur, brand_id, barcode, ten, don_vi) -> int | None:
    if not barcode:
        return None
    cur.execute(
        "INSERT INTO products (brand_id, ma_barcode, ten_san_pham, don_vi_tinh) "
        "VALUES (%s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "  ten_san_pham = IF(ten_san_pham = '', VALUES(ten_san_pham), ten_san_pham),"
        "  id = LAST_INSERT_ID(id)",
        (brand_id, barcode, ten, don_vi or 'Hộp')
    )
    return cur.lastrowid


def import_nhap_kho(cur, rows: list[dict]):
    count = 0
    for r in rows:
        bid = upsert_brand(cur, r['brand'])
        pid = upsert_product(cur, bid, r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'])
        if not pid:
            continue
        cur.execute(
            "INSERT INTO nhap_kho (product_id, ma_sp, so_luong, han_su_dung, dot_nhap) "
            "VALUES (%s, %s, %s, %s, %s)",
            (pid, r['ma_sp'], r['so_luong'], r['han_su_dung'], r['dot_nhap'])
        )
        count += 1
    print(f"  → nhap_kho: {count} dòng")


def import_tieu_huy(cur, rows: list[dict]):
    count = 0
    for r in rows:
        bid = upsert_brand(cur, r['brand'])
        pid = upsert_product(cur, bid, r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'])
        if not pid:
            continue
        cur.execute(
            "INSERT INTO tieu_huy (product_id, so_luong, han_su_dung, co_chung_tu) "
            "VALUES (%s, %s, %s, %s)",
            (pid, r['so_luong'], r['han_su_dung'], r['co_chung_tu'])
        )
        count += 1
    print(f"  → tieu_huy: {count} dòng")


def import_ton_kho_csr(cur, rows: list[dict]):
    count = 0
    for r in rows:
        bid = upsert_brand(cur, r['brand'])
        pid = upsert_product(cur, bid, r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'])
        if not pid:
            continue
        cur.execute(
            "INSERT INTO ton_kho_csr (product_id, ma_sp, so_luong, han_su_dung, ghi_chu) "
            "VALUES (%s, %s, %s, %s, %s)",
            (pid, r['ma_sp'], r['so_luong'], r['han_su_dung'], r['ghi_chu'])
        )
        count += 1
    print(f"  → ton_kho_csr: {count} dòng")


def import_xuat_kho(cur, rows: list[dict]):
    count = 0
    for r in rows:
        bid = upsert_brand(cur, r['brand'])
        pid = upsert_product(cur, bid, r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'])
        if not pid:
            continue
        cur.execute(
            "INSERT INTO xuat_kho_ffm (product_id, ma_sp, sl_de_xuat, han_su_dung) "
            "VALUES (%s, %s, %s, %s)",
            (pid, r['ma_sp'], r['sl_de_xuat'], r['han_su_dung'])
        )
        count += 1
    print(f"  → xuat_kho_ffm: {count} dòng")


def import_kho_khong_ct(cur, rows: list[dict]):
    count = 0
    for r in rows:
        bid = upsert_brand(cur, r['brand'])
        pid = upsert_product(cur, bid, r['ma_barcode'], r['ten_san_pham'], 'Hộp') if r['ma_barcode'] else None
        cur.execute(
            "INSERT INTO kho_hcns_khong_ct (product_id, ten_san_pham, so_luong, han_su_dung) "
            "VALUES (%s, %s, %s, %s)",
            (pid, r['ten_san_pham'], r['so_luong'], r['han_su_dung'])
        )
        count += 1
    print(f"  → kho_hcns_khong_ct: {count} dòng")


# ════════════════════════════════════════════════════════════
# 4. MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("=" * 55)
    print("  OQR KHO IMPORT — NAS → MySQL")
    print("=" * 55)

    # Tải file từ NAS
    bio = load_from_nas()

    # Đọc tất cả sheets
    all_sheets = pd.read_excel(bio, sheet_name=None, header=0)
    print(f"📂 Đọc được {len(all_sheets)} sheets: {list(all_sheets.keys())}\n")

    # Parse từng sheet
    sheet_names = list(all_sheets.keys())
    rows_nhap    = parse_nhap_kho(all_sheets[sheet_names[0]], sheet_names[0])
    rows_tieu    = parse_tieu_huy(all_sheets[sheet_names[1]])
    rows_csr     = parse_ton_kho_csr(all_sheets[sheet_names[2]])
    rows_xuat    = parse_xuat_kho(all_sheets[sheet_names[3]])
    rows_khongct = parse_kho_khong_ct(all_sheets[sheet_names[4]])

    print(f"📊 Đã parse:")
    print(f"   Sheet 1 - Nhập kho   : {len(rows_nhap)} dòng")
    print(f"   Sheet 2 - Tiêu huỷ  : {len(rows_tieu)} dòng")
    print(f"   Sheet 3 - Tồn CSR   : {len(rows_csr)} dòng")
    print(f"   Sheet 4 - Xuất FFM  : {len(rows_xuat)} dòng")
    print(f"   Sheet 5 - HCNS KCT  : {len(rows_khongct)} dòng")
    print()

    # Import vào MySQL
    print("🗄️  Đang import vào MySQL...")
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            import_nhap_kho(cur, rows_nhap)
            import_tieu_huy(cur, rows_tieu)
            import_ton_kho_csr(cur, rows_csr)
            import_xuat_kho(cur, rows_xuat)
            import_kho_khong_ct(cur, rows_khongct)
        conn.commit()
        print("\n✅ Import hoàn tất!")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi, rollback: {e}")
        raise
    finally:
        conn.close()

    # Tóm tắt
    print("\n📋 Kiểm tra nhanh:")
    conn2 = pymysql.connect(**DB)
    with conn2.cursor() as cur:
        for tbl in ['brands', 'products', 'nhap_kho', 'tieu_huy',
                    'ton_kho_csr', 'xuat_kho_ffm', 'kho_hcns_khong_ct']:
            cur.execute(f"SELECT COUNT(*) as n FROM {tbl}")
            n = cur.fetchone()['n']
            print(f"   {tbl:<25}: {n} dòng")
    conn2.close()


if __name__ == "__main__":
    main()