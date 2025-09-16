FROM node:20-slim

WORKDIR /app

# install git for pulling the repo
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# clone the OPI repo
RUN git clone https://github.com/bestinslot-xyz/OPI.git

WORKDIR /app/OPI/modules/brc20_api

# install deps
RUN npm install

# expose the port api.js uses
EXPOSE ${API_PORT:-8000}

CMD ["node", "api.js"]