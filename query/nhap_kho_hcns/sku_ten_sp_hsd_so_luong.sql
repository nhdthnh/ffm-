SELECT
    id,
    ma_barcode as SKU,
    ten_san_pham as 'Tên SP',
    don_vi_tinh as 'Đơn vị tính',
    han_su_dung as 'Hạn sử dụng',
    so_luong as 'Số lượng'
from nhap_kho_hcns
where {filters}