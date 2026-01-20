import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from loguru import logger
import sys

def init_db():
    # Connection parameters for the default postgres database
    # We assume 'postgres' user exists with password '2310' as provided by user
    db_params = {
        "user": "postgres",
        "password": "2310",
        "host": "localhost",
        "port": "5432",
        "dbname": "postgres"  # connect to default db first
    }

    try:
        logger.info("Connecting to default 'postgres' database...")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # 1. Create User
        logger.info("Creating user 'rfp_user'...")
        try:
            cur.execute("CREATE USER rfp_user WITH PASSWORD '2310';")
            logger.info("User 'rfp_user' created.")
        except psycopg2.errors.DuplicateObject:
            logger.info("User 'rfp_user' already exists.")
        
        # 2. Create Database
        logger.info("Creating database 'rfp_bid_db'...")
        try:
            cur.execute("CREATE DATABASE rfp_bid_db OWNER rfp_user;")
            logger.info("Database 'rfp_bid_db' created.")
        except psycopg2.errors.DuplicateDatabase:
            logger.info("Database 'rfp_bid_db' already exists.")

        cur.close()
        conn.close()

        # 3. Connect to new database to setup extensions and grants
        logger.info("Connecting to 'rfp_bid_db'...")
        db_params["dbname"] = "rfp_bid_db"
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # 4. Create Extension
        logger.info("Creating 'vector' extension...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("Extension 'vector' created/verified.")

        # 5. Grant Privileges
        logger.info("Granting privileges...")
        cur.execute("GRANT ALL ON SCHEMA public TO rfp_user;")
        # These might fail if no tables exist yet, but schema grant is most important for future
        cur.execute("ALTER SCHEMA public OWNER TO rfp_user;")
        
        logger.success("Database initialization completed successfully.")
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
