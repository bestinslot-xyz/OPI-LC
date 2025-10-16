# ---- builder ----
FROM rust:1.87-slim AS builder

RUN apt-get update && \
    apt-get install -y clang pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN cargo install --locked --git https://github.com/bestinslot-xyz/brc20-programmable-module.git --tag v0.15.0

# ---- runtime ----
FROM debian:bookworm-slim AS runtime

# only if prog needs ssl/etc at runtime:
RUN apt-get update && \
    apt-get install -y libssl3 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/cargo/bin/brc20-prog /usr/local/bin/brc20-prog

CMD ["brc20-prog", "-l", "info"]