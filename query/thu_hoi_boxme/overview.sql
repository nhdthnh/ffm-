SELECT 
    sku AS SKU,
    ten_sp AS 'Tên SP',
    SUM(sl_thuc_nhan) AS 'Tổng nhận',
    SUM(sl_da_xuat) AS 'Tổng xuất',
    SUM(con_lai) AS 'Tổng còn lại',
    doi_tac AS 'Đối tác',
    phan_loai AS 'Nguồn',
    CASE 
        WHEN tinh_trang_san_pham REGEXP 'hết hạn|đã qua sử dụng|ko có barcode|ko có seal|mất seal|không có in date|mờ date|cận date|khui seal|CTKM hết thời hạn' 
            THEN 'Hàng hư hỏng'
        WHEN tinh_trang_san_pham REGEXP 'bị lỗi|bể ô phấn|không đủ số lượng' 
            THEN 'Hàng lỗi'
        WHEN tinh_trang_san_pham REGEXP 'cấn móp|bạc màu|dơ|rách hộp|rách bao bì' 
            THEN 'Hàng lỗi ngoại quan'
        WHEN tinh_trang_san_pham = 'sản phẩm nguyên vẹn' 
            THEN 'Hàng nguyên vẹn'
        ELSE 'Chưa phân loại' 
    END AS 'Phân loại hàng'
FROM thu_hoi_boxme 
WHERE {filters}
GROUP BY 
    SKU, 
    `Tên SP`, 
    `Phân loại hàng`,
    `Đối tác`,
    `Nguồn`;