FROM rust:1.87-slim

# install build deps
RUN apt-get update && \
    apt-get install -y clang pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install brc20-prog
RUN cargo install --locked --git https://github.com/bestinslot-xyz/brc20-programmable-module.git

CMD [ "brc20-prog", "-l", "info" ]