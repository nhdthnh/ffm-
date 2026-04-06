select
id,
    sku as SKU,
    ten_sp as 'Tên SP',
    han_su_dung as 'Hạn sử dụng',
    tinh_trang_san_pham as 'Tình trạng sản phẩm',
    ( CASE 
        WHEN tinh_trang_san_pham LIKE '%hết hạn%' 
          OR hsd_con_lai_thang < 0 THEN 'Hết hạn'
        WHEN tinh_trang_san_pham LIKE '%đã qua sử dụng%' 
          OR tinh_trang_san_pham LIKE '%ko có barcode%' 
          OR tinh_trang_san_pham LIKE '%ko có seal%' 
          OR tinh_trang_san_pham LIKE '%mất seal%'
          OR tinh_trang_san_pham LIKE '%không có in date%'
          OR tinh_trang_san_pham LIKE '%mờ date%'
          OR tinh_trang_san_pham LIKE '%cận date%'
          OR tinh_trang_san_pham LIKE '%khui seal%'
          OR tinh_trang_san_pham LIKE '%CTKM hết thời hạn%' THEN 'Hàng hư hỏng'
        WHEN tinh_trang_san_pham LIKE '%bị lỗi%' 
          OR tinh_trang_san_pham LIKE '%bể ô phấn%' 
          OR tinh_trang_san_pham LIKE '%không đủ số lượng%' THEN 'Hàng lỗi'
        WHEN tinh_trang_san_pham LIKE '%cấn móp%' 
          OR tinh_trang_san_pham LIKE '%bạc màu%' 
          OR tinh_trang_san_pham LIKE '%dơ%' 
          OR tinh_trang_san_pham LIKE '%rách hộp%'
          OR tinh_trang_san_pham LIKE '%rách bao bì%' THEN 'Hàng lỗi ngoại quan'
        WHEN tinh_trang_san_pham = 'sản phẩm nguyên vẹn' THEN 'Hàng nguyên vẹn'
        ELSE 'Chưa phân loại' 
    END 
    ) as 'Phân loại',
    ROUND(hsd_tieu_chuan_thang, 0) as 'HSD Tiêu chuẩn (tháng)',
    ROUND(hsd_con_lai_thang, 2) as 'HSD Còn lại (tháng)',
    ROUND(pct_hsd_con_lai, 2) as '% HSD Còn lại',
    sl_thuc_nhan as 'SL Thực nhận',
    sl_da_xuat as 'SL Đã xuất',
    con_lai as 'Còn lại',
    ma_tham_chieu as 'Mã tham chiếu',
    ghi_chu as 'Ghi chú'
from thu_hoi_boxme
where {filters}