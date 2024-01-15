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

On some systems, requests is not installed by default. If you get "requests" not found error while running the client, run this:
```sh
python3 -m pip install requests;
```

## Setup Light Client

1) Download files, restore DB from last backup

```sh
git clone https://github.com/bestinslot-xyz/OPI-LC.git
cd OPI-LC/brc20/psql
wget https://opi-light-client-files.fra1.digitaloceanspaces.com/light_client_brc20_last.dump
sudo -u postgres pg_restore -U postgres -Fc -d postgres < light_client_brc20_last.dump
rm light_client_brc20_last.dump
```

2) Run initialise_psql.py to initialise .env config

```sh
python3 initialise_psql.py
```

## Run OPI Light-Client

```sh
python3 brc20_light_client_psql.py
```

# (Optional) Setup API


## Installing NodeJS

These steps are following the guide at [here](https://github.com/nodesource/distributions).

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

NODE_MAJOR=20
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list

sudo apt-get update
sudo apt-get install nodejs -y
```

## Installing node modules

```bash
cd OPI-LC/brc20/api; npm install;
```

## Setup API

Run initialise_api.py to initialise .env config

```sh
cd OPI-LC/brc20/api; python3 initialise_api.py
```

## Run API

```sh
node api.js
```
