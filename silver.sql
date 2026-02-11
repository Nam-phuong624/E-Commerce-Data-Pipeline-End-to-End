
drop table if exists silver.orders_dataset;
CREATE TABLE silver.orders_dataset AS 
(
    WITH cleaned_data AS (
    SELECT 
        order_id, customer_id, branch_code, carrier_name, 
        -- Chuẩn hóa trạng thái đơn hàng
        INITCAP(LOWER(CASE WHEN order_status LIKE 'đã giao' THEN 'delivered' ELSE order_status END)) AS order_status,
        
        -- Chuyển đổi các cột TEXT sang TIMESTAMP chuẩn
        CASE 
            WHEN POSITION('/' IN order_purchase_timestamp) = 5 THEN TO_TIMESTAMP(order_purchase_timestamp, 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN order_purchase_timestamp) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(order_purchase_timestamp, 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(order_purchase_timestamp AS TIMESTAMP)
        END AS order_purchase_timestamp,

        CASE 
            WHEN POSITION('/' IN order_delivered_customer_date) = 5 THEN TO_TIMESTAMP(nullif(order_delivered_customer_date, 'NaT'), 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN order_delivered_customer_date) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(nullif(order_delivered_customer_date, 'NaT'), 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(nullif(order_delivered_customer_date, 'NaT') AS TIMESTAMP)
        END AS order_delivered_customer_date,

        CASE 
            WHEN POSITION('/' IN order_approved_at) = 5 THEN TO_TIMESTAMP(order_approved_at, 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN order_approved_at) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(order_approved_at, 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(order_approved_at AS TIMESTAMP)
        END AS order_approved_at,

        CASE 
            WHEN POSITION('/' IN order_delivered_carrier_date) = 5 THEN TO_TIMESTAMP(order_delivered_carrier_date, 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN order_delivered_carrier_date) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(order_delivered_carrier_date, 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(order_delivered_carrier_date AS TIMESTAMP)
        END AS order_delivered_carrier_date,

        CASE 
            WHEN POSITION('/' IN order_estimated_delivery_date) = 5 THEN TO_TIMESTAMP(order_estimated_delivery_date, 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN order_estimated_delivery_date) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(order_estimated_delivery_date, 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(order_estimated_delivery_date AS TIMESTAMP)
        END AS order_estimated_delivery_date
    FROM bronze.orders_dataset
)
SELECT *,
    -- Trích xuất khóa Ngày và Giờ (Dùng để nối với Dim_Date và Dim_Time)
    order_purchase_timestamp::DATE AS order_purchase_date,
    EXTRACT(HOUR FROM order_purchase_timestamp)::INT AS order_purchase_hour,
    NOW() AS created_at
    FROM cleaned_data
    WHERE order_approved_at >= order_purchase_timestamp
    AND order_delivered_carrier_date >= order_approved_at
    AND (
        order_delivered_customer_date IS NULL
        OR order_delivered_customer_date >= order_delivered_carrier_date
      )
    -- limit 100
);



drop table if exists silver.order_items_dataset;
create table silver.order_items_dataset as 
(
    with cleaned_data as (
    select order_id, 
        order_item_id, 
        product_id, 
        seller_id,
        regexp_replace(replace(price, ',', '.'), '[^0-9.]', '', 'g') as price, 
        regexp_replace(replace(freight_value, ',', '.'), '[^0-9.]', '', 'g') as freight_value,
        branch_code, 
        CASE 
            WHEN POSITION('/' IN shipping_limit_date) = 5 THEN TO_TIMESTAMP(shipping_limit_date, 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN shipping_limit_date) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(shipping_limit_date, 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(shipping_limit_date AS TIMESTAMP)
        END AS shipping_limit_date
        -- row_number() over(partition by branch_code) as rn
    from bronze.order_items_dataset
    )
    select *,
        shipping_limit_date::DATE AS shipping_limit_day,
        now() created_at
    from cleaned_data day
    -- where rn = 1
);


drop table if exists silver.products_dataset;
create table silver.products_dataset as 
(
    with cte as (
    select product_id, 
    initcap(coalesce(case when lower(product_category_name) = 'vòng bi' then 'bearings'
        when lower(product_category_name) = 'mỡ bôi trơn' then 'lubricants'
        when lower(product_category_name) = 'phớt chặn' then 'seals'
        when lower(product_category_name) = 'dụng cụ' then 'tools'
        else product_category_name
    end, 'Unknown')) as product_category_name,
    product_weight_g::numeric, product_length_cm::numeric, product_height_cm::numeric, 
    product_width_cm::numeric, branch_code
    from bronze.products_dataset
)
, table_ref as -- tạo bảng tham chiếu các chỉ số của mỗi category
    (
        select distinct product_category_name, product_weight_g, product_length_cm,
                product_height_cm, product_width_cm
        from cte
        where product_category_name <> 'Unknown'
    )
, table_final as 
(
    select cte.product_id,
        case when cte.product_category_name like 'Unknown' 
                then tr.product_category_name
            else cte.product_category_name
        end as product_category_name,
        cte.product_weight_g,
        cte.product_length_cm,
        cte.product_height_cm,
        cte.product_width_cm,
        cte.branch_code,
        row_number() 
        over(partition by product_id
            order by (case when cte.branch_code like 'HCM' then 1 
                        when cte.branch_code like 'HN' then 2 else 3 end) asc
        ) as rn
    from cte 
    left join table_ref tr
    on tr.product_weight_g = cte.product_weight_g
    and tr.product_length_cm = cte.product_length_cm
    and tr.product_height_cm = cte.product_height_cm
    and tr.product_width_cm = cte.product_width_cm
)
select product_id, product_category_name, product_weight_g, product_length_cm,
    product_height_cm, product_width_cm, branch_code, 
    now() created_at
from table_final
where rn = 1
order by 2
);


drop table if exists silver.order_customer_dataset;
create table silver.order_customer_dataset as 
(
    select customer_id, customer_unique_id,customer_zip_code_prefix,
    case when customer_city like 'Thành phố%' then 'TP. Hồ Chí Minh'
        else customer_city
    end as customer_city,
    case when customer_state like 'HCMC' then 'TP. Hồ Chí Minh'
        when customer_state like 'HN' then 'Hà Nội'
        when customer_state like 'DN' then 'Đà Nẵng'
    end as customer_state,
    branch_code,
    now() created_at 
    from bronze.order_customer_dataset
);


drop table if exists silver.order_payments_dataset;
create table silver.order_payments_dataset as 
(
    select order_id, payment_sequential::int,
    initcap(replace(payment_type, '_', ' ')) as payment_type,
    payment_installments::int,
    round(regexp_replace(replace(payment_value, ',', '.'), '[^0-9.]', '', 'g')::numeric, 2) AS payment_value,
    branch_code, now() created_at
    from bronze.order_payments_dataset
);



drop table if exists silver.order_reviews_dataset;
create table silver.order_reviews_dataset as 
(
    with cte as 
(
    select review_id, order_id, review_score::int, 
        CASE 
            WHEN POSITION('/' IN review_creation_date) = 5 THEN TO_TIMESTAMP(nullif(review_creation_date, 'NaT'), 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN review_creation_date) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(nullif(review_creation_date, 'NaT'), 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(nullif(review_creation_date, 'NaT') AS TIMESTAMP)
        END AS review_creation_date,
        CASE 
            WHEN POSITION('/' IN review_answer_timestamp) = 5 THEN TO_TIMESTAMP(nullif(review_answer_timestamp, 'NaT'), 'YYYY/MM/DD HH24:MI:SS')
            WHEN POSITION('/' IN review_answer_timestamp) BETWEEN 1 AND 4 THEN TO_TIMESTAMP(nullif(review_answer_timestamp, 'NaT'), 'DD/MM/YYYY HH24:MI:SS')  
            ELSE CAST(nullif(review_answer_timestamp, 'NaT') AS TIMESTAMP)
        END AS review_answer_timestamp,
        branch_code
    from bronze.order_reviews_dataset
    )
    select *,
        review_creation_date::DATE AS review_creation_day,
        EXTRACT(HOUR FROM review_creation_date) AS review_creation_hour,
        
        review_answer_timestamp::DATE AS review_answer_day,
        EXTRACT(HOUR FROM review_answer_timestamp) AS review_answer_hour,

        -- Tính thời gian phản hồi
        FLOOR(EXTRACT(EPOCH FROM (review_answer_timestamp - review_creation_date)) / 3600) AS response_hours,
        now() created_at
    from cte 
    -- where review_answer_timestamp is null
);


drop table if exists silver.sellers_dataset;
create table silver.sellers_dataset as 
(
    select seller_id, seller_zip_code_prefix::int,
    case when seller_city like 'Thành%' then 'TP. Hồ Chí Minh'
        else seller_city
    end as seller_city,
    case when seller_state like 'HCMC' then 'TP. Hồ Chí Minh'
        when seller_state like 'HN' then 'Hà Nội'
        when seller_state like 'DN' then 'Đà Nẵng'
    end as seller_state, branch_code,
    now() created_at
    from bronze.sellers_dataset
);



drop table if exists silver.geolocation_dataset;
create table silver.geolocation_dataset as 
(
    select geolocation_zip_code_prefix, geolocation_lat, geolocation_lng,
    geolocation_city,
     case when geolocation_state like 'HCMC' then 'TP. Hồ Chí Minh'
        when geolocation_state like 'HN' then 'Hà Nội'
        when geolocation_state like 'DN' then 'Đà Nẵng'
    end as geolocation_state, branch_code,
    now() created_at 
    from bronze.geolocation_dataset
);



drop table if exists silver.date;
create table silver.date as 
(
    WITH date_range AS (
    SELECT 
        MIN(order_purchase_timestamp)::date AS start_date,
        MAX(order_delivered_customer_date)::date AS end_date
    FROM silver.orders_dataset
    )
    , cte as
    (
        SELECT 
        generate_series(start_date, end_date, '1 day'::interval)::date AS "date"
        FROM date_range
    )
    select *,
        extract(year from "date") as "year",
        extract(quarter from "date") as "quarter",
        extract(month from "date") as "month",
        case when extract(dow from "date") = 0 then 'Sun'
            when extract(dow from "date") = 1 then 'Mon'
            when extract(dow from "date") = 2 then 'Tue'
            when extract(dow from "date") = 3 then 'Wed'
            when extract(dow from "date") = 4 then 'Thur'
            when extract(dow from "date") = 5 then 'Fri'
            when extract(dow from "date") = 6 then 'Sat'
        end as "day_of_week",
        now() created_at 
    from cte 
);


select *
from bronze.order_reviews_dataset
where review_answer_timestamp like 'NaT'
or review_creation_date like 'NaT'
