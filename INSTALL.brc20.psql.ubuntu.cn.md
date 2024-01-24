# 在 Ubuntu 22.04 上安装 OPI 轻客户端的详细安装指南

## 安装 PostgreSQL

1) 首先安装并运行 postgresql 二进制文件。

```sh
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql.service
```

2) 设置一些可选参数，此步骤是 *可选的*。

```sh
sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses TO '*';"
sudo -u postgres psql -c "ALTER SYSTEM SET max_connections TO 2000;"
```

3) 为默认用户设置密码。用你的密码替换 `<password>`（密码中不要使用 !，它可能会干扰 shell 转义）

```sh
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '<password>';"
```

4) 重启 postgres 服务以应用新配置。

```sh
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '<password>';"
```

## 安装 Python 库


1) 如果未安装 pip，请先进行安装。可参考[pip官方文档](https://pip.pypa.io/en/stable/installation/)。

```sh
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
rm get-pip.py
```

或者

```sh
sudo apt update
sudo apt install python3-pip
```

2) 安装依赖

```sh
python3 -m pip install python-dotenv;
python3 -m pip install psycopg2-binary;
python3 -m pip install buidl;
```

在一些系统上，默认不安装 requests。如果在运行客户端时遇到 "requests" 未找到错误，请运行此命令：

```sh
python3 -m pip install requests;
```

## 设置轻客户端

1) 下载文件，从最后的备份中恢复数据库

```sh
git clone https://github.com/bestinslot-xyz/OPI-LC.git
cd OPI-LC/brc20/psql
wget https://opi-light-client-files.fra1.digitaloceanspaces.com/light_client_brc20_last.dump
sudo -u postgres pg_restore -U postgres -Fc -d postgres < light_client_brc20_last.dump
rm light_client_brc20_last.dump
```

请注意，请在下载和解压时耐心等待，避免文件损坏。

2) 运行 `initialise_psql.py` 来初始化 `.env` 配置

```sh
python3 initialise_psql.py
```

## 运行 OPI 轻客户端

```sh
python3 brc20_light_client_psql.py
```

# (可选) 设置 API


## 安装 NodeJS

按照[这里的指南](https://github.com/nodesource/distributions)进行以下步骤。

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

## 安装 node 模块

```bash
cd OPI-LC/brc20/api; npm install;
```

## 设置 API

运行 `initialise_api.py` 来初始化 .env 配置

```sh
python3 initialise_api.py
```

## 运行 API

```sh
node api.js
```
