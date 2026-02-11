import pandas as pd
from shared_customers import generate_customer_pool

customers = pd.DataFrame(
    generate_customer_pool(
        n_unique_customers=10000,
        n_customer_ids=20000,
    )
)

customers.to_csv("src_data/shared/shared_customers.csv", index=False)
