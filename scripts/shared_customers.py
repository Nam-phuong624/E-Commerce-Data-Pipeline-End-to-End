import random
from faker import Faker

fake = Faker("vi_VN")


def generate_customer_pool(
    n_unique_customers=10000,
    n_customer_ids=20000,
):
    unique_ids = [fake.uuid4()[:16] for _ in range(n_unique_customers)]

    customers = []
    for i in range(n_customer_ids):
        customers.append(
            {
                "customer_id": f"CUST_{i}",
                "customer_unique_id": random.choice(unique_ids),
            }
        )

    return customers
