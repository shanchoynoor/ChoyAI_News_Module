import os
import re
import json
import time
import requests
import feedparser
from datetime import datetime, timezone
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from user_logging import init_db, log_user_interaction
import threading
import logging

logging.basicConfig(level=logging.WARNING)

# File to persist sent news links
SENT_NEWS_FILE = "sent_news.json"

# ===================== SENT NEWS PERSISTENCE =====================
def load_sent_news():
    """Load sent news links from file."""
    if not os.path.exists(SENT_NEWS_FILE):
        return set()
    try:
        with open(SENT_NEWS_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_sent_news(sent_links):
    """Save sent news links to file."""
    try:
        with open(SENT_NEWS_FILE, "w") as f:
            json.dump(list(sent_links), f)
    except Exception as e:
        print("Failed to save sent news:", e)

# ===================== MARKDOWN ESCAPE =====================
def escape_markdown_v2(text):
    """Escapes special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    escape_chars = r'_\*\[\]()~`>#+=|{}.!-'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# ===================== ENVIRONMENT VARIABLES =====================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FINNHUB_API = os.getenv("FINNHUB_API_KEY")

# ===================== UTILITIES =====================
def human_readable_number(num):
    """Format large numbers with suffixes (K, M, B, T)."""
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

def send_telegram(msg, chat_id):
    """Send a message to a Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=data)
    if not r.ok:
        print("Telegram send failed:", r.text)
    return r.ok

def get_hours_ago(published):
    """Returns a string like 'Xhr ago' or 'Yd ago' for any valid date in the past."""
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
        days = int(hours // 24)
        if days > 0:
            return f"{days}d ago"
        elif hours > 0:
            return f"{hours}hr ago"
        else:
            minutes = int((delta.total_seconds() % 3600) // 60)
            return f"{minutes}min ago"
    except Exception:
        return None

# ===================== RSS FETCHING =====================
def fetch_rss_entries(sources, limit=5, max_per_source=3, max_age_hours=12):
    """
    Always return `limit` news entries per category.
    Strictly prefer the most recent news overall (from any source, max 3 per source).
    Only use older news if not enough recent items.
    """
    sent_links = load_sent_news()
    new_links = set()
    now = datetime.now(timezone.utc)
    min_timestamp = now.timestamp() - max_age_hours * 3600
    recent_entries = []
    older_entries = []

    def fetch_source(name_url):
        name, url = name_url
        results_recent = []
        results_older = []
        try:
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
                if not published_parsed:
                    continue
                published_dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                title = escape_markdown_v2(getattr(entry, "title", "No Title").replace('[', '').replace(']', ''))
                link = getattr(entry, "link", "#")
                if link in sent_links or link == "#":
                    continue
                published_str = get_hours_ago(published_parsed)
                if not published_str:
                    continue
                entry_obj = {
                    "title": title,
                    "link": link,
                    "source": escape_markdown_v2(name),
                    "published": published_str,
                    "timestamp": published_dt.timestamp()
                }
                if published_dt.timestamp() >= min_timestamp:
                    results_recent.append(entry_obj)
                else:
                    results_older.append(entry_obj)
        except Exception as e:
            print(f"Error fetching {name}: {e}")
        # Sort by recency
        results_recent.sort(key=lambda x: x["timestamp"], reverse=True)
        results_older.sort(key=lambda x: x["timestamp"], reverse=True)
        return (results_recent, results_older)

    # Fetch all feeds in parallel
    with ThreadPoolExecutor(max_workers=min(8, len(sources))) as executor:
        futures = [executor.submit(fetch_source, item) for item in sources.items()]
        for future in as_completed(futures):
            recents, olders = future.result()
            recent_entries.extend(recents)
            older_entries.extend(olders)

    # Sort all recent entries by recency
    recent_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    older_entries.sort(key=lambda x: x["timestamp"], reverse=True)

    # Pick up to limit, max max_per_source per source, from recent_entries
    picked = []
    per_source_count = {}
    for entry in recent_entries:
        count = per_source_count.get(entry["source"], 0)
        if count < max_per_source and entry not in picked:
            picked.append(entry)
            per_source_count[entry["source"]] = count + 1
        if len(picked) >= limit:
            break
    # If still not enough, fill with older news (beyond max_age_hours), still respecting max_per_source
    if len(picked) < limit:
        for entry in older_entries:
            count = per_source_count.get(entry["source"], 0)
            if count < max_per_source and entry not in picked:
                picked.append(entry)
                per_source_count[entry["source"]] = count + 1
            if len(picked) >= limit:
                break
    # Save sent links
    for entry in picked:
        new_links.add(entry["link"])
    sent_links.update(new_links)
    save_sent_news(sent_links)
    # Remove timestamp before returning
    for entry in picked:
        entry.pop("timestamp", None)
    return picked

# ===================== BANGLA FONT CONVERSION =====================
def to_bangla(text):
    """Placeholder for Bangla font conversion (returns text as is)."""
    return text

# ===================== NEWS FORMATTING =====================
def format_news(title, entries, bangla=False):
    """Format news entries for display."""
    msg = f"*{title}:*\n"
    for idx, e in enumerate(entries, 1):
        display_title = to_bangla(e['title']) if bangla else e['title']
        msg += f"{idx}. [{display_title}]({e['link']}) - {e['source']} ({e['published']})\n"
    return msg + "\n"

# ===================== DEEPSEEK AI SUMMARY =====================
def get_crypto_summary_with_deepseek(market_cap, market_cap_change, volume, volume_change, fear_greed, big_caps, gainers, losers, api_key):
    """Get crypto summary from DeepSeek AI."""
    prompt = (
        "Here is the latest crypto market data:\n"
        f"- Market Cap: {market_cap} ({market_cap_change})\n"
        f"- Volume: {volume} ({volume_change})\n"
        f"- Fear/Greed Index: {fear_greed}/100\n"
        f"- Big Cap Crypto: {big_caps}\n"
        f"- Top Gainers: {gainers}\n"
        f"- Top Losers: {losers}\n\n"
        "Write a short summary paragraph about the current crypto market status and predict if the market will be bullish or bearish tomorrow. Also, provide your confidence as a percentage (e.g., 75%) in your prediction. Be concise and insightful."
    )
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()

# ===================== NEWS CATEGORIES =====================
def get_local_news():
    """Fetch and format local Bangladeshi news."""
    bd_sources = {
        "Prothom Alo": "https://www.prothomalo.com/feed",
        "BDNews24": "https://bdnews24.com/feed",
        "Bangladesh Pratidin": "https://www.bd-pratidin.com/rss.xml",
        "Dhaka Tribune": "https://www.dhakatribune.com/articles.rss",
        "Jugantor": "https://www.jugantor.com/rss.xml",
        "Samakal": "https://samakal.com/rss.xml",
        "Jagonews24": "https://www.jagonews24.com/rss.xml",
        "Kaler Kantho": "https://www.kalerkantho.com/rss.xml",
        "Ittefaq": "https://www.ittefaq.com.bd/rss.xml",
        "Shomoy TV": "https://www.shomoynews.com/rss.xml",
    }
    return format_news("🇧🇩 LOCAL NEWS", fetch_rss_entries(bd_sources), bangla=True)

def get_global_news():
    """Fetch and format global news."""
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
    """Fetch and format technology news."""
    tech_sources = {
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss",
        "CNET": "https://www.cnet.com/rss/news/",
        "Social Media Today": "https://www.socialmediatoday.com/rss.xml",
        "Tech Times": "https://www.techtimes.com/rss/tech.xml",
        "Droid Life": "https://www.droid-life.com/feed/",
        "Live Science": "https://www.livescience.com/home/feed/site.xml",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "Engadget": "https://www.engadget.com/rss.xml",
        "Mashable": "https://mashable.com/feed",
        "Gizmodo": "https://gizmodo.com/rss",
        "ZDNet": "https://www.zdnet.com/news/rss.xml",
        "VentureBeat": "https://venturebeat.com/feed/",
        "The Next Web": "https://thenextweb.com/feed/",
        "TechRadar": "https://www.techradar.com/rss",
        "Android Authority": "https://www.androidauthority.com/feed",
        "MacRumors": "https://www.macrumors.com/macrumors.xml"
    }
    return format_news("🚀 TECH NEWS", fetch_rss_entries(tech_sources))

def get_sports_news():
    """Fetch and format sports news, prioritizing football, cricket, and celebrity news."""
    sports_sources = {
        "ESPN": "https://www.espn.com/espn/rss/news",
        "Sky Sports": "https://www.skysports.com/rss/12040",
        "BBC Sport": "http://feeds.bbci.co.uk/sport/rss.xml?edition=uk",
        "NBC Sports": "https://scores.nbcsports.com/rss/headlines.asp",
        "Yahoo Sports": "https://sports.yahoo.com/rss/",
        "The Guardian Sport": "https://www.theguardian.com/sport/rss",
        "CBS Sports": "https://www.cbssports.com/rss/headlines/",
        "Bleacher Report": "https://bleacherreport.com/articles/feed",
        "Sports Illustrated": "https://www.si.com/rss/si_topstories.rss",
        "Reuters Sports": "http://feeds.reuters.com/reuters/sportsNews",
        "Fox Sports": "https://www.foxsports.com/feedout/syndicatedContent?categoryId=0",
        "USA Today Sports": "https://rssfeeds.usatoday.com/usatodaycomsports-topstories",
        "Sporting News": "https://www.sportingnews.com/us/rss",
        "Goal.com": "https://www.goal.com/en/feeds/news?fmt=rss",
        "NBA": "https://www.nba.com/rss/nba_rss.xml",
        "NFL": "http://www.nfl.com/rss/rsslanding?searchString=home"
    }
    all_entries = fetch_rss_entries(sports_sources, limit=20)  # Fetch more to allow filtering
    football_keywords = [
        'football', 'soccer', 'fifa', 'uefa', 'champions league', 'premier league', 'la liga', 'bundesliga',
        'serie a', 'euro', 'world cup', 'goal', 'match', 'fixture', 'score', 'draw', 'win', 'penalty', 'final',
        'quarterfinal', 'semifinal', 'tournament', 'cup', 'league', 'ronaldo', 'messi', 'mbappe', 'haaland', 'bellingham',
        'live', 'vs', 'minute', 'kick-off', 'halftime', 'fulltime', 'result', 'update', 'lineup', 'stadium', 'group', 'knockout'
    ]
    cricket_keywords = [
        'cricket', 'icc', 't20', 'odi', 'test', 'ipl', 'bpl', 'psl', 'cpl', 'big bash', 'wicket', 'run', 'six', 'four',
        'over', 'innings', 'batsman', 'bowler', 'all-rounder', 'match', 'score', 'result', 'final', 'semi-final', 'quarter-final',
        'world cup', 'asia cup', 'shakib', 'kohli', 'rohit', 'babar', 'warner', 'root', 'williamson', 'smith', 'starc', 'rashid',
        'live', 'vs', 'innings break', 'powerplay', 'chase', 'target', 'runs', 'wickets', 'umpire', 'no-ball', 'wide', 'out', 'not out', 'review', 'super over', 'rain', 'dl method', 'points table', 'series', 'trophy', 'stadium', 'captain', 'squad', 'team', 'playing xi', 'update', 'result', 'scorecard', 'highlights', 'stream', 'broadcast', 'telecast', 'coverage', 'commentary', 'fixture', 'schedule', 'venue', 'fans', 'crowd', 'tickets', 'stadium', 'pitch', 'toss', 'bat', 'bowl', 'field', 'catch', 'drop', 'boundary', 'partnership', 'century', 'fifty', 'duck', 'debut', 'retire', 'injury', 'suspension', 'ban', 'controversy', 'award', 'record', 'milestone', 'legend', 'icon', 'star', 'hero', 'superstar', 'profile', 'tribute', 'obituary', 'death', 'birthday', 'marriage', 'divorce'
    ]
    def is_football(entry):
        title = entry['title'].lower()
        return any(kw in title for kw in football_keywords)
    def is_cricket(entry):
        title = entry['title'].lower()
        return any(kw in title for kw in cricket_keywords)
    football_news = [e for e in all_entries if is_football(e)]
    cricket_news = [e for e in all_entries if is_cricket(e) and e not in football_news]
    top_football = football_news[:2]
    top_cricket = cricket_news[:1]
    celebrity_keywords = [
        'star', 'legend', 'coach', 'manager', 'transfer', 'sign', 'deal', 'injury', 'scandal', 'award', 'record',
        'retire', 'comeback', 'controversy', 'ban', 'suspension', 'mvp', 'gold', 'silver', 'bronze', 'medal',
        'olympic', 'world record', 'breaking', 'exclusive', 'statement', 'announcement', 'trending', 'viral', 'hot',
        'player', 'celebrity', 'icon', 'hero', 'captain', 'superstar', 'profile', 'tribute', 'obituary', 'death', 'birthday', 'marriage', 'divorce'
    ]
    def is_celebrity(entry):
        title = entry['title'].lower()
        return any(kw in title for kw in celebrity_keywords)
    celebrity_news = [e for e in all_entries if is_celebrity(e) and e not in top_football and e not in top_cricket]
    top_celebrity = celebrity_news[:2]
    other_news = [e for e in all_entries if e not in top_football and e not in top_cricket and e not in top_celebrity]
    picked = top_football + top_cricket + top_celebrity
    if len(picked) < 5:
        picked += other_news[:5-len(picked)]
    return format_news("🏆 SPORTS NEWS", picked)

def get_crypto_news():
    """Fetch and format crypto and finance news."""
    crypto_sources = {
        "Cointelegraph": "https://cointelegraph.com/rss",
        "Decrypt": "https://decrypt.co/feed",
        "Coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "Forbes Crypto": "https://www.forbes.com/crypto-blockchain/feed/",
        "Bloomberg Crypto": "https://www.bloomberg.com/crypto/rss",
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "CNBC Finance": "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "Financial Times": "https://www.ft.com/?format=rss",
        "MarketWatch": "https://www.marketwatch.com/rss/topstories",
        "Bloomberg Markets": "https://www.bloomberg.com/feed/podcast/etf-report.xml",
        "The Block": "https://www.theblock.co/rss",
        "CryptoSlate": "https://cryptoslate.com/feed/",
        "Bitcoin Magazine": "https://bitcoinmagazine.com/.rss/full/",
        "Investing.com": "https://www.investing.com/rss/news_301.rss"
    }
    return format_news("🪙  FINANCE & CRYPTO NEWS", fetch_rss_entries(crypto_sources))

# ===================== CRYPTO DATA =====================
def fetch_crypto_market():
    """Fetch and format global crypto market data."""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        resp = requests.get(url)
        if not resp.ok:
            raise Exception("CoinGecko API error")
        data = resp.json().get("data", {})
        market_cap = data.get("total_market_cap", {}).get("usd")
        volume = data.get("total_volume", {}).get("usd")
        market_change = data.get("market_cap_change_percentage_24h_usd")
        if None in (market_cap, volume, market_change):
            raise Exception("Missing market data")
        volume_yesterday = volume / (1 + market_change / 100)
        volume_change = ((volume - volume_yesterday) / volume_yesterday) * 100
        # Fear/Greed index
        try:
            fg_resp = requests.get("https://api.alternative.me/fng/?limit=1")
            fg_data = fg_resp.json().get("data", [{}])
            fear_index = fg_data[0].get("value")
            if not fear_index or not str(fear_index).isdigit():
                fear_index = "N/A"
        except Exception:
            fear_index = "N/A"
        market_cap_str = human_readable_number(market_cap) if market_cap else "N/A"
        market_cap_change_str = f"{market_change:+.2f}%" if market_change is not None else "N/A"
        volume_str = human_readable_number(volume) if volume else "N/A"
        volume_change_str = f"{volume_change:+.2f}%" if volume_change is not None else "N/A"
        fear_greed_str = str(fear_index)
        return (market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, market_cap, market_change, volume, volume_change, fear_index)
    except Exception:
        return ("N/A", "N/A", "N/A", "N/A", "N/A", 0, 0, 0, 0, 0)

def fetch_big_cap_prices():
    """Fetch and format big cap crypto prices."""
    ids = "bitcoin,ethereum,ripple,binancecoin,solana,tron,dogecoin,cardano"
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        resp = requests.get(url, params=params)
        data = resp.json()
        if not isinstance(data, list):
            raise Exception("Invalid CoinGecko response")
        msg = "*💎 Crypto Big Cap:*\n"
        for c in data:
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            msg += f"{symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
        return msg + "\n"
    except Exception:
        return "*Crypto Big Cap:*\nN/A\n\n"

def fetch_top_movers():
    """Fetch and format top crypto gainers and losers."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100}
        resp = requests.get(url, params=params)
        data = resp.json()
        if not isinstance(data, list):
            raise Exception("Invalid CoinGecko response")
        gainers = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
        losers = sorted(data, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]
        msg = "*🔺 Crypto Top Gainers:*\n"
        for i, c in enumerate(gainers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
        msg += "\n*🔻 Crypto Top Losers:*\n"
        for i, c in enumerate(losers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
        return msg + "\n"
    except Exception:
        return "*Top Movers Error:* N/A\n\n"

def fetch_crypto_market_data():
    """
    Returns a tuple: (market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, market_cap, market_change, volume, volume_change, fear_greed)
    """
    try:
        url = "https://api.coingecko.com/api/v3/global"
        resp = requests.get(url)
        if not resp.ok:
            raise Exception("CoinGecko API error")
        data = resp.json().get("data", {})
        market_cap = data.get("total_market_cap", {}).get("usd")
        volume = data.get("total_volume", {}).get("usd")
        market_change = data.get("market_cap_change_percentage_24h_usd")
        if None in (market_cap, volume, market_change):
            raise Exception("Missing market data")
        volume_yesterday = volume / (1 + market_change / 100)
        volume_change = ((volume - volume_yesterday) / volume_yesterday) * 100
        # Fear/Greed index
        try:
            fg_resp = requests.get("https://api.alternative.me/fng/?limit=1")
            fg_data = fg_resp.json().get("data", [{}])
            fear_index = fg_data[0].get("value")
            if not fear_index or not str(fear_index).isdigit():
                fear_index = "N/A"
        except Exception:
            fear_index = "N/A"
        market_cap_str = human_readable_number(market_cap) if market_cap else "N/A"
        market_cap_change_str = f"{market_change:+.2f}%" if market_change is not None else "N/A"
        volume_str = human_readable_number(volume) if volume else "N/A"
        volume_change_str = f"{volume_change:+.2f}%" if volume_change is not None else "N/A"
        fear_greed_str = str(fear_index)
        return (market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, market_cap, market_change, volume, volume_change, fear_index)
    except Exception:
        return ("N/A", "N/A", "N/A", "N/A", "N/A", 0, 0, 0, 0, 0)

# ===================== WEATHER =====================
def get_dhaka_weather():
    try:
        api_key = os.getenv("WEATHERAPI_KEY")
        if not api_key:
            return "🌦️ Dhaka: Weather N/A"
        url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q=Dhaka&days=1&aqi=yes&alerts=no"
        resp = requests.get(url)
        data = resp.json()
        forecast = data["forecast"]["forecastday"][0]
        day = forecast["day"]
        temp_min = day["mintemp_c"]
        temp_max = day["maxtemp_c"]
        rain_chance = day.get("daily_chance_of_rain", 0)
        uv_val = day.get("uv", "N/A")
        aq = data.get("current", {}).get("air_quality", {})
        pm25 = aq.get("pm2_5")
        def pm25_to_aqi(pm25):
            breakpoints = [
                (0.0, 12.0, 0, 50),
                (12.1, 35.4, 51, 100),
                (35.5, 55.4, 101, 150),
                (55.5, 150.4, 151, 200),
                (150.5, 250.4, 201, 300),
                (250.5, 500.4, 301, 500)
            ]
            try:
                pm25 = float(pm25)
                for bp in breakpoints:
                    if bp[0] <= pm25 <= bp[1]:
                        Clow, Chigh, Ilow, Ihigh = bp[0], bp[1], bp[2], bp[3]
                        aqi = ((Ihigh - Ilow) / (Chigh - Clow)) * (pm25 - Clow) + Ilow
                        return round(aqi)
            except Exception:
                pass
            return None
        aqi_val = None
        if pm25 is not None:
            aqi_val = pm25_to_aqi(pm25)
        if aqi_val is None:
            epa_index = aq.get("us-epa-index")
            if epa_index is not None:
                epa_index = int(epa_index)
                if epa_index == 1:
                    aqi_val = 50
                elif epa_index == 2:
                    aqi_val = 100
                elif epa_index == 3:
                    aqi_val = 150
                elif epa_index == 4:
                    aqi_val = 200
                elif epa_index == 5:
                    aqi_val = 300
                elif epa_index == 6:
                    aqi_val = 400
        if aqi_val is not None:
            if aqi_val <= 50:
                aq_str = "Good"
            elif aqi_val <= 100:
                aq_str = "Moderate"
            elif aqi_val <= 150:
                aq_str = "Unhealthy for Sensitive Groups"
            elif aqi_val <= 200:
                aq_str = "Unhealthy"
            elif aqi_val <= 300:
                aq_str = "Very Unhealthy"
            else:
                aq_str = "Hazardous"
        else:
            aq_str = "N/A"
            aqi_val = "N/A"
        try:
            uv_val_num = float(uv_val)
            if uv_val_num < 3:
                uv_str = "Low"
            elif uv_val_num < 6:
                uv_str = "Moderate"
            elif uv_val_num < 8:
                uv_str = "High"
            elif uv_val_num < 11:
                uv_str = "Very High"
            else:
                uv_str = "Extreme"
        except Exception:
            uv_str = str(uv_val)
        rain_emoji = "🌧️ "
        aq_emoji = "🫧 "
        uv_emoji = "🔆 "
        lines = [
            f"🌦️ Dhaka: {temp_min:.1f}°C ~ {temp_max:.1f}°C",
            f"{rain_emoji}Rain: {rain_chance}%",
            f"{aq_emoji}AQI: {aq_str} ({aqi_val})",
            f"{uv_emoji}UV: {uv_str} ({uv_val})"
        ]
        return "\n".join(lines)
    except Exception:
        return "🌦️ Dhaka: Weather N/A"

# ===================== COINLIST LOADING =====================
COINLIST_PATH = os.path.join(os.path.dirname(__file__), "coinlist.json")
_coinlist_cache = None
_coinlist_lock = threading.Lock()
def load_coinlist():
    global _coinlist_cache
    with _coinlist_lock:
        if _coinlist_cache is not None:
            return _coinlist_cache
        try:
            with open(COINLIST_PATH, "r") as f:
                _coinlist_cache = json.load(f)
        except Exception as e:
            print(f"Failed to load coinlist.json: {e}")
            _coinlist_cache = []
        return _coinlist_cache

# Helper: symbol to id lookup (case-insensitive)
def get_coin_id_from_symbol(symbol):
    coinlist = load_coinlist()
    symbol = symbol.lower()
    for c in coinlist:
        if c.get("symbol", "").lower() == symbol:
            logging.debug(f"Found symbol: {symbol} -> {c['id']}")
            return c["id"], c["name"]
    logging.debug(f"Symbol not found: {symbol}")
    return None, None

# ===================== MAIN ENTRY =====================
def build_news_digest(return_msg=False, chat_id=None):
    """Main entry point: builds and prints or sends the news digest."""
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"*DAILY NEWS DIGEST*\n_{now}_\n\n"
    msg += get_local_news()
    msg += get_global_news()
    msg += get_tech_news()
    msg += get_sports_news()
    msg += get_crypto_news()
    msg += fetch_crypto_market()
    msg += fetch_big_cap_prices()
    msg += fetch_top_movers()

    if return_msg:
        return msg
    # Default: send to Telegram (for legacy usage)
    if chat_id is not None:
        send_telegram(msg, chat_id)
    else:
        print("No chat_id provided for sending news digest.")

def get_crypto_ai_summary():
    """Return only the AI crypto market summary (for /cryptostats)."""
    market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, _, _, _, _, _ = fetch_crypto_market_data()
    big_caps_msg = fetch_big_cap_prices()
    top_movers_msg = fetch_top_movers()
    DEEPSEEK_API = os.getenv("DEEPSEEK_API")
    if not DEEPSEEK_API:
        return "AI summary not available."
    if any(x == "N/A" for x in [market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str]):
        return "AI summary not available."
    # Compose the same prompt as in /news
    big_caps_str = big_caps_msg.replace('*💎 Crypto Big Cap:*\n', '').replace('\n', ', ').strip(', ')
    gainers_str = ''
    losers_str = ''
    # Extract gainers/losers from top_movers_msg
    lines = top_movers_msg.splitlines()
    gainers = []
    losers = []
    section = None
    for line in lines:
        if 'Top Gainers' in line:
            section = 'gainers'
            continue
        if 'Top Losers' in line:
            section = 'losers'
            continue
        if section == 'gainers' and line.strip():
            gainers.append(line.strip())
        if section == 'losers' and line.strip():
            losers.append(line.strip())
    gainers_str = ', '.join([l.split('. ',1)[-1] for l in gainers])
    losers_str = ', '.join([l.split('. ',1)[-1] for l in losers])
    ai_summary = get_crypto_summary_with_deepseek(
        market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, big_caps_str, gainers_str, losers_str, DEEPSEEK_API
    )
    ai_summary_clean = re.sub(r'^\s*prediction:.*$', '', ai_summary, flags=re.IGNORECASE | re.MULTILINE).strip()
    if ai_summary_clean and not ai_summary_clean.rstrip().endswith('.'):
        ai_summary_clean = ai_summary_clean.rstrip() + '.'
    # Add prediction line logic as in /news
    summary_lower = ai_summary.lower()
    accuracy_match = re.search(r'(\d{2,3})\s*%\s*(?:confidence|accuracy|probability)?', ai_summary)
    try:
        accuracy = int(accuracy_match.group(1)) if accuracy_match else 80
    except Exception:
        accuracy = 80
    if accuracy <= 60:
        prediction_line = "\nPrediction For tomorrow: 🤔 (No clear prediction)"
    elif "bullish" in summary_lower and accuracy > 60:
        prediction_line = f"\nPrediction For Tomorrow: BULLISH 🟢 ({accuracy}% probability)"
    elif "bearish" in summary_lower and accuracy > 60:
        prediction_line = f"\nPrediction For Tomorrow: BEARISH 🔴 ({accuracy}% probability)"
    else:
        prediction_line = "\nPrediction For Tomorrow: 🤔 (No clear prediction)"
    return f"*🤖 AI Market Summary:*\n{ai_summary_clean}\n{prediction_line}"

def get_coin_stats(symbol):
    """Return price and 24h % change for a given coin symbol (e.g. BTC, ETH)."""
    try:
        coin_id, coin_name = get_coin_id_from_symbol(symbol)
        if not coin_id:
            return f"Coin '{symbol.upper()}' not found in local list."
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": coin_id}
        data = requests.get(url, params=params).json()
        if not data:
            return f"Coin '{symbol.upper()}' not found."
        c = data[0]
        price = c['current_price']
        change = c.get('price_change_percentage_24h', 0)
        if price >= 1:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:.6f}"
        symbol_upper = c['symbol'].upper()
        arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
        change_str = f"({change:+.2f}%)"
        return f"{symbol_upper}: {price_str} {change_str}{arrow}"
    except Exception:
        return f"Error fetching data for '{symbol.upper()}'."

def get_coin_stats_ai(symbol):
    """Return price, 24h % change, and DeepSeek AI summary for a given coin symbol (e.g. BTC, ETH), in a professional, structured format."""
    try:
        coin_id, coin_name = get_coin_id_from_symbol(symbol)
        if not coin_id:
            return f"Coin '{symbol.upper()}' not found in local list."
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": coin_id}
        data = requests.get(url, params=params).json()
        if not data:
            return f"Coin '{symbol.upper()}' not found."
        c = data[0]
        price = c['current_price']
        change = c.get('price_change_percentage_24h', 0)
        high_24h = c.get('high_24h', 0)
        low_24h = c.get('low_24h', 0)
        market_cap = c.get('market_cap', 0)
        volume = c.get('total_volume', 0)
        symbol_upper = c['symbol'].upper()
        # Format price: 2 decimals if >=1, 6 decimals if <1
        if price >= 1:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:.6f}"
        change_str = f"({change:+.2f}%)"
        arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
        high_str = f"${high_24h:,.2f}" if high_24h >= 1 else f"${high_24h:.6f}"
        low_str = f"${low_24h:,.2f}" if low_24h >= 1 else f"${low_24h:.6f}"
        market_cap_str = human_readable_number(market_cap)
        volume_str = human_readable_number(volume)
        # Compose explicit prompt for DeepSeek AI
        prompt = (
            f"Coin: {symbol_upper}\n"
            f"Current Price: {price_str} {change_str}{arrow}\n"
            f"24h High: {high_str}\n"
            f"24h Low: {low_str}\n"
            f"Market Cap: {market_cap_str}\n"
            f"24h Volume: {volume_str}\n"
            "\n"
            "Write a concise, professional summary of the current market, technicals, and sentiment for this coin, using the data above. "
            "Format your answer in these sections (use the exact section headers):\n"
            "Summary: [1-2 sentences about price, range, cap, volume, and sentiment]\n"
            "Key Levels: [List resistance/support, e.g. Resistance: $X (24h high), Support: $Y (24h low)]\n"
            "Sentiment: [Short, clear sentiment line]\n"
            "Technicals: [Short-term trend, e.g. Neutral, Bullish, Bearish]\n"
            "Prediction For Tomorrow: [BULLISH/BEARISH/NEUTRAL/NO CLEAR PREDICTION] ([probability% if possible])\n"
            "Do not include extra text, disclaimers, or markdown."
        )
        DEEPSEEK_API = os.getenv("DEEPSEEK_API")
        if not DEEPSEEK_API:
            ai_summary = "AI summary not available."
        else:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {DEEPSEEK_API}"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 180,
                "temperature": 0.7
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                ai_summary = response.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                ai_summary = "AI summary not available."
        # Post-process to enforce format
        import re
        def extract_section(text, header):
            pat = rf"{header}:(.*?)(?=\n[A-Z][a-zA-Z ]+:|$)"
            m = re.search(pat, text, re.DOTALL)
            return m.group(1).strip() if m else None
        summary = extract_section(ai_summary, "Summary")
        key_levels = extract_section(ai_summary, "Key Levels")
        sentiment = extract_section(ai_summary, "Sentiment")
        technicals = extract_section(ai_summary, "Technicals")
        prediction = extract_section(ai_summary, "Prediction For Tomorrow")
        # Fallbacks if missing
        if not summary:
            summary = f"{symbol_upper} is trading at {price_str} {change_str}{arrow}, 24h range {low_str} - {high_str}. Market cap: {market_cap_str}, 24h volume: {volume_str}."
        # --- Key Levels formatting ---
        # Always print Resistance and Support on separate lines, with dash
        if key_levels:
            # Try to extract resistance/support from AI output, else fallback
            res = re.search(r'Resist[a-zA-Z]*:?\s*([$\d.,]+).*?(24h high)?', key_levels, re.IGNORECASE)
            sup = re.search(r'Support:?\s*([$\d.,]+).*?(24h low)?', key_levels, re.IGNORECASE)
            res_val = res.group(1) if res else high_str
            sup_val = sup.group(1) if sup else low_str
            key_levels_fmt = f"- Resistance: {res_val} (24h high)\n- Support: {sup_val} (24h low)"
        else:
            key_levels_fmt = f"- Resistance: {high_str} (24h high)\n- Support: {low_str} (24h low)"
        if not sentiment:
            sentiment = "Mixed."
        if not technicals:
            technicals = "Neutral."
        # Prediction line logic
        pred_line = prediction if prediction else "🤔 (No clear prediction)"
        # Try to extract probability and trend
        pred_prob = re.search(r'(\d{2,3})\s*%.*', pred_line)
        pred_trend = None
        if any(x in pred_line.lower() for x in ["bullish", "bearish", "neutral"]):
            if "bullish" in pred_line.lower():
                pred_trend = "BULLISH 🟢"
            elif "bearish" in pred_line.lower():
                pred_trend = "BEARISH 🔴"
            elif "neutral" in pred_line.lower():
                pred_trend = "NEUTRAL 🟡"
        else:
            pred_trend = "🤔 (No clear prediction)"
        if pred_prob and pred_trend and pred_trend != "🤔 (No clear prediction)":
            pred_line = f"{pred_trend} ({pred_prob.group(1)}% probability)"
        elif pred_trend:
            pred_line = pred_trend
        else:
            pred_line = "🤔 (No clear prediction)"
        # Compose final message
        msg = (
            f"Price: {symbol_upper} {price_str} {change_str}{arrow}\n"
            f"Summary: {summary}\n\n"
            f"Key Levels:\n{key_levels_fmt}\n\n"
            f"Sentiment: {sentiment}\n\n"
            f"Technicals: {technicals}\n\n"
            f"Prediction For Tomorrow: {pred_line}"
        )
        return msg
    except Exception:
        return f"Error fetching data for '{symbol.upper()}'."

def clean_ai_summary(summary):
    # Remove HTML tags
    summary = re.sub(r'<[^>]+>', '', summary)
    return summary

def format_ai_prediction(summary):
    # Find prediction line and probability
    match = re.search(r'Prediction For Tomorrow: (.+?) \((\d{2,3})% (confidence|probability)\)', summary, re.IGNORECASE)
    if match:
        trend = match.group(1).strip().upper()
        percent = int(match.group(2))
        if percent > 60 and ("BULLISH" in trend or "BEARISH" in trend):
            new_line = f"Prediction For Tomorrow: {trend} ({percent}% Probability)"
        else:
            new_line = "Prediction For Tomorrow: CONSOLIDATION"
        summary = re.sub(r'Prediction For Tomorrow: .+?\(\d{2,3}% (confidence|probability)\)', new_line, summary, flags=re.IGNORECASE)
    else:
        # If not matching, just replace 'confidence' with 'Probability' if present
        summary = re.sub(r'(\d{2,3})% confidence', r'\1% Probability', summary, flags=re.IGNORECASE)
    return summary

def get_help_text():
    return (
        "*ChoyNewsBot Commands:*\n"
        "/news - Get the full daily news digest\n"
        "/cryptostats - Get only the crypto AI market summary\n"
        "/weather - Get Dhaka weather\n"
        "/<coin> - Get price and 24h change for a coin (e.g. /btc, /eth, /doge)\n"
        "/<coin>stats - Get price, 24h change, and AI summary (e.g. /btcstats)\n"
        "/help - Show this help message\n"
    )

# --- Telegram polling bot ---
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    resp = requests.get(url, params=params)
    return resp.json().get("result", [])

def handle_updates(updates):
    for update in updates:
        message = update.get("message")
        if not message:
            continue
        chat_id = message["chat"]["id"]
        user = message["from"]
        user_id = user.get("id")
        username = user.get("username")
        first_name = user.get("first_name")
        last_name = user.get("last_name")
        # Log user interaction
        log_user_interaction(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            message_type=message.get("text", "other"),
            location=str(message.get("location")) if message.get("location") else None
        )
        text = message.get("text", "").lower().strip()
        logging.debug(f"Received text: {text}")
        # Welcome message for new users (first interaction)
        if message.get("new_chat_members") or text in ["/start"]:
            send_telegram("Welcome to ChoyNewsBot!", chat_id)
            send_telegram(get_help_text(), chat_id)
            continue
        if text == "/help":
            send_telegram(get_help_text(), chat_id)
            continue
        if text == "/cryptostats":
            send_telegram(get_crypto_ai_summary(), chat_id)
            continue
        if text == "/weather":
            send_telegram(get_dhaka_weather(), chat_id)
            continue
        if text in ["/news"]:
            send_telegram("Loading latest news...", chat_id)
            # Build and send the full digest using build_news_digest
            build_news_digest(return_msg=False, chat_id=chat_id)
            continue
        # --- Coin stats handlers ---
        # /[coin]stats (e.g. /btcstats)
        if text.startswith("/") and text.endswith("stats") and len(text) > 6:
            symbol = text[1:-5]  # remove leading / and trailing stats
            if symbol:
                reply = get_coin_stats_ai(symbol)
                send_telegram(reply, chat_id)
                continue
        # /[coin] (e.g. /btc)
        if text.startswith("/") and len(text) > 1 and text[1:].isalpha():
            symbol = text[1:]
            reply = get_coin_stats(symbol)
            send_telegram(reply, chat_id)
            continue
def main():
    init_db()
    print("Bot started. Listening for messages...")
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if updates:
            handle_updates(updates)
            last_update_id = updates[-1]["update_id"] + 1
        time.sleep(2)

if __name__ == "__main__":
    main()
