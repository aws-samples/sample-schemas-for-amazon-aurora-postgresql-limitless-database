\echo Create E-Commerce sample schema:
\echo +------------------------------------------+
\echo '                      '
\echo Create ec_sample SCHEMA: 
\echo +----------------------+
Create SCHEMA ec_sample ;
\echo '                      '
\echo Create standard tables:
\echo +----------------------+
\echo '                      '
\echo Create customers table:
\echo +----------------------+

CREATE TABLE ec_sample.customers ( 
    customer_id BIGINT,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    phone VARCHAR NOT NULL,
    zipcode INT,
    updated_at DATE,
    PRIMARY KEY (customer_id)
);
\echo '                      '
\echo Create orders table:
\echo +-------------------+

CREATE TABLE ec_sample.orders (
    customer_id BIGINT,
    order_id BIGINT,
    order_date TIMESTAMP,
    order_status VARCHAR,
    updated_at TIMESTAMP,
    PRIMARY KEY (customer_id, order_id)
);
\echo '                      '
\echo Create orderdetails table:
\echo +-------------------------+

CREATE TABLE ec_sample.orderdetails (
    customer_id BIGINT,
    order_id BIGINT,
    orderline_id INT,
    product_id BIGINT,
    quantity INT,
    PRIMARY KEY (customer_id, order_id ,orderline_id)
);
\echo '                      '
\echo Create products table:
\echo +--------------------+

CREATE TABLE ec_sample.products (
    product_id BIGINT,
    product_name VARCHAR,
    price FLOAT,
    description VARCHAR,
    updated_at DATE,
    PRIMARY KEY (product_id)
);
