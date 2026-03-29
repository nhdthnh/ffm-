select
    id,
    ma_barcode as SKU,
    ten_san_pham as "Tên SP",
    han_su_dung as "Hạn sử dụng",
    so_luong as "Số lượng",
    ghi_chu as "Ghi chú"
from kho_hcns_khong_chung_tu
where {filters}