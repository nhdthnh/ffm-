import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, load_query

def render_filters():
    engine = get_engine()
    with engine.begin() as conn:
        # SKUs Filter
        q_skus = load_query("kho_hcns_khong_chung_tu/sku_san_pham_FILTER.sql")
        df_skus = pd.read_sql(q_skus, conn)
        sku_options = []
        for _, row in df_skus.iterrows():
            sku_options.append({
                "label": f"{row['sku']} - {row['ten_san_pham']}",
                "sku": row['sku']
            })
            
    # Render UI layout
    col1, = st.columns([1])
        
    with col1:
        sku_labels = [opt["label"] for opt in sku_options]
        selected_sku_label = st.multiselect("Tìm kiếm SKU / Sản phẩm", sku_labels, placeholder="Chọn SKU hoặc Sản phẩm")
        
    selected_skus = [opt["sku"] for opt in sku_options if opt["label"] in selected_sku_label]
    
    return selected_skus
