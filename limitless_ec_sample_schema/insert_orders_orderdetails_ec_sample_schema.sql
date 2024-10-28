-- change CID MAX number based on the number of cusotemrs , currently it set to 10M customers.
-- change pid (pid1 and pid2) min and max based on the number of products , currently it set to 1M product.
\set cid random(1, 10000000)
\set pid1 random(1, 500000)
\set pid2 random(500001, 1000000)
\set q1 random(1, 5)
\set q2 random(1, 5)
select nextval('ec_sample.order_id_seq') as order_id \gset
INSERT INTO ec_sample.orders (customer_id,order_id,order_date,order_status,updated_at) VALUES  (:cid,:order_id,now(),'ordered',now() ) ;
INSERT INTO ec_sample.orderdetails (customer_id,order_id,orderline_id,product_id,quantity) VALUES  (:cid,:order_id ,1,:pid1 ,:q1 ) ;
INSERT INTO ec_sample.orderdetails (customer_id,order_id,orderline_id,product_id,quantity) VALUES  (:cid,:order_id ,2,:pid2 ,:q2 ) ;
