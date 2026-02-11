import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
import os
import uuid
# from shared_customers import generate_customer_pool

fake = Faker("vi_VN")

HN_CONF = {
    "daily_range": (40, 60),
    "price_scale": 1.0,
    "carriers": ["GHTK", "Viettel Post", "GHN", "VNPost"],
    "loyalty_rate": 0.15,
    "cancel_rate": 0.05,
}


def generate_hanoi_branch_data_final():
    output_path = "src_data/branch_hn"
    os.makedirs(output_path, exist_ok=True)

    # =========================
    # 1. LOAD MASTER PRODUCTS
    # =========================
    master_file = "/home/namphuong/project_cv/master_products_reference.csv"
    if not os.path.exists(master_file):
        print(f"❌ Lỗi: Không tìm thấy file {master_file}")
        return

    df_master = pd.read_csv(master_file)

    start_date, end_date = datetime(2020, 1, 1), datetime(2025, 1, 1)
    days = (end_date - start_date).days

    # =========================
    # 2. MASTER DATA HÀ NỘI
    # =========================
    hn_districts = [
        "Quận Ba Đình",
        "Quận Hoàn Kiếm",
        "Quận Hai Bà Trưng",
        "Quận Đống Đa",
        "Quận Cầu Giấy",
        "Quận Long Biên",
    ]

    geo = pd.DataFrame(
        [
            {
                "geolocation_zip_code_prefix": i,
                "geolocation_lat": round(random.uniform(20.95, 21.05), 6),
                "geolocation_lng": round(random.uniform(105.75, 105.85), 6),
                "geolocation_city": random.choice(hn_districts),
                "geolocation_state": "HN",
            }
            for i in range(2000, 2020)
        ]
    )
    shared_customers = pd.read_csv("src_data/shared/shared_customers.csv")
    customers = shared_customers.sample(
        n=5000,  # số customer của HCM
        replace=False,
    ).copy()

    customers["customer_city"] = "Hà Nội"
    customers["customer_state"] = "HN"
    customers["customer_zip_code_prefix"] = np.random.choice(
        geo["geolocation_zip_code_prefix"].values, size=len(customers)
    )

    customers["branch_code"] = "HN"

    sellers = pd.DataFrame(
        [
            {
                "seller_id": f"SELL_HN_{i}",
                "seller_zip_code_prefix": random.choice(
                    geo["geolocation_zip_code_prefix"].values
                ),
                "seller_city": "Hà Nội",
                "seller_state": "HN",
            }
            for i in range(10)
        ]
    )

    # =========================
    # 3. PRODUCTS – VN CATEGORY
    # =========================
    product_map_vn = {
        "Bearings": "vòng bi",
        "Lubricants": "mỡ bôi trơn",
        "Seals": "phớt chặn",
        "Tools": "dụng cụ",
    }

    products_hn = df_master.copy()
    products_hn["product_category_name"] = products_hn["product_category_name"].map(
        product_map_vn
    )

    # =========================
    # 4. LOYAL CUSTOMERS
    # =========================
    loyal_pool = random.sample(
        list(customers["customer_id"].unique()),
        k=int(len(customers) * HN_CONF["loyalty_rate"]),
    )

    # =========================
    # 5. TRANSACTIONAL DATA
    # =========================
    orders, items, payments, reviews = [], [], [], []

    for i in range(days):
        curr_date = start_date + timedelta(days=i)
        daily_count = random.randint(*HN_CONF["daily_range"])

        for _ in range(daily_count):
            oid = str(uuid.uuid4())[:16]

            cid = (
                random.choice(loyal_pool)
                if random.random() < 0.3
                else random.choice(customers["customer_id"].values)
            )

            carrier = random.choice(HN_CONF["carriers"])
            buy_ts = curr_date + timedelta(hours=random.randint(8, 20))

            delay_days = (
                random.randint(1, 2)
                if carrier in ["GHN", "GHTK"]
                else random.randint(4, 8)
            )

            status_rand = random.random()
            if status_rand < HN_CONF["cancel_rate"]:
                status = "canceled"
            elif status_rand < HN_CONF["cancel_rate"] + 0.03:
                status = "returned"
            else:
                status = "delivered"

            orders.append(
                {
                    "order_id": oid,
                    "customer_id": cid,
                    "order_status": status,
                    "carrier_name": carrier,
                    "order_purchase_timestamp": buy_ts.strftime("%d/%m/%Y %H:%M"),
                    "order_approved_at": (buy_ts + timedelta(hours=2)).strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    "order_delivered_carrier_date": (
                        buy_ts + timedelta(days=1)
                    ).strftime("%d/%m/%Y %H:%M"),
                    "order_delivered_customer_date": (
                        (buy_ts + timedelta(days=delay_days)).strftime("%d/%m/%Y %H:%M")
                        if status == "delivered"
                        else None
                    ),
                    "order_estimated_delivery_date": (
                        buy_ts + timedelta(days=3)
                    ).strftime("%d/%m/%Y %H:%M"),
                }
            )

            # ===== ITEMS =====
            p_id = random.choice(products_hn["product_id"].values)
            price = round(random.uniform(100, 900) * HN_CONF["price_scale"], 2)

            items.append(
                {
                    "order_id": oid,
                    "order_item_id": 1,
                    "product_id": p_id,
                    "seller_id": random.choice(sellers["seller_id"].values),
                    "price": price,
                    "freight_value": 15.0,
                    "shipping_limit_date": (buy_ts + timedelta(days=3)).strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                }
            )

            # ===== PAYMENTS =====
            payments.append(
                {
                    "order_id": oid,
                    "payment_sequential": 1,
                    "payment_type": random.choice(
                        ["credit_card", "bank_transfer", "cod", "e_wallet"]
                    ),
                    "payment_installments": 1,
                    "payment_value": f"{price + 15:.0f} VND",
                }
            )

            # ===== REVIEWS =====
            # ===== REVIEWS – HÀ NỘI (HN) =====

            create_review = False
            score = None

            # Delivered: ~20% có review
            if status == "delivered":
                if random.random() < 0.20:
                    create_review = True
                    score = random.choices(
                        [1, 2, 3, 4, 5],
                        weights=[0.05, 0.10, 0.20, 0.30, 0.35],
                    )[0]

            # Returned: ~30% có review, score thấp
            elif status == "returned":
                if random.random() < 0.30:
                    create_review = True
                    score = random.choice([1, 2])

            # Canceled: KHÔNG review

            if create_review:
                reviews.append(
                    {
                        "review_id": fake.uuid4()[:16],
                        "order_id": oid,
                        "review_score": score,
                        "review_creation_date": buy_ts + timedelta(days=delay_days + 1),
                        "review_answer_timestamp": buy_ts + timedelta(days=delay_days + 2),
                    }
                )

    # =========================
    # 6. EXPORT CSV
    # =========================
    export_map = {
        "geolocation_dataset": geo,
        "order_customer_dataset": customers,
        "sellers_dataset": sellers,
        "products_dataset": products_hn,
        "orders_dataset": pd.DataFrame(orders),
        "order_items_dataset": pd.DataFrame(items),
        "order_payments_dataset": pd.DataFrame(payments),
        "order_reviews_dataset": pd.DataFrame(reviews),
    }

    for name, df in export_map.items():
        df.to_csv(
            os.path.join(output_path, f"HN_{name}.csv"),
            index=False,
            encoding="utf-8-sig",
        )

    print("✅ Đã hoàn tất Hà Nội (All-Branch Logic Applied).")


if __name__ == "__main__":
    generate_hanoi_branch_data_final()
