# Crypto Exchange

A simulated crypto exchange built in python for a university assignment, which makes use of a client-server architecture

---

## Overview

Users connect as clients to the exchange server which allows them to create accounts, build portfolios, and buy/sell assets for their portfolio using funds which have been deposited into their crypto account wallet

---

## Architecture

- **Server** - manages accounts, portfolios, and transactions using a SQLite3 database
- **Clients** - connect to the server using sockets to interact with the exchange

---

## Features

- Account creation and login
- Ability to buy/sell assets
- Ability to view portfolio and balance

---

## Getting Started

### Download (Windows)
Download the latest .exe files from -

1. Run 'server.exe' first
2. Then run one or more of the client exes to connect to the server

### Run from source
```bash
python src/server/server.py
python src/clients/client_1.py
```

---

## Built With

- Python
- SQLite3
- Sockets & Threading

---

## Disclaimer

This is a simulated exchange built for educational purposes only. No real money or assets are involved
