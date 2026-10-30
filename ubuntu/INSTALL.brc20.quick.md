# BRC20 Quick Ubuntu Installation Guide

Set `DB_PASSWD` and `NETWORK_TYPE` in `.env`, then run from this directory:

```bash
bash run.ubuntu.sh # This installs opi-indexer and runs the light client with the BRC2.0 engine
bash run-api.ubuntu.sh # This runs the OPI API (optional)
```

`run.ubuntu.sh` installs Postgres, Rust and `opi-indexer` (from the [OPI repository](https://github.com/bestinslot-xyz/OPI)), and uses the values in `.env`. You can modify it as needed.

The light client and the API run as the systemd services `opi-light` (`opi-indexer brc20 light`) and `opi-api` (`opi-indexer api`), which restart on failure and start on boot. After changing `.env`, run `sudo systemctl restart opi-light opi-api` to apply it.

```bash
systemctl status opi-light opi-api # Check that both are running
journalctl -u opi-light -f # Follow the light client logs
```

To stop them, run:

```bash
bash stop.ubuntu.sh
bash stop-api.ubuntu.sh # (if you ran the api)
```

## Switching from the brc20-index and brc20-prog services

Hosts that ran the earlier setup switch in place: `opi-light` opens the same database and the same engine data (`BRC20_PROG_DB_PATH`), and indexing resumes from the last block.

1. Keep a copy of your `.env`, and move this checkout to the new setup:

```bash
cp .env ../opi-lc.env.bak
git checkout -- .env
git fetch origin
git checkout opi-monolith
```

2. Carry over `DB_PASSWD`, `DB_DATABASE`, `REPORT_TO_INDEXER`, `REPORT_NAME`, `BRC20_PROG_DB_PATH` and the `API_*` and `RATE_LIMIT_*` values from `../opi-lc.env.bak` into the new `.env`. On signet, set `NETWORK_TYPE="signet"`.
3. Run the scripts again:

```bash
bash run.ubuntu.sh
bash run-api.ubuntu.sh
```

`run.ubuntu.sh` stops and removes the `brc20-index` and `brc20-prog` services, and `run-api.ubuntu.sh` removes the `brc20-api` PM2 process.

On its first start the light client checks the current-balance tables once, and rebuilds them when an older version left them partly built. When the engine data is behind the database, it rolls back to the engine's height and replays those blocks with every hash verified.
