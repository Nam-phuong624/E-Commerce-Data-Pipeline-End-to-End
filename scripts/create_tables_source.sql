-- Khởi tạo cấu trúc các lớp dữ liệu
CREATE SCHEMA IF NOT EXISTS bronze; -- Dữ liệu thô, hợp nhất từ các chi nhánh
CREATE SCHEMA IF NOT EXISTS silver; -- Dữ liệu đã làm sạch, chuẩn hóa định dạng
CREATE SCHEMA IF NOT EXISTS gold;   -- Dữ liệu phục vụ báo cáo, phân tích (tổng hợp)


-- 1. Bảng Địa lý
CREATE TABLE bronze.geolocation_dataset (
    geolocation_zip_code_prefix TEXT,
    geolocation_lat TEXT,
    geolocation_lng TEXT,
    geolocation_city TEXT,
    geolocation_state TEXT,
    branch_code TEXT -- Cột định danh nguồn (HCM, HN, DN) [cite: 7]
);

-- 2. Bảng Khách hàng
CREATE TABLE bronze.order_customer_dataset (
    customer_id TEXT,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT,
    branch_code TEXT
);

-- 3. Bảng Đơn hàng (Quan trọng nhất)
CREATE TABLE bronze.orders_dataset (
    order_id TEXT,
    customer_id TEXT,
    order_status TEXT, -- Nhận diện được 'đã giao', 'DELIVERED', 'delivered'
    order_purchase_timestamp TEXT, -- Chứa cả 'DD/MM/YYYY' và 'YYYY/MM/DD'
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT,
    branch_code TEXT
);

-- 4. Bảng Thanh toán
CREATE TABLE bronze.order_payments_dataset (
    order_id TEXT,
    payment_sequential TEXT,
    payment_type TEXT,
    payment_installments TEXT,
    payment_value TEXT, -- Chứa cả dấu phẩy '100,50' và chữ 'VND'
    branch_code TEXT
);

-- 5. Bảng Đánh giá
CREATE TABLE bronze.order_reviews_dataset (
    review_id TEXT,
    order_id TEXT,
    review_score TEXT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT,
    review_answer_timestamp TEXT,
    branch_code TEXT
);

-- 6. Bảng Sản phẩm
CREATE TABLE bronze.products_dataset (
    product_id TEXT,
    product_category_name TEXT, -- Nhận diện 'vòng bi' và 'bearings'
    product_name_lenght TEXT,
    product_description_lenght TEXT,
    product_photos_qty TEXT,
    product_weight_g TEXT,
    product_length_cm TEXT,
    product_height_cm TEXT,
    product_width_cm TEXT,
    branch_code TEXT
);

-- 7. Bảng Người bán
CREATE TABLE bronze.sellers_dataset (
    seller_id TEXT,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT,
    branch_code TEXT
);

-- 8. Bảng Chi tiết mặt hàng
CREATE TABLE bronze.order_items_dataset (
    order_id TEXT,
    order_item_id TEXT,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TEXT,
    price TEXT,
    freight_value TEXT,
    branch_code TEXT
);



-- Xóa toàn bộ 8 bảng nếu chúng tồn tại
DROP TABLE IF EXISTS bronze.merged_geolocation_dataset;
DROP TABLE IF EXISTS bronze.merged_order_customer_dataset;
DROP TABLE IF EXISTS bronze.merged_orders_dataset;
DROP TABLE IF EXISTS bronze.merged_order_payments_dataset;
DROP TABLE IF EXISTS bronze.merged_order_reviews_dataset;
DROP TABLE IF EXISTS bronze.merged_products_dataset;
DROP TABLE IF EXISTS bronze.merged_sellers_dataset;
DROP TABLE IF EXISTS bronze.merged_order_items_dataset;