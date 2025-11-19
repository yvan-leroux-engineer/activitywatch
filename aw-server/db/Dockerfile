FROM timescale/timescaledb:latest-pg15-oss

# Copy initialization script
COPY init-db.sql /docker-entrypoint-initdb.d/init-db.sql

# Migrations directory is kept for reference
# Actual migrations are run by the API server on startup via SQLx

