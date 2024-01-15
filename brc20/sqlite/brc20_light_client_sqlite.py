# pip install python-dotenv
# pip install buidl

import os, sys, requests
from dotenv import load_dotenv
import traceback, time, codecs, json, random
import sqlite3
import hashlib
import buidl

## global variables
ticks = {}
in_commit = False
block_events_str = ""
EVENT_SEPARATOR = "|"
CAN_BE_FIXED_INDEXER_VERSIONS = [ ]
INDEXER_VERSION = "opi-brc20-light-client-sqlite v0.2.0"
DB_VERSION = 1

## load env variables
load_dotenv()
db_database_name = os.getenv("DB_DATABASE_FILE") or "db.sqlite3"

first_inscription_height = int(os.getenv("FIRST_INSCRIPTION_HEIGHT") or "767430")
first_brc20_height = int(os.getenv("FIRST_BRC20_HEIGHT") or "779832")

report_to_indexer = (os.getenv("REPORT_TO_INDEXER") or "true") == "true"
report_url = os.getenv("REPORT_URL") or "https://api.opi.network/report_block"
report_retries = int(os.getenv("REPORT_RETRIES") or "10")
report_name = os.getenv("REPORT_NAME") or "opi_brc20_light_client_sqlite"

create_extra_tables = (os.getenv("CREATE_EXTRA_TABLES") or "false") == "true"

## connect to db
conn = sqlite3.connect(db_database_name, isolation_level=None)
cur = conn.cursor()

def execute_with_params(sql, params):
  global cur
  last_param_idx = 0
  while True:
    ## find %s in sql
    idx = sql.find('%s')
    if idx == -1: break
    ## replace %s with :param<last_param_idx>
    sql = sql[:idx] + ':param' + str(last_param_idx) + sql[idx+2:]
    last_param_idx += 1
  obj = {}
  for i in range(last_param_idx):
    obj['param' + str(i)] = params[i]
  cur.execute(sql, obj)

## create tables if not exists
## does brc20_block_hashes table exist?
cur.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='brc20_block_hashes';''')
if cur.fetchone()[0] == 0:
  print("Initialising database...")
  ## execute db_init.sql
  with open('db_init_sqlite.sql', 'r') as f:
    sql = f.read()
    cur.executescript(sql)
  conn.commit()

if create_extra_tables:
  cur.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='brc20_extras_block_hashes';''')
  if cur.fetchone()[0] == 0:
    print("Initialising extra tables...")
    with open('db_init_extra_sqlite.sql', 'r') as f:
      sql = f.read()
      cur.executescript(sql)
    conn.commit()

## helper functions

def utf8len(s):
  return len(s.encode('utf-8'))

def is_positive_number(s, do_strip=False):
  try:
    if do_strip:
      s = s.strip()
    try:
      if len(s) == 0: return False
      for ch in s:
        if ord(ch) > ord('9') or ord(ch) < ord('0'):
          return False
      return True
    except: return False
  except: return False ## has to be a string

def is_positive_number_with_dot(s, do_strip=False):
  try:
    if do_strip:
      s = s.strip()
    try:
      dotFound = False
      if len(s) == 0: return False
      if s[0] == '.': return False
      if s[-1] == '.': return False
      for ch in s:
        if ord(ch) > ord('9') or ord(ch) < ord('0'):
          if ch != '.': return False
          if dotFound: return False
          dotFound = True
      return True
    except: return False
  except: return False ## has to be a string

def get_number_extended_to_18_decimals(s, decimals, do_strip=False):
  if do_strip:
    s = s.strip()
  
  if '.' in s:
    normal_part = s.split('.')[0]
    if len(s.split('.')[1]) > decimals or len(s.split('.')[1]) == 0: ## more decimal digit than allowed or no decimal digit after dot
      return None
    decimals_part = s.split('.')[1][:decimals]
    decimals_part += '0' * (18 - len(decimals_part))
    return int(normal_part + decimals_part)
  else:
    return int(s) * 10 ** 18

def is_used_or_invalid(inscription_id):
  global event_types
  execute_with_params('''select coalesce(sum(case when event_type = %s then 1 else 0 end), 0) as inscr_cnt,
                        coalesce(sum(case when event_type = %s then 1 else 0 end), 0) as transfer_cnt
                        from brc20_events where inscription_id = %s;''', (event_types["transfer-inscribe"], event_types["transfer-transfer"], inscription_id,))
  row = cur.fetchall()[0]
  return (row[0] != 1) or (row[1] != 0)

def fix_numstr_decimals(num_str, decimals):
  if len(num_str) <= 18:
    num_str = '0' * (18 - len(num_str)) + num_str
    num_str = '0.' + num_str
    if decimals < 18:
      num_str = num_str[:-18+decimals]
  else:
    num_str = num_str[:-18] + '.' + num_str[-18:]
    if decimals < 18:
      num_str = num_str[:-18+decimals]
  if num_str[-1] == '.': num_str = num_str[:-1] ## remove trailing dot
  return num_str

def script_to_address(pkscript):
  if pkscript is None: return None
  script = buidl.Script.parse(raw=bytearray.fromhex(pkscript))
  if script.is_p2pkh():
    return buidl.P2PKHScriptPubKey(script.commands[2]).address()
  elif script.is_p2sh():
    return buidl.P2SHScriptPubKey(script.commands[1]).address()
  elif script.is_p2wpkh():
    return buidl.P2WPKHScriptPubKey(script.commands[1]).address()
  elif script.is_p2wsh():
    return buidl.P2WSHScriptPubKey(script.commands[1]).address()
  elif script.is_p2tr():
    return buidl.P2TRScriptPubKey(script.commands[1]).address()
  else:
    return None

def get_event_str(event, event_type, inscription_id):
  global ticks
  if event_type == "deploy-inscribe":
    decimals_int = int(event["decimals"])
    res = "deploy-inscribe;"
    res += inscription_id + ";"
    res += event["deployer_pkScript"] + ";"
    res += event["tick"] + ";"
    res += fix_numstr_decimals(event["max_supply"], decimals_int) + ";"
    res += event["decimals"] + ";"
    res += fix_numstr_decimals(event["limit_per_mint"], decimals_int)
    return res
  elif event_type == "mint-inscribe":
    decimals_int = ticks[event["tick"]][2]
    res = "mint-inscribe;"
    res += inscription_id + ";"
    res += event["minted_pkScript"] + ";"
    res += event["tick"] + ";"
    res += fix_numstr_decimals(event["amount"], decimals_int)
    return res
  elif event_type == "transfer-inscribe":
    decimals_int = ticks[event["tick"]][2]
    res = "transfer-inscribe;"
    res += inscription_id + ";"
    res += event["source_pkScript"] + ";"
    res += event["tick"] + ";"
    res += fix_numstr_decimals(event["amount"], decimals_int)
    return res
  elif event_type == "transfer-transfer":
    decimals_int = ticks[event["tick"]][2]
    res = "transfer-transfer;"
    res += inscription_id + ";"
    res += event["source_pkScript"] + ";"
    if event["spent_pkScript"] is not None:
      res += event["spent_pkScript"] + ";"
    else:
      res += ";"
    res += event["tick"] + ";"
    res += fix_numstr_decimals(event["amount"], decimals_int)
    return res
  else:
    print("EVENT TYPE ERROR!!")
    exit(1)

def get_sha256_hash(s):
  return hashlib.sha256(s.encode('utf-8')).hexdigest()





## caches
transfer_inscribe_event_cache = {} ## single use cache for transfer inscribe events
def get_transfer_inscribe_event(inscription_id):
  global transfer_inscribe_event_cache, event_types
  if inscription_id in transfer_inscribe_event_cache:
    event = transfer_inscribe_event_cache[inscription_id]
    del transfer_inscribe_event_cache[inscription_id]
    return event
  execute_with_params('''select event from brc20_events where event_type = %s and inscription_id = %s;''', (event_types["transfer-inscribe"], inscription_id,))
  return json.loads(cur.fetchall()[0][0])

def save_transfer_inscribe_event(inscription_id, event):
  transfer_inscribe_event_cache[inscription_id] = event

balance_cache = {}
def get_last_balance(pkscript, tick):
  global balance_cache
  cache_key = pkscript + tick
  if cache_key in balance_cache:
    return balance_cache[cache_key]
  execute_with_params('''select overall_balance, available_balance from brc20_historic_balances where pkscript = %s and tick = %s order by block_height desc, id desc limit 1;''', (pkscript, tick))
  row = cur.fetchone()
  balance_obj = None
  if row is None:
    balance_obj = {
      "overall_balance": 0,
      "available_balance": 0
    }
  else:
    balance_obj = {
      "overall_balance": int(row[0]),
      "available_balance": int(row[1])
    }
  balance_cache[cache_key] = balance_obj
  return balance_obj

def check_available_balance(pkScript, tick, amount):
  last_balance = get_last_balance(pkScript, tick)
  available_balance = last_balance["available_balance"]
  if available_balance < amount: return False
  return True

def reset_caches():
  global balance_cache, transfer_inscribe_event_cache
  balance_cache = {}
  transfer_inscribe_event_cache = {}

def deploy_inscribe(block_height, inscription_id, deployer_pkScript, deployer_wallet, tick, max_supply, decimals, limit_per_mint):
  global ticks, in_commit, block_events_str, event_types
  cur.execute("BEGIN;")
  in_commit = True

  event = {
    "deployer_pkScript": deployer_pkScript,
    "deployer_wallet": deployer_wallet,
    "tick": tick,
    "max_supply": str(max_supply),
    "decimals": str(decimals),
    "limit_per_mint": str(limit_per_mint)
  }
  block_events_str += get_event_str(event, "deploy-inscribe", inscription_id) + EVENT_SEPARATOR
  execute_with_params('''insert into brc20_events (event_type, block_height, inscription_id, event)
    values (%s, %s, %s, %s);''', (event_types["deploy-inscribe"], block_height, inscription_id, json.dumps(event)))
  
  execute_with_params('''insert into brc20_tickers (tick, max_supply, decimals, limit_per_mint, remaining_supply, block_height)
    values (%s, %s, %s, %s, %s, %s);''', (tick, str(max_supply), decimals, str(limit_per_mint), str(max_supply), block_height))
  
  cur.execute("COMMIT;")
  in_commit = False
  ticks[tick] = [max_supply, limit_per_mint, decimals]

def mint_inscribe(block_height, inscription_id, minted_pkScript, minted_wallet, tick, amount):
  global ticks, in_commit, block_events_str, event_types
  cur.execute("BEGIN;")
  in_commit = True

  event = {
    "minted_pkScript": minted_pkScript,
    "minted_wallet": minted_wallet,
    "tick": tick,
    "amount": str(amount)
  }
  block_events_str += get_event_str(event, "mint-inscribe", inscription_id) + EVENT_SEPARATOR
  execute_with_params('''insert into brc20_events (event_type, block_height, inscription_id, event)
    values (%s, %s, %s, %s) returning id;''', (event_types["mint-inscribe"], block_height, inscription_id, json.dumps(event)))
  event_id = cur.fetchone()[0]
  execute_with_params('''select remaining_supply from brc20_tickers where tick = %s;''', (tick,))
  remaining_supply = cur.fetchone()[0]
  remaining_supply = int(remaining_supply)
  remaining_supply -= amount
  execute_with_params('''update brc20_tickers set remaining_supply = %s where tick = %s;''', (str(remaining_supply), tick))

  last_balance = get_last_balance(minted_pkScript, tick)
  last_balance["overall_balance"] += amount
  last_balance["available_balance"] += amount
  execute_with_params('''insert into brc20_historic_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height, event_id) 
                values (%s, %s, %s, %s, %s, %s, %s);''', 
                (minted_pkScript, minted_wallet, tick, str(last_balance["overall_balance"]), str(last_balance["available_balance"]), block_height, event_id))
  
  cur.execute("COMMIT;")
  in_commit = False
  ticks[tick][0] -= amount

def transfer_inscribe(block_height, inscription_id, source_pkScript, source_wallet, tick, amount):
  global in_commit, block_events_str, event_types
  cur.execute("BEGIN;")
  in_commit = True

  event = {
    "source_pkScript": source_pkScript,
    "source_wallet": source_wallet,
    "tick": tick,
    "amount": str(amount)
  }
  block_events_str += get_event_str(event, "transfer-inscribe", inscription_id) + EVENT_SEPARATOR
  execute_with_params('''insert into brc20_events (event_type, block_height, inscription_id, event)
    values (%s, %s, %s, %s) returning id;''', (event_types["transfer-inscribe"], block_height, inscription_id, json.dumps(event)))
  event_id = cur.fetchone()[0]
  
  last_balance = get_last_balance(source_pkScript, tick)
  last_balance["available_balance"] -= amount
  execute_with_params('''insert into brc20_historic_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height, event_id)
                values (%s, %s, %s, %s, %s, %s, %s);''', 
                (source_pkScript, source_wallet, tick, str(last_balance["overall_balance"]), str(last_balance["available_balance"]), block_height, event_id))
  
  cur.execute("COMMIT;")
  in_commit = False
  save_transfer_inscribe_event(inscription_id, event)

def transfer_transfer_normal(block_height, inscription_id, spent_pkScript, spent_wallet, tick, amount, using_tx_id):
  global in_commit, block_events_str, event_types
  cur.execute("BEGIN;")
  in_commit = True

  inscribe_event = get_transfer_inscribe_event(inscription_id)
  source_pkScript = inscribe_event["source_pkScript"]
  source_wallet = inscribe_event["source_wallet"]
  event = {
    "source_pkScript": source_pkScript,
    "source_wallet": source_wallet,
    "spent_pkScript": spent_pkScript,
    "spent_wallet": spent_wallet,
    "tick": tick,
    "amount": str(amount),
    "using_tx_id": str(using_tx_id)
  }
  block_events_str += get_event_str(event, "transfer-transfer", inscription_id) + EVENT_SEPARATOR
  execute_with_params('''insert into brc20_events (event_type, block_height, inscription_id, event)
    values (%s, %s, %s, %s) returning id;''', (event_types["transfer-transfer"], block_height, inscription_id, json.dumps(event)))
  event_id = cur.fetchone()[0]
  
  last_balance = get_last_balance(source_pkScript, tick)
  last_balance["overall_balance"] -= amount
  execute_with_params('''insert into brc20_historic_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height, event_id)
                values (%s, %s, %s, %s, %s, %s, %s);''', 
                (source_pkScript, source_wallet, tick, str(last_balance["overall_balance"]), str(last_balance["available_balance"]), block_height, event_id))
  
  if spent_pkScript != source_pkScript:
    last_balance = get_last_balance(spent_pkScript, tick)
  last_balance["overall_balance"] += amount
  last_balance["available_balance"] += amount
  execute_with_params('''insert into brc20_historic_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height, event_id) 
                values (%s, %s, %s, %s, %s, %s, %s);''', 
                (spent_pkScript, spent_wallet, tick, str(last_balance["overall_balance"]), str(last_balance["available_balance"]), block_height, -1 * event_id)) ## negated to make a unique event_id
  
  cur.execute("COMMIT;")
  in_commit = False

def transfer_transfer_spend_to_fee(block_height, inscription_id, tick, amount, using_tx_id):
  global in_commit, block_events_str, event_types
  cur.execute("BEGIN;")
  in_commit = True

  inscribe_event = get_transfer_inscribe_event(inscription_id)
  source_pkScript = inscribe_event["source_pkScript"]
  source_wallet = inscribe_event["source_wallet"]
  event = {
    "source_pkScript": source_pkScript,
    "source_wallet": source_wallet,
    "spent_pkScript": None,
    "spent_wallet": None,
    "tick": tick,
    "amount": str(amount),
    "using_tx_id": str(using_tx_id)
  }
  block_events_str += get_event_str(event, "transfer-transfer", inscription_id) + EVENT_SEPARATOR
  execute_with_params('''insert into brc20_events (event_type, block_height, inscription_id, event)
    values (%s, %s, %s, %s) returning id;''', (event_types["transfer-transfer"], block_height, inscription_id, json.dumps(event)))
  event_id = cur.fetchone()[0]
  
  last_balance = get_last_balance(source_pkScript, tick)
  last_balance["available_balance"] += amount
  execute_with_params('''insert into brc20_historic_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height, event_id) 
                values (%s, %s, %s, %s, %s, %s, %s);''', 
                (source_pkScript, source_wallet, tick, str(last_balance["overall_balance"]), str(last_balance["available_balance"]), block_height, event_id))
  
  cur.execute("COMMIT;")
  in_commit = False


def update_event_hashes(block_height):
  global block_events_str
  if len(block_events_str) > 0 and block_events_str[-1] == EVENT_SEPARATOR: block_events_str = block_events_str[:-1] ## remove last separator
  block_event_hash = get_sha256_hash(block_events_str)
  cumulative_event_hash = None
  execute_with_params('''select cumulative_event_hash from brc20_cumulative_event_hashes where block_height = %s;''', (block_height - 1,))
  temp = cur.fetchone()
  if temp is None:
    cumulative_event_hash = block_event_hash
  else:
    cumulative_event_hash = get_sha256_hash(temp[0] + block_event_hash)
  execute_with_params('''INSERT INTO brc20_cumulative_event_hashes (block_height, block_event_hash, cumulative_event_hash) VALUES (%s, %s, %s);''', (block_height, block_event_hash, cumulative_event_hash))
  return cumulative_event_hash

max_block_height_of_opi_network_cache = None
max_block_height_of_opi_network_cache_ts = 0
max_block_height_of_opi_network_cache_timeout = 15
def get_max_block_height_of_opi_network():
  global max_block_height_of_opi_network_cache, max_block_height_of_opi_network_cache_ts, max_block_height_of_opi_network_cache_timeout
  if max_block_height_of_opi_network_cache is not None and time.time() - max_block_height_of_opi_network_cache_ts < max_block_height_of_opi_network_cache_timeout:
    return max_block_height_of_opi_network_cache
  url = 'https://opi.network/api/get_best_verified_block'
  for _ in range(10):
    try:
      r = requests.get(url)
      if r.status_code != 200:
        print("Error getting best block from OPI network")
        time.sleep(2)
        continue
      max_block_height_of_opi_network_cache = int(r.json()["data"]["best_verified_block"])
      max_block_height_of_opi_network_cache_ts = time.time()
      return max_block_height_of_opi_network_cache
    except:
      print("Error getting best block from OPI network")
      time.sleep(2)
      continue
  return None

events_providers = []
def get_events_providers():
  global events_providers
  events_providers = []
  url = 'https://opi.network/api/get_verified_event_providers'
  for _ in range(10):
    try:
      r = requests.get(url)
      if r.status_code != 200:
        print("Error getting event providers from OPI network")
        time.sleep(2)
        continue
      events_providers_temp = r.json()["data"]
      for ep in events_providers_temp:
        events_providers.append(ep["url"])
      if len(events_providers) == 0:
        print("No event providers found on OPI network")
        time.sleep(2)
        continue
      return True
    except:
      print("Error getting event providers from OPI network")
      time.sleep(2)
      continue
  return False

get_block_info_from_opi_network_cache = None
get_block_info_from_opi_network_cache_ts = 0
get_block_info_from_opi_network_cache_timeout = 15
get_block_info_from_opi_network_cache_block_height = None
def get_block_info_from_opi_network(block_height):
  global get_block_info_from_opi_network_cache, get_block_info_from_opi_network_cache_ts, get_block_info_from_opi_network_cache_timeout, get_block_info_from_opi_network_cache_block_height
  if get_block_info_from_opi_network_cache_block_height == block_height and get_block_info_from_opi_network_cache is not None and time.time() - get_block_info_from_opi_network_cache_ts < get_block_info_from_opi_network_cache_timeout:
    return get_block_info_from_opi_network_cache
  block_hash = None
  opi_cumulative_event_hash = None
  url = 'https://opi.network/api/get_best_hashes_for_block/' + str(block_height)
  for _ in range(10):
    try:
      r = requests.get(url)
      if r.status_code != 200:
        print("Error getting best hash info from OPI network")
        time.sleep(2)
        continue
      js = r.json()
      block_hash = js["data"]["best_block_hash"]
      opi_cumulative_event_hash = js["data"]["best_cumulative_hash"]
      get_block_info_from_opi_network_cache = [block_hash, opi_cumulative_event_hash]
      get_block_info_from_opi_network_cache_ts = time.time()
      get_block_info_from_opi_network_cache_block_height = block_height
      return get_block_info_from_opi_network_cache
    except:
      print("Error getting best hash info from OPI network")
      time.sleep(2)
      continue
  return [None, None]

def get_block_from_opi_network(block_height):
  global events_providers
  events = None
  block_hash, opi_cumulative_event_hash = get_block_info_from_opi_network(block_height)
  if block_hash is None or opi_cumulative_event_hash is None: return [None, None, None]
  if block_height < first_brc20_height: return [[], block_hash, opi_cumulative_event_hash]
  inner_event_providers = events_providers.copy()
  while len(inner_event_providers) != 0:
    event_provider = random.choice(inner_event_providers)
    print("Trying to get events from " + event_provider)
    url = event_provider + '/v1/brc20/block_height'
    try:
      r = requests.get(url)
      if r.status_code != 200:
        print("Error getting block height from OPI network")
        inner_event_providers.remove(event_provider)
        time.sleep(0.1)
        continue
      if int(r.text) < block_height:
        print("Block not indexed yet by event provider!!")
        print("Event Provider block height: " + r.text)
        print("Requested block height: " + str(block_height))
        inner_event_providers.remove(event_provider)
        time.sleep(0.1)
        continue
    except:
      print("Error getting block height from OPI network")
      inner_event_providers.remove(event_provider)
      time.sleep(0.1)
      continue
    url = event_provider + '/v1/brc20/activity_on_block?block_height=' + str(block_height)
    for _ in range(10):
      try:
        r = requests.get(url)
        if r.status_code != 200:
          print("Error getting events from OPI network")
          time.sleep(1)
          continue
        events = r.json()["result"]
        return [events, block_hash, opi_cumulative_event_hash]
      except:
        print("Error getting events from OPI network")
        time.sleep(1)
        continue
  return [None, None, None]

def index_block(block_height):
  global ticks, block_events_str
  print("Indexing block " + str(block_height))
  block_events_str = ""
  error = False
  
  events, block_hash, opi_cumulative_event_hash = get_block_from_opi_network(block_height)
  if events is None:
    print("An error happened while fetching the events.")
    return False
  
  if len(events) == 0:
    print("No events found for block " + str(block_height))
    our_cumulative_event_hash = update_event_hashes(block_height)
    if our_cumulative_event_hash != opi_cumulative_event_hash:
      print("Cumulative event hash mismatch!!")
      print("OPI cumulative event hash: " + opi_cumulative_event_hash)
      print("Our cumulative event hash: " + our_cumulative_event_hash)
      return False
    execute_with_params('''INSERT INTO brc20_block_hashes (block_height, block_hash) VALUES (%s, %s);''', (block_height, block_hash))
    return True
  print("Event count: ", len(events))

  ## refresh ticks
  sttm = time.time()
  cur.execute('''select tick, remaining_supply, limit_per_mint, decimals from brc20_tickers;''')
  ticks_ = cur.fetchall()
  ticks = {}
  for t in ticks_:
    ticks[t[0]] = [int(t[1]), int(t[2]), int(t[3])]
  print("Ticks refreshed in " + str(time.time() - sttm) + " seconds")
  
  idx = 0
  for event in events:
    idx += 1
    if idx % 100 == 0:
      print(idx, '/', len(events))
    
    if "tick" not in event: 
      error = True
      break ## invalid event

    tick = event["tick"]
    try: tick = tick.lower()
    except:
      error = True 
      break ## invalid tick
    if utf8len(tick) != 4: 
      error = True
      break ## invalid tick
    
    # handle deploy
    if event["event_type"] == 'deploy-inscribe':
      if tick in ticks: 
        error = True
        break ## already deployed

      if "max_supply" not in event: 
        error = True
        break ## invalid event
      if "inscription_id" not in event:
        error = True
        break ## invalid event
      if "deployer_pkScript" not in event:
        error = True
        break ## invalid event
      #if "deployer_wallet" not in event:
      #  error = True
      #  break ## invalid event
      if "decimals" not in event:
        error = True
        break ## invalid event
      if "limit_per_mint" not in event:
        error = True
        break ## invalid event

      if not is_positive_number(event["decimals"]): 
        error = True
        break ## invalid decimals
      if not is_positive_number(event["max_supply"]): 
        error = True
        break
      if not is_positive_number(event["limit_per_mint"]): 
        error = True
        break ## invalid limit per mint
      
      decimals = int(event["decimals"])
      if decimals > 18: 
        error = True
        break ## invalid decimals

      max_supply = int(event["max_supply"])
      if max_supply is None: 
        error = True
        break ## invalid max supply
      if max_supply > (2**64-1) * (10**18) or max_supply <= 0: 
        error = True
        break ## invalid max supply

      limit_per_mint = int(event["limit_per_mint"])
      if limit_per_mint is None: 
        error = True
        break ## invalid limit per mint
      if limit_per_mint > (2**64-1) * (10**18) or limit_per_mint <= 0: 
        error = True
        break ## invalid limit per mint
      
      
      inscr_id = event["inscription_id"]
      deployer_pkScript = event["deployer_pkScript"]
      deployer_wallet = script_to_address(event["deployer_pkScript"])
      deploy_inscribe(block_height, inscr_id, deployer_pkScript, deployer_wallet, tick, max_supply, decimals, limit_per_mint)
    
    # handle mint
    if event["event_type"] == 'mint-inscribe':
      if tick not in ticks: 
        error = True
        break ## not deployed

      if "amount" not in event: 
        error = True
        break ## invalid event
      if "inscription_id" not in event:
        error = True
        break ## invalid event
      if "minted_pkScript" not in event:
        error = True
        break ## invalid event
      #if "minted_wallet" not in event:
      #  error = True
      #  break ## invalid event

      if not is_positive_number(event["amount"]): 
        error = True
        break ## invalid amount

      amount = int(event["amount"])
      if amount is None: 
        error = True
        break ## invalid amount
      if amount > (2**64-1) * (10**18) or amount <= 0: 
        error = True
        break ## invalid amount

      if ticks[tick][0] <= 0: 
        error = True
        break ## mint ended

      if ticks[tick][1] is not None and amount > ticks[tick][1]: 
        error = True
        break ## mint too much

      if amount > ticks[tick][0]: ## mint too much
        error = True
        break ## mint too much

      inscr_id = event["inscription_id"]
      minted_pkScript = event["minted_pkScript"]
      minted_wallet = script_to_address(event["minted_pkScript"])
      mint_inscribe(block_height, inscr_id, minted_pkScript, minted_wallet, tick, amount)
    
    # handle transfer
    if event["event_type"] == 'transfer-inscribe':
      if tick not in ticks: 
        error = True
        break ## not deployed

      if "amount" not in event: 
        error = True
        break ## invalid event
      if "inscription_id" not in event:
        error = True
        break ## invalid event
      if "source_pkScript" not in event:
        error = True
        break ## invalid event
      #if "source_wallet" not in event:
      #  error = True
      #  break ## invalid event

      if not is_positive_number(event["amount"]): 
        error = True
        break ## invalid amount

      amount = int(event["amount"])
      if amount is None: 
        error = True
        break ## invalid amount
      if amount > (2**64-1) * (10**18) or amount <= 0: 
        error = True
        break ## invalid amount

      inscr_id = event["inscription_id"]
      source_pkScript = event["source_pkScript"]
      source_wallet = script_to_address(event["source_pkScript"])
      ## check if available balance is enough
      if not check_available_balance(source_pkScript, tick, amount): 
        error = True
        break ## not enough available balance
      transfer_inscribe(block_height, inscr_id, source_pkScript, source_wallet, tick, amount)

    # handle transfer
    if event["event_type"] == 'transfer-transfer':
      if tick not in ticks: 
        error = True
        break ## not deployed

      if "amount" not in event: 
        error = True
        break ## invalid event
      if "inscription_id" not in event:
        error = True
        break ## invalid event
      if "source_pkScript" not in event:
        error = True
        break ## invalid event
      #if "source_wallet" not in event:
      #  error = True
      #  break ## invalid event
      if "spent_pkScript" not in event:
        error = True
        break ## invalid event
      #if "spent_wallet" not in event:
      #  error = True
      #  break ## invalid event

      if not is_positive_number(event["amount"]): 
        error = True
        break ## invalid amount

      amount = int(event["amount"])
      if amount is None: 
        error = True
        break ## invalid amount
      if amount > (2**64-1) * (10**18) or amount <= 0: 
        error = True
        break ## invalid amount

      inscr_id = event["inscription_id"]
      source_pkScript = event["source_pkScript"]
      source_wallet = script_to_address(event["source_pkScript"])
      spent_pkScript = event["spent_pkScript"]
      spent_wallet = script_to_address(event["spent_pkScript"])
      ## check if available balance is enough
      if is_used_or_invalid(inscr_id): 
        error = True
        break ## already used or invalid
      if spent_pkScript is None: transfer_transfer_spend_to_fee(block_height, inscr_id, tick, amount, -1)
      else: transfer_transfer_normal(block_height, inscr_id, spent_pkScript, spent_wallet, tick, amount, -1)
  
  if error:
    return False
  
  our_cumulative_event_hash = update_event_hashes(block_height)
  if our_cumulative_event_hash != opi_cumulative_event_hash:
    print("Cumulative event hash mismatch!!")
    print("OPI cumulative event hash: " + opi_cumulative_event_hash)
    print("Our cumulative event hash: " + our_cumulative_event_hash)
    return False
  # end of block
  execute_with_params('''INSERT INTO brc20_block_hashes (block_height, block_hash) VALUES (%s, %s);''', (block_height, block_hash))
  conn.commit()
  print("ALL DONE")
  return True



def check_for_reorg():
  cur.execute('select block_height, block_hash from brc20_block_hashes order by block_height desc limit 1;')
  last_block = cur.fetchone()
  if last_block is None: return None ## nothing indexed yet

  opi_block_hash, opi_cumulative_event_hash = get_block_info_from_opi_network(last_block[0])
  if opi_block_hash == last_block[1]: return None ## last block hashes are the same, no reorg

  print("REORG DETECTED!!")
  cur.execute('select block_height, block_hash from brc20_block_hashes order by block_height desc limit 10;')
  hashes = cur.fetchall() ## get last 10 hashes
  for h in hashes:
    opi_block_hash, opi_cumulative_event_hash = get_block_info_from_opi_network(h[0])
    if opi_block_hash == h[1]: ## found reorg height by a matching hash
      print("REORG HEIGHT FOUND: " + str(h[0]))
      return h[0]
  
  ## bigger than 10 block reorg is not supported by ord
  print("CRITICAL ERROR!!")
  sys.exit(1)

def reorg_fix(reorg_height):
  global event_types
  cur.execute('begin;')
  execute_with_params('delete from brc20_tickers where block_height > %s;', (reorg_height,)) ## delete new tickers
  ## fetch mint events for reverting remaining_supply in other tickers
  execute_with_params('''select event from brc20_events where event_type = %s and block_height > %s;''', (event_types["mint-inscribe"], reorg_height,))
  rows = cur.fetchall()
  tick_changes = {}
  for row in rows:
    event = json.loads(row[0])
    tick = event["tick"]
    amount = int(event["amount"])
    if tick not in tick_changes:
      tick_changes[tick] = 0
    tick_changes[tick] += amount
  for tick in tick_changes:
    execute_with_params('''select remaining_supply from brc20_tickers where tick = %s;''', (tick,))
    remaining_supply = cur.fetchone()[0]
    remaining_supply = int(remaining_supply)
    remaining_supply += tick_changes[tick]
    execute_with_params('''update brc20_tickers set remaining_supply = %s where tick = %s;''', (str(remaining_supply), tick))
  execute_with_params('delete from brc20_historic_balances where block_height > %s;', (reorg_height,)) ## delete new balances
  execute_with_params('delete from brc20_events where block_height > %s;', (reorg_height,)) ## delete new events
  execute_with_params('delete from brc20_cumulative_event_hashes where block_height > %s;', (reorg_height,)) ## delete new bitmaps
  execute_with_params('delete from brc20_block_hashes where block_height > %s;', (reorg_height,)) ## delete new block hashes
  cur.execute('commit;')
  reset_caches()

def check_if_there_is_residue_from_last_run():
  cur.execute('''select max(block_height) from brc20_block_hashes;''')
  row = cur.fetchone()
  current_block = None
  if row[0] is None: current_block = first_inscription_height
  else: current_block = row[0] + 1
  residue_found = False
  cur.execute('''select coalesce(max(block_height), -1) from brc20_events;''')
  temp = cur.fetchone()
  if temp is not None and temp[0] >= current_block:
    residue_found = True
    print("residue on brc20_events")
  cur.execute('''select coalesce(max(block_height), -1) from brc20_historic_balances;''')
  temp = cur.fetchone()
  if temp is not None and temp[0] >= current_block:
    residue_found = True
    print("residue on historic balances")
  cur.execute('''select coalesce(max(block_height), -1) from brc20_tickers;''')
  temp = cur.fetchone()
  if temp is not None and temp[0] >= current_block:
    residue_found = True
    print("residue on tickers")
  cur.execute('''select coalesce(max(block_height), -1) from brc20_cumulative_event_hashes;''')
  temp = cur.fetchone()
  if temp is not None and temp[0] >= current_block:
    residue_found = True
    print("residue on cumulative hashes")
  if residue_found:
    print("There is residue from last run, rolling back to " + str(current_block - 1))
    reorg_fix(current_block - 1)
    print("Rolled back to " + str(current_block - 1))
    return

def check_if_there_is_residue_on_extra_tables_from_last_run():
  cur.execute('''select max(block_height) from brc20_extras_block_hashes;''')
  row = cur.fetchone()
  current_block = None
  if row[0] is None: current_block = first_inscription_height
  else: current_block = row[0] + 1
  residue_found = False
  cur.execute('''select coalesce(max(block_height), -1) from brc20_unused_tx_inscrs;''')
  temp = cur.fetchone()
  if temp is not None and temp[0] >= current_block:
    residue_found = True
    print("residue on brc20_unused_tx_inscrs")
  cur.execute('''select coalesce(max(block_height), -1) from brc20_current_balances;''')
  temp = cur.fetchone()
  if temp is not None and temp[0] >= current_block:
    residue_found = True
    print("residue on brc20_current_balances")
  if residue_found:
    print("There is residue on extra tables from last run, rolling back to " + str(current_block - 1))
    reorg_on_extra_tables(current_block - 1)
    print("Rolled back to " + str(current_block - 1))
    return

cur.execute('select event_type_name, event_type_id from brc20_event_types;')
event_types = {}
for row in cur.fetchall():
  event_types[row[0]] = row[1]

event_types_rev = {}
for key in event_types:
  event_types_rev[event_types[key]] = key

if not get_events_providers():
  print("Error getting event providers from OPI network")
  exit(1)

def reindex_cumulative_hashes():
  global event_types_rev, ticks
  cur.execute('''delete from brc20_cumulative_event_hashes;''')
  cur.execute('''select min(block_height), max(block_height) from brc20_block_hashes;''')
  row = cur.fetchone()
  min_block = row[0]
  max_block = row[1]

  sttm = time.time()
  cur.execute('''select tick, remaining_supply, limit_per_mint, decimals from brc20_tickers;''')
  ticks_ = cur.fetchall()
  ticks = {}
  for t in ticks_:
    ticks[t[0]] = [int(t[1]), int(t[2]), int(t[3])]
  print("Ticks refreshed in " + str(time.time() - sttm) + " seconds")

  print("Reindexing cumulative hashes from " + str(min_block) + " to " + str(max_block))
  for block_height in range(min_block, max_block + 1):
    print("Reindexing block " + str(block_height))
    block_events_str = ""
    execute_with_params('''select event, event_type, inscription_id from brc20_events where block_height = %s order by id asc;''', (block_height,))
    rows = cur.fetchall()
    for row in rows:
      event = json.loads(row[0])
      event_type = event_types_rev[row[1]]
      inscription_id = row[2]
      block_events_str += get_event_str(event, event_type, inscription_id) + EVENT_SEPARATOR
    update_event_hashes(block_height)

cur.execute('select indexer_version from brc20_indexer_version;')
temp = cur.fetchone()
if temp is None:
  execute_with_params('insert into brc20_indexer_version (indexer_version, db_version) values (%s, %s);', (INDEXER_VERSION, DB_VERSION,))
else:
  db_indexer_version = temp[0]
  if db_indexer_version != INDEXER_VERSION:
    print("Indexer version mismatch!!")
    if db_indexer_version not in CAN_BE_FIXED_INDEXER_VERSIONS:
      print("This version (" + db_indexer_version + ") cannot be fixed, please reset tables and reindex.")
      exit(1)
    else:
      print("This version (" + db_indexer_version + ") can be fixed, fixing in 5 secs...")
      time.sleep(5)
      reindex_cumulative_hashes()
      cur.execute('alter table brc20_indexer_version add column if not exists db_version int4;') ## next versions will use DB_VERSION for DB check
      execute_with_params('update brc20_indexer_version set indexer_version = %s, db_version = %s;', (INDEXER_VERSION, DB_VERSION,))
      print("Fixed.")


def try_to_report_with_retries(to_send):
  global report_url, report_retries
  for _ in range(0, report_retries):
    try:
      r = requests.post(report_url, json=to_send)
      if r.status_code == 200:
        print("Reported hashes to metaprotocol indexer indexer.")
        return
      else:
        print("Error while reporting hashes to metaprotocol indexer indexer, status code: " + str(r.status_code))
    except:
      print("Error while reporting hashes to metaprotocol indexer indexer, retrying...")
    time.sleep(1)
  print("Error while reporting hashes to metaprotocol indexer indexer, giving up.")

def report_hashes(block_height):
  global report_to_indexer
  if not report_to_indexer:
    print("Reporting to metaprotocol indexer is disabled.")
    return
  execute_with_params('''select block_event_hash, cumulative_event_hash from brc20_cumulative_event_hashes where block_height = %s;''', (block_height,))
  row = cur.fetchone()
  block_event_hash = row[0]
  cumulative_event_hash = row[1]
  execute_with_params('''select block_hash from brc20_block_hashes where block_height = %s;''', (block_height,))
  block_hash = cur.fetchone()[0]
  to_send = {
    "name": report_name,
    "type": "brc20",
    "node_type": "light_client_sqlite",
    "version": INDEXER_VERSION,
    "db_version": DB_VERSION,
    "block_height": block_height,
    "block_hash": block_hash,
    "block_event_hash": block_event_hash,
    "cumulative_event_hash": cumulative_event_hash
  }
  print("Sending hashes to metaprotocol indexer indexer...")
  try_to_report_with_retries(to_send)

def reorg_on_extra_tables(reorg_height):
  cur.execute('begin;')
  execute_with_params('delete from brc20_current_balances where block_height > %s RETURNING pkscript, tick;', (reorg_height,)) ## delete new balances
  rows = cur.fetchall()
  ## fetch balances of deleted rows for reverting balances
  for r in rows:
    pkscript = r[0]
    tick = r[1]
    execute_with_params(''' select overall_balance, available_balance, wallet, block_height
                    from brc20_historic_balances 
                    where block_height <= %s and pkscript = %s and tick = %s
                    order by id desc
                    limit 1;''', (reorg_height, pkscript, tick))
    temp = cur.fetchone()
    if temp is not None:
      balance = temp
      execute_with_params('''insert into brc20_current_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height)
                      values (%s, %s, %s, %s, %s, %s);''', (pkscript, balance[2], tick, balance[0], balance[1], balance[3]))
  
  cur.execute('DELETE FROM brc20_unused_tx_inscrs;')
  execute_with_params('''with tempp as (
                  select inscription_id, event, id, block_height
                  from brc20_events
                  where event_type = %s and block_height <= %s
                ), tempp2 as (
                  select inscription_id, event
                  from brc20_events
                  where event_type = %s and block_height <= %s
                )
                select t.event, t.id, t.block_height, t.inscription_id
                from tempp t
                left join tempp2 t2 on t.inscription_id = t2.inscription_id
                where t2.inscription_id is null;''', (event_types['transfer-inscribe'], reorg_height, event_types['transfer-transfer'], reorg_height))
  rows = cur.fetchall()
  for row in rows:
    new_event = json.loads(row[0])
    event_id = row[1]
    block_height = row[2]
    inscription_id = row[3]
    execute_with_params('''INSERT INTO brc20_unused_tx_inscrs (inscription_id, tick, amount, current_holder_pkscript, current_holder_wallet, event_id, block_height)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                    (inscription_id, new_event["tick"], str(new_event["amount"]), new_event["source_pkScript"], new_event["source_wallet"], event_id, block_height))

  execute_with_params('delete from brc20_extras_block_hashes where block_height > %s;', (reorg_height,)) ## delete new block hashes
  cur.execute('commit;')

def initial_index_of_extra_tables():
  cur.execute('begin;')
  print("resetting brc20_unused_tx_inscrs")
  cur.execute('DELETE FROM brc20_unused_tx_inscrs;')
  print("selecting unused txes")
  execute_with_params('''with tempp as (
                  select inscription_id, event, id, block_height
                  from brc20_events
                  where event_type = %s
                ), tempp2 as (
                  select inscription_id, event
                  from brc20_events
                  where event_type = %s
                )
                select t.event, t.id, t.block_height, t.inscription_id
                from tempp t
                left join tempp2 t2 on t.inscription_id = t2.inscription_id
                where t2.inscription_id is null;''', (event_types['transfer-inscribe'], event_types['transfer-transfer']))
  rows = cur.fetchall()
  print("inserting unused txes")
  idx = 0
  for row in rows:
    idx += 1
    if idx % 200 == 0: print(idx, '/', len(rows))
    new_event = json.loads(row[0])
    event_id = row[1]
    block_height = row[2]
    inscription_id = row[3]
    execute_with_params('''INSERT INTO brc20_unused_tx_inscrs (inscription_id, tick, amount, current_holder_pkscript, current_holder_wallet, event_id, block_height)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                    (inscription_id, new_event["tick"], str(new_event["amount"]), new_event["source_pkScript"], new_event["source_wallet"], event_id, block_height))
  
  print("resetting brc20_current_balances")
  cur.execute('DELETE FROM brc20_current_balances;')
  print("selecting current balances")
  cur.execute('''with tempp as (
                    select max(id) as id
                    from brc20_historic_balances
                    group by pkscript, tick
                  )
                  select bhb.pkscript, bhb.tick, bhb.overall_balance, bhb.available_balance, bhb.wallet, bhb.block_height
                  from tempp t
                  left join brc20_historic_balances bhb on bhb.id = t.id
                  order by bhb.pkscript asc, bhb.tick asc;''')
  rows = cur.fetchall()
  print("inserting current balances")
  idx = 0
  for r in rows:
    idx += 1
    if idx % 200 == 0: print(idx, '/', len(rows))
    pkscript = r[0]
    tick = r[1]
    overall_balance = r[2]
    available_balance = r[3]
    wallet = r[4]
    block_height = r[5]
    execute_with_params('''insert into brc20_current_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height)
                   values (%s, %s, %s, %s, %s, %s);''', (pkscript, wallet, tick, overall_balance, available_balance, block_height))
  
  print("resetting brc20_extras_block_hashes")
  cur.execute('DELETE FROM brc20_extras_block_hashes;')
  print("inserting brc20_extras_block_hashes")
  cur.execute('''select block_height, block_hash from brc20_block_hashes order by block_height asc;''')
  rows = cur.fetchall()
  idx = 0
  for row in rows:
    idx += 1
    if idx % 200 == 0: print(idx, '/', len(rows))
    block_height = row[0]
    block_hash = row[1]
    execute_with_params('''INSERT INTO brc20_extras_block_hashes (block_height, block_hash) VALUES (%s, %s);''', (block_height, block_hash))

  cur.execute('commit;')

def index_extra_tables(block_height, block_hash):
  ebh_current_height = 0
  cur.execute('select max(block_height) as current_ebh_height from brc20_extras_block_hashes;')
  temp = cur.fetchone()
  if temp is not None:
    res = temp[0]
    if res is not None:
      ebh_current_height = res
  if ebh_current_height >= block_height:
    print("reorg detected on extra tables, rolling back to: " + str(block_height))
    reorg_on_extra_tables(block_height - 1)
  
  print("updating extra tables for block: " + str(block_height))

  execute_with_params('''select pkscript, wallet, tick, overall_balance, available_balance 
                 from brc20_historic_balances 
                 where block_height = %s 
                 order by id asc;''', (block_height,))
  balance_changes = cur.fetchall()
  if len(balance_changes) == 0:
    print("No balance_changes found for block " + str(block_height))
  else:
    balance_changes_map = {}
    for balance_change in balance_changes:
      pkscript = balance_change[0]
      tick = balance_change[2]
      key = pkscript + '_' + tick
      balance_changes_map[key] = balance_change
    print("Balance_change count: ", len(balance_changes_map))
    idx = 0
    for key in balance_changes_map:
      new_balance = balance_changes_map[key]
      idx += 1
      if idx % 200 == 0: print(idx, '/', len(balance_changes_map))
      execute_with_params('''INSERT INTO brc20_current_balances (pkscript, wallet, tick, overall_balance, available_balance, block_height) VALUES (%s, %s, %s, %s, %s, %s)
                     ON CONFLICT (pkscript, tick) 
                     DO UPDATE SET overall_balance = EXCLUDED.overall_balance
                                , available_balance = EXCLUDED.available_balance
                                , block_height = EXCLUDED.block_height;''', new_balance + (block_height,))
    
  execute_with_params('''select event, id, event_type, inscription_id 
                 from brc20_events where block_height = %s and (event_type = %s or event_type = %s) 
                 order by id asc;''', (block_height, event_types['transfer-inscribe'], event_types['transfer-transfer'],))
  events = cur.fetchall()
  if len(events) == 0:
    print("No events found for block " + str(block_height))
  else:
    print("Events count: ", len(events))
    idx = 0
    for row in events:
      new_event = json.loads(row[0])
      event_id = row[1]
      new_event["event_type"] = event_types_rev[row[2]]
      new_event["inscription_id"] = row[3]
      idx += 1
      if idx % 200 == 0: print(idx, '/', len(events))
      if new_event["event_type"] == 'transfer-inscribe':
        execute_with_params('''INSERT INTO brc20_unused_tx_inscrs (inscription_id, tick, amount, current_holder_pkscript, current_holder_wallet, event_id, block_height)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (inscription_id) DO NOTHING''', 
                        (new_event["inscription_id"], new_event["tick"], str(new_event["amount"]), new_event["source_pkScript"], new_event["source_wallet"], event_id, block_height))
      elif new_event["event_type"] == 'transfer-transfer':
        execute_with_params('''DELETE FROM brc20_unused_tx_inscrs WHERE inscription_id = %s;''', (new_event["inscription_id"],))
      else:
        print("Unknown event type: " + new_event["event_type"])
        sys.exit(1)

  execute_with_params('''INSERT INTO brc20_extras_block_hashes (block_height, block_hash) VALUES (%s, %s);''', (block_height, block_hash))
  return True

def check_extra_tables():
  global first_inscription_height
  try:
    cur.execute('''
      select min(ebh.block_height) as ebh_tocheck_height
      from brc20_extras_block_hashes ebh
      left join brc20_block_hashes bh on bh.block_height = ebh.block_height
      where bh.block_hash != ebh.block_hash
    ''')
    ebh_tocheck_height = 0
    temp = cur.fetchone()
    if temp is not None:
      res = temp[0]
      if res is not None:
        ebh_tocheck_height = res
        print("hash diff found on block: " + str(ebh_tocheck_height))
    if ebh_tocheck_height == 0:
      cur.execute('select max(block_height) as current_ebh_height from brc20_extras_block_hashes;')
      temp = cur.fetchone()
      if temp is not None:
        res = temp[0]
        if res is not None:
          ebh_tocheck_height = res + 1
    if ebh_tocheck_height == 0:
      print("no extra table data found")
      ebh_tocheck_height = first_inscription_height
    cur.execute('''select max(block_height) from brc20_block_hashes;''')
    main_block_height = first_inscription_height
    temp = cur.fetchone()
    if temp is not None:
      res = temp[0]
      if res is not None:
        main_block_height = res
    if ebh_tocheck_height > main_block_height:
      print("no new extra table data found")
      return
    while ebh_tocheck_height <= main_block_height:
      if ebh_tocheck_height == first_inscription_height:
        print("initial indexing of extra tables, may take a few minutes")
        initial_index_of_extra_tables()
        return
      execute_with_params('''select block_hash from brc20_block_hashes where block_height = %s;''', (ebh_tocheck_height,))
      block_hash = cur.fetchone()[0]
      if index_extra_tables(ebh_tocheck_height, block_hash):
        print("extra table data indexed for block: " + str(ebh_tocheck_height))
        ebh_tocheck_height += 1
      else:
        print("extra table data index failed for block: " + str(ebh_tocheck_height))
        return
  except:
    traceback.print_exc()
    return

check_if_there_is_residue_from_last_run()
if create_extra_tables:
  check_if_there_is_residue_on_extra_tables_from_last_run()
  print("checking extra tables")
  check_extra_tables()

last_report_height = 0
while True:
  check_if_there_is_residue_from_last_run()
  if create_extra_tables:
    check_if_there_is_residue_on_extra_tables_from_last_run()
  cur.execute('''select max(block_height) from brc20_block_hashes;''')
  row = cur.fetchone()
  current_block = None
  if row[0] is None: current_block = first_inscription_height
  else: current_block = row[0] + 1
  max_block_height_of_opi_network = get_max_block_height_of_opi_network()
  if max_block_height_of_opi_network is None:
    print("Waiting for OPI network...")
    time.sleep(5)
    continue

  if current_block > max_block_height_of_opi_network:
    print("Waiting for new blocks...")
    time.sleep(5)
    continue
  
  print("Processing block %s" % current_block)
  reorg_height = check_for_reorg()
  if reorg_height is not None:
    print("Rolling back to ", reorg_height)
    reorg_fix(reorg_height)
    print("Rolled back to " + str(reorg_height))
    continue
  try:
    if index_block(current_block):
      print("Block %s indexed." % current_block)
      if create_extra_tables:
        print("checking extra tables")
        check_extra_tables()
      if max_block_height_of_opi_network - current_block < 10 or current_block - last_report_height > 100: ## do not report if there are more than 10 blocks to index
        report_hashes(current_block)
        last_report_height = current_block
    else:
      print("Block %s index failed." % current_block)
      time.sleep(5)
  except:
    traceback.print_exc()
    if in_commit: ## rollback commit if any
      print("rolling back")
      cur.execute('''ROLLBACK;''')
      in_commit = False
    time.sleep(10)
