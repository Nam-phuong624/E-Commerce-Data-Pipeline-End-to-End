import psycopg2
from psycopg2 import extensions
import os


def setup_project_database():
    # 1. Thông số kết nối (Điều chỉnh theo máy của bạn)
    db_params = {
        "host": os.getenv(
            "DB_HOST", "db_hcm"
        ),  # Quan trọng: đổi localhost thành tên service
        "user": os.getenv("DB_USER", "namphuong"),
        "password": os.getenv("DB_PASS", "2104"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": "postgres",  # Kết nối vào db mặc định để tạo db mới
    }

    conn = None
    try:
        # KẾT NỐI ĐỂ TẠO DATABASE
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Tạo Database mới cho dự án SKF Intern
        db_name = "branch_hcm"
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Đã tạo Database: {db_name}")
        else:
            print(f"ℹ️ Database {db_name} đã tồn tại.")

        cur.close()
        conn.close()

        # KẾT NỐI VÀO DATABASE MỚI ĐỂ TẠO SCHEMA
        db_params["database"] = db_name
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # 2. TẠO CÁC SCHEMA THEO KIẾN TRÚC MEDALLION
        schemas = ["bronze", "silver", "gold", "logging"]
        for schema in schemas:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        print(f"✅ Đã tạo các Schemas: {', '.join(schemas)}")

        # 3. TẠO BẢNG LOG LỖI (Quan trọng để gây ấn tượng với SKF)
        create_log_table = """
        CREATE TABLE IF NOT EXISTS logging.error_logs (
            log_id SERIAL PRIMARY KEY,
            source_name VARCHAR(50),      -- 'Hanoi_Excel', 'Distributor_CSV', 'HCMC_SQL'
            table_name VARCHAR(50),
            error_message TEXT,
            raw_data JSONB,               -- Lưu lại dòng dữ liệu bị lỗi để kiểm tra
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cur.execute(create_log_table)
        print("✅ Đã tạo bảng logging.error_logs để quản trị tính toàn vẹn dữ liệu.")

        conn.commit()
        print("\n🚀 Hạ tầng dữ liệu đã sẵn sàng để bơm dữ liệu từ Faker!")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()


if __name__ == "__main__":
    setup_project_database()
