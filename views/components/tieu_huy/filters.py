import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, load_query

def render_filters():
    engine = get_engine()
    with engine.begin() as conn:
        
        # Phân loại Filter
        q_phan_loai = load_query("tieu_huy/chung_tu_FILTER.sql")
        df_phan_loai = pd.read_sql(q_phan_loai, conn)
        
        # SKUs Filter
        q_skus = load_query("tieu_huy/SKU_san_pham_FILTER.sql")
        df_skus = pd.read_sql(q_skus, conn)
        sku_options = []
        for _, row in df_skus.iterrows():
            sku_options.append({
                "label": f"{row['sku']} - {row['ten_sp']}",
                "sku": row['sku']
            })
        
        phan_loai_options = []
        for _, row in df_phan_loai.iterrows():
            phan_loai_options.append(row['phan_loai'])
        
            
    # Render UI layout
    col1, col2 = st.columns([1, 1.5])
    with col1:
        selected_phan_loai = st.selectbox("Chọn phân loại", ["Tất cả"] + phan_loai_options)
        
    with col2:
        sku_labels = [opt["label"] for opt in sku_options]
        selected_sku_label = st.multiselect("Tìm kiếm SKU / Sản phẩm", sku_labels, placeholder="Chọn SKU hoặc Sản phẩm")
        
    selected_skus = [opt["sku"] for opt in sku_options if opt["label"] in selected_sku_label]
    
    return selected_phan_loai, selected_skus