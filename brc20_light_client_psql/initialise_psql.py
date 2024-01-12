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
  DB_USER="postgres"
  DB_HOST="localhost"
  DB_PORT="5432"
  DB_DATABASE="postgres"
  DB_PASSWD=""
  FIRST_INSCRIPTION_HEIGHT="767430"
  FIRST_BRC20_HEIGHT="779832"
  REPORT_TO_INDEXER="true"
  REPORT_URL="https://api.opi.network/report_block"
  REPORT_RETRIES="10"
  REPORT_NAME=""
  CREATE_EXTRA_TABLES="true"
  print("Initialising .env file")
  print("leave blank to use default values")
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
  res = input("First inscription height (Default: 767430) leave default for correct hash reporting: ")
  if res != '':
    FIRST_INSCRIPTION_HEIGHT = res
  res = input("First brc20 height (Default: 779832) leave default for correct hash reporting: ")
  if res != '':
    FIRST_BRC20_HEIGHT = res
  res = input("Report to main indexer (Default: true): ")
  if res != '':
    REPORT_TO_INDEXER = res
  if REPORT_TO_INDEXER == 'true':
    res = input("Report URL (Default: https://api.opi.network/report_block): ")
    if res != '':
      REPORT_URL = res
    res = input("Report retries (Default: 10): ")
    if res != '':
      REPORT_RETRIES = res
    while True:
      res = input("Report name: ")
      if res != '':
        REPORT_NAME = res
        break
      else:
        print('Report name cannot be empty')
  res = input("Create extra tables for faster queries (Default: true) set to true for creating brc20_current_balances and brc20_unused_tx_inscrs tables: ")
  if res != '':
    CREATE_EXTRA_TABLES = res
  f = open('.env', 'w')
  f.write("DB_USER=\""+DB_USER+"\"\n")
  f.write("DB_HOST=\""+DB_HOST+"\"\n")
  f.write("DB_PORT=\""+DB_PORT+"\"\n")
  f.write("DB_DATABASE=\""+DB_DATABASE+"\"\n")
  f.write("DB_PASSWD=\""+DB_PASSWD+"\"\n")
  f.write("FIRST_INSCRIPTION_HEIGHT=\""+FIRST_INSCRIPTION_HEIGHT+"\"\n")
  f.write("FIRST_BRC20_HEIGHT=\""+FIRST_BRC20_HEIGHT+"\"\n")
  f.write("REPORT_TO_INDEXER=\""+REPORT_TO_INDEXER+"\"\n")
  f.write("REPORT_URL=\""+REPORT_URL+"\"\n")
  f.write("REPORT_RETRIES=\""+REPORT_RETRIES+"\"\n")
  f.write("REPORT_NAME=\""+REPORT_NAME+"\"\n")
  f.write("CREATE_EXTRA_TABLES=\""+CREATE_EXTRA_TABLES+"\"\n")
  f.close()

