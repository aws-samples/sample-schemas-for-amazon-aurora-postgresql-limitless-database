\echo Create the SEQUENCEs:
\echo +-------------------+

CREATE SEQUENCE ec_sample.customer_id_seq  ;
CREATE SEQUENCE ec_sample.product_id_seq  ;
CREATE SEQUENCE ec_sample.order_id_seq  ;

\echo '                      '
\echo Create the FUNCTIONs:
\echo +-------------------+

CREATE OR REPLACE FUNCTION ec_sample.random_text(length INTEGER)
        RETURNS TEXT
        LANGUAGE PLPGSQL
        AS $$
        DECLARE
            possible_chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
            output TEXT := '';
            i INT4;
            pos INT4;
        BEGIN
     
            FOR i IN 1..length LOOP
                pos := ec_sample.random_range(1, length(possible_chars));
                output := output || substr(possible_chars, pos, 1);
            END LOOP;
     
            RETURN output;
        END;
        $$;

CREATE OR REPLACE FUNCTION ec_sample.random_range(INTEGER, INTEGER)
        RETURNS INTEGER
        LANGUAGE SQL
        AS $$
            SELECT ($1 + FLOOR(($2 - $1 + 1) * random() ))::INTEGER;
        $$; 
         
CREATE OR REPLACE FUNCTION ec_sample.random_between(low INT ,high INT) 
   RETURNS INT AS
$$
BEGIN
   RETURN floor(random()* (high-low + 1) + low);
END;
$$ language 'plpgsql' STRICT;
