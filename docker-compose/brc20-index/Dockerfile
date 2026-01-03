# ---- builder ----
FROM rust:1.88-slim AS builder

RUN apt-get update && \
    apt-get install -y pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# build only brc20-index from the repo
RUN cargo install --locked --git https://github.com/bestinslot-xyz/OPI.git brc20-index --tag v2.0.6

# ---- runtime ----
FROM debian:bookworm-slim

# runtime deps (ssl + certs for https etc.)
RUN apt-get update && \
    apt-get install -y libssl3 ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/cargo/bin/brc20-index /usr/local/bin/brc20-index

CMD ["brc20-index", "-l", "info"]
