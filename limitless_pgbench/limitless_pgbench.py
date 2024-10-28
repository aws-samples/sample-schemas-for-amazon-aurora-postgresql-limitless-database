#!/usr/bin/python3

"""
A wrapper to run pgbench benchmarks for "Amazon Aurora Limitless Database"

Running pgbench on an "Amazon Aurora Limitless Database"
requires some considertation to the distributed nature of the
system.Standard pgbench does not understand how to:

1 / Shard the pgbench_ tables
2 / Use an appropriate shard key
3 / Aware of the router endpoints that a Limitless endpoint points to.

Running pgbench with the limitless_pgbench takes care of these considerations.Nothing more than this perl script and a Postgres Client is required. See README.md for more details.

"""

import os
import re
import subprocess
import argparse
import sys

# Helper function to trim whitespace
def trim(string):
    return re.sub(r'^\s+|\s+$', '', string)

# Function to check prerequisites
def prereq_check():
    try:
        subprocess.run(["pgbench", "-V"], check=True)
        subprocess.run(["psql", "-V"], check=True)
    except subprocess.CalledProcessError:
        raise SystemExit("pgbench or psql is not in the PATH")

    if 'PGPASSWORD' not in os.environ:
        raise SystemExit("PGPASSWORD must be set as an environment variable")
"""
GetLimitlessEndpoints()

Establishes a connection to the database using the hostname provided
and determine if it's a Limitless cluster. If so, figure out the number
of routers and continue converting the hostname to an IP address until
we have up to the # of routers worth of IP addresses. We spend a max
of 2 minutes searching for IP addresses.

The list of IP addresses discovered are then passed as a load balanced
set of hosts to pgbench to ensure we load balance the workload. This
is only important for the benchmark workload, so we delay doing this
work only then.

"""

# Function to get limitless endpoints
def get_limitless_endpoints(connstring_check, host):
    check_limitless_sql = (
        "SELECT COUNT(*) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n "
        "ON n.oid = p.pronamespace "
        "WHERE n.nspname = 'rds_aurora' AND proname = 'limitless_stat_activity'"
    )
    ll_routers_sql = "SELECT STRING_AGG(dns_host, ',') dns_string FROM aurora_limitless_router_endpoints()"

    endpoint = os.getenv('PGHOST', '') if host == "" else host

    check_if_limitless = trim(
        subprocess.getoutput(f"psql {connstring_check} -Aqt -c \"{check_limitless_sql}\"")
    )
    if int(check_if_limitless) == 1:
        print("\n**Limitless Cluster detected. Discovering router endpoints:")
        ll_routers_string = trim(subprocess.getoutput(f"psql {connstring_check} -t -c \"{ll_routers_sql}\""))
        if not args.limitless_workload and not args.initialize:
            raise SystemExit("ERROR: The --limitless-workload argument must be provided for a limitless cluster unless --initialize is used.")
        return ["-h", ll_routers_string, "-U", args.username, "-d", args.dbname]
    else:
        return connstring_check

"""
ParseArguments()

Parse the command line arguments.

The result of this function is setting 2 globals.

"connstring_check" which is the connection string to be used
by pgbench or psql.

"pgbench_flags" which are the flags to be passed to the pgbench
command.
"""

# Function to parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--help", action="help", help="Show this help message and exit")

    # Connection related options
    parser.add_argument("-h", "--host", type=str, default="")
    parser.add_argument("-p", "--port", type=int, default=None)
    parser.add_argument("-d", "--dbname", type=str, default="")
    parser.add_argument("-U", "--username", type=str, default="")

    # pgbench related options
    parser.add_argument("-s", "--scale", type=int, default=0)
    parser.add_argument("-i", "--initialize", action="store_true")
    parser.add_argument("-c", "--clients", type=int, default=0)
    parser.add_argument("--limitless-workload", type=str, default="")
    parser.add_argument("-f", "--file", type=str, default="")
    parser.add_argument("-b", "--builtin", type=str, default="")
    parser.add_argument("--pipelined", action="store_true")

    args, unknown_args = parser.parse_known_args()

    if args.dbname == "" and "PGDATABASE" not in os.environ:
        os.environ['PGDATABASE'] = os.getlogin()
    elif args.dbname:
        os.environ['PGDATABASE'] = args.dbname

    connstring_check = ""
    if args.host:
        connstring_check += f"-h {args.host} "
    if args.port:
        connstring_check += f"-p {args.port} "
    if args.username:
        connstring_check += f"-U {args.username} "

    pgbench_flags = f"-c {args.clients} " + " ".join(unknown_args)

    if args.file:
        pgbench_flags += f" -f {args.file}"
    if args.builtin:
        pgbench_flags += f" -b {args.builtin}"

    return args, connstring_check.strip(), pgbench_flags.strip().split()

if __name__ == "__main__":
    # If no options are provided
    if len(sys.argv) == 1:
        print("No arguments provided. Use --help for more information.")
        exit(1)

    # Parse arguments first
    args, connstring_check, pgbench_flags = parse_arguments()

    # Run the prerequisite check if not --help
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help']:
        parser = argparse.ArgumentParser()
        parser.print_help()
        exit(0)

    # Run the prerequisite check
    prereq_check()
    
    connstring_final = get_limitless_endpoints(connstring_check, args.host) #if args.host == '' else connstring_check.split()
    #connstring_final = connstring_check.split()
    #print(f"connstring_final: {connstring_final}")

    if args.initialize:
        # Initialize SQL script
        init_sql = r"""
            SELECT 10 AS tellers \gset
            SELECT 1 AS branches \gset

            DROP TABLE IF EXISTS pgbench_accounts CASCADE;
            DROP TABLE IF EXISTS pgbench_branches CASCADE;
            DROP TABLE IF EXISTS pgbench_history CASCADE;
            DROP TABLE IF EXISTS pgbench_tellers CASCADE;
            DROP TABLE IF EXISTS pgbench_init_queue CASCADE;

            SET rds_aurora.limitless_create_table_mode='sharded';
            SET rds_aurora.limitless_create_table_shard_key='{"bid"}';

            CREATE TABLE pgbench_accounts (
                aid bigint NOT NULL,
                bid integer,
                abalance integer,
                filler character(84)
            );

            CREATE TABLE pgbench_branches (
                bid integer NOT NULL,
                bbalance integer,
                filler character(88)
            );

            CREATE TABLE pgbench_history (
                tid integer,
                bid integer,
                aid bigint,
                delta integer,
                mtime timestamp without time zone,
                filler character(22)
            );

            CREATE TABLE pgbench_tellers (
                tid integer NOT NULL,
                bid integer,
                tbalance integer,
                filler character(84)
            );

            INSERT INTO pgbench_branches(bid, bbalance)
            SELECT bid, 0
            FROM generate_series(1, :branches * :scale) as bid;

            INSERT INTO pgbench_tellers(tid, bid, tbalance)
            SELECT tid, (tid - 1) / :tellers + 1, 0
            FROM generate_series(1, :tellers * :scale) as tid;

            SET rds_aurora.limitless_create_table_mode='standard';

            CREATE TABLE pgbench_init_queue ( branch INT );
            INSERT INTO pgbench_init_queue SELECT b FROM GENERATE_SERIES(1, :scale) b;

            CREATE OR REPLACE PROCEDURE pgbench_init_accounts()
            LANGUAGE plpgsql
            AS $$
            DECLARE
                accounts int = 100000;
                startv bigint;
                endv bigint;
                remaining int;
            BEGIN
                WHILE true
                LOOP
                    WITH d AS (
                        DELETE FROM pgbench_init_queue WHERE branch =
                        (SELECT branch FROM pgbench_init_queue FOR UPDATE SKIP LOCKED LIMIT 1)
                        RETURNING coalesce((branch), 0)::bigint as branch
                    ),
                    a AS (
                    SELECT
                        CASE WHEN d.branch= 1 THEN 1 ELSE (d.branch * accounts - accounts) + 1 END start,
                        (d.branch * accounts) end
                    FROM d
                    )
                    SELECT * FROM a INTO startv, endv;
                    COMMIT;

                    INSERT INTO pgbench_accounts(aid,bid,abalance,filler)
                    SELECT aid, (aid - 1) / accounts + 1, 0, ''
                    FROM generate_series(startv, endv) as aid
                    WHERE startv > 0;

                    SELECT count(*) INTO remaining FROM pgbench_init_queue;

                    IF (remaining = 0)
                    THEN
                        exit;
                    END IF;
                END LOOP;
            END$$;
        """
        
        with subprocess.Popen(["psql"] + connstring_final + ["-v", f"scale={args.scale}"], stdin=subprocess.PIPE) as pipe:
            pipe.communicate(init_sql.encode())
            if pipe.returncode != 0:
                raise SystemExit("Failed to initialize pgbench.")
        
        # Load SQL script
        load_sql = "CALL pgbench_init_accounts();"
        with subprocess.Popen(["pgbench"] + connstring_final + ["-n", f"-c{args.clients}", "-t1", "-f-"] , stdin=subprocess.PIPE) as pipe:
            pipe.communicate(load_sql.encode())
            if pipe.returncode != 0:
                raise SystemExit("Failed to load pgbench accounts.")
        
        # Post initialization SQL script
        postinit_sql = """
            ALTER TABLE pgbench_accounts
            ADD CONSTRAINT pgbench_accounts_pkey PRIMARY KEY (aid, bid);

            ALTER TABLE pgbench_branches
            ADD CONSTRAINT pgbench_branches_pkey PRIMARY KEY (bid);

            ALTER TABLE pgbench_tellers
            ADD CONSTRAINT pgbench_tellers_pkey PRIMARY KEY (tid, bid);

            VACUUM (FREEZE) pgbench_accounts, pgbench_branches, pgbench_tellers;
        """
        
        with subprocess.Popen(["psql"] + connstring_final + ["-f-"] , stdin=subprocess.PIPE) as pipe:
            pipe.communicate(postinit_sql.encode())
            if pipe.returncode != 0:
                raise SystemExit("Failed to finalize pgbench initialization.")
    else:
    # if the user did not request a limitless workload, just do the work as requested.
        #connstring_final = get_limitless_endpoints('', args.host) if args.host == '' else connstring_check.split()
        if args.limitless_workload:
        # Handle limitless workload
                benchmark_sql = ""
                if args.limitless_workload not in ["simple-update", "select-only", "tpcb-like"]:
                    raise SystemExit("Invalid limitless-workload set")
    
                    if args.limitless_workload == "simple-update":
                        benchmark_sql = r"""
                                \set aid random(1, 100000 * :scale)
                            \set bid random(1, 1 * :scale)
                            \set tid random(1, 10 * :scale)
                            \set delta random(-5000, 5000)
                            BEGIN;
                                UPDATE pgbench_accounts SET abalance = abalance + :delta WHERE aid = :aid AND bid = :bid;
                                SELECT abalance FROM pgbench_accounts WHERE aid = :aid AND bid = :bid;
                                INSERT INTO pgbench_history (tid, bid, aid, delta, mtime) VALUES (:tid, :bid, :aid, :delta, CURRENT_TIMESTAMP);
                            END;
                        """
                    elif args.limitless_workload == "select-only":
                        benchmark_sql = r"""
                            \set aid random(1, 100000 * :scale)
                            \set bid (:aid - 1) / 100000 + 1
                            SELECT abalance FROM pgbench_accounts WHERE aid = :aid AND bid = :bid;
                        """
                else:
                    benchmark_sql = r"""
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
                    """
    
                benchmark_cmd = ["pgbench"] + connstring_final + pgbench_flags + ["--file=-"]
                env = os.environ.copy()
                env['PGLOADBALANCEHOSTS'] = "random"
                #print(f"exeucted PGLOADBALANCEHOSTS: ", env['PGLOADBALANCEHOSTS'])

                #print(f"benchmark_cmd: {benchmark_cmd}")
                with subprocess.Popen(benchmark_cmd, stdin=subprocess.PIPE, env = env) as pipe:
                    if args.pipelined:
                        benchmark_sql = f"\\startpipeline\n{benchmark_sql}\n\\endpipeline"
    
                    pipe.communicate(benchmark_sql.encode())
                    if pipe.returncode != 0:
                        raise SystemExit("Failed to run limitless workload benchmark.")
        else:
            print(f"last statement: {connstring_final}, {pgbench_flags}")
            subprocess.run(["pgbench"] + connstring_final + pgbench_flags, check=True)

