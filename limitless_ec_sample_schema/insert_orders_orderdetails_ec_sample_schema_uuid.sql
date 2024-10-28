-- change CID MAX number based on the number of cusotemrs , currently it set to 10M customers.
-- change pid (pid1 and pid2) min and max based on the number of products , currently it set to 1M product.
\set cid random(1, 10000000)
\set pid1 random(1, 500000)
\set pid2 random(500001, 1000000)
\set q1 random(1, 5)
\set q2 random(1, 5)
select uuid_generate_v4() as order_id_uuid \gset
INSERT INTO ec_sample.orders (customer_id,order_id,order_date,order_status,updated_at) VALUES  (:cid,':order_id_uuid',now(),'ordered',now() ) ;
INSERT INTO ec_sample.orderdetails (customer_id,order_id,orderline_id,product_id,quantity) VALUES  (:cid,':order_id_uuid' ,1,:pid1 ,:q1 ) ;
INSERT INTO ec_sample.orderdetails (customer_id,order_id,orderline_id,product_id,quantity) VALUES  (:cid,':order_id_uuid' ,2,:pid2 ,:q2 ) ;
