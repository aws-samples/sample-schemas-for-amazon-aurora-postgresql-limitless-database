\echo '                      '
\echo Converting the standard tables to limitless tables:
\echo +---------------------------------------------+
\echo '                      '
\echo Convert customers table to sharded table using customer_id shard key :
\echo +---------------------------------------------------------------------+
\echo '                      '
CALL rds_aurora.limitless_alter_table_type_sharded('ec_sample.customers', ARRAY['customer_id']);
\echo '                      '
\echo Convert orders and  orderdetails tables to collocated tables:
\echo +---------------------------------------------------------+
\echo '                      '
CALL rds_aurora.limitless_alter_table_type_sharded('ec_sample.orders', ARRAY['customer_id'], 'ec_sample.customers');
CALL rds_aurora.limitless_alter_table_type_sharded('ec_sample.orderdetails', ARRAY['customer_id'], 'ec_sample.customers');
\echo '                      '
\echo Convert products table to a reference table:
\echo +------------------------------------------+
\echo '                      '
CALL rds_aurora.limitless_alter_table_type_reference('ec_sample.products');
