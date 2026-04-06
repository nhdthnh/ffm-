"""
views/template.py — Tải xuống file mẫu Excel
"""

import os
import streamlit as st

TEMPLATES_DIR = "templates"

TEMPLATE_FILES = [
    {
        "file": "(ALL) FFM_Tổng hợp hàng xuất kho Boxme về văn phòng.xlsx",
        "label": "FFM · Tổng hợp hàng xuất kho Boxme",
        "desc": "Dùng để import dữ liệu **Thu hồi Boxme**. Sheet cần dùng: `Tổng hợp thu hồi`.",
        "icon": "📦",
    },
    {
        "file": "OQR_TỔN KHO HCNS.xlsx",
        "label": "OQR · Tồn kho HCNS",
        "desc": "Dùng để import dữ liệu **Nhập kho HCNS**, **Tồn CSR**, và **HCNS không chứng từ**.",
        "icon": "🏭",
    },
]


def show():
    st.markdown("## 📄 Template · Tải xuống file mẫu")
    st.markdown("---")

    st.info(
        "📌 Tải về file Excel mẫu bên dưới, nhập dữ liệu vào đúng sheet được chỉ định, "
        "sau đó sử dụng chức năng **Import** trong từng module tương ứng. "
        "**Xóa sạch dữ liệu cũ** trước khi nhập dữ liệu mới để tránh trùng lặp."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    cols = st.columns(len(TEMPLATE_FILES))

    for i, tmpl in enumerate(TEMPLATE_FILES):
        filepath = os.path.join(TEMPLATES_DIR, tmpl["file"])
        with cols[i]:
            st.markdown(f"""
            <div style="background:#f8fffe; border:1px solid #d1fae5; border-radius:12px;
                        padding:20px; min-height:180px;">
                <div style="font-size:32px; margin-bottom:10px;">{tmpl['icon']}</div>
                <div style="font-size:15px; font-weight:600; color:#0a2a1a; margin-bottom:8px;">{tmpl['label']}</div>
                <div style="font-size:13px; color:#555; line-height:1.5;">{tmpl['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label=f"📥 Tải xuống",
                    data=file_bytes,
                    file_name=tmpl["file"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"dl_{i}",
                )
            else:
                st.error(f"❌ Không tìm thấy file: `{tmpl['file']}`")
