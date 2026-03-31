import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, load_query

def render_filters():
    engine = get_engine()
    with engine.begin() as conn:  
        # Ngày cập nhật Filter
        q_ngay = load_query("hang_ton_csr/ngay_cap_nhap_FILTER.sql")
        df_ngay = pd.read_sql(text(q_ngay), conn)
        ngay_options = [str(row['ngay_cap_nhap']) for _, row in df_ngay.iterrows() if pd.notnull(row['ngay_cap_nhap'])]

        # SKUs Filter
        q_skus = load_query("hang_ton_csr/sku_ten_san_pham_FILTER.sql")
        df_skus = pd.read_sql(text(q_skus), conn)
        sku_options = []
        for _, row in df_skus.iterrows():
            sku_options.append({
                "label": f"{row['sku']} - {row['ten_san_pham']}",
                "sku": row['sku']
            })
            
    # Render UI layout
    col1, col2 = st.columns([1, 1.5])
    with col1:
        selected_ngay = st.selectbox("Chọn Ngày Cập Nhật", ["Tất cả"] + ngay_options)
        
    with col2:
        sku_labels = [opt["label"] for opt in sku_options]
        selected_sku_label = st.multiselect("Tìm kiếm SKU / Sản phẩm", sku_labels, placeholder="Chọn SKU hoặc Sản phẩm")
        
    selected_skus = [opt["sku"] for opt in sku_options if opt["label"] in selected_sku_label]
    
    return selected_ngay, selected_skus