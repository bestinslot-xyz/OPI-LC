# OPI-LC - Open Protocol Indexer - Light Client

**OPI-LC**, is a light client for **meta-protocols** on Bitcoin. **OPI-LC** uses **OPI Network** to fetch valid event hashes for a block and **OPI API** for fetching events for the block. Then it re-calculates the hashes itself to validate the events.

OPI-LC supports **PostgreSQL** for better performance.

Currently OPI-LC only supports **BRC-20**, we'll add new modules over time. Pull Requests are welcomed for other meta-protocols.

This repository holds the install guides and configuration. The light client itself is `opi-indexer` from the [bestinslot-xyz/OPI repository](https://github.com/bestinslot-xyz/OPI): one binary that runs the BRC-20 light client (`opi-indexer brc20 light`) with the BRC2.0 programmable module in process, and serves the OPI API (`opi-indexer api`). A light client needs no bitcoind: the BRC2.0 engine's Bitcoin lookups come from data the OPI network's full nodes publish.

## BRC-20 Light Client / API

**BRC-20 Light Client** is the first module of OPI-LC. It follows the official protocol rules hosted [here](https://layer1.gitbook.io/layer1-foundation/protocols/brc-20/indexing). BRC-20 Light Client saves all historical balance changes, BRC-20 events, current balances and unused transfer inscriptions to the database.

In addition to indexing all events, it calculates a block hash and cumulative hash of all events, and compares them with the verified hash from opi network.

It also calculates a hash of all BRC-20 programmable module traces in the current block, and a cumulative hash of the traces.

The [BRC-20 Indexer section of the OPI README](https://github.com/bestinslot-xyz/OPI/tree/opi-monolith#brc-20-indexer) gives the pseudocode for both hash calculations.

There is an optional block event hash reporting system pointed at https://api.opi.network/report_block. It is off in this repository's `.env` files: set `REPORT_TO_INDEXER` to true to report, and change `REPORT_NAME` to differentiate your node from others.

**OPI API** exposes activity on block (block events), balance of a wallet at the start of a given height, current balance of a wallet, block hash and cumulative hash at a given block, hash of all current balances, brc20 holders of a ticker, and unused transfer inscriptions of a ticker or a wallet. It also serves ticker, holder, wallet balance and event-feed routes, and a push feed of block events; the [API section of the OPI README](https://github.com/bestinslot-xyz/OPI/tree/opi-monolith#api) lists every route.

The light client also serves the BRC2.0 engine's JSON-RPC (`eth_call`, `debug_traceTransaction`) on `127.0.0.1:18545`. It takes no credentials, so keep it on loopback or firewall it.

# Setup

For installation guides:

- BRC20
  - Docker compose
    - [en](docker-compose/INSTALL.brc20.docker.md)
  - Ubuntu
    - Quick setup
      - [en](ubuntu/INSTALL.brc20.quick.md)
    - Detailed - You likely won't need this, unless you want to customize something
      - [en](ubuntu/INSTALL.brc20.md)

Hosts that ran the earlier `brc20-index`, `brc20-prog` and `brc20-api` setup switch in place, keeping their database and BRC2.0 engine data; each guide has a section for it.

> [!NOTE]
> Both setups build `opi-indexer` from the OPI repository's `opi-monolith` branch. The Docker setup takes the ref from `OPI_REF` in its `.env`, so it can stay on a release tag.
