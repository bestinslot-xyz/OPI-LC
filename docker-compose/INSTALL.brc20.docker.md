# BRC20 Docker Compose Installation Guide

The compose file runs three services from one `opi-indexer` image, built from the [OPI repository](https://github.com/bestinslot-xyz/OPI):

- `db`: Postgres 16.
- `light`: the BRC-20 light client (`opi-indexer brc20 light`), with the BRC2.0 engine in process. It serves the engine's JSON-RPC on `127.0.0.1:18545`.
- `api`: the OPI API (`opi-indexer api`) on port 8000.

There is no bitcoind: the light client takes the OPI network's verified block data and recomputes every hash itself.

Install [Docker](https://docs.docker.com/get-docker/) with [Docker Compose](https://docs.docker.com/compose/install/).

## Fresh install

1. In `docker-compose/.env`, set `DB_PASSWD` to a strong password and `NETWORK_TYPE` to `mainnet` or `signet`. Postgres keeps the password of its first start.
2. Start the services:

```bash
docker compose up -d --build
```

3. Follow the light client:

```bash
docker compose logs -f light
curl -s localhost:8000/v1/brc20/block_height
```

The first build compiles `opi-indexer`, which takes a while.

## Switching from the three-image setup

Hosts that ran the earlier `brc20-index`, `brc20-prog` and `brc20-api` images switch in place. The compose project (`opi-lc`) and the volumes (`db_data`, `brc20_prog_data`) keep their names, so the database and the engine data carry over, and indexing resumes from the last block.

1. Stop the old services, from this directory on the old checkout:

```bash
docker compose down
```

2. Optional backup of the database, while the old setup is down:

```bash
docker compose up -d db
docker compose exec db createdb -U postgres -T postgres postgres_snap
docker compose stop db
```

3. Move the checkout to the new setup, keeping a copy of your `.env`:

```bash
cp .env ../opi-lc.env.bak
git checkout -- .env
git fetch origin
git checkout opi-monolith
```

Then carry over `DB_PASSWD`, `REPORT_TO_INDEXER`, `REPORT_NAME` and `API_PORT` from `../opi-lc.env.bak` into the new `.env`. On signet, set `NETWORK_TYPE="signet"`.
4. Start the new services; `--remove-orphans` removes the old `brc20-index`, `brc20-prog` and `brc20-api` containers:

```bash
docker compose up -d --build --remove-orphans
```

On its first start the light client checks the current-balance tables once, and rebuilds them when an older version left them partly built. When the engine data is behind the database, it rolls back to the engine's height and replays those blocks with every hash verified.

The old `.env` keys `BRC20_PROG_RPC_SERVER_USER` and `BRC20_PROG_RPC_SERVER_PASSWORD` have no effect: the engine's JSON-RPC takes no credentials and is published on the host's loopback only.

## Updating

```bash
docker compose up -d --build
```

The build fetches `OPI_REF` (in `.env`) from the OPI repository again, so it picks up new commits on a branch. Set `OPI_REF` to a release tag to stay on that release. The data lives in the Docker volumes and survives rebuilds.

## Ports

- `8000` (`API_PORT` in `.env`): the OPI API, on all interfaces, rate limited by `RATE_LIMIT_*`.
- `127.0.0.1:18545`: the BRC2.0 engine's JSON-RPC (`eth_call`, `debug_traceTransaction`). Change the `light` service's `ports` to publish it elsewhere, behind a firewall.
