# OPI-LC - Open Protocol Indexer - Light Client

**OPI-LC**, is a light client for **meta-protocols** on Bitcoin. **OPI-LC** uses **OPI Network** to fetch valid event hashes for a block and **OPI API** for fetching events for the block. Then it re-calculates the hashes itself to validate the events.

OPI-LC supports both **PostgreSQL** for better performance, and **Sqlite3** for ease of setup.

Currently OPI-LC only supports **BRC-20**, we'll add new modules over time. Pull Requests are welcomed for other meta-protocols.

## BRC-20 Light Client / API

**BRC-20 Light Client** is the first module of OPI-LC. It follows the official protocol rules hosted [here](https://layer1.gitbook.io/layer1-foundation/protocols/brc-20/indexing). BRC-20 Light Client saves all historical balance changes and all BRC-20 events. Also optionally it can store current balance table and unused transfer inscriptions table.

In addition to indexing all events, it also calculates a block hash and cumulative hash of all events and compares with verified hash from opi network. Here's the pseudocode for hash calculation:
```python
## Calculation starts at block 767430 which is the first inscription block

EVENT_SEPARATOR = '|'
## max_supply, limit_per_mint, amount decimal count is the same as ticker's decimals (no trailing dot if decimals is 0)
## tickers are lowercase
for event in block_events:
  if event is 'deploy-inscribe':
    block_str += 'deploy-inscribe;<inscr_id>;<deployer_pkscript>;<ticker>;<max_supply>;<decimals>;<limit_per_mint>' + EVENT_SEPARATOR
  if event is 'mint-inscribe':
    block_str += 'mint-inscribe;<inscr_id>;<minter_pkscript>;<ticker>;<amount>' + EVENT_SEPARATOR
  if event is 'transfer-inscribe':
    block_str += 'transfer-inscribe;<inscr_id>;<source_pkscript>;<ticker>;<amount>' + EVENT_SEPARATOR
  if event is 'transfer-transfer':
    ## if sent as fee, sent_pkscript is empty
    block_str += 'transfer-transfer;<inscr_id>;<source_pkscript>;<sent_pkscript>;<ticker>;<amount>' + EVENT_SEPARATOR

if block_str.last is EVENT_SEPARATOR: block_str.remove_last()
block_hash = sha256_hex(block_str)
## for first block last_cumulative_hash is empty
cumulative_hash = sha256_hex(last_cumulative_hash + block_hash)
```

There is an optional block event hash reporting system pointed at https://api.opi.network/report_block. If you want to exclude your node from this, just change `REPORT_TO_INDEXER` variable in `brc20/psql/.env` and `brc20/sqlite/.env`.
Also do not forget to change `REPORT_NAME` to differentiate your node from others.

**BRC-20 API** exposes activity on block (block events), balance of a wallet at the start of a given height, current balance of a wallet, block hash and cumulative hash at a given block and hash of all current balances. Also if optional extra tables are created, it exposes brc20 holders of a ticker, unused tx inscriptions of a ticker and unused tx inscriptions of a wallet.

# Setup

For detailed installation guides:
- BRC20
  - Ubuntu
    - [PostgreSQL](INSTALL.brc20.psql.ubuntu.md)
    - [SQLite3](INSTALL.brc20.sqlite.ubuntu.md)

# Update

- Stop all clients and apis
- Update the repo (`git pull`)
- Re-run all clients and apis
