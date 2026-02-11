import pandas as pd
import os
from sqlalchemy import create_engine, text

# 1. CẤU HÌNH KẾT NỐI
# # Nguồn: Database chi nhánh HCM
# SOURCE_DB_URL = "postgresql+psycopg2://namphuong:2104@localhost:5432/branch_hcm"
# # Đích: Database tổng hợp (ví dụ: olist_central)
# DEST_DB_URL = "postgresql+psycopg2://namphuong:2104@localhost:5432/postgres"

SOURCE_DB_URL = "postgresql+psycopg2://namphuong:2104@db_hcm:5432/branch_hcm"
DEST_DB_URL = "postgresql+psycopg2://namphuong:2104@db_central:5432/postgres"
engine_hcm = create_engine(SOURCE_DB_URL)
engine_central = create_engine(DEST_DB_URL)


def prepare_dest_db():
    """Tạo schema bronze ở database đích nếu chưa có"""
    with engine_central.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze;"))
        conn.commit()
    print("✅ Đã chuẩn bị Schema 'bronze' tại Database đích.")


def pure_ingest_and_merge():
    # Danh sách 8 nhóm bảng cốt lõi
    table_types = [
        "orders_dataset",
        "order_items_dataset",
        "products_dataset",
        "order_customer_dataset",
        "order_payments_dataset",
        "order_reviews_dataset",
        "sellers_dataset",
        "geolocation_dataset",
    ]

    branches = {"HN": "src_data/branch_hn", "DN": "src_data/branch_dn"}

    for t_type in table_types:
        print(f"\n📦 Đang xử lý nhóm: {t_type}...")
        all_dfs = []

        # --- BƯỚC 1: LẤY DỮ LIỆU TỪ DB HCM (SOURCE) ---
        try:
            hcm_table = (
                f"olist_{t_type}"
                if t_type != "geolocation_dataset"
                else "olist_geolocation_dataset"
            )

            # Đọc từ engine_hcm
            df_hcm = pd.read_sql(
                f"SELECT * FROM bronze.{hcm_table}", engine_hcm
            ).astype(str)
            df_hcm["branch_code"] = "HCM"
            all_dfs.append(df_hcm)
            print(f"   ✅ Đã nạp {len(df_hcm)} dòng từ SQL HCM")
        except Exception as e:
            print(f"   ⚠️ Không tìm thấy bảng HCM: {t_type}")

        # --- BƯỚC 2: QUÉT VÀ ĐỌC FILE CSV (HN & DN) ---
        for b_code, b_path in branches.items():
            file_name = f"{b_code}_{t_type}.csv"
            full_path = os.path.join(b_path, file_name)

            if os.path.exists(full_path):
                try:
                    df_csv = pd.read_csv(full_path, dtype=str)
                    if df_csv.empty:
                        print(f"   ⚠️ File rỗng (0 rows): {file_name}, skip")
                        continue

                    df_csv["branch_code"] = b_code
                    all_dfs.append(df_csv)
                    print(f"   ✅ Đã nạp {len(df_csv)} dòng từ file {file_name}")

                except pd.errors.EmptyDataError:
                    print(f"   ⚠️ File rỗng (0 bytes): {file_name}, skip")

                print(f"   ✅ Đã nạp {len(df_csv)} dòng từ file {file_name}")

        # --- BƯỚC 3: HỢP NHẤT VÀ LƯU VÀO DATABASE ĐÍCH (DESTINATION) ---
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            merged_table_name = f"{t_type}"

            # Ghi vào engine_central
            final_df.to_sql(
                merged_table_name,
                engine_central,
                schema="bronze",
                if_exists="replace",
                index=False,
            )
            print(
                f"🚀 THÀNH CÔNG: Đã lưu {len(final_df)} dòng vào olist_central.bronze.{merged_table_name}"
            )


if __name__ == "__main__":
    # Đảm bảo bạn đã tạo database 'olist_central' trong Postgres trước khi chạy
    try:
        prepare_dest_db()
        pure_ingest_and_merge()
    except Exception as e:
        print(f"❌ LỖI HỆ THỐNG: {e}")
