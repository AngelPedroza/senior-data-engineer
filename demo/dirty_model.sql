{{ config(materialized='table') }}

WITH raw_orders AS (
  SELECT *
  FROM ANALYTICS.RAW.ORDERS
  WHERE 1=1
),

ranked AS (
  SELECT
    ROW_NUMBER() OVER (ORDER BY updated_at) AS order_sk,
    customer_id,
    amount_cents,
    CURRENT_TIMESTAMP AS loaded_at,
    updated_at
  FROM raw_orders
)

SELECT DISTINCT
  r.order_sk,
  r.customer_id,
  r.amount_cents,
  r.loaded_at,
  c.first_name,
  c.last_name,
  c.email,
  c.country,
  c.segment,
  c.created_at
FROM ranked r
JOIN {{ ref('dim_customers') }} c
  ON r.customer_id = c.customer_id;
