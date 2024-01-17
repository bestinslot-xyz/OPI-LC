CREATE TABLE brc20_block_hashes (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	block_height int4 NOT NULL,
	block_hash text NOT NULL,
);
CREATE UNIQUE INDEX brc20_block_hashes_block_height_idx ON brc20_block_hashes (block_height);

CREATE TABLE brc20_historic_balances (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	pkscript text NOT NULL,
	wallet text NULL,
	tick varchar(4) NOT NULL,
	overall_balance TEXT NOT NULL,
	available_balance TEXT NOT NULL,
	block_height int4 NOT NULL,
	event_id int8 NOT NULL,
);
CREATE UNIQUE INDEX brc20_historic_balances_event_id_idx ON brc20_historic_balances (event_id);
CREATE INDEX brc20_historic_balances_block_height_idx ON brc20_historic_balances (block_height);
CREATE INDEX brc20_historic_balances_pkscript_idx ON brc20_historic_balances (pkscript);
CREATE INDEX brc20_historic_balances_pkscript_tick_block_height_idx ON brc20_historic_balances (pkscript, tick, block_height);
CREATE INDEX brc20_historic_balances_tick_idx ON brc20_historic_balances (tick);
CREATE INDEX brc20_historic_balances_wallet_idx ON brc20_historic_balances (wallet);

CREATE TABLE brc20_events (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	event_type int4 NOT NULL,
	block_height int4 NOT NULL,
	inscription_id text NOT NULL,
	"event" jsonb NOT NULL,
);
CREATE UNIQUE INDEX brc20_events_event_type_inscription_id_idx ON brc20_events (event_type, inscription_id);
CREATE INDEX brc20_events_block_height_idx ON brc20_events (block_height);
CREATE INDEX brc20_events_event_type_idx ON brc20_events (event_type);
CREATE INDEX brc20_events_event_type_block_height_idx ON brc20_events (event_type, block_height);
CREATE INDEX brc20_events_inscription_id_idx ON brc20_events (inscription_id);

CREATE TABLE brc20_tickers (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	tick varchar(4) NOT NULL,
	max_supply TEXT NOT NULL,
	decimals int4 NOT NULL,
	limit_per_mint TEXT NOT NULL,
	remaining_supply TEXT NOT NULL,
	block_height int4 NOT NULL,
);
CREATE UNIQUE INDEX brc20_tickers_tick_idx ON brc20_tickers (tick);

CREATE TABLE brc20_cumulative_event_hashes (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	block_height int4 NOT NULL,
	block_event_hash text NOT NULL,
	cumulative_event_hash text NOT NULL,
);
CREATE UNIQUE INDEX brc20_cumulative_event_hashes_block_height_idx ON brc20_cumulative_event_hashes (block_height);

CREATE TABLE brc20_event_types (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	event_type_name text NOT NULL,
	event_type_id int4 NOT NULL,
);
INSERT INTO brc20_event_types (event_type_name, event_type_id) VALUES ('deploy-inscribe', 0);
INSERT INTO brc20_event_types (event_type_name, event_type_id) VALUES ('mint-inscribe', 1);
INSERT INTO brc20_event_types (event_type_name, event_type_id) VALUES ('transfer-inscribe', 2);
INSERT INTO brc20_event_types (event_type_name, event_type_id) VALUES ('transfer-transfer', 3);

CREATE TABLE brc20_indexer_version (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	indexer_version text NOT NULL,
	db_version int4 NOT NULL,
);
INSERT INTO brc20_indexer_version (indexer_version, db_version) VALUES ("opi-brc20-light-client-sqlite v0.2.0", 1);
