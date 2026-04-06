import streamlit as st
import pandas as pd
from sqlalchemy import text
from utils import get_engine, load_query

def render_data_grid(selected_date, selected_phan_loai, selected_skus):
    engine = get_engine()
    
    q_data_template = load_query("thu_hoi_boxme/sku_san_pham_sl_thuc_nhan_sl_da_xuat_con_lai.sql")
    
    # Prepare WHERE replacements (Chỉ lọc ngày trong SQL)
    date_cond = "1=1" if selected_date == "Tất cả" else "ngay_cap_nhat = :date_val"
    sql_text = q_data_template.replace("{filters}", date_cond)
    
    with engine.begin() as conn:
        params = {"date_val": selected_date} if selected_date != "Tất cả" else {}
        df_data = pd.read_sql(text(sql_text), conn, params=params)

    # Apply Filters in Pandas for safety/flexibility
    if selected_phan_loai != "Tất cả":
        df_data = df_data[df_data['Phân loại'] == selected_phan_loai]

    if selected_skus:
        df_data = df_data[df_data['SKU'].isin(selected_skus)]

    # === TÍNH TOÁN GRAND TOTAL TỔNG ===
    total_nhan = int(df_data['SL Thực nhận'].sum()) if 'SL Thực nhận' in df_data.columns else 0
    total_xuat = int(df_data['SL Đã xuất'].sum()) if 'SL Đã xuất' in df_data.columns else 0
    total_con_lai = int(df_data['Còn lại'].sum()) if 'Còn lại' in df_data.columns else 0
    
    # Hiển thị tóm tắt bằng các thẻ Metric ở trên bảng cho đẹp và rõ ràng
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📌 Số dòng dữ liệu", f"{len(df_data):,}")
    m2.metric("📥 Tổng Thực Nhận", f"{total_nhan:,}")
    m3.metric("📤 Tổng Đã Xuất", f"{total_xuat:,}")
    m4.metric("📦 Tổng Còn Lại", f"{total_con_lai:,}")

    st.subheader("📋 Bảng Dữ Liệu")

    if 'HSD Tiêu chuẩn (tháng)' in df_data.columns:
        df_data['HSD Tiêu chuẩn (tháng)'] = pd.to_numeric(df_data['HSD Tiêu chuẩn (tháng)'], errors='coerce').astype('Int64')
    if 'HSD Còn lại (tháng)' in df_data.columns:
        df_data['HSD Còn lại (tháng)'] = pd.to_numeric(df_data['HSD Còn lại (tháng)'], errors='coerce').round(2)
    if '% HSD Còn lại' in df_data.columns:
        df_data['% HSD Còn lại'] = pd.to_numeric(df_data['% HSD Còn lại'], errors='coerce').round(2)
        
    # Thiết lập màu sắc nền cho từng trạng thái Phân loại
    def color_phan_loai(val):
        if pd.isna(val) or val is None:
            return ''
        val_str = str(val).strip()
        if val_str == 'Hết hạn':
            return 'background-color: #6c757d; color: #ffffff' # xám
        elif val_str == 'Hàng nguyên vẹn':
            return 'background-color: #d4edda; color: #000000' # xanh lá
        elif val_str == 'Hàng lỗi ngoại quan':
            return 'background-color: #fff3cd; color: #000000' # vàng nhạt
        elif val_str == 'Hàng lỗi':
            return 'background-color: #634d0d; color: #ffffff' # vàng đậm hơn
        elif val_str == 'Hàng hư hỏng':
            return 'background-color: #ff2424; color: #ffffff' # đỏ nhạt
        return ''

    styled_df = df_data.style
    
    styled_df = styled_df.format({
        'HSD Còn lại (tháng)': "{:.2f}",
        '% HSD Còn lại': "{:.2f}"
    }, na_rep="")
    
    if 'Phân loại' in df_data.columns:
        try:
            styled_df = styled_df.map(color_phan_loai, subset=['Phân loại'])
        except Exception:
            styled_df = styled_df.applymap(color_phan_loai, subset=['Phân loại'])

    column_config = {}
    try:
        column_config = {
            "Chọn": st.column_config.CheckboxColumn(pinned=True),
            "SKU": st.column_config.TextColumn(pinned=True),
            "Tên SP": st.column_config.TextColumn(pinned=True),
            "Hạn sử dụng": st.column_config.Column(pinned=True),
            "Tình trạng sản phẩm": st.column_config.Column(pinned=True),
            "HSD Còn lại (tháng)": st.column_config.NumberColumn(format="%.2f"),
            "% HSD Còn lại": st.column_config.NumberColumn(format="%.2f"),
            "HSD Tiêu chuẩn (tháng)": st.column_config.NumberColumn(format="%d")
        }
    except Exception:
        column_config = {}

    selected_data = []
    
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
        
        gb = GridOptionsBuilder.from_dataframe(df_data)
        gb.configure_selection('multiple', use_checkbox=True)
        
        cellstyle_jscode = JsCode("""
        function(params) {
            if (!params.value) return null;
            if (params.value === 'Hết hạn') {
                return {'color': '#ffffff', 'backgroundColor': '#6c757d'};
            } else if (params.value === 'Hàng nguyên vẹn') {
                return {'color': '#155724', 'backgroundColor': '#d4edda'};
            } else if (params.value === 'Hàng lỗi ngoại quan') {
                return {'color': '#856404', 'backgroundColor': '#fff3cd'};
            } else if (params.value === 'Hàng lỗi') {
                return {'color': '#856404', 'backgroundColor': '#ffeeba'};
            } else if (params.value === 'Hàng hư hỏng') {
                return {'color': '#721c24', 'backgroundColor': '#f8d7da'};
            }
            return null;
        }
        """)
        gb.configure_column("Phân loại", cellStyle=cellstyle_jscode)
        
        gb.configure_column("SKU", pinned='left')
        gb.configure_column("Tên SP", pinned='left')
        
        # Format HSD
        gb.configure_column("HSD Tiêu chuẩn (tháng)", 
                            type=["numericColumn"], 
                            valueFormatter=JsCode("function(params) { return params.value == null ? '' : Math.floor(params.value); }"))

        gb.configure_column("HSD Còn lại (tháng)", 
                            type=["numericColumn"], 
                            valueFormatter=JsCode("function(params) { return params.value == null ? '' : Number(params.value).toFixed(2); }"))
                            
        gb.configure_column("% HSD Còn lại", 
                            type=["numericColumn"], 
                            valueFormatter=JsCode("function(params) { return params.value == null ? '' : Number(params.value).toFixed(2); }"))
        
        # Gắn hàng Grand Total (Tổng cộng) ghim cứng dưới đáy bảng AgGrid
        gb.configure_grid_options(
            pinnedBottomRowData=[{
                "Tên SP": "🎯 TỔNG CỘNG:",
                "SL Thực nhận": total_nhan,
                "SL Đã xuất": total_xuat,
                "Còn lại": total_con_lai
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
                styled_df, 
                use_container_width=True, 
                hide_index=True,
                selection_mode="multi-row",
                on_select="rerun"
            )
            selected_indices = grid_response.get('selection', {}).get('rows', [])
            selected_data = df_data.iloc[selected_indices].to_dict(orient='records')
            
        except Exception:
            st.info("💡 MÁY BÁO: Để có Màu sắc sinh động đồng thời có hộp Chọn, anh vui lòng chạy lệnh `pip install streamlit-aggrid` trên Terminal.")
            edited_df = st.data_editor(
                df_data, 
                use_container_width=True, 
                hide_index=True,
                column_config=column_config
            )
            selected_data = edited_df[edited_df['Chọn'] == True].to_dict(orient='records')

    if st.button("➕ Thêm vào danh sách", type="primary"):
        if selected_data:
            for row_data in selected_data:
                item = row_data.copy()
                item['custom_da_xuat'] = int(item.get('SL Đã xuất', 0))
                item['custom_note'] = ''
                st.session_state.cart.append(item)
            st.success(f"Đã thêm {len(selected_data)} sản phẩm!")
            st.rerun()
        else:
            st.warning("Vui lòng tích chọn sản phẩm trong bảng (hoặc menu tìm kiếm) trước.")
