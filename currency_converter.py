#!/usr/bin/env python3
"""Currency Converter CLI - convert, list, history commands and rate alerts."""

import click
import requests
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from tabulate import tabulate

API_BASE = "https://open.er-api.com/v6"
ALERT_FILE = Path.home() / ".currency_alerts.json"


def handle_error(r: dict) -> bool:
    """Return True if response has an error, print it."""
    if r.get("result") != "success":
        msg = r.get("result", "Unknown error")
        click.echo(f"Error: {msg}", err=True)
        return True
    return False


def load_alerts() -> dict:
    """Load saved rate alerts from disk."""
    if ALERT_FILE.exists():
        with open(ALERT_FILE) as f:
            return json.load(f)
    return {}


def save_alerts(alerts: dict):
    """Save rate alerts to disk."""
    with open(ALERT_FILE, "w") as f:
        json.dump(alerts, f, indent=2)


@click.group()
@click.version_option(version="1.1.0")
def cli():
    """Currency Converter CLI - convert, list, track exchange rates and set alerts."""
    pass


@cli.command()
@click.option("--from", "frm", default="USD", help="Source currency code (e.g. USD)")
@click.option("--to", "to", required=True, help="Target currency code (e.g. SGD)")
@click.option("--amount", type=float, default=1.0, help="Amount to convert")
def convert(frm, to, amount):
    """Convert an amount from one currency to another."""
    frm = frm.upper()
    to = to.upper()
    click.echo(f"Fetching exchange rate for {frm} -> {to}...")
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
    click.echo(f"
{amount} {frm} = {result:.2f} {to}")
    click.echo(f"Rate: 1 {frm} = {rate:.4f} {to} (updated {updated})")

    # Check alerts
    alerts = load_alerts()
    pair = f"{frm}_{to}"
    if pair in alerts:
        target_rate = alerts[pair]["rate"]
        direction = alerts[pair]["direction"]
        if direction == "above" and rate >= target_rate:
            click.echo(f"
[BELL] ALERT: {frm}/{to} rate ({rate:.4f}) is ABOVE your target ({target_rate:.4f})!")
        elif direction == "below" and rate <= target_rate:
            click.echo(f"
[BELL] ALERT: {frm}/{to} rate ({rate:.4f}) is BELOW your target ({target_rate:.4f})!")
        elif direction == "either":
            click.echo(f"
[BELL] ALERT: {frm}/{to} rate ({rate:.4f}) hit your target ({target_rate:.4f})!")


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
        "ILS": "Israeli Shekel", "EGP": "Egyptian Pound", "PKR": "Pakistani Rupee",
        "BDT": "Bangladeshi Taka", "LKR": "Sri Lankan Rupee", "NPR": "Nepalese Rupee",
        "MMK": "Myanmar Kyat", "KHR": "Cambodian Riel", "LAK": "Lao Kip",
        "BND": "Brunei Dollar", "TWD": "Taiwan Dollar", "RON": "Romanian Leu",
        "BGN": "Bulgarian Lev", "HRK": "Croatian Kuna", "ISK": "Icelandic Krona",
        "UAH": "Ukrainian Hryvnia", "NGN": "Nigerian Naira", "KES": "Kenyan Shilling",
        "GHS": "Ghanaian Cedi", "TZS": "Tanzanian Shilling", "UGX": "Ugandan Shilling",
        "MAD": "Moroccan Dirham", "TND": "Tunisian Dinar", "DZD": "Algerian Dinar",
        "LBP": "Lebanese Pound", "JOD": "Jordanian Dinar", "IQD": "Iraqi Dinar",
        "KWD": "Kuwaiti Dinar", "BHD": "Bahraini Dinar", "OMR": "Omani Rial",
        "QAR": "Qatari Riyal", "CLP": "Chilean Peso", "COP": "Colombian Peso",
        "PEN": "Peruvian Sol", "ARS": "Argentine Peso", "UYU": "Uruguayan Peso",
        "VES": "Venezuelan Bolivar",
    }
    table = []
    for code in sorted(rates.keys()):
        name = names.get(code, code)
        table.append([code, name])
    click.echo(f"
{len(table)} currencies available:
")
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

    click.echo(f"Fetching {days}-day history for {frm} -> {to}...")
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
        click.echo(f"
Historical rates: 1 {frm} = X {to}
")
        click.echo(tabulate(table, headers=["Date", f"Rate ({to})"], tablefmt="grid"))


@cli.command()
@click.option("--from", "frm", default="USD", help="Base currency code")
@click.option("--to", "to", required=True, help="Target currency code")
@click.option("--rate", type=float, required=True, help="Target exchange rate")
@click.option("--direction", type=click.Choice(["above", "below", "either"]), default="either",
              help="Trigger alert when rate goes above, below, or either side of target")
@click.option("--remove", is_flag=True, help="Remove alert for this currency pair")
def alert(frm, to, rate, direction, remove):
    """Set rate alerts - get notified when a rate hits your target."""
    frm = frm.upper()
    to = to.upper()
    pair = f"{frm}_{to}"
    alerts = load_alerts()

    if remove:
        if pair in alerts:
            del alerts[pair]
            save_alerts(alerts)
            click.echo(f"Alert removed for {frm}/{to}")
        else:
            click.echo(f"No alert found for {frm}/{to}")
        return

    alerts[pair] = {"rate": rate, "direction": direction}
    save_alerts(alerts)
    click.echo(f"Alert set: {frm}/{to} - notify when rate goes {direction} {rate:.4f}")
    click.echo(f"   Run 'currency-converter convert --from {frm} --to {to}' to check current rate")


@cli.command()
def alerts_list():
    """List all active rate alerts."""
    alerts = load_alerts()
    if not alerts:
        click.echo("No rate alerts set. Use: currency-converter alert --from USD --to SGD --rate 1.35 --direction above")
        return

    table = []
    for pair, info in sorted(alerts.items()):
        frm, to = pair.split("_")
        try:
            r = requests.get(f"{API_BASE}/latest/{frm}", timeout=10).json()
            current = r.get("rates", {}).get(to, None)
            if current:
                diff = ((current - info["rate"]) / info["rate"]) * 100
                diff_str = f"{diff:+.2f}%"
            else:
                diff_str = "N/A"
        except Exception as e:
            current = "?"
            diff_str = "?"

        table.append([pair, f"{info['rate']:.4f}", info["direction"], f"{current if isinstance(current, str) else f'{current:.4f}'}", diff_str])

    click.echo(f"
{len(table)} active alerts:
")
    click.echo(tabulate(table, headers=["Pair", "Target", "Direction", "Current", "Diff %"], tablefmt="grid"))


if __name__ == "__main__":
    cli()
