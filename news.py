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

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for troubleshooting

# Set API key globals early so helpers can use them
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

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
    logging.debug(f"Sending message to chat_id={chat_id}: {msg[:100]}...")
    r = requests.post(url, data=data)
    if not r.ok:
        print("Telegram send failed:", r.text)
        logging.error(f"Telegram send failed: {r.text}")
    else:
        logging.debug(f"Telegram send succeeded: {r.text}")
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
        big_caps_list = []
        for c in data:
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            big_caps_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        return msg + "\n", ", ".join(big_caps_list)
    except Exception:
        return "*Crypto Big Cap:*\nN/A\n\n", "N/A"

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
        gainers_list = []
        for i, c in enumerate(gainers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            gainers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        msg += "\n*🔻 Crypto Top Losers:*\n"
        losers_list = []
        for i, c in enumerate(losers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            losers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        return msg + "\n", ", ".join(gainers_list), ", ".join(losers_list)
    except Exception:
        return "*Top Movers Error:* N/A\n\n", "N/A", "N/A"

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

def fetch_big_cap_prices_data():
    ids = "bitcoin,ethereum,ripple,binancecoin,solana,tron,dogecoin,cardano"
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {"vs_currency": "usd", "ids": ids}
        resp = requests.get(url, params=params)
        data = resp.json()
        if not isinstance(data, list):
            raise Exception("Invalid CoinGecko response")
        msg = "*💎 Crypto Big Cap:*\n"
        big_caps_list = []
        for c in data:
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            big_caps_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        return msg + "\n", ", ".join(big_caps_list)
    except Exception:
        return "*Crypto Big Cap:*\nN/A\n\n", "N/A"

def fetch_top_movers_data():
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
        gainers_list = []
        for i, c in enumerate(gainers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            gainers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        msg += "\n*🔻 Crypto Top Losers:*\n"
        losers_list = []
        for i, c in enumerate(losers, 1):
            symbol = c.get('symbol', '').upper()
            price = c.get('current_price')
            change = c.get('price_change_percentage_24h', 0)
            arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
            if price is None:
                price_str = "N/A"
            elif price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"
            msg += f"{i}. {symbol}: {price_str} ({change:+.2f}%)" + arrow + "\n"
            losers_list.append(f"{symbol}: {price_str} ({change:+.2f}%)" + arrow)
        return msg + "\n", ", ".join(gainers_list), ", ".join(losers_list)
    except Exception:
        return "*Top Movers Error:* N/A\n\n", "N/A", "N/A"

def get_coin_id_from_symbol(symbol):
    """Return CoinGecko coin id for a given symbol (case-insensitive), or None if not found."""
    symbol = symbol.lower()
    for entry in load_coinlist():
        if entry.get("symbol", "").lower() == symbol:
            return entry.get("id"), entry.get("name")
    return None, None

def get_asset_stats(symbol, asset_type="crypto", ai_summary=True):
    """Unified handler for /coin, /coinstats, /stock, /forex commands using Twelve Data."""
    base_msg = fetch_twelvedata_stats(symbol, asset_type)
    if not ai_summary:
        return base_msg
    # Compose prompt for DeepSeek AI
    prompt = (
        f"Asset: {symbol.upper()}\n"
        f"{base_msg}\n"
        "Give a short summary of the current market, technicals, and sentiment for this asset. "
        "Include a forecast for the next 24h (bullish/bearish/neutral), and mention key resistance/support levels if possible. "
        "Be concise and insightful."
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
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            ai_summary = response.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            ai_summary = "AI summary not available."
    import re
    ai_summary_clean = re.sub(r'^#+\\s*'+symbol.upper()+r'.*$', '', ai_summary, flags=re.IGNORECASE | re.MULTILINE).strip()
    if ai_summary_clean and not ai_summary_clean.rstrip().endswith('.'):
        ai_summary_clean = ai_summary_clean.rstrip() + '.'
    # --- Prediction extraction ---
    pred = 'N/A'
    pred_emoji = '🤔'
    pred_map = {
        'buy': '🟢 Buy',
        'hold': '🟠 Hold',
        'sell': '🔴 Sell',
    }
    pred_line = ''
    pred_match = re.search(r'\\b(buy|hold|sell)\\b', ai_summary.lower())
    if pred_match:
        pred = pred_map.get(pred_match.group(1), '🤔')
        pred_line = f"Prediction (24hr): {pred}"
    else:
        if 'bullish' in ai_summary.lower():
            pred_line = "Prediction (24hr): 🟢 Buy"
        elif 'bearish' in ai_summary.lower():
            pred_line = "Prediction (24hr): 🔴 Sell"
        elif 'neutral' in ai_summary.lower():
            pred_line = "Prediction (24hr): 🟠 Hold"
        else:
            pred_line = "Prediction (24hr): 🤔"
    return f"{base_msg}\nMarket Summary: {ai_summary_clean}\n\n{pred_line}"

# ===================== HELPER AND PLACEHOLDER DEFINITIONS =====================
def load_coinlist():
    global _coinlist_cache
    if '_coinlist_cache' in globals() and _coinlist_cache is not None:
        return _coinlist_cache
    try:
        with open("coinlist.json", "r") as f:
            _coinlist_cache = json.load(f)
    except Exception:
        _coinlist_cache = []
    return _coinlist_cache

def fetch_twelvedata_stats(symbol, asset_type="crypto"):
    if not TWELVE_DATA_API_KEY:
        return f"Twelve Data API key not set."
    base_url = "https://api.twelvedata.com"
    params = {"symbol": symbol.upper(), "apikey": TWELVE_DATA_API_KEY}
    if asset_type == "crypto":
        params["exchange"] = "BINANCE"
        params["interval"] = "1day"
    try:
        price_url = f"{base_url}/price"
        price_resp = requests.get(price_url, params=params, timeout=10)
        price_data = price_resp.json()
        price = float(price_data.get("price"))
    except Exception:
        price = None
    try:
        quote_url = f"{base_url}/quote"
        quote_resp = requests.get(quote_url, params=params, timeout=10)
        quote_data = quote_resp.json()
        change = float(quote_data.get("percent_change", 0))
        high_24h = float(quote_data.get("high", 0))
        low_24h = float(quote_data.get("low", 0))
    except Exception:
        change = 0
        high_24h = low_24h = 0
    arrow = ' ▲' if change > 0 else (' ▼' if change < 0 else '')
    price_str = f"${price:,.2f}" if price and price >= 1 else (f"${price:.6f}" if price else "N/A")
    change_str = f"({change:+.2f}%)"
    try:
        rsi_url = f"{base_url}/rsi"
        rsi_params = params.copy()
        rsi_params["interval"] = "1day"
        rsi_params["time_period"] = 14
        rsi_resp = requests.get(rsi_url, params=rsi_params, timeout=10)
        rsi_data = rsi_resp.json()
        rsi_val = list(rsi_data.get("values", [{}]))[0].get("rsi", "N/A")
    except Exception:
        rsi_val = "N/A"
    try:
        ma_url = f"{base_url}/ma"
        ma_params = params.copy()
        ma_params["interval"] = "1day"
        ma_params["time_period"] = 30
        ma_params["series_type"] = "close"
        ma_resp = requests.get(ma_url, params=ma_params, timeout=10)
        ma_data = ma_resp.json()
        ma30_val = list(ma_data.get("values", [{}]))[0].get("ma", "N/A")
        if ma30_val != "N/A":
            ma30_val = float(ma30_val)
            ma30_val = f"${ma30_val:,.2f}" if ma30_val >= 1 else f"${ma30_val:.6f}"
    except Exception:
        ma30_val = "N/A"
    try:
        hist_url = f"{base_url}/time_series"
        hist_params = params.copy()
        hist_params["interval"] = "1day"
        hist_params["outputsize"] = 365
        hist_resp = requests.get(hist_url, params=hist_params, timeout=10)
        hist_data = hist_resp.json()
        closes = [float(x["close"]) for x in hist_data.get("values", []) if "close" in x]
        if closes:
            min_52w = min(closes)
            max_52w = max(closes)
            range_52w = f"${min_52w:,.2f} ~ ${max_52w:,.2f}" if max_52w >= 1 else f"${min_52w:.6f} ~ ${max_52w:.6f}"
        else:
            range_52w = "N/A"
    except Exception:
        range_52w = "N/A"
    support = f"${low_24h:,.2f}" if low_24h else "N/A"
    resistance = f"${high_24h:,.2f}" if high_24h else "N/A"
    msg = (
        f"Price: {symbol.upper()} {price_str} {change_str}{arrow}\n"
        f"Technicals:\n- Support: {support}\n- Resistance: {resistance}\n- RSI: {rsi_val}\n- MA30 (moving average): {ma30_val}\n- Price Range (52w): {range_52w}\n"
    )
    return msg

def get_help_text():
    logging.debug("get_help_text called")
    return (
        """*ChoyNewsBot Help:*
/start - Welcome message
/help - Show this help message
/support - Contact developer
/news - Daily news digest
/cryptostats - Crypto market summary
/weather - Dhaka weather
/[symbol] - Asset stats (e.g. /btc, /aapl, /eurusd)
/[symbol]stats - Asset stats + AI summary (e.g. /btcstats, /aaplstats)
"""
    )

def get_support_text():
    logging.debug("get_support_text called")
    return (
        """*Support:*
[Contact Developer](https://t.me/shanchoy)
Email: shanchoyzone@gmail.com
"""
    )

def get_crypto_ai_summary():
    logging.debug("get_crypto_ai_summary called")
    return "Crypto AI summary is temporarily unavailable."

def get_dhaka_weather():
    logging.debug("get_dhaka_weather called")
    return "Weather for Dhaka: 30°C, Partly Cloudy. (Demo)"

def get_coin_stats_ai(symbol):
    logging.debug(f"get_coin_stats_ai called for {symbol}")
    return f"Stats+AI for {symbol.upper()} are temporarily unavailable."

def get_coin_stats(symbol):
    logging.debug(f"get_coin_stats called for {symbol}")
    return f"Stats for {symbol.upper()} are temporarily unavailable."

# ===================== HANDLER REFACTOR =====================
def handle_updates(updates):
    logging.debug(f"handle_updates called with {len(updates)} updates: {updates}")
    for update in updates:
        message = update.get("message")
        if not message:
            logging.debug(f"Update without message: {update}")
            continue
        chat_id = message["chat"]["id"]
        user = message["from"]
        user_id = user.get("id")
        username = user.get("username")
        first_name = user.get("first_name")
        last_name = user.get("last_name")
        logging.debug(f"Processing message from user_id={user_id}, username={username}, chat_id={chat_id}")
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
        if text == "/support":
            send_telegram(get_support_text(), chat_id)
            continue
        if text == "/cryptostats":
            send_telegram(get_crypto_ai_summary(), chat_id)
            continue
        if text == "/weather":
            send_telegram(get_dhaka_weather(), chat_id)
            continue
        if text in ["/news"]:
            send_telegram("Loading latest news...", chat_id)
            # --- Bangladesh holiday info ---
            now_dt = datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M")
            def get_bd_holiday():
                try:
                    api_key = os.getenv("CALENDARIFIC_API_KEY")
                    if not api_key:
                        return ""
                    url = f"https://calendarific.com/api/v2/holidays?api_key={api_key}&country=BD&year={now_dt.year}"
                    resp = requests.get(url)
                    data = resp.json()
                    holidays = data.get("response", {}).get("holidays", [])
                    today_str = now_dt.strftime("%Y-%m-%d")
                    upcoming = None
                    for h in holidays:
                        h_date = h.get("date", {}).get("iso", "")
                        if h_date == today_str:
                            return f"🎉 *Today's Holiday:* {h['name']}"
                        elif h_date > today_str:
                            if not upcoming or h_date < upcoming["date"]:
                                upcoming = {"date": h_date, "name": h["name"]}
                    if upcoming:
                        # Format date as 'Jul 4, 2025'
                        up_date = datetime.strptime(upcoming["date"], "%Y-%m-%d").strftime("%b %d, %Y")
                        return f"🎉 *Next Holiday:* {upcoming['name']} ({up_date})"
                    return ""
                except Exception as e:
                    return ""
            holiday_line = get_bd_holiday()
            # Build the full digest as before
            digest = f"*📢 DAILY NEWS DIGEST*\n_{now_str}_\n\n"
            digest += get_dhaka_weather() + "\n"
            if holiday_line:
                digest += f"{holiday_line}\n"
            digest += "\n"
            digest += get_local_news()
            digest += get_global_news()
            digest += get_tech_news()
            digest += get_sports_news()
            digest += get_crypto_news()
            
            # --- Collect crypto data for DeepSeek summary ---
            market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, market_cap, market_cap_change, volume, volume_change, fear_greed = fetch_crypto_market_data()
            def arrow_only(val):
                try:
                    v = float(val.replace('%','').replace('+','').replace(',',''))
                except Exception:
                    return ''
                if v > 0:
                    return ' ▲'
                elif v < 0:
                    return ' ▼'
                else:
                    return ''
            cap_arrow = arrow_only(market_cap_change_str)
            vol_arrow = arrow_only(volume_change_str)
            # --- FEAR/GREED EMOJI & SUGGESTION ---
            def fear_greed_emoji_suggestion(fear_val):
                try:
                    fg = int(fear_val)
                except Exception:
                    return '😨', '(N/A)'
                if fg <= 24:
                    return '😱', '(🟢 Buy)'
                elif fg <= 49:
                    return '😨', '(🟡 Buy Slowly)'
                elif fg <= 74:
                    return '😏', '(🟠 Hold)'
                else:
                    return '🤯', '(🔴 Sell)'
            fg_emoji, fg_suggestion = fear_greed_emoji_suggestion(fear_greed)
            # Format with brackets for percentage
            def add_brackets(val):
                if val and not val.startswith('('):
                    return f'({val})'
                return val
            market_cap_change_str_b = add_brackets(market_cap_change_str)
            volume_change_str_b = add_brackets(volume_change_str)
            crypto_section = (
                f"*📊 CRYPTO MARKET:*\n"
                f"💰 Market Cap: {market_cap_str} {market_cap_change_str_b}{cap_arrow}\n"
                f"💵 Volume: {volume_str} {volume_change_str_b}{vol_arrow}\n"
                f"{fg_emoji} Fear/Greed: {fear_greed_str}/100 → {fg_suggestion}\n\n"
            )
            big_caps_msg, big_caps_str = fetch_big_cap_prices_data()
            crypto_section += big_caps_msg
            top_movers_msg, gainers_str, losers_str = fetch_top_movers_data()
            crypto_section += top_movers_msg
            DEEPSEEK_API = os.getenv("DEEPSEEK_API")
            ai_summary = None
            prediction_line = ""
            if DEEPSEEK_API and all(x != "N/A" for x in [market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, big_caps_str, gainers_str, losers_str]):
                ai_summary = get_crypto_summary_with_deepseek(
                    market_cap_str, market_cap_change_str, volume_str, volume_change_str, fear_greed_str, big_caps_str, gainers_str, losers_str, DEEPSEEK_API
                )
                import re
                ai_summary_clean = re.sub(r'^\s*prediction:.*$', '', ai_summary, flags=re.IGNORECASE | re.MULTILINE).strip()
                if ai_summary_clean and not ai_summary_clean.rstrip().endswith('.'):
                    ai_summary_clean = ai_summary_clean.rstrip() + '.'
                crypto_section += f"\n*🤖 AI Market Summary:*\n{ai_summary_clean}\n"
                summary_lower = ai_summary.lower()
                accuracy_match = re.search(r'(\d{2,3})\s*%\s*(?:confidence|accuracy|probability)?', ai_summary)
                try:
                    accuracy = int(accuracy_match.group(1)) if accuracy_match else 80
                except Exception:
                    accuracy = 80
                if accuracy <= 60:
                    prediction_line = "\nPrediction For tomorrow: CONSOLIDATION 🤔"
                elif "bullish" in summary_lower and accuracy > 60:
                    prediction_line = f"\nPrediction For Tomorrow: BULLISH 🟢 ({accuracy}% probability)"
                elif "bearish" in summary_lower and accuracy > 60:
                    prediction_line = f"\nPrediction For Tomorrow: BEARISH 🔴 ({accuracy}% probability)"
                else:
                    prediction_line = "\nPrediction For Tomorrow: CONSOLIDATION! 🤔"
                crypto_section += prediction_line
            crypto_section += "\n\n\n- Built by Shanchoy"
            # --- SPLIT DIGEST: send news and crypto in separate messages at CRYPTO MARKET marker ---
            marker = "*📊 CRYPTO MARKET:*\n"
            idx = digest.find(marker)
            if idx != -1:
                news_part = digest[:idx]
                crypto_part = digest[idx:] + crypto_section[len(marker):]  # Avoid duplicate marker
                send_telegram(news_part, chat_id)
                send_telegram(crypto_part, chat_id)
            else:
                # fallback: send as two messages
                send_telegram(digest, chat_id)
                send_telegram(crypto_section, chat_id)
            continue
        # --- Unified asset stats handlers ---
        # /[symbol]stats (e.g. /btcstats, /aaplstats, /eurusdstats)
        if text.startswith("/") and text.endswith("stats") and len(text) > 6:
            symbol = text[1:-5]  # remove leading / and trailing stats
            if symbol:
                # Use coinlist for crypto detection
                coin_id, _ = get_coin_id_from_symbol(symbol)
                if coin_id:
                    asset_type = "crypto"
                elif len(symbol) == 6 and symbol.isalpha():
                    asset_type = "forex"
                else:
                    asset_type = "stock"
                reply = get_asset_stats(symbol, asset_type, ai_summary=True)
                send_telegram(reply, chat_id)
                continue
        # /[symbol] (e.g. /btc, /aapl, /eurusd)
        if text.startswith("/") and len(text) > 1 and text[1:].isalpha():
            symbol = text[1:]
            # Use coinlist for crypto detection
            coin_id, _ = get_coin_id_from_symbol(symbol)
            if coin_id:
                asset_type = "crypto"
            elif len(symbol) == 6 and symbol.isalpha():
                asset_type = "forex"
            else:
                asset_type = "stock"
            reply = get_asset_stats(symbol, asset_type, ai_summary=False)
            send_telegram(reply, chat_id)
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
def get_updates(offset=None, timeout=30):
    """Poll Telegram for new updates/messages."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    try:
        logging.debug(f"Polling Telegram getUpdates with params: {params}")
        resp = requests.get(url, params=params, timeout=timeout+5)
        if resp.ok:
            data = resp.json()
            logging.debug(f"getUpdates response: {data}")
            return data.get("result", [])
        else:
            print("Failed to fetch updates:", resp.text)
            logging.error(f"Failed to fetch updates: {resp.text}")
            return []
    except Exception as e:
        print("Error in get_updates:", e)
        logging.error(f"Error in get_updates: {e}")
        return []
def main():
    init_db()
    print("Bot started. Listening for messages...")
    logging.info("Bot started. Listening for messages...")
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        logging.debug(f"Main loop got {len(updates)} updates.")
        if updates:
            handle_updates(updates)
            last_update_id = updates[-1]["update_id"] + 1
        time.sleep(2)

if __name__ == "__main__":
    main()