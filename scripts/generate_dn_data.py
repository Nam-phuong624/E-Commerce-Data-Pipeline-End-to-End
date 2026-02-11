import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
import uuid
# from shared_customers import generate_customer_pool
from faker import Faker

DN_CONF = {
    "daily_range": (15, 30),
    "price_scale": 0.8,
    "carriers": ["VNPost", "Viettel Post", "GHTK"],
    "loyalty_rate": 0.10,
    "cancel_rate": 0.08,
}
fake = Faker("vi_VN")

def generate_danang_branch_data_final():
    output_path = "src_data/branch_dn"
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
    # 2. MASTER DATA ĐỊA PHƯƠNG
    # =========================
    dn_districts = [
        "Quận Hải Châu",
        "Quận Thanh Khê",
        "Quận Sơn Trà",
        "Quận Ngũ Hành Sơn",
        "Quận Liên Chiểu",
    ]

    geo = pd.DataFrame(
        [
            {
                "geolocation_zip_code_prefix": i,
                "geolocation_lat": round(random.uniform(16.02, 16.08), 6),
                "geolocation_lng": round(random.uniform(108.18, 108.25), 6),
                "geolocation_city": random.choice(dn_districts),
                "geolocation_state": "DN",
            }
            for i in range(5000, 5015)
        ]
    )

    shared_customers = pd.read_csv("src_data/shared/shared_customers.csv")
    customers = shared_customers.sample(
        n=3000,  # số customer của HCM
        replace=False,
    ).copy()

    customers["customer_city"] = "Đà Nẵng"
    customers["customer_state"] = "DN"
    customers["customer_zip_code_prefix"] = np.random.choice(
        geo["geolocation_zip_code_prefix"].values, size=len(customers)
    )

    customers["branch_code"] = "DN"

    sellers = pd.DataFrame(
        [
            {
                "seller_id": f"SELL_DN_{i}",
                "seller_zip_code_prefix": random.choice(
                    geo["geolocation_zip_code_prefix"].values
                ),
                "seller_city": "Đà Nẵng",
                "seller_state": "DN",
            }
            for i in range(5)
        ]
    )

    # =========================
    # 3. PRODUCTS (DIRTY MODE)
    # =========================
    products_dn = df_master.copy()
    mask = np.random.rand(len(products_dn)) < 0.14
    products_dn.loc[mask, "product_category_name"] = None

    # =========================
    # 4. LOYAL CUSTOMERS
    # =========================
    loyal_pool = random.sample(
        list(customers["customer_id"].unique()),
        k=max(1, int(len(customers) * DN_CONF["loyalty_rate"])),
    )

    # =========================
    # 5. TRANSACTIONAL DATA
    # =========================
    orders, items, payments, reviews = [], [], [], []

    for i in range(days):
        curr_date = start_date + timedelta(days=i)
        daily_count = random.randint(*DN_CONF["daily_range"])

        for _ in range(daily_count):
            oid = str(uuid.uuid4())[:16]

            cid = (
                random.choice(loyal_pool)
                if random.random() < 0.3
                else random.choice(customers["customer_id"].values)
            )

            carrier = random.choice(DN_CONF["carriers"])
            buy_ts = curr_date + timedelta(hours=random.randint(8, 20))

            delay_days = (
                random.randint(1, 2) if carrier == "GHTK" else random.randint(4, 9)
            )

            status_rand = random.random()
            if status_rand < DN_CONF["cancel_rate"]:
                status = "canceled"
            elif status_rand < DN_CONF["cancel_rate"] + 0.03:
                status = "returned"
            else:
                status = "delivered"

            orders.append(
                {
                    "order_id": oid,
                    "customer_id": cid,
                    "order_status": status.upper(),
                    "carrier_name": carrier,
                    "order_purchase_timestamp": buy_ts.strftime("%Y/%m/%d %H:%M"),
                    "order_approved_at": (buy_ts + timedelta(hours=1)).strftime(
                        "%Y/%m/%d %H:%M"
                    ),
                    "order_delivered_carrier_date": (
                        buy_ts + timedelta(days=1)
                    ).strftime("%Y/%m/%d %H:%M"),
                    "order_delivered_customer_date": (
                        (buy_ts + timedelta(days=delay_days)).strftime("%Y/%m/%d %H:%M")
                        if status == "delivered"
                        else None
                    ),
                    "order_estimated_delivery_date": (
                        buy_ts + timedelta(days=3)
                    ).strftime("%Y/%m/%d %H:%M"),
                }
            )

            # ===== ITEMS =====
            p_id = random.choice(products_dn["product_id"].values)
            price_num = round(random.uniform(100, 800) * DN_CONF["price_scale"], 2)

            items.append(
                {
                    "order_id": oid,
                    "order_item_id": 1,
                    "product_id": p_id,
                    "seller_id": random.choice(sellers["seller_id"].values),
                    "price": f"{price_num:.2f}".replace(".", ","),
                    "freight_value": "20,00",
                    "shipping_limit_date": (buy_ts + timedelta(days=5)).strftime(
                        "%Y/%m/%d %H:%M"
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
                    "payment_value": f"{price_num + 20:.2f}".replace(".", ","),
                }
            )

            # ===== REVIEWS =====
            # ===== REVIEWS – ĐÀ NẴNG (DN) =====

            # ===== REVIEWS – ĐÀ NẴNG (DN) =====
            create_review = False
            score = None

            # Delivered: ~12% có review
            if status == "delivered":
                if random.random() < 0.12:
                    create_review = True
                    score = random.choices(
                        [1, 2, 3, 4, 5],
                        weights=[0.08, 0.12, 0.20, 0.30, 0.30],
                    )[0]

            # Returned: ~20% có review
            elif status == "returned":
                if random.random() < 0.20:
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
        "products_dataset": products_dn,
        "orders_dataset": pd.DataFrame(orders),
        "order_items_dataset": pd.DataFrame(items),
        "order_payments_dataset": pd.DataFrame(payments),
        "order_reviews_dataset": pd.DataFrame(reviews),
    }

    for name, df in export_map.items():
        df.to_csv(
            os.path.join(output_path, f"DN_{name}.csv"),
            index=False,
            encoding="utf-8-sig",
        )

    print("✅ Đã hoàn tất Đà Nẵng (All-Branch Logic Applied).")


if __name__ == "__main__":
    generate_danang_branch_data_final()
