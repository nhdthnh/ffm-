import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, load_query

def render_filters():
    engine = get_engine()
    with engine.begin() as conn:
        # Dates Filter
        q_dates = load_query("nhap_kho_hcns/ngay_nhap.sql")
        df_dates = pd.read_sql(q_dates, conn)
        date_col = next((c for c in df_dates.columns if 'ngay' in c.lower()), df_dates.columns[0])
        date_options = df_dates[date_col].dropna().astype(str).unique().tolist()
        
        # SKUs Filter
        q_skus = load_query("nhap_kho_hcns/sku_san_pham_FILTER.sql")
        df_skus = pd.read_sql(q_skus, conn)
        sku_options = []
        for _, row in df_skus.iterrows():
            sku_options.append({
                "label": f"{row['sku']} - {row['ten_sp']}",
                "sku": row['sku']
            })
            
    # Render UI layout
    col1, col2 = st.columns([1, 1.5])
    with col1:
        selected_date = st.selectbox("Chọn Ngày nhập", ["Tất cả"] + date_options)
        
    with col2:
        sku_labels = [opt["label"] for opt in sku_options]
        selected_sku_label = st.multiselect("Tìm kiếm SKU / Sản phẩm", sku_labels, placeholder="Chọn SKU hoặc Sản phẩm")
        
    selected_skus = [opt["sku"] for opt in sku_options if opt["label"] in selected_sku_label]
    
    return selected_date, selected_skus
