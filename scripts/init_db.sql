-- Create user if not exists (ignore error if exists)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'rfp_user') THEN

      CREATE ROLE rfp_user LOGIN PASSWORD '2310';
   END IF;
END
$do$;

-- Grant privileges (needed if we are creating db as superuser but want rfp_user to own it eventually)
ALTER USER rfp_user WITH PASSWORD '2310';

-- Create database (cannot be run inside transaction block, so we run it separately if possible, or assume it doesn't exist. 
-- However, running CREATE DATABASE inside a script run via psql -f might fail if already connected to it or if conditional logic is tricky. 
-- We will try to create it. If it exists, it will error, which we can ignore or handle.)
-- Note: conditional CREATE DATABASE is hard in SQL script. 
-- BETTER APPROACH: We will use separate commands in python or just accept that it might fail if exists.
-- But the user instructions say "Create database".

-- Since we are running this via psql, we can just try to create it. 
-- If it fails, we continue.
DROP DATABASE IF EXISTS rfp_bid_db;
CREATE DATABASE rfp_bid_db OWNER rfp_user;

-- Connect to the new database
\c rfp_bid_db

-- Enable pgvector (must be superuser)
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO rfp_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO rfp_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO rfp_user;

-- Set ownership of schema public just to be sure
ALTER SCHEMA public OWNER TO rfp_user;
