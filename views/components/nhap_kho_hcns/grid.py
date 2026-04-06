import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, load_query

def render_data_grid(selected_date, selected_skus):
    engine = get_engine()
    
    q_data_template = load_query("nhap_kho_hcns/sku_ten_sp_hsd_so_luong.sql")
    
    # Prepare WHERE replacements (Chỉ lọc ngày trong SQL)
    date_cond = "1=1" if selected_date == "Tất cả" else "ngay_nhap = :date_val"
    sql_text = q_data_template.replace("{filters}", date_cond)
    
    with engine.begin() as conn:
        params = {"date_val": selected_date} if selected_date != "Tất cả" else {}
        df_data = pd.read_sql(text(sql_text), conn, params=params)

    # Apply Filters in Pandas for safety/flexibility
    if selected_skus:
        df_data = df_data[df_data['SKU'].isin(selected_skus)]

    # === TÍNH TOÁN GRAND TOTAL TỔNG ===
    total_nhan = int(df_data['Số lượng'].sum()) if 'Số lượng' in df_data.columns else 0
    
    # Hiển thị tóm tắt bằng các thẻ Metric ở trên bảng cho đẹp và rõ ràng
    m1, m2 = st.columns(2)
    m1.metric("📌 Số dòng dữ liệu", f"{len(df_data):,}")
    m2.metric("📥 Tổng Số Lượng", f"{total_nhan:,}")

    st.subheader("📋 Bảng Dữ Liệu")
    selected_data = []
    
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
        
        gb = GridOptionsBuilder.from_dataframe(df_data)
        gb.configure_selection('multiple', use_checkbox=True)
        
        gb.configure_column("SKU", pinned='left')
        gb.configure_column("Tên SP", pinned='left')
        
        # Gắn hàng Grand Total (Tổng cộng) ghim cứng dưới đáy bảng AgGrid
        gb.configure_grid_options(
            pinnedBottomRowData=[{
                "Tên SP": "🎯 TỔNG CỘNG:",
                "Số lượng": total_nhan,
            }]
        )
        
        gridOptions = gb.build()
        
        grid_response = AgGrid(
            df_data, 
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            theme="streamlit",
            height=400,
            width='100%'
        )
        
        selected_data = grid_response['selected_rows']
        if isinstance(selected_data, pd.DataFrame):
            selected_data = selected_data.to_dict(orient='records')
        
    except Exception:
        # FALLBACK: Dataframe native Streamlit
        try:
            st.markdown("*Đang hiển thị dạng bảng thông minh (Có hỗ trợ Chọn hàng)*")
            grid_response = st.dataframe(
                df_data, 
                use_container_width=True, 
                hide_index=True,
                selection_mode="multi-row",
                on_select="rerun"
            )
            selected_indices = grid_response.get('selection', {}).get('rows', [])
            selected_data = df_data.iloc[selected_indices].to_dict(orient='records')
            
        except Exception:
            st.info("💡 Cài `pip install streamlit-aggrid` để có bảng màu và checkbox chọn hàng.")
            edited_df = st.data_editor(
                df_data, 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config
            )
            selected_data = edited_df[edited_df['Chọn'] == True].to_dict(orient='records')
    if st.button("➕ Thêm vào danh sách", type="primary"):
        if selected_data:
            if 'cart' not in st.session_state:
                st.session_state.cart = []
            for row_data in selected_data:
                item = row_data.copy()
                item['custom_da_xuat'] = int(item.get('Số lượng', 0))
                item['custom_note'] = ''
                st.session_state.cart.append(item)
            st.success(f"Đã thêm {len(selected_data)} sản phẩm!")
            st.rerun()
        else:
            st.warning("Vui lòng tích chọn sản phẩm trong bảng (hoặc menu tìm kiếm) trước.")