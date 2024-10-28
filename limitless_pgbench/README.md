# limitless_pgbench
#### A wrapper for pgbench designed to run a version of the pgbench built-in scripts for ```Amazon Aurora Limitless Database```

## Purpose
Running pgbench on an ```Amazon Aurora Limitless Database``` requires some considertation due to the distributed nature of the system. Standard pgbench does not understand how to:

1. Shard the pgbench_* tables
2. Use an appropriate shard key
3. Distribute connections across all routers
4. Take advantage of the multiple shards to initialize a pgbench dataset

```limitless_pgbench``` is a wrapper for the standard ```pgbench``` that deals with the above by points. 

## Prerequisites:

1. Perl
2. PostgreSQL client of version 16 or higher in the PATH.
    Note: PostgreSQL client Version 16 or higher allows for [connection load balancing](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-LOAD-BALANCE-HOSTS). This is beneficial for Limitless to distribute connections to multiple routers.
3. Familialarity with pgbench [0]


## Usage Notes:

Below are the differences between standard ```pgbench``` and ```limitless_pgbench```

1. Unlike standard pgbench, the ```-d``` should be passed to specify the dbname.
2. ```--limitless-workload``` is an option to execute a specific built-in workload. The valid options are "tpcp-like", "simple-update" and "select-only". This will run the built-in workloads allowed by a standard pgbench [2], but with modifications for Limitless. The workloads ad associated scripts are:
    ##### tpcb-like:
    ```
    \set aid random(1, 100000 * :scale)
    \set bid (:aid - 1) / 100000 + 1
    \set tid random(1, 10 * :scale)
    \set delta random(-5000, 5000)
    BEGIN;
        UPDATE pgbench_accounts SET abalance = abalance + :delta WHERE aid = :aid AND bid = :bid;
        SELECT abalance FROM pgbench_accounts WHERE aid = :aid AND bid = :bid;
        UPDATE pgbench_tellers SET tbalance = tbalance + :delta WHERE tid = :tid AND bid = :bid;
        UPDATE pgbench_branches SET bbalance = bbalance + :delta WHERE bid = :bid;
        INSERT INTO pgbench_history (tid, bid, aid, delta, mtime) VALUES (:tid, :bid, :aid, :delta, NULL);
    END; 
    ```

    ##### Simple Update:
    ```
    \set aid random(1, 100000 * :scale)
    \set bid random(1, 1 * :scale)
    \set tid random(1, 10 * :scale)
    \set delta random(-5000, 5000)
    BEGIN;
        UPDATE pgbench_accounts SET abalance = abalance + :delta WHERE aid = :aid AND bid = :bid;;
        SELECT abalance FROM pgbench_accounts WHERE aid = :aid AND bid = :bid;;
        INSERT INTO pgbench_history (tid, bid, aid, delta, mtime) VALUES (:tid, :bid, :aid, :delta, CURRENT_TIMESTAMP);
    END;
    ```

    ##### Select Only:
    ```
    \set aid random(1, 100000 * :scale)
    \set bid (:aid - 1) / 100000 + 1
    SELECT abalance FROM pgbench_accounts WHERE aid = :aid AND bid = :bid;   
    ```
3. ```--pipelined``` is an option to execute a specific built-in workload in pipelined mode [1].
4. When a pgbench benchmark script is executed, the hostname in the connection is checked for being a Limitless Cluster endpoint. If so, the router endpoints are then discovered and used to connect to pgbench. This is done to ensure that the benchmark workload is evenly distributed across all routers.
5. During the ```initialize``` step, the command line can accept a ```-c``` flag to run the ```initialize``` step with multiple clients. This speeds up this step and takes advantage of the distributed nature of the Limitless Cluster and speed up this step.
6. The database password must be set in the ```PGPASSWORD``` environment variable.

## Example
The following example demostrates how to run a pgbench on a ```Amazon Aurora Limitless Database```. In this example, the Limitless endpoint is ```demo-1.limitless-abcdefghijk.us-east-1.rds.amazonaws.com```, the user is ```postgres``` and the database is ```postgres_limitless```. 50 clients and a scale of 250 is used.

### Running the Initialize step
```
export PGPASSWORD=password; ./limitless_pgbench -h my-limitless-cluster.limitless-xxxxxxx.us-east-1.rds.amazonaws.com -d postgres_limitless -U postgres -i -s250 -c50
pgbench (PostgreSQL) 16.2
psql (PostgreSQL) 16.2
 
**Limitless Cluster detected. Discovering router endpoints:
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
DROP TABLE
SET
SET
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
INSERT 0 250
INSERT 0 2500
SET
CREATE TABLE
INSERT 0 250
CREATE PROCEDURE
pgbench (16.2, server 16.4)
pgbench: pghost: cluster-xxxx--node-49831-instance-84200.xxxx.us-east-1.rds.amazonaws.com pgport: 5432 nclients: 50 nxacts: 1 dbName: postgres_limitless
transaction type: -
scaling factor: 1
query mode: simple
number of clients: 50
number of threads: 1
maximum number of tries: 1
number of transactions per client: 1
number of transactions actually processed: 50/50
number of failed transactions: 0 (0.000%)
latency average = 39762.247 ms
initial connection time = 15752.807 ms
tps = 1.257474 (without initial connection time)
ALTER TABLE
ALTER TABLE
ALTER TABLE
VACUUM
```
### Running the Benchmark
Notice that there is a step to discover the router endpoints of a Limitless endpoint.
```
export PGPASSWORD=password;./limitless_pgbench -h my-limitless-cluster.limitless-xxxxx.us-east-1.rds.amazonaws.com -d postgres_limitless -U postgres -T120 -c50 --limitless-workload=simple-update
pgbench (PostgreSQL) 16.2
psql (PostgreSQL) 16.2
 
**Limitless Cluster detected. Discovering router endpoints:
pgbench (16.2, server 16.4)
pgbench: pghost: cluster-xxxxx--node-66346-instance-16418.xxxx.us-east-1.rds.amazonaws.com pgport: 5432 nclients: 50 duration: 120 dbName: postgres_limitless
starting vacuum...end.
transaction type: -
scaling factor: 1
query mode: simple
number of clients: 50
number of threads: 1
maximum number of tries: 1
duration: 120 s
number of transactions actually processed: 262156
number of failed transactions: 0 (0.000%)
latency average = 22.718 ms
initial connection time = 963.662 ms
tps = 2200.920752 (without initial connection time)
```
## References
[0] https://www.postgresql.org/docs/current/pgbench.html

[1] https://www.postgresql.org/docs/current/pgbench.html#PGBENCH-METACOMMAND-PIPELINE

[2] https://www.postgresql.org/docs/current/pgbench.html#PGBENCH-OPTION-BUILTIN
