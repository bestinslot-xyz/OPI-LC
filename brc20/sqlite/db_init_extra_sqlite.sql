CREATE TABLE brc20_current_balances (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	pkscript text NOT NULL,
	wallet text NULL,
	tick varchar(4) NOT NULL,
	overall_balance TEXT NOT NULL,
	available_balance TEXT NOT NULL,
	block_height int4 NOT NULL
);
CREATE UNIQUE INDEX brc20_current_balances_pkscript_tick_idx ON brc20_current_balances (pkscript, tick);
CREATE UNIQUE INDEX brc20_current_balances_wallet_tick_idx ON brc20_current_balances (wallet, tick);
CREATE INDEX brc20_current_balances_block_height_idx ON brc20_current_balances (block_height);
CREATE INDEX brc20_current_balances_pkscript_idx ON brc20_current_balances (pkscript);
CREATE INDEX brc20_current_balances_tick_idx ON brc20_current_balances (tick);
CREATE INDEX brc20_current_balances_wallet_idx ON brc20_current_balances (wallet);

CREATE TABLE brc20_unused_tx_inscrs (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	inscription_id text NOT NULL,
	tick varchar(4) NOT NULL,
	amount TEXT NOT NULL,
	current_holder_pkscript text NOT NULL,
	current_holder_wallet text NULL,
	event_id int8 NOT NULL,
	block_height int4 NOT NULL
);
CREATE UNIQUE INDEX brc20_unused_tx_inscrs_inscription_id_idx ON brc20_unused_tx_inscrs (inscription_id);
CREATE INDEX brc20_unused_tx_inscrs_tick_idx ON brc20_unused_tx_inscrs (tick);
CREATE INDEX brc20_unused_tx_inscrs_pkscript_idx ON brc20_unused_tx_inscrs (current_holder_pkscript);
CREATE INDEX brc20_unused_tx_inscrs_wallet_idx ON brc20_unused_tx_inscrs (current_holder_wallet);
CREATE INDEX brc20_unused_tx_inscrs_wallet_tick_idx ON brc20_unused_tx_inscrs (current_holder_wallet, tick);
CREATE INDEX brc20_unused_tx_inscrs_pkscript_tick_idx ON brc20_unused_tx_inscrs (current_holder_pkscript, tick);

CREATE TABLE brc20_extras_block_hashes (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	block_height int4 NOT NULL,
	block_hash text NOT NULL
);
CREATE UNIQUE INDEX brc20_extras_block_hashes_block_height_idx ON brc20_extras_block_hashes (block_height);