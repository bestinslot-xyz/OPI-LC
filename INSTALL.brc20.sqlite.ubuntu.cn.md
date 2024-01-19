# 在 Ubuntu 22.04 上安装 OPI 轻客户端的详细安装指南

## 安装 Python 库

1) 如果未安装 pip，请用以下命令进行安装。可参考[pip官方文档](https://pip.pypa.io/en/stable/installation/)。

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

2) 安装依赖项

```sh
python3 -m pip install python-dotenv;
python3 -m pip install buidl;
```

在某些系统上，默认情况下未安装 requests。如果在运行客户端时遇到 "requests not found" 错误，请运行以下命令：

```sh
python3 -m pip install requests;
```

## 安装解压缩工具以进行备份还原

```sh
sudo apt update
sudo apt install bzip2
```

## 设置轻客户端

1) 克隆代码，并从最后一个备份还原数据库

```sh
git clone https://github.com/bestinslot-xyz/OPI-LC.git
cd OPI-LC/brc20/sqlite
wget https://opi-light-client-files.fra1.digitaloceanspaces.com/light_client_brc20_sqlite_last.sqlite3.tar.bz2
tar -xvf light_client_brc20_sqlite_last.sqlite3.tar.bz2
rm light_client_brc20_sqlite_last.sqlite3.tar.bz2
```
请注意，下载的bz2压缩包有8G，解压后的文件超过40G，所以请在下载和解压时耐心等待，避免文件损坏。

2) 运行 `initialise_sqlite.py` 初始化 .env 配置

```sh
python3 initialise_sqlite.py
```
在设置时，除了选择name以外，均可使用默认选项。name只是一个标识，当做昵称设置即可，不会影响客户端的运行。

## 运行 OPI 轻客户端

```sh
python3 brc20_light_client_sqlite.py
```

# (可选) 设置 API

## 安装 NodeJS

按照[这里的指南](https://github.com/nodesource/distributions)执行以下步骤。

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

## 安装节点模块

```bash
cd OPI-LC/brc20/api; npm install;
```

## 设置 API

运行 `initialise_api.py` 初始化 .env 配置

```sh
python3 initialise_api.py
```

## 运行 API

```sh
node api.js
```