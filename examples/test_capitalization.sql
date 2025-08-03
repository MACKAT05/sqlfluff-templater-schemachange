-- Tests capitalization rules
-- CP01: keywords
-- CP02: identifiers
-- CP03: functions
USE database {{ database_name }};
use schema {{ schema_name }};

create table Orders (
    order_id integer primary key,
    customer_name varchar(255) not null,
    order_date timestamp default current_timestamp(),
    total_amount decimal(10,2)
);

-- Mixed case issues
Select 
    Order_Id,
    Customer_Name,
    COUNT(*) as total_orders,
    SUM(total_amount) AS revenue
From Orders 
where order_date >= CURRENT_DATE() - 30
group by Order_Id, Customer_Name
having COUNT(*) > 1
order by revenue DESC;