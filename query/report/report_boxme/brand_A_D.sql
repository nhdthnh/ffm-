select bsc.brand as "Brand", sum(bsc.available_quantity) as "Hàng A có thể xuất", sum(bsc.d1_available_quantity) as "Hàng D1 có thể xuất", sum(bsc.d2_available_quantity) as "Hàng D2 có thể xuất", sum(bsc.d3_available_quantity) as "Hàng D3 có thể xuất", sum(
        bsc.damaged_available_quantity
    ) as "Hàng D có thể xuất"
from boxme.boxme_stock_check bsc
group by
    bsc.brand
order by sum(bsc.available_quantity) desc