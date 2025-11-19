# Multi-stage build for aw-server-rust
# Using stable Rust 1.85 (supports dependencies requiring newer Rust)
FROM rust:1.85-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    ca-certificates \
    perl \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy workspace Cargo files
COPY Cargo.toml Cargo.lock ./
COPY aw-server/Cargo.toml ./aw-server/
COPY aw-datastore/Cargo.toml ./aw-datastore/
COPY aw-models/Cargo.toml ./aw-models/
COPY aw-query/Cargo.toml ./aw-query/
COPY aw-transform/Cargo.toml ./aw-transform/
COPY aw-client-rust/Cargo.toml ./aw-client-rust/

# Build dependencies (cached layer)
RUN cargo build --release --workspace || true

# Copy source code
COPY . .

# Copy migrations directory for SQLx (needed at compile time for migrate! macro)
COPY aw-datastore/migrations ./aw-datastore/migrations

# Build application
# Note: SQLx migrate! macro embeds migrations at compile time
RUN cargo build --release --workspace

# Runtime stage
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /app/target/release/aw-server /app/aw-server

# Copy migrations directory for runtime (SQLx needs them at runtime)
COPY --from=builder /app/aw-datastore/migrations ./aw-datastore/migrations

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (not published - accessed via reverse proxy)
EXPOSE 8080

# Health check (using sh and /dev/tcp since wget/curl not available in slim image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c 'exec 3<>/dev/tcp/localhost/8080 && echo -e "GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n" >&3 && cat <&3 | grep -q "ok" || exit 1' || exit 1

# Note: Migrations are run automatically on startup by the worker thread

# Run application
CMD ["./aw-server"]

