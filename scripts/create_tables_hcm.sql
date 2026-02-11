CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE bronze.olist_geolocation_dataset (

    geolocation_zip_code_prefix INT,

    geolocation_lat DECIMAL(10, 8),

    geolocation_lng DECIMAL(10, 8),

    geolocation_city VARCHAR(100),

    geolocation_state CHAR(2)

);



CREATE TABLE bronze.olist_order_customer_dataset (

    customer_id VARCHAR(50),

    customer_unique_id VARCHAR(50),

    customer_zip_code_prefix INT,

    customer_city VARCHAR(100),

    customer_state CHAR(2)

);

CREATE TABLE bronze.olist_orders_dataset (

    order_id VARCHAR(50),

    customer_id VARCHAR(50),

    order_status VARCHAR(20),

    order_purchase_timestamp timestamp,

    order_approved_at timestamp,

    order_delivered_carrier_date timestamp,

    order_delivered_customer_date timestamp,

    order_estimated_delivery_date timestamp

);



CREATE TABLE bronze.olist_order_payments_dataset (

    order_id VARCHAR(50),

    payment_sequential INT,

    payment_type VARCHAR(20),

    payment_installments INT,

    payment_value DECIMAL(10, 2)

);



CREATE TABLE bronze.olist_order_reviews_dataset (

    review_id VARCHAR(50),

    order_id VARCHAR(50),

    review_score INT,

    review_comment_title TEXT,

    review_comment_message TEXT,

    review_creation_date timestamp,

    review_answer_timestamp timestamp

);

CREATE TABLE bronze.olist_products_dataset (

    product_id VARCHAR(50),

    product_category_name VARCHAR(100),

    product_name_lenght INT,

    product_description_lenght INT,

    product_photos_qty INT,

    product_weight_g INT,

    product_length_cm INT,

    product_height_cm INT,

    product_width_cm INT

);



CREATE TABLE bronze.olist_sellers_dataset (

    seller_id VARCHAR(50),

    seller_zip_code_prefix INT,

    seller_city VARCHAR(100),

    seller_state CHAR(2)

);



CREATE TABLE bronze.olist_order_items_dataset (

    order_id VARCHAR(50),

    order_item_id INT,

    product_id VARCHAR(50),

    seller_id VARCHAR(50),

    shipping_limit_date timestamp,

    price DECIMAL(10, 2),

    freight_value DECIMAL(10, 2)

);


ALTER TABLE bronze.olist_geolocation_dataset 
ALTER COLUMN geolocation_lat TYPE DECIMAL(11, 8),
ALTER COLUMN geolocation_lng TYPE DECIMAL(11, 8);

