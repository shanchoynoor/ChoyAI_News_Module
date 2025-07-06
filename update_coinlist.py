import requests
import json

coins = requests.get("https://api.coingecko.com/api/v3/coins/markets", params={
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
    "page": 1
}).json()

coins += requests.get("https://api.coingecko.com/api/v3/coins/markets", params={
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 250,
    "page": 2
}).json()

coinlist = [
    {"symbol": c["symbol"], "id": c["id"], "name": c["name"]}
    for c in coins
]

with open("coinlist.json", "w") as f:
    json.dump(coinlist, f, indent=2)

    #latest commit