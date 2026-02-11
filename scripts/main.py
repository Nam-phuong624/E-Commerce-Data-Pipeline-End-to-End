import os
from sqlalchemy import text

# Import các hàm từ script hiện có của bạn
from generate_dn_data import generate_danang_branch_data_final
from generate_hcm_data import generate_and_import_data_v2
from generate_hn_data import generate_hanoi_branch_data_final
from merge_table import (
    prepare_dest_db,
    pure_ingest_and_merge,
    engine_hcm,
    engine_central,
)
from connect import setup_project_database
import time


# =========================
# UTILS: HÀM THỰC THI SQL
# =========================
def execute_sql_file(file_path, engine):
    """Đọc và thực thi file .sql để khởi tạo cấu trúc bảng"""
    if not os.path.exists(file_path):
        print(f"   ⚠️ Cảnh báo: Không tìm thấy file {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Loại bỏ các dòng chú thích và lấy nội dung SQL
            sql_commands = f.read()

        with engine.connect() as conn:
            # Thực thi toàn bộ nội dung file SQL
            conn.execute(text(sql_commands))
            conn.commit()
        print(f"   ✅ Đã thực thi cấu trúc từ: {file_path}")
    except Exception as e:
        print(f"   ❌ Lỗi khi chạy file SQL {file_path}: {e}")
        raise


# =========================
# MAIN PIPELINE
# =========================
def main():
    print("\n🚀 START DATA ENGINEERING PIPELINE (DOCKER VERSION)\n")

    try:
        print("⏳ Waiting for PostgreSQL to be ready...")
        time.sleep(15)
        # --- STEP 0: CẤU HÌNH HẠ TẦNG ---
        print("🔹 STEP 0: Initialize Infrastructure")
        # 0.1. Tạo Database và các Schema cơ bản
        setup_project_database()
        time.sleep(10)
        # 0.2. Tạo bảng cho chi nhánh HCM (Sử dụng engine từ merge_table)
        print("   -> Creating Tables for HCM Branch...")
        execute_sql_file("scripts/create_tables_hcm.sql", engine_hcm)

        # 0.3. Tạo bảng cho Database tổng hợp (Central)
        print("   -> Creating Tables for Central Data Warehouse...")
        execute_sql_file("scripts/create_tables_source.sql", engine_central)
        print("✅ DONE: Infrastructure is ready\n")

        # --- STEP 1-3: TẠO DỮ LIỆU ---
        print("🔹 STEP 1: Generate Đà Nẵng data (CSV)")
        generate_danang_branch_data_final()
        print("✅ DONE: Đà Nẵng\n")

        print("🔹 STEP 2: Generate Hồ Chí Minh data (PostgreSQL)")
        generate_and_import_data_v2()
        print("✅ DONE: Hồ Chí Minh\n")

        print("🔹 STEP 3: Generate Hà Nội data (CSV)")
        generate_hanoi_branch_data_final()
        print("✅ DONE: Hà Nội\n")

        # --- STEP 4: HỢP NHẤT DỮ LIỆU ---
        print("🔹 STEP 4: Merge all branches into Central DB")
        prepare_dest_db()
        pure_ingest_and_merge()  # Đọc từ DB HCM và các file CSV để gộp vào Central
        print("✅ DONE: Merge tables\n")

        print("🎉 PIPELINE FINISHED SUCCESSFULLY")

    except Exception as e:
        print("\n❌ PIPELINE FAILED")
        print(f"💥 Error Details: {e}")
        # Log lỗi vào bảng logging nếu cần thiết
        raise


if __name__ == "__main__":
    main()
