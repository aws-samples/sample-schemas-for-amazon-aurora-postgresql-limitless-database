\echo '                      '
\echo Insert 1M product:
\echo +----------------+

INSERT INTO ec_sample.products (product_id,product_name,price,description,updated_at)
SELECT nextval('ec_sample.product_id_seq'),
    'book' || i,floor(random() * 100 + 1)::int ,'book'|| ' ' || i ,now()
FROM generate_series(1, 1000000) as i;
\echo '                      '
\echo Insert 10M customers:
\echo +-------------------+

INSERT INTO ec_sample.customers (customer_id ,first_name,last_name ,email ,phone , zipcode ,updated_at )
select nextval('ec_sample.customer_id_seq') , ec_sample.random_text(6) ,ec_sample.random_text(6) ,ec_sample.random_text(10)||'@email.com', ec_sample.random_between(100,900)::int||'-'||ec_sample.random_between(200,900)::int||'-'||ec_sample.random_between(1000,10000)::int, ec_sample.random_between(10000,100000)::int,now()
from generate_series(1, 10000000) ;
