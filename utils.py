"""
utils.py — Tiện ích dùng chung: kết nối DB, load SQL, xử lý kiểu dữ liệu
==========================================================================
Tất cả module trong dự án import từ file này.
"""

import os
import re
import urllib.parse

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

# ── Cấu hình kết nối Database ─────────────────────────────────────────────────
DB_HOST = "192.168.1.119"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "Oqr@18009413"
DB_NAME = "oqr_kho"


@st.cache_resource
def get_engine():
    """Tạo SQLAlchemy engine với connection pooling. Cached theo session."""
    db_pass_quoted = urllib.parse.quote(DB_PASS)
    conn_str = f"mysql+pymysql://{DB_USER}:{db_pass_quoted}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(conn_str)


def load_query(filename: str) -> str:
    """
    Đọc file SQL từ thư mục `query/`.
    Tự động loại bỏ dấu chấm cuối câu (nếu có).

    Args:
        filename: Đường dẫn tương đối từ thư mục `query/`, vd: "thu_hoi_boxme/overview.sql"

    Returns:
        Nội dung câu SQL dạng string.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    query_path = os.path.join(base_dir, "query", filename)

    with open(query_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Loại bỏ dấu chấm cuối câu SQL (nếu vô tình có)
    if content.endswith("."):
        content = content[:-1]

    return content


# ── Hàm xử lý dữ liệu an toàn ────────────────────────────────────────────────

def safe_str(val) -> str | None:
    """Chuyển về string, trả về None nếu rỗng hoặc null."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s and s not in ("-", "nan", "NaN") else None


def safe_int(val, default: int = 0) -> int:
    """Chuyển về int an toàn."""
    try:
        f = float(val)
        return int(f) if not pd.isna(f) else default
    except (TypeError, ValueError):
        return default


def safe_float(val) -> float | None:
    """Chuyển về float an toàn, làm tròn 6 chữ số."""
    try:
        f = float(val)
        return None if pd.isna(f) else round(f, 6)
    except (TypeError, ValueError):
        return None


def safe_date(val) -> str | None:
    """
    Chuẩn hóa ngày tháng về định dạng YYYY-MM-DD.
    Hỗ trợ: DD/MM/YYYY, YYYY-MM-DD, và các dạng có hậu tố 00:00:00.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None

    s = re.sub(r"\s*00:00:00$", "", str(val).strip())
    if s in ("", "-", "nan", "NaN"):
        return None

    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"

    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]

    return None


def safe_barcode(val) -> str | None:
    """
    Chuẩn hóa barcode/SKU: ưu tiên chuyển về int (loại .0),
    fallback về string nếu không phải số.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return str(int(float(val)))
    except (TypeError, ValueError):
        return safe_str(val)
