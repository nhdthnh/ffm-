# 📦 Kho nội bộ OQR — v2.0

Hệ thống quản lý kho nội bộ của **OQR Co., Ltd** được xây dựng bằng Streamlit, kết nối MariaDB nội bộ.

---

## 🗂️ Cấu trúc dự án

```
ffm-/
├── app.py                        # Entrypoint chính: routing, sidebar, session
├── utils.py                      # Kết nối DB, load SQL, helper functions
├── utils_auth.py                 # Hệ thống xác thực & phân quyền RBAC
│
├── .streamlit/
│   └── config.toml               # Tắt sidebar navigation mặc định
│
├── query/                        # Toàn bộ câu SQL, phân theo module
│   ├── thu_hoi_boxme/
│   ├── nhap_kho_hcns/
│   ├── hang_ton_csr/
│   ├── kho_hcns_khong_chung_tu/
│   ├── tieu_huy/
│   └── report/
│
├── views/                        # Các trang (pages)
│   ├── login.py                  # Màn hình đăng nhập
│   ├── about.py                  # Thông tin phiên bản
│   ├── report.py                 # Nhúng Google Looker Studio
│   ├── template.py               # Tải file Excel mẫu
│   ├── system_logs.py            # Nhật ký hệ thống
│   ├── user_management.py        # Quản lý người dùng & phân quyền
│   ├── thu_hoi_boxme.py
│   ├── hang_nhap_kho_hcns.py
│   ├── hang_ton_csr.py
│   ├── kho_hcns_khong_chung_tu.py
│   ├── tieu_huy.py
│   └── components/               # Sub-components theo module
│       ├── _shared.py            # CSS dùng chung (inject_cart_css)
│       ├── thu_hoi_boxme/
│       ├── nhap_kho_hcns/
│       ├── ton_csr/
│       ├── kho_hcns_khong_chung_tu/
│       └── tieu_huy/
│
├── templates/                    # File Excel mẫu để import
│   ├── (ALL) FFM_Tổng hợp hàng xuất kho Boxme về văn phòng.xlsx
│   └── OQR_TỔN KHO HCNS.xlsx
│
├── log/
│   └── db_log.xlsx               # Database người dùng + nhật ký hoạt động
│
└── src/                          # Scripts hỗ trợ (import, migration)
    ├── create_oqr_kho_tables.py
    ├── import_thu_hoi_boxme.py
    ├── import_to_db.py
    └── import hcns.py
```

---

## 🚀 Cài đặt & Khởi chạy

### 1. Yêu cầu

- Python 3.11+
- Kết nối mạng nội bộ đến `192.168.1.119` (MariaDB)

### 2. Cài dependencies

```bash
pip install streamlit sqlalchemy pymysql pandas openpyxl
# Tùy chọn (bảng có màu + checkbox):
pip install streamlit-aggrid
```

### 3. Khởi chạy

```bash
cd C:\Users\OQR\Desktop\ffm-
streamlit run app.py
```

Ứng dụng mở trên `http://localhost:8501`.

---

## 🔐 Hệ thống xác thực & phân quyền

### Tài khoản người dùng

Lưu tại `log/db_log.xlsx` — sheet `users`.

| Cột | Mô tả |
|-----|-------|
| `user` | Tên đăng nhập |
| `password` | Mật khẩu (plain text, khuyến nghị đổi sang SHA256) |
| `full_name` | Tên hiển thị |
| `email` | Email |
| `is_active` | `1` = hoạt động, `0` = bị khoá |
| `is_superadmin` | `1` = bypass toàn bộ phân quyền |
| `session_version` | Tăng khi admin sửa → tự động đăng xuất phiên cũ |
| `perm_*` | Quyền theo từng trang (xem bên dưới) |

### Mức quyền (`perm_*`)

| Giá trị | Ý nghĩa |
|---------|---------|
| `0` | Không có quyền — trang bị ẩn khỏi menu |
| `1` | Xem (read-only) — không thể import/sửa/xóa |
| `2` | Ghi — xem + import Excel + cập nhật DB |
| `9` | Quản trị — toàn quyền kể cả xóa hàng loạt |

### Danh sách quyền theo trang

| Slug | Trang |
|------|-------|
| `perm_report` | 📊 Report |
| `perm_thu_hoi_boxme` | 📦 Thu hồi Boxme |
| `perm_nhap_kho_hcns` | 📥 Hàng nhập kho HCNS |
| `perm_hang_ton_csr` | 🧾 Hàng tồn CSR |
| `perm_hcns_khong_ct` | 📋 HCNS không chứng từ |
| `perm_tieu_huy` | 🗑️ Tiêu hủy |
| `perm_template` | 📄 Template |
| `perm_system_logs` | 📓 Nhật ký hệ thống |
| `perm_about` | ℹ️ About |
| `perm_user_mgmt` | 🔐 Quản lý người dùng |

---

## 📋 Hướng dẫn sử dụng từng module

### 📦 Thu hồi Boxme
1. Tải template: **📄 Template** → *FFM · Tổng hợp hàng xuất kho Boxme*
2. Nhập dữ liệu vào sheet **`Tổng hợp thu hồi`**
3. Vào trang **Thu hồi Boxme** → mở **Import Data từ file Excel** → upload file
4. Nhấn **Tiến hành Import** → dữ liệu ghi thêm vào bảng `thu_hoi_boxme`
5. Dùng bộ lọc (ngày / phân loại / SKU) để tìm hàng
6. Tích chọn hàng → **Thêm vào danh sách** → chỉnh **Đã xuất** → **Cập nhật Database**

### 📥 Hàng nhập kho HCNS
1. Template: **OQR · Tồn kho HCNS**
2. Import → bảng `nhap_kho_hcns`
3. Chọn hàng → cập nhật số lượng đã xuất

### 🧾 Hàng tồn CSR
- Dữ liệu bảng `ton_csr_co_chung_tu`
- Import và cập nhật tồn kho

### 📋 HCNS không chứng từ
- Dữ liệu bảng `kho_hcns_khong_chung_tu`

### 🗑️ Tiêu hủy
- Import → **TRUNCATE** bảng cũ → nạp dữ liệu mới
- ⚠️ Mỗi lần import sẽ xóa toàn bộ dữ liệu cũ trong bảng `tieu_huy`

### 📊 Report
- Nhúng Google Looker Studio — cần kết nối internet

### 📄 Template
- Tải file Excel mẫu để import dữ liệu

### 📓 Nhật ký hệ thống
- Xem lịch sử thao tác theo người dùng
- Hỗ trợ tìm kiếm từ khóa và giới hạn số dòng

### 🔐 Quản lý người dùng
- Chỉ dành cho tài khoản có `perm_user_mgmt = 9`
- Tạo / sửa / xóa / khoá tài khoản
- Phân quyền từng trang cho từng user

---

## 🛠️ Cấu hình Database

Chỉnh sửa trong `utils.py`:

```python
DB_HOST = "192.168.1.119"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "..."
DB_NAME = "oqr_kho"
```

---

## 🗃️ Cấu trúc Database (`oqr_kho`)

| Bảng | Module |
|------|--------|
| `thu_hoi_boxme` | Thu hồi Boxme |
| `nhap_kho_hcns` | Hàng nhập kho HCNS |
| `ton_csr_co_chung_tu` | Hàng tồn CSR |
| `kho_hcns_khong_chung_tu` | HCNS không chứng từ |
| `tieu_huy` | Tiêu hủy |

---

## 📝 Nhật ký phiên bản

| Phiên bản | Ngày | Nội dung |
|-----------|------|---------|
| **v2.0** | 06/04/2026 | UI/UX redesign toàn bộ, clean code, README, shared CSS |
| v1.1 | 03/04/2026 | Login SHA256, RBAC hoàn chỉnh, session version |
| v1.0 | 28/03/2026 | Ra mắt lần đầu |

---

*OQR Co., Ltd · Hệ thống quản lý kho nội bộ*
