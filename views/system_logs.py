"""
views/system_logs.py — Trang nhật ký hoạt động hệ thống
"""

import streamlit as st
import utils_auth


def show():
    st.markdown("## 📓 Nhật ký Hệ thống")
    st.markdown("Lịch sử thao tác của tất cả tài khoản, sắp xếp mới nhất lên đầu.")

    utils_auth.require_perm("perm_system_logs", required=1)

    df_logs = utils_auth.get_logs()

    if df_logs.empty:
        st.info("Chưa có dữ liệu nhật ký nào.")
        return

    # Sắp xếp mới nhất lên đầu
    if "time" in df_logs.columns:
        df_logs = df_logs.sort_values(by="time", ascending=False)

    # ── Bộ lọc ──────────────────────────────────────────────────────────────
    col_a, col_b = st.columns([3, 1])
    with col_a:
        search_query = st.text_input("🔍 Tìm kiếm nội dung log", placeholder="Nhập từ khóa...")
    with col_b:
        limit = st.number_input("Số dòng hiển thị", min_value=10, max_value=5000, value=200, step=50)

    if search_query:
        df_logs = df_logs[df_logs["log"].astype(str).str.contains(search_query, case=False, na=False)]

    df_logs = df_logs.head(int(limit))

    # ── Hiển thị bảng ────────────────────────────────────────────────────────
    st.dataframe(
        df_logs,
        use_container_width=True,
        hide_index=True,
        column_config={
            "time": st.column_config.DatetimeColumn("⏰ Thời gian", format="DD/MM/YYYY HH:mm:ss"),
            "log": st.column_config.TextColumn("📝 Nội dung thao tác"),
        },
    )
    st.caption(f"Hiển thị **{len(df_logs):,}** dòng.")
