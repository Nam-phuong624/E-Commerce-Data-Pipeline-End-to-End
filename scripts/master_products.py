import pandas as pd
import random

# Tạo danh mục chuẩn
product_categories = ["Bearings", "Lubricants", "Seals", "Tools"]

master_products = []
for i in range(100):
    master_products.append(
        {
            "product_id": f"PROD_{i}",
            "product_category_name": random.choice(product_categories),
            "product_weight_g": random.randint(100, 5000),
            "product_length_cm": random.randint(10, 50),
            "product_height_cm": random.randint(5, 20),
            "product_width_cm": random.randint(10, 50),
        }
    )

df_master = pd.DataFrame(master_products)
# Lưu lại làm "Sự thật" để các chi nhánh dùng chung
df_master.to_csv("/home/namphuong/project_cv/master_products_reference.csv", index=False)
