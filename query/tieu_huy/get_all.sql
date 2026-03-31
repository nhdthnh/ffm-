select
    id,
    ma_barcode as 'Mã Barcode',
    ten_san_pham as 'Tên SP',
    so_luong as 'Số lượng',
    phan_loai as 'Phân loại',
    han_su_dung as 'HSD',
    ngay_cap_nhap as 'Ngày cập nhật'
from tieu_huy
where {filters}