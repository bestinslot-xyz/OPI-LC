# BRC20 Quick Ubuntu Installation Guide

For a quick setup, you can run the following commands on Ubuntu:

```bash
bash run.ubuntu.sh # This runs BRC2.0 and the indexer
bash run-api.ubuntu.sh # This runs the BRC20 API (optional)
```

The script will install dependencies, and use the values in `.env` file. You can modify it as needed.

To stop them, run:

```bash
bash stop.ubuntu.sh
bash stop-api.ubuntu.sh # (if you ran the api)
```
