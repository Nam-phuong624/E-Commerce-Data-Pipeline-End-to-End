drop table if exists gold.fact_sales_performance;
create table gold.fact_sales_performance as 
(
  select od.order_id, 
      od.customer_id, 
      od.order_purchase_timestamp,
      od.order_status, 
      opd.payment_type, 
      oid.price, 
      oid.product_id,
      od.branch_code,
      now() created_at 
  from silver.orders_dataset od
  left join silver.order_items_dataset oid 
  on od.order_id = oid.order_id
  left join silver.order_payments_dataset opd
  on od.order_id = opd.order_id
);


drop table if exists gold.fact_operations_delivery;
create table gold.fact_operations_delivery as 
(
  select od.order_id, 
      od.carrier_name,
      od.order_status,
      oid.shipping_limit_date,
      od.order_delivered_customer_date::date - od.order_approved_at::date as days_to_delivery,
      od.order_estimated_delivery_date::date  - od.order_delivered_customer_date::date as days_late, -- ngày âm là sớm hơn/ dương là trễ hơn dự kiến
      od.order_delivered_carrier_date::date - od.order_approved_at::date as processing_time,
      (case when (od.order_estimated_delivery_date::date  - od.order_delivered_customer_date::date) < 0 then 1 else 0 end) as is_late,
      now() created_at
  from silver.orders_dataset od 
  left join silver.order_items_dataset oid 
  on od.order_id = oid.order_id
);



drop table if exists gold.fact_customer_satisfaction;
create table gold.fact_customer_satisfaction as 
(
  select rd.review_id,
      od.order_id,
      rd.review_score,
      rd.response_hours,
      pd.product_category_name,
      od.order_status,
      oid.product_id,
      od.order_delivered_customer_date,
      now() created_at
  from silver.orders_dataset od
  left join silver.order_items_dataset oid
  on od.order_id = oid.order_id
  left join silver.products_dataset pd
  on oid.product_id = pd.product_id
  left join silver.order_reviews_dataset rd 
  on od.order_id = rd.order_id
);



drop table if exists gold.dim_customers_segmented;
create table gold.dim_customers_segmented as 
(
    with segment_rn as
(
    select cd.customer_unique_id,
        row_number() over(partition by cd.customer_unique_id order by od.order_purchase_timestamp desc) as recency,
        count(od.order_id) over(partition by cd.customer_unique_id) as frequency,
        sum(oid.price::numeric) over(partition by cd.customer_unique_id) as monetary
    from silver.orders_dataset od 
    left join silver.order_customer_dataset cd
    on od.customer_id = cd.customer_id
    left join silver.order_items_dataset oid 
    on od.order_id = oid.order_id
)
  , segment_score as
  (
      select * , 
          ntile(4) over(order by recency asc) as rn_score, -- 1: mua gần nhất, 4 xa nhất
          ntile(4) over(order by frequency desc) as fn_score, -- 1: mua nhiều nhất, 4 ít nhất
          ntile(4) over(order by monetary desc) as mn_score, -- 1: chi nhiều tiền nhất, 4 ít nhất
          concat(ntile(4) over(order by recency asc), ntile(4) over(order by frequency desc), ntile(4) over(order by monetary desc)) as merge_score
      from segment_rn 
  )
      select customer_unique_id,
          frequency as total_order,
          monetary as total_spend,
        case when merge_score ~ '^111$' then 'VIP' 
            when merge_score ~ '^[1-2][1-2][1-4]$' then 'Loyal' 
            when merge_score ~ '^[1-2][3-4]1$' then 'Big Spenders' 
            when merge_score ~ '^[1-2][3-4][2-4]$' then 'Potential' 
            when merge_score ~ '^14[1-4]$' then 'New customers' 
            when merge_score ~ '^[3-4][1-2][1-2]$' then 'Risk' 
            when merge_score ~ '^[3-4][3-4][3-4]$' then 'Lost' 
            else 'Khác'
        end as segment_customer
    from segment_score
    where recency = 1
)

-- select count(distinct ocd.customer_unique_id)  
-- from silver.orders_dataset od
-- left join silver.order_customer_dataset ocd
-- on od.customer_id = ocd.customer_id 
