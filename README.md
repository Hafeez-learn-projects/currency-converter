# Currency Converter CLI

A simple CLI tool to convert currencies, list available currencies, and view historical exchange rates.

## Features
- **convert** — Live exchange rate conversion between any two currencies
- **list** — Display all available currency codes and names
- **history** — View historical exchange rates for the past N days

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Convert 100 USD to SGD
python currency_converter.py convert --from USD --to SGD --amount 100

# List all available currencies
python currency_converter.py list

# Show 7-day history of USD to SGD
python currency_converter.py history --from USD --to SGD --days 7

# Show help
python currency_converter.py --help
```

## APIs Used
- [open.er-api.com](https://open.er-api.com) — live exchange rates (free, no API key)
- [frankfurter.app](https://api.frankfurter.app) — historical rates (free, no API key)

## Tech Stack
- Python 3.11+
- Click — CLI framework
- requests — HTTP client
- tabulate — formatted tables