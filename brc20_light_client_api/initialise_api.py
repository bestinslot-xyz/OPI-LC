# pip install python-dotenv

import os
from dotenv import load_dotenv

init_env = True

# does .env file exist?
if os.path.isfile('.env'):
  res = input("Do you want to re-initialise .env file? (y/n) ")
  if res != 'y':
    init_env = False

if init_env:
  # .env file
  DB_TYPE="psql"
  DB_USER="postgres"
  DB_HOST="localhost"
  DB_PORT="5432"
  DB_DATABASE="postgres"
  DB_PASSWD=""
  DB_SSL="true"
  DB_MAX_CONNECTIONS=10
  DB_DATABASE_FILE="../brc20_light_client_sqlite/db.sqlite3"
  USE_EXTRA_TABLES="true"
  API_HOST="127.0.0.1"
  API_PORT="8000"
  API_TRUSTED_PROXY_CNT="0"
  print("Initialising .env file")
  print("leave blank to use default values")
  while True:
    res = input("BRC20 Postgres DB type (Default: psql) set to sqlite for sqlite version: ")
    if res != '':
      DB_TYPE = res
      if DB_TYPE != 'sqlite' and DB_TYPE != 'psql':
        print('DB type can only be sqlite or psql')
      else:
        break
  if DB_TYPE == 'psql':
    use_other_env = False
    other_env_exists = os.path.isfile('../brc20_light_client_psql/.env')
    if other_env_exists:
      res = input(".env on brc20_light_client_psql already exists, do you want to use values from there? (y/n) ")
      if res == 'y':
        use_other_env = True
    if use_other_env:
      load_dotenv(dotenv_path='../brc20_light_client_psql/.env')
      DB_USER = os.getenv("DB_USER") or "postgres"
      DB_HOST = os.getenv("DB_HOST") or "localhost"
      DB_PORT = os.getenv("DB_PORT") or "5432"
      DB_DATABASE = os.getenv("DB_DATABASE") or "postgres"
      DB_PASSWD = os.getenv("DB_PASSWD")
      DB_SSL = os.getenv("DB_SSL") or "true"
      DB_MAX_CONNECTIONS = os.getenv("DB_MAX_CONNECTIONS") or "10"
      USE_EXTRA_TABLES = os.getenv("CREATE_EXTRA_TABLES") or "true"
    else:
      res = input("BRC20 Postgres DB username (Default: postgres): ")
      if res != '':
        DB_USER = res
      res = input("BRC20 Postgres DB host (Default: localhost) leave default if postgres is installed on the same machine: ")
      if res != '':
        DB_HOST = res
      res = input("BRC20 Postgres DB port (Default: 5432): ")
      if res != '':
        DB_PORT = res
      res = input("BRC20 Postgres DB name (Default: postgres) leave default if no new dbs are created: ")
      if res != '':
        DB_DATABASE = res
      res = input("BRC20 Postgres DB password: ")
      DB_PASSWD = res
      res = input("BRC20 Postgres DB use SSL (Default: true) may need to be set to false on Windows machines: ")
      if res != '':
        DB_SSL = res
      res = input("BRC20 Postgres DB max connections (Default: 10): ")
      if res != '':
        DB_MAX_CONNECTIONS = res
      res = input("Use extra tables (Default: true): ")
      if res != '':
        USE_EXTRA_TABLES = res
  elif DB_TYPE == 'sqlite':
    use_other_env = False
    other_env_exists = os.path.isfile('../brc20_light_client_sqlite/.env')
    if other_env_exists:
      res = input(".env on brc20_light_client_sqlite already exists, do you want to use values from there? (y/n) ")
      if res == 'y':
        use_other_env = True
    if use_other_env:
      load_dotenv(dotenv_path='../brc20_light_client_sqlite/.env')
      DB_DATABASE_FILE = "../brc20_light_client_sqlite/" + (os.getenv("DB_DATABASE_FILE") or "db.sqlite3")
      USE_EXTRA_TABLES = os.getenv("CREATE_EXTRA_TABLES") or "true"
    else:
      res = input("BRC20 SQLite DB file path (Default: ../brc20_light_client_sqlite/db.sqlite3): ")
      if res != '':
        DB_DATABASE_FILE = res
      res = input("Use extra tables (Default: true): ")
      if res != '':
        USE_EXTRA_TABLES = res
  res = input("API host (Default: 127.0.0.1): ")
  if res != '':
    API_HOST = res
  res = input("API port (Default: 8000): ")
  if res != '':
    API_PORT = res
  res = input("API trusted proxy count (Default: 0) if there are known proxies such as nginx in front of API, set this to the number of proxies: ")
  if res != '':
    API_TRUSTED_PROXY_CNT = res
  f = open('.env', 'w')
  f.write('DB_TYPE="' + DB_TYPE + '"\n')
  f.write('DB_USER="' + DB_USER + '"\n')
  f.write('DB_HOST="' + DB_HOST + '"\n')
  f.write('DB_PORT="' + DB_PORT + '"\n')
  f.write('DB_DATABASE="' + DB_DATABASE + '"\n')
  f.write('DB_PASSWD="' + DB_PASSWD + '"\n')
  f.write('DB_SSL="' + DB_SSL + '"\n')
  f.write('DB_MAX_CONNECTIONS=' + str(DB_MAX_CONNECTIONS) + '\n')
  f.write('DB_DATABASE_FILE="' + DB_DATABASE_FILE + '"\n')
  f.write('USE_EXTRA_TABLES="' + USE_EXTRA_TABLES + '"\n')
  f.write('API_HOST="' + API_HOST + '"\n')
  f.write('API_PORT="' + API_PORT + '"\n')
  f.write('API_TRUSTED_PROXY_CNT="' + API_TRUSTED_PROXY_CNT + '"\n')
  f.close()
