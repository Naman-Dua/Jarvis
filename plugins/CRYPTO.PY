"""Cryptocurrency price plugin for Kora."""

import re

import requests


DESCRIPTION = "Fetch current crypto prices for Bitcoin, Ethereum, and Litecoin."

COINS = {
    "bitcoin": "bitcoin",
    "btc": "bitcoin",
    "ethereum": "ethereum",
    "eth": "ethereum",
    "litecoin": "litecoin",
    "ltc": "litecoin",
}

CRYPTO_PATTERN = re.compile(
    r"\b(?:crypto|cryptocurrency|bitcoin|btc|ethereum|eth|litecoin|ltc)\b",
    re.IGNORECASE,
)


def matches(text):
    return bool(CRYPTO_PATTERN.search(str(text)))


def _requested_coin_ids(text):
    lowered = str(text).lower()
    found = []
    for alias, coin_id in COINS.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered) and coin_id not in found:
            found.append(coin_id)
    return found or ["bitcoin", "ethereum", "litecoin"]


def handle_command(text):
    coin_ids = _requested_coin_ids(text)
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return {"action": "crypto_price", "reply": f"I could not fetch crypto prices right now: {exc}"}

    parts = []
    for coin_id in coin_ids:
        item = data.get(coin_id, {})
        price = item.get("usd")
        change = item.get("usd_24h_change")
        if price is None:
            continue
        if change is None:
            parts.append(f"{coin_id.title()}: ${price:,.2f}")
        else:
            parts.append(f"{coin_id.title()}: ${price:,.2f} ({change:+.2f}% 24h)")

    if not parts:
        return {"action": "crypto_price", "reply": "I could not find a price for that coin."}
    return {"action": "crypto_price", "reply": "Crypto prices: " + "; ".join(parts) + "."}
