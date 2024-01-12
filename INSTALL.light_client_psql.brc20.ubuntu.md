# Detailed Installation Guide for OPI Light Client on Ubuntu 22.04

## Installing PostgreSQL

1) First install and run postgresql binaries.

```sh
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql.service
```

2) Set some optional parameters, this step is *optional*.

```sh
sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses TO '*';"
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections TO 2000;"
```

3) Set the password for default user. Replace `<password>` with your password. (do not use ! in password, it may interfere with shell escape)

```sh
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '<password>';"
```

4) Restart postgres service to apply new configuration.

```sh
sudo systemctl restart postgresql
```

## Installing Python Libraries

1) Install pip if you don't have it. [guide](https://pip.pypa.io/en/stable/installation/).

```sh
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
rm get-pip.py
```

or

```sh
sudo apt install python3-pip
```

2) Install dependencies

```sh
python3 -m pip install python-dotenv;
python3 -m pip install psycopg2-binary;
python3 -m pip install buidl;
```

## Setup Light Client

1) Download files, restore DB from last backup

```sh
git clone https://github.com/bestinslot-xyz/OPI-LC.git
cd OPI-LC/brc20_light_client_psql
wget https://opi-light-client-files.fra1.digitaloceanspaces.com/light_client_brc20_last.dump
sudo -u postgres pg_restore -U postgres -Fc -d postgres < light_client_brc20_last.dump
rm light_client_brc20_last.dump
mv .env_psql .env
```

2) Set DB_PASSWD in .env, replace `<password>` with your password. NOTE: if there is `/` in your password replace it with `\/`

```sh
sed -i 's/DB_PASSWD=""/DB_PASSWD="<password>"/g' .env
```

3) Set REPORT_NAME in .env, replace `<name>` with your node name. NOTE: if there is `/` in your password replace it with `\/`

```sh
sed -i 's/REPORT_NAME="opi_brc20_light_client"/REPORT_NAME="<name>"/g' .env
```

4) Run the indexer

```sh
python3 brc20_light_client_psql.py
```
