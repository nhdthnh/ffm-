select
    ma_sp as 'Mã SP',
    ma_barcode as 'Mã Barcode',
    ten_san_pham as 'Tên SP',
    han_su_dung as 'HSD',
    so_luong as 'Số lượng',
    ghi_chu as 'Ghi chú',
    ngay_cap_nhap as 'Ngày cập nhật'
from ton_csr_co_chung_tu
where {filters}