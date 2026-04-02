import mysql.connector

# Cấu hình kết nối
config = {
    'user': 'root',
    'password': 'Oqr@18009413',
    'host': '192.168.1.119',
    'database': 'oqr_kho'
}

def setup_triggers():
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 1. Tìm tất cả các bảng có cột ten_san_pham hoặc ten_sp
        query_find_tables = """
        SELECT TABLE_NAME, COLUMN_NAME 
        FROM information_schema.columns 
        WHERE table_schema = %s 
        AND column_name IN ('ten_san_pham', 'ten_sp')
        """
        cursor.execute(query_find_tables, (config['database'],))
        tables = cursor.fetchall()

        for table_name, col_name in tables:
            # 2. Tìm cột mapping phù hợp (ma_barcode, sku, hoặc ma_sp)
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            existing_cols = [c[0] for c in cursor.fetchall()]
            
            map_col = next((c for c in ['ma_barcode', 'sku', 'ma_sp'] if c in existing_cols), None)
            
            if not map_col:
                print(f"--- Bỏ qua {table_name}: Không có cột mapping.")
                continue

            print(f"Đang thiết lập Trigger cho: {table_name}...")

            # Tên của Trigger (Xóa cái cũ nếu có để tránh lỗi)
            trigger_name_ins = f"tg_{table_name}_sync_name_ins"
            trigger_name_upd = f"tg_{table_name}_sync_name_upd"

            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name_ins}")
            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name_upd}")

            # 3. Tạo Trigger đồng bộ khi INSERT
            sql_ins = f"""
            CREATE TRIGGER {trigger_name_ins}
            BEFORE INSERT ON {table_name}
            FOR EACH ROW
            BEGIN
                DECLARE real_name VARCHAR(255);
                SELECT name INTO real_name FROM omisell_db.product WHERE sku = NEW.{map_col} LIMIT 1;
                IF real_name IS NOT NULL THEN
                    SET NEW.{col_name} = real_name;
                END IF;
            END
            """

            # 4. Tạo Trigger đồng bộ khi UPDATE (Chặn user sửa bừa trên lưới)
            sql_upd = f"""
            CREATE TRIGGER {trigger_name_upd}
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            BEGIN
                DECLARE real_name VARCHAR(255);
                SELECT name INTO real_name FROM omisell_db.product WHERE sku = NEW.{map_col} LIMIT 1;
                IF real_name IS NOT NULL THEN
                    SET NEW.{col_name} = real_name;
                END IF;
            END
            """

            cursor.execute(sql_ins)
            cursor.execute(sql_upd)
            print(f"--- Đã kích hoạt chặn nhập bừa cho {table_name} thành công.")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[HỆ THỐNG PHÒNG THỦ KÍCH HOẠT] User không thể nhập sai tên được nữa.")

    except mysql.connector.Error as err:
        print(f"Lỗi: {err}")

if __name__ == "__main__":
    setup_triggers()