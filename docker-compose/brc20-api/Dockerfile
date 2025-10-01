# ---- builder ----
FROM node:20-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# clone repo
RUN git clone --depth=1 https://github.com/bestinslot-xyz/OPI.git --branch v1.1.0

WORKDIR /app/OPI/modules/brc20_api

# install only prod deps
RUN npm install --omit=dev

# ---- runtime ----
FROM node:20-slim AS runtime
WORKDIR /app

# copy only built api + node_modules
COPY --from=builder /app/OPI/modules/brc20_api /app

# default port
EXPOSE 8000

CMD ["node", "api.js"]