-- Database creation is handled by Docker via POSTGRES_DB env var.
-- Ensure the schema public is ready
GRANT ALL PRIVILEGES ON DATABASE nms TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
