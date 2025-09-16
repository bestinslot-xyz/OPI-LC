# BRC20 Docker Compose Installation Guide

You can use docker-compose to run the services. Make sure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed and then run:

> [!CAUTION]
> Make sure to set the password environment variables in the `.env` file before running the containers such as `DB_PASSWD`, `BRC20_PROG_RPC_SERVER_PASSWORD`, and `BRC20_PROG_RPC_SERVER_USER`.

```bash
docker compose up -d --build
```

To update the services and fetch the latest code, you'll need to recreate the containers, not just restart them. First, stop and remove the containers, then run the `up` command above again:

```bash
docker compose down
docker system prune
```

This will rebuild the images with the latest code from the repositories without losing your data, as the databases are stored in Docker volumes.

Docker compose setup exposes the BRC-20 API on port 8000 by default, and BRC2.0 API on port 18545 (modify the `docker-compose.yml` file to change the ports).
