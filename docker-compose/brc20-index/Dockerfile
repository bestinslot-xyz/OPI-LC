FROM rust:1.87-slim

RUN apt-get update && \
    apt-get install -y pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install brc20-index
RUN cargo install --locked --git https://github.com/bestinslot-xyz/OPI.git brc20-index

CMD [ "brc20-index", "-l", "info" ]
