# OPI-LC - Open Protocol Indexer - Light Client

**OPI-LC**, is a light client for **meta-protocols** on Bitcoin. **OPI-LC** uses **OPI Network** to fetch valid event hashes for a block and **OPI API** for fetching events for the block. Then it re-calculates the hashes itself to validate the events.

OPI-LC supports **PostgreSQL** for better performance.

Currently OPI-LC only supports **BRC-20**, we'll add new modules over time. Pull Requests are welcomed for other meta-protocols.

> [!WARNING]
> OPI-LC implementation is now merged with the better performing OPI v2, and BRC-20 indexer is rewritten to support a light client operation mode, and lives in [bestinslot-xyz/OPI repository](https://github.com/bestinslot-xyz/OPI). Read instructions below on how to install/run.

## BRC-20 Light Client / API

**BRC-20 Light Client** is the first module of OPI-LC. It follows the official protocol rules hosted [here](https://layer1.gitbook.io/layer1-foundation/protocols/brc-20/indexing). BRC-20 Light Client saves all historical balance changes, BRC-20 events, current balances and unused transfer inscriptions to the database.

In addition to indexing all events, it calculates a block hash and cumulative hash of all events, and compares them with the verified hash from opi network.

It also calculates a hash of all BRC-20 programmable module traces in the current block, and a cumulative hash of the traces.

Here's the pseudocode for hash calculation:

```python
## Calculation starts at block 767430 which is the first inscription block

EVENT_SEPARATOR = '|'
## max_supply, limit_per_mint, amount decimal count is the same as ticker's decimals (no trailing dot if decimals is 0)
## ticker_lowercase = lower(ticker)
## ticker_original is the ticker on inscription
for event in block_events:
  if event is 'predeploy-inscribe':
    block_str += 'predeploy-inscribe;<inscr_id>;<predeployer_pkscript>;<hash>;<block_height>' + EVENT_SEPARATOR
  if event is 'deploy-inscribe':
    block_str += 'deploy-inscribe;<inscr_id>;<deployer_pkscript>;<ticker_lowercase>;<ticker_original>;<max_supply>;<decimals>;<limit_per_mint>;<is_self_mint("true" or "false")>' + EVENT_SEPARATOR
  if event is 'mint-inscribe':
    block_str += 'mint-inscribe;<inscr_id>;<minter_pkscript>;<ticker_lowercase>;<ticker_original>;<amount>;<parent_id("" if null)>' + EVENT_SEPARATOR
  if event is 'transfer-inscribe':
    block_str += 'transfer-inscribe;<inscr_id>;<source_pkscript>;<ticker_lowercase>;<ticker_original>;<amount>' + EVENT_SEPARATOR
  if event is 'transfer-transfer':
    ## if sent as fee, sent_pkscript is empty
    block_str += 'transfer-transfer;<inscr_id>;<source_pkscript>;<sent_pkscript>;<ticker_lowercase>;<ticker_original>;<amount>' + EVENT_SEPARATOR
  if event is 'brc20prog-deploy-inscribe':
    block_str += 'brc20prog-deploy-inscribe;<inscr_id>;<source_pkscript>;<data>;<base64_data>' + EVENT_SEPARATOR
  if event is 'brc20prog-deploy-transfer':
    block_str += 'brc20prog-deploy-transfer;<inscr_id>;<source_pkscript>;<spent_pkscript>;<data>;<base64_data>;<byte_len>' + EVENT_SEPARATOR
  if event is 'brc20prog-call-inscribe':
    block_str += '<inscr_id>;<source_pkscript>;<contract_address>;<contract_inscription_id>;<data>;<base64_data>' + EVENT_SEPARATOR
  if event is 'brc20prog-call-transfer':
    block_str += '<inscr_id>;<source_pkscript>;<spent_pkscript>;<contract_address>;<contract_inscription_id>;<data>;<base64_data>' + EVENT_SEPARATOR
  if event is 'brc20prog-transact-inscribe':
    block_str += '<inscr_id>;<source_pkscript>;<data>;<base64_data>' + EVENT_SEPARATOR
  if event is 'brc20prog-transact-transfer':
    block_str += '<inscr_id>;<source_pkscript>;<spent_pkscript>;<data>;<base64_data>;<byte_len>' + EVENT_SEPARATOR
  if event is 'brc20prog-withdraw-inscribe':
    block_str += '<inscr_id>;<source_pkscript>;<ticker_lowercase>;<ticker_original>;<amount>' + EVENT_SEPARATOR
  if event is 'brc20prog-withdraw-transfer':
    block_str += '<inscr_id>;<source_pkscript>;<spent_pkscript>;<ticker_lowercase>;<ticker_original>;<amount>' + EVENT_SEPARATOR

if block_str.last is EVENT_SEPARATOR: block_str.remove_last()
block_hash = sha256_hex(block_str)
## for first block last_cumulative_hash is empty
cumulative_hash = sha256_hex(last_cumulative_hash + block_hash)
```

To calculate the trace hashes in a stable way, the JSON string representation of an EVM trace uses the suggested schema at [RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785). It has implementations in both [Rust](https://docs.rs/serde_json_canonicalizer/latest/serde_json_canonicalizer/) and [Python](https://pypi.org/project/rfc8785/):

```python
EVENT_SEPARATOR = '|'
traces_str = ""
for tx in sorted(block_txes, key=lambda tx: tx['transactionIndex']):
  trace_str = rfc8785.dumps(brc20_prog_client.debug_traceTransaction(tx['hash']).result)
  traces_str += trace_str + EVENT_SEPARATOR
if traces_str.last is EVENT_SEPARATOR: traces_str.remove_last()
traces_hash = sha256_hex(traces_str)
cumulative_traces_hash = sha256_hex(last_cumulative_traces_hash + traces_hash)
```

There is an optional block event hash reporting system pointed at https://api.opi.network/report_block. If you want to exclude your node from this, just change `REPORT_TO_INDEXER` variable in `.env` to false.
Also do not forget to change `REPORT_NAME` to differentiate your node from others.

**BRC-20 API** exposes activity on block (block events), balance of a wallet at the start of a given height, current balance of a wallet, block hash and cumulative hash at a given block and hash of all current balances. Also if optional extra tables are created, it exposes brc20 holders of a ticker, unused tx inscriptions of a ticker and unused tx inscriptions of a wallet.

# Setup

For installation guides:

- BRC20
  - Docker compose
    - [en](docker-compose/INSTALL.brc20.docker.md) 
  - Ubuntu
    - Quick setup
      - [en](ubuntu/INSTALL.brc20.quick.md)
    - Detailed
      - [en](ubuntu/INSTALL.brc20.md)
