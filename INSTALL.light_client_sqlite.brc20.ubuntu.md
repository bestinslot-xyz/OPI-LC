# Detailed Installation Guide for OPI Light Client on Ubuntu 22.04

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
python3 -m pip install buidl;
```

## Setup Light Client

1) Clone repository, restore DB from last backup

```sh
git clone https://github.com/bestinslot-xyz/OPI-LC.git
cd OPI-LC/brc20_light_client_sqlite
wget https://opi-light-client-files.fra1.digitaloceanspaces.com/light_client_brc20_sqlite_last.sqlite3.tar.bz2
tar -xvf light_client_brc20_sqlite_last.sqlite3.tar.bz2
rm light_client_brc20_sqlite_last.sqlite3.tar.bz2
mv .env_sqlite .env
```

2) Set REPORT_NAME in .env, replace `<name>` with your node name. NOTE: if there is `/` in your name replace it with `\/`

```sh
sed -i 's/REPORT_NAME="opi_brc20_light_client_sqlite"/REPORT_NAME="<name>"/g' .env
```

3) Run the indexer

```sh
python3 brc20_light_client_sqlite.py
```
