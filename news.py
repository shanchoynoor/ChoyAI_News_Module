
import os
import requests
import feedparser
from datetime import datetime, timezone
from dotenv import load_dotenv
import re
import json
import time

# File to persist sent news links
SENT_NEWS_FILE = "sent_news.json"

def load_sent_news():
    if not os.path.exists(SENT_NEWS_FILE):
        return set()
    try:
        with open(SENT_NEWS_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_sent_news(sent_links):
    try:
        with open(SENT_NEWS_FILE, "w") as f:
            json.dump(list(sent_links), f)
    except Exception as e:
        print("Failed to save sent news:", e)

def escape_markdown_v2(text):
    """
    Escapes special characters for Telegram MarkdownV2.
    """
    if not text:
        return ""
    escape_chars = r'_*\[\]()~`>#+=|{}.!-'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FINNHUB_API = os.getenv("FINNHUB_API_KEY")

# ===================== UTILITIES =====================

def human_readable_number(num):
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000:
        return f"${num / 1_000_000_000_000:.2f}T"
    elif abs_num >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif abs_num >= 1_000:
        return f"${num / 1_000:.2f}K"
    else:
        return f"${num:.2f}"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=data)
    if not r.ok:
        print("Telegram send failed:", r.text)
    return r.ok

def get_hours_ago(published):
    try:
        if not published:
            return None
        # Accept time.struct_time or tuple
        if isinstance(published, time.struct_time):
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        elif isinstance(published, tuple):
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        else:
            return None
        now = datetime.now(timezone.utc)
        delta = now - dt
        # If published in the future or less than 1 minute ago, skip
        if delta.total_seconds() < 60 or delta.total_seconds() < 0:
            return None
        hours = int(delta.total_seconds() // 3600)
        if hours > 36:
            return None  # Too old
        return f"{hours}hr ago" if hours < 24 else f"{hours // 24}d ago"
    except Exception:
        return None

def fetch_rss_entries(sources, limit=5):
    entries = []
    sent_links = load_sent_news()
    new_links = set()
    for name, url in sources.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published_parsed = None

            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_parsed = entry.published_parsed
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_parsed = entry.updated_parsed
            else:
                for key in ['published', 'updated']:
                    try:
                        published_str = getattr(entry, key, None)
                        if published_str:
                            published_parsed = feedparser._parse_date(published_str)
                            if published_parsed:
                                break
                    except Exception:
                        continue

            title = getattr(entry, "title", "No Title").replace('[', '').replace(']', '')
            link = getattr(entry, "link", "#")

            published_str = get_hours_ago(published_parsed)
            # Only add if not already sent, has valid link, and valid publish date
            if link not in sent_links and link != "#" and published_str:
                entries.append({
                    "title": title,
                    "link": link,
                    "source": name,
                    "published": published_str
                })
                new_links.add(link)
            if len(entries) >= limit:
                # Save new sent links before returning
                sent_links.update(new_links)
                save_sent_news(sent_links)
                return entries
    # Save new sent links before returning
    sent_links.update(new_links)
    save_sent_news(sent_links)
    return entries

def format_news(title, entries):
    msg = f"*{title}:*\n"
    for idx, e in enumerate(entries, 1):
        msg += f"{idx}. [{e['title']}]({e['link']}) - {e['source']} ({e['published']})\n"
    return msg + "\n"

# ===================== NEWS CATEGORIES =====================

def get_local_news():
    bd_sources = {
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "The Daily Star": "https://www.thedailystar.net/frontpage/rss.xml",
        "BDNews24": "https://bdnews24.com/feed",
        "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
        "Jugantor": "https://www.jugantor.com/rss.xml",
        "Samakal": "https://samakal.com/rss.xml",
        "Jagonews24": "https://www.jagonews24.com/rss.xml",
        "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
        "Ittefaq": "https://www.ittefaq.com.bd/rss.xml",
        "Shomoy TV": "https://www.shomoynews.com/rss.xml",
        "Bangladesh Pratidin": "https://www.bd-pratidin.com/rss.xml"
    }
    return format_news("🇧🇩 LOCAL NEWS", fetch_rss_entries(bd_sources))

def get_global_news():
    global_sources = {
        "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss/edition.rss",
        "Reuters": "http://feeds.reuters.com/reuters/topNews",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "New York Post": "https://nypost.com/feed/",
        "The Guardian": "https://www.theguardian.com/world/rss",
        "The Washington Post": "https://feeds.washingtonpost.com/rss/world",
        "MSN": "https://www.msn.com/en-us/feed",
        "NBC News": "https://feeds.nbcnews.com/nbcnews/public/news",
        "The New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "The Economist": "https://www.economist.com/latest/rss.xml",
        "Axios": "https://www.axios.com/rss",
        "Fox News": "https://feeds.foxnews.com/foxnews/latest"
    }
    return format_news("🌍 GLOBAL NEWS", fetch_rss_entries(global_sources))

def get_tech_news():
    tech_sources = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss",
        "CNET": "https://www.cnet.com/rss/news/",
        "Social Media Today": "https://www.socialmediatoday.com/rss.xml",
        "Tech Times": "https://www.techtimes.com/rss/tech.xml",
        "Droid Life": "https://www.droid-life.com/feed/",
        "Live Science": "https://www.livescience.com/home/feed/site.xml"
    }
    return format_news("💻 TECH NEWS", fetch_rss_entries(tech_sources))

def get_sports_news():
    sports_sources = {
        "ESPN": "https://www.espn.com/espn/rss/news",
        "Sky Sports": "https://www.skysports.com/rss/12040",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "NBC Sports": "https://scores.nbcsports.com/rss/headlines.asp",
        "Yahoo Sports": "https://sports.yahoo.com/rss/",
        "The Guardian Sport": "https://www.theguardian.com/sport/rss"
    }
    return format_news("🏆 SPORTS NEWS", fetch_rss_entries(sports_sources))

def get_crypto_news():
    crypto_sources = {
        "Cointelegraph": "https://cointelegraph.com/rss",
        "Decrypt": "https://decrypt.co/feed",
        "Coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "Forbes Crypto": "https://www.forbes.com/crypto-blockchain/feed/",
        "Bloomberg Crypto": "https://www.bloomberg.com/crypto/rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "CNBC Finance": "https://www.cnbc.com/id/10001147/device/rss/rss.html"
    }
    return format_news("🪙  CRYPTO & FINANCE NEWS", fetch_rss_entries(crypto_sources))

# ===================== CRYPTO DATA =====================

def fetch_crypto_market():
    try:
        # Current market data
        url = "https://api.coingecko.com/api/v3/global"
        data = requests.get(url).json()["data"]
        market_cap = data["total_market_cap"]["usd"]
        volume = data["total_volume"]["usd"]
        market_change = data["market_cap_change_percentage_24h_usd"]

        # Estimate volume % change (based on market cap change, as a rough proxy)
        volume_yesterday = volume / (1 + market_change / 100)
        volume_change = ((volume - volume_yesterday) / volume_yesterday) * 100

        # Fear/Greed index
        fear_index = requests.get("https://api.alternative.me/fng/?limit=1").json()["data"][0]["value"]

        return (
            "*📊 CRYPTO MARKET:*\n"
            f"🔹 Market Cap (24h): {human_readable_number(market_cap)} ({market_change:+.2f}%)\n"
            f"🔹 Volume (24h): {human_readable_number(volume)} ({volume_change:+.2f}%)\n"
            f"😨 Fear/Greed Index: {fear_index}/100\n\n"
        )
    except Exception as e:
        return f"*📊 CRYPTO MARKET:*\nError: {escape_markdown_v2(str(e))}\n\n"

def fetch_big_cap_prices():
    ids = "bitcoin,ethereum,ripple,binancecoin,solana,tron,dogecoin,cardano"
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        data = requests.get(url, params=params).json()
        msg = "*Big Cap Crypto:*\n"
        for c in data:
            msg += f"{c['symbol'].upper()}: ${c['current_price']} ({c['price_change_percentage_24h']:+.2f}%)\n"
        return msg + "\n"
    except Exception as e:
        return f"*Big Cap Crypto:*\nError: {e}\n\n"

def fetch_top_movers():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        data = requests.get(url, params={
            "vs_currency": "usd", "order": "market_cap_desc", "per_page": 100
        }).json()

        gainers = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
        losers = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]

        msg = "*🔺 Crypto Top 5 Gainers:*\n"
        for i, c in enumerate(gainers, 1):
            symbol = escape_markdown_v2(c['symbol'].upper())
            price = c['current_price']
            change = c.get('price_change_percentage_24h', 0)
            msg += f"{i}. {symbol}: ${price:.2f} ({change:+.2f}%)\n"

        msg += "\n*🔻 Crypto Top 5 Losers:*\n"
        for i, c in enumerate(losers, 1):
            symbol = escape_markdown_v2(c['symbol'].upper())
            price = c['current_price']
            change = c.get('price_change_percentage_24h', 0)
            msg += f"{i}. {symbol}: ${price:.2f} ({change:+.2f}%)\n"

        return msg + "\n"
    except Exception as e:
        return f"*Top Movers Error:* {escape_markdown_v2(str(e))}\n\n"

# ===================== MAIN =====================

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"*🧠 6-Hourly Global Digest*\n_{now}_\n\n"
    msg += get_local_news()
    msg += get_global_news()
    msg += get_tech_news()
    msg += get_sports_news()
    msg += get_crypto_news()
    msg += fetch_crypto_market()
    msg += fetch_big_cap_prices()
    msg += fetch_top_movers()
    send_telegram(msg)

if __name__ == "__main__":
    main()
