#!/usr/bin/env python3
"""Currency Converter CLI — convert, list, and history commands."""

import click
import requests
import sys
from datetime import datetime, timedelta
from tabulate import tabulate

API_BASE = "https://open.er-api.com/v6"


def handle_error(r: dict) -> bool:
    """Return True if response has an error, print it."""
    if r.get("result") != "success":
        msg = r.get("result", "Unknown error")
        click.echo(f"Error: {msg}", err=True)
        return True
    return False


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Currency Converter CLI — convert, list, and track exchange rate history."""
    pass


@cli.command()
@click.option("--from", "frm", default="USD", help="Source currency code (e.g. USD)")
@click.option("--to", "to", required=True, help="Target currency code (e.g. SGD)")
@click.option("--amount", type=float, default=1.0, help="Amount to convert")
def convert(frm, to, amount):
    """Convert an amount from one currency to another."""
    frm = frm.upper()
    to = to.upper()
    click.echo(f"Fetching exchange rate for {frm} → {to}...")
    r = requests.get(f"{API_BASE}/latest/{frm}", timeout=10).json()

    if handle_error(r):
        sys.exit(1)

    rates = r.get("rates", {})
    rate = rates.get(to)
    if rate is None:
        click.echo(f"Error: Currency {to} not found", err=True)
        sys.exit(1)

    result = rate * amount
    updated = r.get("time_last_update_utc", "unknown")
    click.echo(f"\n{amount} {frm} = {result:.2f} {to}")
    click.echo(f"Rate: 1 {frm} = {rate:.4f} {to} (updated {updated})")


@cli.command()
@click.option("--base", default="USD", help="Base currency code")
def list(base):
    """List all available currency codes and their names."""
    base = base.upper()
    click.echo(f"Fetching currency list with base {base}...")
    r = requests.get(f"{API_BASE}/latest/{base}", timeout=10).json()

    if handle_error(r):
        sys.exit(1)

    rates = r.get("rates", {})
    # Common currency names (fallback for display)
    names = {
        "USD": "US Dollar", "EUR": "Euro", "GBP": "British Pound", "JPY": "Japanese Yen",
        "AUD": "Australian Dollar", "CAD": "Canadian Dollar", "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan", "INR": "Indian Rupee", "SGD": "Singapore Dollar",
        "MYR": "Malaysian Ringgit", "THB": "Thai Baht", "IDR": "Indonesian Rupiah",
        "VND": "Vietnamese Dong", "PHP": "Philippine Peso", "KRW": "South Korean Won",
        "NZD": "New Zealand Dollar", "HKD": "Hong Kong Dollar", "AED": "UAE Dirham",
        "SAR": "Saudi Riyal", "MXN": "Mexican Peso", "BRL": "Brazilian Real",
        "ZAR": "South African Rand", "RUB": "Russian Ruble", "TRY": "Turkish Lira",
        "SEK": "Swedish Krona", "NOK": "Norwegian Krone", "DKK": "Danish Krone",
        "PLN": "Polish Zloty", "CZK": "Czech Koruna", "HUF": "Hungarian Forint",
    }
    table = []
    for code in sorted(rates.keys()):
        name = names.get(code, code)
        table.append([code, name])
    click.echo(f"\n{len(table)} currencies available:\n")
    click.echo(tabulate(table, headers=["Code", "Name"], tablefmt="grid"))


@cli.command()
@click.option("--from", "frm", default="USD", help="Base currency code")
@click.option("--to", "to", required=True, help="Target currency code")
@click.option("--days", default=7, type=int, help="Number of past days to show")
def history(frm, to, days):
    """Show historical exchange rates for the past N days."""
    from datetime import date, timedelta

    frm = frm.upper()
    to = to.upper()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # frankfurter.app provides free historical rates (no API key needed)
    click.echo(f"Fetching {days}-day history for {frm} → {to}...")
    url = f"https://api.frankfurter.app/{start_date}..{end_date}"
    params = {"from": frm, "to": to}

    try:
        r = requests.get(url, params=params, timeout=15).json()
    except Exception as e:
        click.echo(f"Error: Could not reach historical rates API ({e})", err=True)
        sys.exit(1)

    if "error" in r:
        click.echo(f"Error: {r['error'].get('message', 'API error')}", err=True)
        sys.exit(1)

    rates_data = r.get("rates", {})
    table = []
    for d, day_rates in sorted(rates_data.items()):
        rate = day_rates.get(to)
        if rate is not None:
            table.append([d, f"{rate:.4f}"])
        else:
            table.append([d, "N/A"])

    if not table:
        click.echo("No historical data found.")
    else:
        click.echo(f"\nHistorical rates: 1 {frm} = X {to}\n")
        click.echo(tabulate(table, headers=["Date", f"Rate ({to})"], tablefmt="grid"))


if __name__ == "__main__":
    cli()