import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import os
import numpy as np
# from shared_customers import generate_customer_pool

# =========================
# CONFIG
# =========================
fake = Faker("vi_VN")

engine = create_engine("postgresql+psycopg2://namphuong:2104@localhost:5432/branch_hcm")

HCM_CONF = {
    "daily_range": (80, 120),
    "price_scale": 1.2,
    "carriers": ["GHN", "GHTK", "GrabExpress", "Viettel Post"],
    "loyalty_rate": 0.25,
    "cancel_rate": 0.03,
}


MASTER_FILE = "/home/namphuong/project_cv/master_products_reference.csv"


def generate_and_import_data_v2():
    # =========================
    # 1. LOAD MASTER PRODUCTS
    # =========================
    if not os.path.exists(MASTER_FILE):
        print(f"❌ Không tìm thấy file {MASTER_FILE}")
        return

    products = pd.read_csv(MASTER_FILE)
    print("📖 Loaded Master Products")

    # =========================
    # 2. MASTER DATA - HCM
    # =========================
    hcm_districts = [
        "Quận 1",
        "Quận 3",
        "Quận 7",
        "Bình Thạnh",
        "Thủ Đức",
        "Tân Bình",
        "Gò Vấp",
    ]

    geo = pd.DataFrame(
        [
            {
                "geolocation_zip_code_prefix": i,
                "geolocation_lat": round(random.uniform(10.70, 10.85), 8),
                "geolocation_lng": round(random.uniform(106.60, 106.75), 8),
                "geolocation_city": random.choice(hcm_districts),
                "geolocation_state": "HCMC",
            }
            for i in range(1000, 1050)
        ]
    )

    shared_customers = pd.read_csv("src_data/shared/shared_customers.csv")

    customers = shared_customers.sample(
        n=12000,  # số customer của HCM
        replace=False,
    ).copy()

    customers["customer_city"] = "Thành phố Hồ Chí Minh"
    customers["customer_state"] = "HCMC"
    customers["customer_zip_code_prefix"] = np.random.choice(
        geo["geolocation_zip_code_prefix"].values, size=len(customers)
    )

    customers["branch_code"] = "HCM"

    sellers = pd.DataFrame(
        [
            {
                "seller_id": f"SELL_{i}",
                "seller_zip_code_prefix": random.choice(
                    geo["geolocation_zip_code_prefix"].values
                ),
                "seller_city": "Thành phố Hồ Chí Minh",
                "seller_state": "HCMC",
            }
            for i in range(50)
        ]
    )

    # =========================
    # 3. LOYAL CUSTOMERS
    # =========================
    loyal_pool = random.sample(
        list(customers["customer_id"].unique()),
        k=int(len(customers) * HCM_CONF["loyalty_rate"]),
    )

    # =========================
    # 4. TRANSACTIONAL DATA
    # =========================
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 1, 1)
    days = (end_date - start_date).days

    orders, items, payments, reviews = [], [], [], []

    for i in range(days):
        curr_date = start_date + timedelta(days=i)
        daily_count = random.randint(*HCM_CONF["daily_range"])

        for _ in range(daily_count):
            oid = fake.uuid4()[:16]

            cid = (
                random.choice(loyal_pool)
                if random.random() < 0.3
                else random.choice(customers["customer_id"].values)
            )

            carrier = random.choice(HCM_CONF["carriers"])
            buy_ts = curr_date + timedelta(hours=random.randint(8, 20))

            delay_days = (
                random.randint(1, 2)
                if carrier in ["GHN", "GHTK", "GrabExpress"]
                else random.randint(4, 9)
            )

            status_rand = random.random()
            if status_rand < HCM_CONF["cancel_rate"]:
                status = "canceled"
            elif status_rand < HCM_CONF["cancel_rate"] + 0.02:
                status = "returned"
            else:
                status = "delivered"

            orders.append(
                {
                    "order_id": oid,
                    "customer_id": cid,
                    "order_status": status,
                    "carrier_name": carrier,
                    "order_purchase_timestamp": buy_ts,
                    "order_approved_at": buy_ts + timedelta(minutes=30),
                    "order_delivered_carrier_date": buy_ts + timedelta(days=1),
                    "order_delivered_customer_date": (
                        buy_ts + timedelta(days=delay_days)
                        if status == "delivered"
                        else None
                    ),
                    "order_estimated_delivery_date": buy_ts + timedelta(days=3),
                }
            )

            # ===== ITEMS =====
            p_id = random.choice(products["product_id"].values)
            price = round(random.uniform(100, 1000) * HCM_CONF["price_scale"], 2)

            if random.random() < 0.01:
                price = -50.0  # test validation

            items.append(
                {
                    "order_id": oid,
                    "order_item_id": 1,
                    "product_id": p_id,
                    "seller_id": random.choice(sellers["seller_id"].values),
                    "price": price,
                    "freight_value": 20.0,
                    "shipping_limit_date": buy_ts + timedelta(days=3),
                }
            )

            # ===== PAYMENTS =====
            payment_type = random.choices(
                ["credit_card", "bank_transfer", "cod", "e_wallet"],
                weights=[3, 4, 2, 1],
            )[0]

            payments.append(
                {
                    "order_id": oid,
                    "payment_sequential": 1,
                    "payment_type": payment_type,
                    "payment_installments": 1,
                    "payment_value": price + 20,
                }
            )

            # ===== REVIEWS =====
            # ===== REVIEWS (FIXED LOGIC) =====

            create_review = False
            score = None

            if status == "delivered":
                if random.random() < 0.2:
                    create_review = True
                    score = random.choices(
                        [1, 2, 3, 4, 5],
                        weights=[0.05, 0.10, 0.20, 0.30, 0.35],
                    )[0]

            elif status == "returned":
                if random.random() < 0.3:
                    create_review = True
                    score = random.choice([1, 2])

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
    # 5. LOAD TO BRONZE
    # =========================
    data_map = {
        "olist_geolocation_dataset": geo,
        "olist_order_customer_dataset": customers,
        "olist_sellers_dataset": sellers,
        "olist_products_dataset": products,
        "olist_orders_dataset": pd.DataFrame(orders),
        "olist_order_items_dataset": pd.DataFrame(items),
        "olist_order_payments_dataset": pd.DataFrame(payments),
        "olist_order_reviews_dataset": pd.DataFrame(reviews),
    }

    for table, df in data_map.items():
        df.to_sql(
            table,
            engine,
            schema="bronze",
            if_exists="replace",
            index=False,
        )
        print(f"✅ Loaded {len(df)} rows into bronze.{table}")


if __name__ == "__main__":
    generate_and_import_data_v2()
