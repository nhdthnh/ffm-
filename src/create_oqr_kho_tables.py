"""
Tạo 3 bảng trong oqr_kho từ file Excel local:
  1. nhap_kho   — DANH SÁCH HÀNG NHẬP KHO HCNS
  2. tieu_huy   — DANH SÁCH TIÊU HỦY
  3. ton_kho    — DANH SÁCH HÀNG TỒN (CSR có chứng từ + HCNS không chứng từ)

Cài đặt: pip install pandas pymysql openpyxl
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
# DDL — TẠO BẢNG
# ════════════════════════════════════════════════════════════
DDL = """
-- ── 1. Hàng nhập kho ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS nhap_kho (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ma_sp         VARCHAR(20)   NULL COMMENT 'Mã sản phẩm nội bộ',
    ma_barcode    VARCHAR(30)   NOT NULL COMMENT 'Barcode EAN/UPC',
    ten_san_pham  TEXT          NOT NULL,
    don_vi_tinh   VARCHAR(20)   NOT NULL DEFAULT 'Hộp',
    so_luong      INT           NOT NULL DEFAULT 0,
    han_su_dung   DATE          NULL,
    ngay_nhap     DATE          NULL,
    dot_nhap      SMALLINT      NULL COMMENT 'Đợt nhập (lấy từ tên sheet, VD: 17)',
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_barcode (ma_barcode),
    INDEX idx_dot     (dot_nhap)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Danh sách hàng nhập kho HCNS theo đợt';

-- ── 2. Danh sách tiêu huỷ ────────────────────────────────
CREATE TABLE IF NOT EXISTS tieu_huy (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ma_barcode    VARCHAR(30)   NULL COMMENT 'Barcode (NULL nếu không có)',
    ten_san_pham  TEXT          NOT NULL,
    don_vi_tinh   VARCHAR(20)   NULL,
    so_luong      INT           NOT NULL DEFAULT 0,
    han_su_dung   DATE          NULL,
    co_chung_tu   TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '1=Có chứng từ, 0=Không chứng từ',
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_barcode     (ma_barcode),
    INDEX idx_co_chung_tu (co_chung_tu)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Danh sách hàng tiêu huỷ (có & không chứng từ)';

-- ── 3. Tồn kho tổng hợp (CSR + HCNS không chứng từ) ─────
CREATE TABLE IF NOT EXISTS ton_kho (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    ma_sp         VARCHAR(20)   NULL COMMENT 'Mã sản phẩm nội bộ (NULL nếu không có)',
    ma_barcode    VARCHAR(30)   NULL,
    ten_san_pham  TEXT          NOT NULL,
    don_vi_tinh   VARCHAR(20)   NULL DEFAULT 'Hộp',
    so_luong      INT           NOT NULL DEFAULT 0,
    han_su_dung   VARCHAR(100)  NULL COMMENT 'Giữ text vì HSD đôi khi có 2 ngày',
    ghi_chu       VARCHAR(255)  NULL,
    co_chung_tu   TINYINT(1)    NOT NULL DEFAULT 1 COMMENT '1=CSR có chứng từ, 0=HCNS không chứng từ',
    nguon         VARCHAR(20)   NOT NULL DEFAULT 'CSR' COMMENT 'CSR / HCNS',
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_barcode     (ma_barcode),
    INDEX idx_co_chung_tu (co_chung_tu),
    INDEX idx_nguon       (nguon)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Tồn kho tổng hợp — CSR có chứng từ + HCNS không chứng từ';
"""


# ════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════
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
    s = str(val).strip().split('\n')[0].split()[0]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def clean_str(val) -> str | None:
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


# ════════════════════════════════════════════════════════════
# PARSE SHEETS
# ════════════════════════════════════════════════════════════
def parse_nhap_kho(df: pd.DataFrame, sheet_name: str) -> list[dict]:
    m = re.search(r'_(\d+)$', sheet_name)
    dot = int(m.group(1)) if m else None
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get('MÃ BARCODE'))
        if not bc:
            continue
        rows.append({
            'ma_sp'       : clean_str(r.get('MÃ SP')),
            'ma_barcode'  : bc,
            'ten_san_pham': clean_str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM')) or '',
            'don_vi_tinh' : clean_str(r.get('ĐƠN VỊ TÍNH')) or 'Hộp',
            'so_luong'    : int(r.get('SL') or 0),
            'han_su_dung' : parse_date(r.get('HSD')),
            'ngay_nhap'   : parse_date(r.get('Ngày nhập')),
            'dot_nhap'    : dot,
        })
    return rows


def parse_tieu_huy(df: pd.DataFrame) -> list[dict]:
    rows = []
    co_chung_tu = True
    for _, r in df.iterrows():
        ten = clean_str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM'))
        bc  = clean_barcode(r.get('MÃ BARCODE'))
        sl  = r.get('SL')

        # Dòng phân mục (Có chứng từ / Không chứng từ)
        if not bc and pd.isna(sl):
            if ten and 'KHÔNG' in ten.upper():
                co_chung_tu = False
            elif ten and ('CÓ' in ten.upper() or 'CO' in ten.upper()):
                co_chung_tu = True
            continue

        if pd.isna(sl):
            continue

        # Đọc phân loại từ cột "Phân loại" nếu có
        phan_loai = clean_str(r.get('Phân loại'))
        if phan_loai:
            co_chung_tu = 'KHÔNG' not in phan_loai.upper()

        rows.append({
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'don_vi_tinh' : clean_str(r.get('ĐƠN VỊ TÍNH')),
            'so_luong'    : int(float(sl)),
            'han_su_dung' : parse_date(r.get('HSD')),
            'co_chung_tu' : 1 if co_chung_tu else 0,
        })
    return rows


def parse_ton_kho_csr(df: pd.DataFrame) -> list[dict]:
    """Sheet 3: CSR có chứng từ"""
    rows = []
    for _, r in df.iterrows():
        bc = clean_barcode(r.get('MÃ BARCODE'))
        ten = clean_str(r.get('TÊN GỌI CHÍNH THỨC CỦA SẢN PHẨM'))
        if not bc and not ten:
            continue
        hsd_raw = r.get('HSD')
        hsd_str = str(hsd_raw).strip() if not pd.isna(hsd_raw) else None
        if hsd_str and hsd_str.lower() in ('nan', 'none', ''):
            hsd_str = None
        rows.append({
            'ma_sp'       : clean_str(r.get('MÃ SP')),
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'don_vi_tinh' : clean_str(r.get('ĐƠN VỊ TÍNH')) or 'Hộp',
            'so_luong'    : int(r.get('SL') or 0),
            'han_su_dung' : hsd_str,
            'ghi_chu'     : clean_str(r.get('Ghi chú')),
            'co_chung_tu' : 1,
            'nguon'       : 'CSR',
        })
    return rows


def parse_ton_kho_hcns(df: pd.DataFrame) -> list[dict]:
    """Sheet 4: HCNS không chứng từ (khác cấu trúc cột)"""
    df = df.rename(columns=lambda c: c.replace('\n', ' ').strip())
    col_map = {}
    for c in df.columns:
        cu = c.upper()
        if 'BARCODE' in cu:
            col_map['ma_barcode'] = c
        elif 'TÊN' in cu or 'TEN' in cu:
            col_map['ten_san_pham'] = c
        elif 'LƯỢNG' in cu or 'LUONG' in cu or cu == 'SL':
            col_map['so_luong'] = c
        elif 'DỤNG' in cu or 'DUNG' in cu:
            col_map['han_su_dung'] = c

    rows = []
    for _, r in df.iterrows():
        bc  = clean_barcode(r.get(col_map.get('ma_barcode')))
        ten = clean_str(r.get(col_map.get('ten_san_pham')))
        if not bc and not ten:
            continue
        sl_raw = r.get(col_map.get('so_luong'))
        hsd_raw = r.get(col_map.get('han_su_dung'))
        hsd_str = str(hsd_raw).strip() if not pd.isna(hsd_raw) else None
        if hsd_str and hsd_str.lower() in ('nan', 'none', ''):
            hsd_str = None
        rows.append({
            'ma_sp'       : None,
            'ma_barcode'  : bc,
            'ten_san_pham': ten or '',
            'don_vi_tinh' : None,
            'so_luong'    : int(float(sl_raw)) if not pd.isna(sl_raw) else 0,
            'han_su_dung' : hsd_str,
            'ghi_chu'     : None,
            'co_chung_tu' : 0,
            'nguon'       : 'HCNS',
        })
    return rows


# ════════════════════════════════════════════════════════════
# IMPORT VÀO MYSQL
# ════════════════════════════════════════════════════════════
def import_nhap_kho(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO nhap_kho
            (ma_sp, ma_barcode, ten_san_pham, don_vi_tinh, so_luong, han_su_dung, ngay_nhap, dot_nhap)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    count = 0
    for r in rows:
        cur.execute(sql, (
            r['ma_sp'], r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'],
            r['so_luong'], r['han_su_dung'], r['ngay_nhap'], r['dot_nhap'],
        ))
        count += 1
    return count


def import_tieu_huy(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO tieu_huy
            (ma_barcode, ten_san_pham, don_vi_tinh, so_luong, han_su_dung, co_chung_tu)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    count = 0
    for r in rows:
        cur.execute(sql, (
            r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'],
            r['so_luong'], r['han_su_dung'], r['co_chung_tu'],
        ))
        count += 1
    return count


def import_ton_kho(cur, rows: list[dict]) -> int:
    sql = """
        INSERT INTO ton_kho
            (ma_sp, ma_barcode, ten_san_pham, don_vi_tinh, so_luong, han_su_dung, ghi_chu, co_chung_tu, nguon)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    count = 0
    for r in rows:
        cur.execute(sql, (
            r['ma_sp'], r['ma_barcode'], r['ten_san_pham'], r['don_vi_tinh'],
            r['so_luong'], r['han_su_dung'], r['ghi_chu'], r['co_chung_tu'], r['nguon'],
        ))
        count += 1
    return count


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  OQR KHO — Tạo bảng & Import từ Excel local → MySQL")
    print("=" * 60)

    # Đọc Excel
    print(f"\n📂 Đọc file: {LOCAL_FILE}")
    all_sheets = pd.read_excel(LOCAL_FILE, sheet_name=None, header=0)
    sheet_names = list(all_sheets.keys())
    print(f"   Số sheets: {len(sheet_names)}")
    for i, s in enumerate(sheet_names):
        print(f"   [{i+1}] {s}")

    # Parse
    rows_nhap  = parse_nhap_kho(all_sheets[sheet_names[0]], sheet_names[0])
    rows_tieu  = parse_tieu_huy(all_sheets[sheet_names[1]])
    rows_csr   = parse_ton_kho_csr(all_sheets[sheet_names[2]])
    rows_hcns  = parse_ton_kho_hcns(all_sheets[sheet_names[3]])
    rows_ton   = rows_csr + rows_hcns

    print(f"\n📊 Dữ liệu đã parse:")
    print(f"   nhap_kho : {len(rows_nhap):>4} dòng  ← {sheet_names[0]}")
    print(f"   tieu_huy : {len(rows_tieu):>4} dòng  ← {sheet_names[1]}")
    print(f"   ton_kho  : {len(rows_ton):>4} dòng  ← {sheet_names[2]} + {sheet_names[3]}")
    print(f"              ({len(rows_csr)} CSR có CT + {len(rows_hcns)} HCNS không CT)")

    # Kết nối MySQL
    print(f"\n🔌 Kết nối MySQL {DB['host']}:{DB['port']} / {DB['database']} ...")
    conn = pymysql.connect(**DB)
    print("   ✅ Kết nối thành công!")

    try:
        with conn.cursor() as cur:
            # Tạo bảng
            print("\n🏗️  Tạo bảng (nếu chưa tồn tại)...")
            for stmt in DDL.strip().split(';'):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)
            print("   ✅ Tạo xong 3 bảng: nhap_kho | tieu_huy | ton_kho")

            # Import dữ liệu
            print("\n📥 Đang import dữ liệu...")
            n1 = import_nhap_kho(cur, rows_nhap)
            print(f"   nhap_kho : {n1} dòng đã chèn")
            n2 = import_tieu_huy(cur, rows_tieu)
            print(f"   tieu_huy : {n2} dòng đã chèn")
            n3 = import_ton_kho(cur, rows_ton)
            print(f"   ton_kho  : {n3} dòng đã chèn")

        conn.commit()
        print("\n✅ Commit thành công!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Lỗi — đã rollback: {e}")
        raise
    finally:
        conn.close()

    # Kiểm tra nhanh
    print("\n📋 Kiểm tra số dòng trong DB:")
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
