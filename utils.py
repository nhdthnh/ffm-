import urllib.parse
from sqlalchemy import create_engine
import os
import streamlit as st

# Database constants
DB_HOST = "192.168.1.119"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "Oqr@18009413"
DB_NAME = "oqr_kho"

@st.cache_resource
def get_engine():
    db_pass_quoted = urllib.parse.quote(DB_PASS)
    conn_str = f"mysql+pymysql://{DB_USER}:{db_pass_quoted}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(conn_str)

def load_query(filename):
    # absolute path based on this utils.py location at project root
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    query_file = os.path.join(curr_dir, "query", filename)
    if not os.path.exists(query_file):
        query_file = os.path.join(curr_dir, "..", "query", filename)
        
    with open(query_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if content.endswith('.'):
            content = content[:-1]
        return content

import pandas as pd
import re

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
