"""
views/user_management.py
=========================
Trang quản lý người dùng và phân quyền — chỉ dành cho người có quyền quản trị.
"""

import streamlit as st
import pandas as pd
import utils_auth
from utils_auth import PERM_SLUGS, PERM_LABELS, PERM_LEVEL_LABELS
import time


def show():
    # ── Kiểm tra quyền ───────────────────────────────────────────────────────
    utils_auth.require_perm("perm_user_mgmt", required=9)

    st.title("🔐 Quản lý Người dùng & Phân quyền")
    st.markdown("---")

    is_superadmin = st.session_state.get("is_superadmin", False)
    current_user = st.session_state.get("username", "")

    tab1, tab2, tab3 = st.tabs([
        "👥 Danh sách người dùng",
        "➕ Thêm / Sửa người dùng",
        "🗑️ Xoá người dùng",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — Danh sách người dùng
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("📋 Danh sách tài khoản trong hệ thống")

        df = utils_auth.get_all_users()

        if df.empty:
            st.info("Chưa có người dùng nào.")
        else:
            # Bộ lọc
            search = st.text_input("🔍 Tìm kiếm theo username / họ tên", placeholder="Nhập từ khoá...", key="search_user")
            if search:
                mask = (
                    df["user"].astype(str).str.contains(search, case=False, na=False) |
                    df.get("full_name", pd.Series(dtype=str)).astype(str).str.contains(search, case=False, na=False)
                )
                df = df[mask]

            # Hiển thị bảng
            display_cols = ["user", "full_name", "email", "is_active", "is_superadmin"] + PERM_SLUGS
            display_cols = [c for c in display_cols if c in df.columns]

            col_config = {
                "user": st.column_config.TextColumn("👤 Tài khoản", width="medium"),
                "full_name": st.column_config.TextColumn("📝 Họ tên", width="medium"),
                "email": st.column_config.TextColumn("📧 Email", width="medium"),
                "is_active": st.column_config.CheckboxColumn("✅ Hoạt động"),
                "is_superadmin": st.column_config.CheckboxColumn("👑 Siêu quản trị"),
            }
            for slug in PERM_SLUGS:
                col_config[slug] = st.column_config.NumberColumn(
                    PERM_LABELS.get(slug, slug),
                    help="0=Không, 1=Xem, 2=Ghi, 9=Admin",
                    min_value=0, max_value=9,
                    width="small",
                )

            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config=col_config,
            )

            st.markdown("---")
            st.markdown("**Chú giải mức quyền:**")
            cols = st.columns(4)
            for i, (level, label) in enumerate(PERM_LEVEL_LABELS.items()):
                cols[i].markdown(f"**`{level}`** — {label}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — Thêm / Sửa người dùng
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        mode = st.radio("Chế độ", ["➕ Thêm mới", "✏️ Sửa người dùng hiện có"], horizontal=True, key="user_mode_radio")
        st.markdown("---")

        # Chọn user cần sửa
        existing_username = None
        existing_data = {}
        if mode == "✏️ Sửa người dùng hiện có":
            df_all = utils_auth.get_all_users()
            users_list = df_all["user"].astype(str).tolist() if not df_all.empty else []
            if not users_list:
                st.info("Chưa có người dùng nào để sửa.")
            else:
                existing_username = st.selectbox("Chọn tài khoản để sửa", users_list, key="edit_user_select")
                raw = utils_auth.get_user(existing_username)
                if raw:
                    existing_data = raw

        st.subheader("📝 Thông tin tài khoản")

        col_a, col_b = st.columns(2)
        with col_a:
            inp_user = st.text_input(
                "Tên đăng nhập *",
                value=existing_data.get("user", ""),
                disabled=(mode == "✏️ Sửa người dùng hiện có"),
                placeholder="vd: nguyen.van.a",
                key=f"inp_user_{mode}"
            )
            inp_full_name = st.text_input(
                "Họ và tên",
                value=existing_data.get("full_name", ""),
                placeholder="Nguyễn Văn A",
                key=f"inp_name_{mode}"
            )
        with col_b:
            inp_email = st.text_input(
                "Email",
                value=existing_data.get("email", ""),
                placeholder="email@example.com",
                key=f"inp_email_{mode}"
            )
            inp_is_active = st.toggle(
                "✅ Tài khoản hoạt động",
                value=int(float(str(existing_data.get("is_active", 1)))) == 1,
                key=f"inp_active_{mode}"
            )

        # Mật khẩu
        st.markdown("#### 🔑 Mật khẩu")
        pw_col1, pw_col2 = st.columns(2)
        with pw_col1:
            if mode == "✏️ Sửa người dùng hiện có":
                change_pw = st.checkbox("Thay đổi mật khẩu", key="edit_change_pw")
            else:
                change_pw = True

            inp_password = st.text_input(
                "Mật khẩu mới" if mode == "✏️ Sửa người dùng hiện có" else "Mật khẩu *",
                type="password",
                disabled=(mode == "✏️ Sửa người dùng hiện có" and not change_pw),
                key=f"inp_pw1_{mode}"
            )
        with pw_col2:
            inp_password2 = st.text_input(
                "Xác nhận mật khẩu",
                type="password",
                disabled=(mode == "✏️ Sửa người dùng hiện có" and not change_pw),
                key=f"inp_pw2_{mode}"
            )

        # Superadmin (chỉ superadmin mới đặt được)
        if is_superadmin:
            current_super = int(float(str(existing_data.get("is_superadmin", 0)))) == 1
            # Không thể bỏ superadmin của chính mình
            disabled_super = (mode == "✏️ Sửa người dùng hiện có" and existing_username == current_user)
            inp_is_superadmin = st.toggle(
                "👑 Siêu quản trị (bypass toàn bộ phân quyền)",
                value=current_super,
                disabled=disabled_super,
                help="Siêu quản trị có toàn quyền trên mọi trang, không bị giới hạn bởi phân quyền.",
                key=f"inp_super_{mode}"
            )
        else:
            inp_is_superadmin = bool(int(float(str(existing_data.get("is_superadmin", 0)))))

        # ── Phân quyền từng trang ───────────────────────────────────────────
        st.markdown("---")
        st.subheader("🔒 Phân quyền theo trang")
        st.caption("0 = Không có quyền | 1 = Xem | 2 = Ghi | 9 = Quản trị")

        perm_values = {}
        n_cols = 2
        perm_chunks = [PERM_SLUGS[i:i+n_cols] for i in range(0, len(PERM_SLUGS), n_cols)]

        for chunk in perm_chunks:
            cols = st.columns(n_cols)
            for ci, slug in enumerate(chunk):
                default_val = int(float(str(existing_data.get(slug, 0))))
                options = [0, 1, 2, 9]
                option_labels = [PERM_LEVEL_LABELS[o] for o in options]
                try:
                    def_idx = options.index(default_val)
                except ValueError:
                    def_idx = 0
                selected_label = cols[ci].selectbox(
                    PERM_LABELS.get(slug, slug),
                    options=option_labels,
                    index=def_idx,
                    key=f"perm_{mode}_{slug}",
                )
                # Map label → int
                reverse = {v: k for k, v in PERM_LEVEL_LABELS.items()}
                perm_values[slug] = reverse.get(selected_label, 0)

        st.markdown("---")

        # Nút lưu
        btn_label = "💾 Tạo tài khoản" if mode == "➕ Thêm mới" else "💾 Cập nhật"
        if st.button(btn_label, type="primary", use_container_width=True, key=f"btn_save_{mode}"):
            # Validation
            errors = []
            if mode == "➕ Thêm mới":
                if not inp_user.strip():
                    errors.append("Tên đăng nhập không được để trống.")
                if not inp_password:
                    errors.append("Mật khẩu không được để trống.")
            if change_pw and inp_password and inp_password != inp_password2:
                errors.append("Mật khẩu xác nhận không khớp.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                user_data = {
                    "user": inp_user.strip(),
                    "full_name": inp_full_name.strip(),
                    "email": inp_email.strip(),
                    "is_active": "1" if inp_is_active else "0",
                    "is_superadmin": "1" if inp_is_superadmin else "0",
                }
                if change_pw and inp_password:
                    user_data["password"] = inp_password

                user_data.update({slug: str(v) for slug, v in perm_values.items()})

                if mode == "➕ Thêm mới":
                    with st.spinner("Đang tạo tài khoản..."):
                        ok, msg = utils_auth.create_user(user_data)
                else:
                    with st.spinner("Đang cập nhật thông tin..."):
                        ok, msg = utils_auth.update_user(
                            existing_username, user_data,
                            change_password=(change_pw and bool(inp_password)),
                        )

                if ok:
                    st.success(msg)
                    st.toast(msg, icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
                    st.toast(msg, icon="❌")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — Xoá người dùng
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.subheader("⚠️ Xoá tài khoản người dùng")
        st.warning("Thao tác này không thể hoàn tác. Hãy cân nhắc trước khi xóa.")

        df_all = utils_auth.get_all_users()
        users_deletable = [u for u in df_all["user"].astype(str).tolist() if u != current_user]

        if not users_deletable:
            st.info("Không có tài khoản nào để xoá (ngoài tài khoản đang đăng nhập).")
        else:
            del_user = st.selectbox("Chọn tài khoản cần xoá", users_deletable, key="del_user_select")

            # Hiển thị thông tin user cần xoá
            del_info = utils_auth.get_user(del_user)
            if del_info:
                c1, c2, c3 = st.columns(3)
                c1.metric("👤 Tài khoản", del_info.get("user", ""))
                c2.metric("📝 Họ tên", del_info.get("full_name", ""))
                c3.metric(
                    "👑 Superadmin",
                    "Có" if int(float(str(del_info.get("is_superadmin", 0)))) == 1 else "Không"
                )

            confirm = st.checkbox(
                f"✅ Tôi xác nhận muốn xoá tài khoản **{del_user}** và không thể hoàn tác.",
                key="confirm_delete",
            )

            if st.button("🗑️ Xoá tài khoản", type="primary", disabled=not confirm, key="btn_delete"):
                ok, msg = utils_auth.delete_user(del_user)
                if ok:
                    st.success(msg)
                    st.toast(msg, icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
                    st.toast(msg, icon="❌")

        st.markdown("---")
        st.subheader("🔒 Khoá / Mở khoá tài khoản")
        st.caption("Khoá tài khoản sẽ không cho phép đăng nhập, nhưng không xoá dữ liệu.")

        all_users = df_all["user"].astype(str).tolist() if not df_all.empty else []
        lock_user = st.selectbox("Chọn tài khoản", [u for u in all_users if u != current_user], key="lock_user_select")

        if lock_user:
            lock_info = utils_auth.get_user(lock_user)
            is_locked = int(float(str(lock_info.get("is_active", 1)))) == 0 if lock_info else False
            btn_text = "🔓 Mở khoá tài khoản" if is_locked else "🔒 Khoá tài khoản"
            st.markdown(f"Trạng thái hiện tại: **{'🔒 Đang bị khoá' if is_locked else '✅ Đang hoạt động'}**")

            if st.button(btn_text, key="btn_lock"):
                ok, msg = utils_auth.toggle_user_lock(lock_user)
                if ok:
                    st.success(msg)
                    st.toast(msg, icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
                    st.toast(msg, icon="❌")
