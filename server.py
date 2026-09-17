import flask
from flask import request, jsonify, send_from_directory
import requests
import feedparser
import time
import json
import os
import redis
import sqlite3
import threading
import schedule
import socket
import concurrent.futures
from urllib.parse import urlparse, urljoin
from datetime import datetime
from bs4 import BeautifulSoup

# Ensure default socket timeout to prevent indefinite hangs
socket.setdefaulttimeout(8)

app = flask.Flask(__name__, static_folder='.')

# --- CONFIG ---
CACHE_DURATION = 1800  # 30 minutes in seconds
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 (compatible; PrismBot/1.0; +https://prism.glassgallery.my.id)'
DB_FILE = os.environ.get('DB_FILE', 'prism.db')

# --- CLASSIFICATION KEYWORDS ---
CATEGORY_KEYWORDS = {
    'tech': [
        'software', 'linux', 'apple', 'google', 'microsoft', 'code', 'coding', 'app', 'apps', 'iphone', 'android',
        'crypto', 'data', 'cyber', 'security', 'hardware', 'developer', 'programming', 'kernel', 'open source',
        'rust', 'python', 'javascript', 'computing', 'cloud', 'devops', 'server', 'database', 'firmware', 'vulnerability'
    ],
    'ai': [
        'ai', 'artificial intelligence', 'gpt', 'llm', 'machine learning', 'deep learning', 'neural', 'openai',
        'deepmind', 'anthropic', 'claude', 'gemini', 'transformer', 'weights', 'inference', 'vision',
        'agent', 'diffusion', 'prompt', 'rag', 'embeddings', 'chatbot', 'synthetic'
    ],
    'design': [
        'design', 'ui', 'ux', 'typography', 'css', 'layout', 'aesthetic', 'branding', 'graphic', 'web design',
        'interface', 'interaction', 'figma', 'creative', 'poster', 'visual', 'font', 'minimalism', 'archival',
        'portfolio', 'sketch', 'illustration', 'colors'
    ],
    'gaming': [
        'game', 'games', 'gaming', 'nintendo', 'xbox', 'ps5', 'playstation', 'steam', 'esports', 'zelda', 'mario',
        'rpg', 'fps', 'unreal engine', 'unity', 'gameplay', 'modding', 'pc gaming', 'console'
    ],
    'science': [
        'space', 'nasa', 'astronomy', 'physics', 'biology', 'chemistry', 'research', 'study', 'planet',
        'galaxy', 'quantum', 'telescope', 'climate', 'ecology', 'lab', 'scientist', 'evolution', 'genetics',
        'cosmos', 'mars', 'earth', 'fossil', 'experiment'
    ],
    'world': [
        'world', 'global', 'geopolitics', 'international', 'diplomacy', 'treaty', 'un', 'europe', 'asia',
        'americas', 'africa', 'middle east', 'war', 'conflict', 'peace', 'election', 'government', 'nation',
        'foreign policy', 'president', 'prime minister', 'border', 'summit'
    ],
    'business': [
        'stock', 'stocks', 'market', 'markets', 'ceo', 'revenue', 'economy', 'economic', 'bank', 'banking',
        'finance', 'investment', 'investor', 'trade', 'startup', 'venture', 'ipo', 'earnings', 'inflation',
        'fed', 'wall street', 'dollar', 'treasury', 'acquisition'
    ],
    'entertainment': [
        'movie', 'movies', 'film', 'films', 'cinema', 'hollywood', 'netflix', 'series', 'actor', 'actress',
        'director', 'tv', 'television', 'streaming', 'theater', 'drama', 'box office', 'celebrity', 'oscars',
        'premiere', 'trailer', 'comedy'
    ],
    'music': [
        'song', 'songs', 'album', 'albums', 'music', 'musician', 'band', 'artist', 'concert', 'tour',
        'track', 'vinyl', 'spotify', 'guitar', 'instrumental', 'producer', 'soundtrack', 'hip hop', 'rock',
        'pop', 'indie', 'jazz', 'billboard', 'record'
    ],
    'sports': [
        'score', 'scores', 'team', 'league', 'tournament', 'championship', 'cup', 'nba', 'nfl', 'football',
        'soccer', 'premier league', 'fifa', 'cricket', 'olympic', 'olympics', 'athlete', 'race', 'f1', 'tennis',
        'basketball', 'baseball', 'golf', 'stadium', 'player'
    ],
    'food': [
        'recipe', 'recipes', 'cooking', 'cook', 'chef', 'restaurant', 'restaurants', 'cuisine', 'dish',
        'dinner', 'lunch', 'breakfast', 'baking', 'bakery', 'tasting', 'flavor', 'culinary', 'gastronomy',
        'ingredient', 'delicious', 'foodie', 'wine', 'coffee'
    ],
    'travel': [
        'travel', 'hotel', 'hotels', 'destination', 'flight', 'airline', 'airlines', 'tourism', 'tourist',
        'vacation', 'resort', 'passport', 'visa', 'journey', 'island', 'backpacking', 'itinerary', 'expedition',
        'cruise', 'airport', 'scenic', 'getaway'
    ],
    'health': [
        'health', 'medicine', 'medical', 'hospital', 'doctor', 'wellness', 'nutrition', 'disease', 'mental health',
        'fitness', 'therapy', 'virus', 'vaccine', 'clinical', 'pharmaceutical', 'diet', 'cardio', 'sleep',
        'symptom', 'cancer', 'treatment', 'fda'
    ]
}

# --- REDIS CONNECTION ---
redis_host = os.environ.get('REDIS_HOST', 'shared-redis')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_db = int(os.environ.get('REDIS_DB', 0))

try:
    cache = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3
    )
except Exception as e:
    print(f"[Redis] Init error: {e}")
    cache = None


# --- DATABASE ---
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'rss',
                enabled INTEGER DEFAULT 1
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles_cache (
                category TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
        ''')

        # Core high-reliability seed feeds
        seeds = [
            # EDAN / GLASS GALLERY ARCHIVE
            ('Wong Edan', 'https://wp.glassgallery.my.id/feed/', 'edan', 'rss'),

            # TECH
            ('Hacker News', 'https://news.ycombinator.com/rss', 'tech', 'hn'),
            ('The Verge', 'https://www.theverge.com/rss/index.xml', 'tech', 'rss'),
            ('Wired', 'https://www.wired.com/feed/rss', 'tech', 'rss'),
            ('TechCrunch', 'https://techcrunch.com/feed/', 'tech', 'rss'),
            ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index', 'tech', 'rss'),
            ('Engadget', 'https://www.engadget.com/rss.xml', 'tech', 'rss'),

            # AI
            ('MIT Tech Review (AI)', 'https://www.technologyreview.com/feed/', 'ai', 'rss'),
            ('Google AI Blog', 'http://feeds.feedburner.com/blogspot/gJZg', 'ai', 'rss'),
            ('TechCrunch AI', 'https://techcrunch.com/category/artificial-intelligence/feed/', 'ai', 'rss'),
            ('Simon Willison (AI)', 'https://simonwillison.net/atom/everything/', 'ai', 'rss'),

            # DESIGN
            ('Smashing Magazine', 'https://www.smashingmagazine.com/feed/', 'design', 'rss'),
            ('Design Milk', 'https://design-milk.com/feed/', 'design', 'rss'),

            # WORLD
            ('BBC News (World)', 'http://feeds.bbci.co.uk/news/world/rss.xml', 'world', 'rss'),
            ('The Guardian (World)', 'https://www.theguardian.com/world/rss', 'world', 'rss'),
            ('Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml', 'world', 'rss'),

            # SCIENCE
            ('Science Daily', 'https://www.sciencedaily.com/rss/all.xml', 'science', 'rss'),
            ('Scientific American', 'http://rss.sciam.com/ScientificAmerican-Global', 'science', 'rss'),
            ('NASA', 'https://www.nasa.gov/rss/dyn/breaking_news.rss', 'science', 'rss'),
            ('Phys.org', 'https://phys.org/rss-feed/', 'science', 'rss'),

            # BUSINESS
            ('Forbes', 'https://www.forbes.com/most-popular/feed/', 'business', 'rss'),
            ('Fortune', 'https://fortune.com/feed', 'business', 'rss'),
            ('Bloomberg', 'https://feeds.bloomberg.com/markets/news.rss', 'business', 'rss'),

            # GAMING
            ('Polygon', 'https://www.polygon.com/rss/index.xml', 'gaming', 'rss'),
            ('Kotaku', 'https://kotaku.com/rss', 'gaming', 'rss'),
            ('Eurogamer', 'https://www.eurogamer.net/?format=rss', 'gaming', 'rss'),

            # ENTERTAINMENT
            ('Variety', 'https://variety.com/feed/', 'entertainment', 'rss'),

            # MUSIC
            ('Pitchfork', 'https://pitchfork.com/feed/feed-news/rss', 'music', 'rss'),

            # SPORTS
            ('ESPN', 'https://www.espn.com/espn/rss/news', 'sports', 'rss'),

            # FOOD
            ('Eater', 'https://www.eater.com/rss/index.xml', 'food', 'rss'),

            # TRAVEL
            ('NYT Travel', 'https://rss.nytimes.com/services/xml/rss/nyt/Travel.xml', 'travel', 'rss'),
            ('The Points Guy', 'https://thepointsguy.com/feed/', 'travel', 'rss'),

            # HEALTH
            ('NYT Health', 'https://rss.nytimes.com/services/xml/rss/nyt/Health.xml', 'health', 'rss'),
            ('BBC Health', 'https://feeds.bbci.co.uk/news/health/rss.xml', 'health', 'rss'),
            ('NPR Health', 'https://feeds.npr.org/1128/rss.xml', 'health', 'rss')
        ]

        cur = conn.execute('SELECT count(*) FROM feeds')
        if cur.fetchone()[0] == 0:
            print("[DB] Seeding new database with core feeds...")
            conn.executemany(
                'INSERT OR IGNORE INTO feeds (name, url, category, type) VALUES (?, ?, ?, ?)',
                seeds
            )
        else:
            # Ensure essential seeds exist
            conn.executemany(
                'INSERT OR IGNORE INTO feeds (name, url, category, type) VALUES (?, ?, ?, ?)',
                seeds
            )
        conn.commit()


# --- HELPERS ---
def get_domain(url):
    try:
        host = urlparse(url).hostname
        if host:
            return host.replace('www.', '')
        return 'Self'
    except Exception:
        return 'Self'


def score_category(text):
    text = text.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for k in keywords:
            if len(k) <= 3:
                import re
                scores[cat] += len(re.findall(r'\b' + re.escape(k) + r'\b', text))
            else:
                scores[cat] += text.count(k)

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] >= 2:
        return best_cat, scores[best_cat]
    return 'other', 0


def smart_classify(feed_title, feed_desc, entries):
    """Multi-factor classification with weighted scoring."""
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}

    # 1. Feed title (weight: 4)
    title_lower = (feed_title or "").lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if len(kw) <= 3:
                import re
                if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
                    scores[cat] += 4
            elif kw in title_lower:
                scores[cat] += 4

    # 2. Feed description (weight: 2)
    desc_lower = (feed_desc or "").lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in desc_lower:
                scores[cat] += 2

    # 3. Entries title + summary + tags (weight: 1 for text, 3 for category tags)
    for entry in (entries or [])[:20]:
        title = getattr(entry, 'title', '')
        summary = getattr(entry, 'summary', '')
        entry_text = f"{title} {summary}".lower()
        for cat, kws in CATEGORY_KEYWORDS.items():
            for kw in kws:
                if kw in entry_text:
                    scores[cat] += 1

        tags = getattr(entry, 'tags', [])
        if tags and isinstance(tags, list):
            for t in tags:
                tag_term = (t.get('term', '') if isinstance(t, dict) else str(t)).lower()
                for cat, kws in CATEGORY_KEYWORDS.items():
                    if any(kw in tag_term for kw in kws):
                        scores[cat] += 3

    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]
    if best_score >= 3:
        return best_cat, best_score
    return 'other', 0



# --- FETCHERS ---
def fetch_hn():
    """Fetch Hacker News top stories with fast RSS and fallback."""
    # Fast path: HN RSS feed returns all 30 frontpage entries in one HTTP call
    try:
        r = requests.get('https://news.ycombinator.com/rss', timeout=5, headers={'User-Agent': USER_AGENT})
        if r.status_code == 200:
            d = feedparser.parse(r.content)
            stories = []
            for entry in d.entries[:50]:
                link = getattr(entry, 'link', None)
                title = getattr(entry, 'title', None)
                if not link or not title:
                    continue

                comments_url = getattr(entry, 'comments', link)
                story_id = comments_url.split("id=")[-1] if "id=" in comments_url else link
                pub_time = time.mktime(entry.published_parsed) if getattr(entry, 'published_parsed', None) else time.time()

                stories.append({
                    'title': title,
                    'url': link,
                    'score': 100,
                    'author': getattr(entry, 'author', 'Hacker News'),
                    'time': pub_time,
                    'domain': get_domain(link),
                    'commentsUrl': comments_url,
                    'id': story_id,
                    'source_name': 'Hacker News'
                })
            if stories:
                return stories
    except Exception as e:
        print(f"[HN] RSS fetch failed: {e}")

    # Fallback: Firebase API
    try:
        r = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json', timeout=4)
        ids = r.json()[:15]
        stories = []
        for sid in ids:
            try:
                ir = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{sid}.json', timeout=2)
                if ir.status_code == 200:
                    item = ir.json()
                    if item and 'url' in item:
                        stories.append({
                            'title': item.get('title'),
                            'url': item.get('url'),
                            'score': item.get('score', 0),
                            'author': item.get('by', 'unknown'),
                            'time': item.get('time', time.time()),
                            'domain': get_domain(item.get('url')),
                            'commentsUrl': f'https://news.ycombinator.com/item?id={sid}',
                            'id': str(sid),
                            'source_name': 'Hacker News'
                        })
            except Exception:
                continue
        return stories
    except Exception as e:
        print(f"[HN] Firebase fallback failed: {e}")
        return []


def fetch_rss(url, source_name):
    """Fetch RSS with strict HTTP timeout and safe XML parsing."""
    try:
        resp = requests.get(url, timeout=6, headers={'User-Agent': USER_AGENT})
        if resp.status_code != 200:
            return [], ""

        d = feedparser.parse(resp.content)
        items = []
        full_text_for_scoring = ""

        for entry in d.entries[:210]:
            link = getattr(entry, 'link', None)
            title = getattr(entry, 'title', None)
            if not title or not link:
                continue

            full_text_for_scoring += f"{title} "
            pub_time = time.time()
            if getattr(entry, 'published_parsed', None):
                try:
                    pub_time = time.mktime(entry.published_parsed)
                except Exception:
                    pub_time = time.time()

            author = getattr(entry, 'author', None) or d.feed.get('title', source_name)

            # Extract media enclosure or thumbnail image if available
            image_url = None
            if hasattr(entry, 'media_content') and entry.media_content:
                for mc in entry.media_content:
                    if isinstance(mc, dict) and (mc.get('medium') == 'image' or 'image' in mc.get('type', '')):
                        image_url = mc.get('url')
                        break
            if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
                for enc in entry.enclosures:
                    if isinstance(enc, dict) and 'image' in enc.get('type', ''):
                        image_url = enc.get('href') or enc.get('url')
                        break
            if not image_url and hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                if isinstance(entry.media_thumbnail, list) and len(entry.media_thumbnail) > 0:
                    image_url = entry.media_thumbnail[0].get('url')

            items.append({
                'title': title,
                'url': link,
                'score': 0,
                'author': author,
                'time': pub_time,
                'domain': get_domain(link),
                'commentsUrl': link,
                'id': getattr(entry, 'id', link),
                'source_name': source_name,
                'image': image_url
            })

        return items, full_text_for_scoring
    except Exception as e:
        return [], ""


def _fetch_single_feed(feed):
    if feed['type'] == 'hn':
        return fetch_hn(), ""
    return fetch_rss(feed['url'], feed['name'])


def fetch_category(cat):
    """Fetch all enabled feeds for a category in parallel and persist cache."""
    with get_db() as conn:
        feeds = conn.execute("SELECT * FROM feeds WHERE category=? AND enabled=1", (cat,)).fetchall()

    if not feeds:
        return []

    aggregated_news = []
    max_workers = min(len(feeds), 8)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_fetch_single_feed, f): f for f in feeds}
        for future in concurrent.futures.as_completed(future_map):
            try:
                items, _ = future.result()
                if items:
                    aggregated_news.extend(items)
            except Exception:
                pass

    # Deduplicate by URL or title
    seen = set()
    unique_news = []
    for item in aggregated_news:
        key = item.get('url') or item.get('title')
        if key and key not in seen:
            seen.add(key)
            unique_news.append(item)

    unique_news.sort(key=lambda x: x.get('time', 0), reverse=True)
    unique_news = unique_news[:210]

    if unique_news:
        json_data = json.dumps(unique_news)
        # 1. Update Redis
        if cache:
            try:
                cache.set(f"news:{cat}", json_data, ex=CACHE_DURATION)
            except Exception as e:
                print(f"[Redis] Set error for {cat}: {e}")

        # 2. Update persistent SQLite cache
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO articles_cache (category, data, updated_at) VALUES (?, ?, ?)",
                    (cat, json_data, int(time.time()))
                )
                conn.commit()
        except Exception as e:
            print(f"[DB] Cache save error for {cat}: {e}")

    return unique_news


# --- DISCOVERY & CLASSIFICATION ---
def find_rss_link(html, base_url):
    """Extract RSS or Atom feed link with multi-pattern discovery and fallback endpoints."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 1. Standard <link rel="alternate" type="...">
        for link in soup.find_all('link'):
            rel = [r.lower() for r in link.get('rel', [])] if isinstance(link.get('rel'), list) else str(link.get('rel', '')).lower()
            ltype = link.get('type', '').lower()
            if 'alternate' in rel or 'feed' in rel:
                if any(t in ltype for t in ('rss', 'atom', 'xml')):
                    href = link.get('href')
                    if href:
                        return urljoin(base_url, href)

        # 2. Direct <link type="application/rss+xml"> (even without rel="alternate")
        for link in soup.find_all('link'):
            ltype = link.get('type', '').lower()
            if 'application/rss+xml' in ltype or 'application/atom+xml' in ltype:
                href = link.get('href')
                if href:
                    return urljoin(base_url, href)

        # 3. Look for <a> tags with feed links
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            if href.endswith(('.rss', '.atom', '/feed', '/rss', '/feed.xml', '/rss.xml')):
                return urljoin(base_url, a['href'])
    except Exception:
        pass

    # 4. Probe common endpoints on domain root
    try:
        parsed = urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        for path in ['/feed', '/feed/', '/rss', '/rss.xml', '/atom.xml']:
            candidate = origin + path
            try:
                r = requests.head(candidate, timeout=2, headers={'User-Agent': USER_AGENT}, allow_redirects=True)
                if r.status_code == 200:
                    ctype = r.headers.get('Content-Type', '').lower()
                    if any(t in ctype for t in ('xml', 'rss', 'atom')):
                        return candidate
            except Exception:
                continue
    except Exception:
        pass

    return None


EXCLUDED_DOMAINS = {
    'self', '', 'github.com', 'youtube.com', 'youtu.be', 'twitter.com', 'x.com',
    'reddit.com', 'facebook.com', 'instagram.com', 'linkedin.com', 'news.ycombinator.com',
    'google.com', 't.co', 'bit.ly', 'medium.com'
}


def discover_feeds(articles):
    """Auto-discover feeds from incoming articles across all categories."""
    if not articles:
        return

    import random
    candidates = []
    seen_domains = set()
    for item in articles:
        domain = item.get('domain', '').lower()
        if domain and domain not in EXCLUDED_DOMAINS and domain not in seen_domains:
            seen_domains.add(domain)
            candidates.append(item)

    if not candidates:
        return

    targets = random.sample(candidates, min(len(candidates), 5))
    for t in targets:
        domain = t.get('domain', '')
        url = t.get('url', '')
        if not url:
            continue

        try:
            with get_db() as conn:
                existing = conn.execute(
                    "SELECT 1 FROM feeds WHERE url LIKE ? OR name LIKE ? LIMIT 1",
                    (f"%{domain}%", f"%{domain}%")
                ).fetchone()
                if existing:
                    continue

            r = requests.get(url, timeout=5, headers={'User-Agent': USER_AGENT})
            if r.status_code != 200:
                continue

            feed_url = find_rss_link(r.text, url)
            if not feed_url:
                continue

            # Validate candidate feed
            feed_resp = requests.get(feed_url, timeout=5, headers={'User-Agent': USER_AGENT})
            if feed_resp.status_code != 200:
                continue

            d = feedparser.parse(feed_resp.content)
            if not d.entries:
                continue

            feed_name = d.feed.get('title') or domain
            feed_desc = d.feed.get('description', '')

            # Smart classification
            cat, score = smart_classify(feed_name, feed_desc, d.entries)

            with get_db() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO feeds (name, url, category, type, enabled) VALUES (?, ?, ?, 'rss', 1)",
                    (feed_name[:60], feed_url, cat)
                )
                conn.commit()
                print(f"[Discovery] Discovered & classified '{feed_name}' -> '{cat}' (score: {score})")

        except Exception:
            pass


def classify_pending_feeds():
    """Re-classify any feeds in 'other' category using multi-factor signals."""
    try:
        with get_db() as conn:
            pending = conn.execute("SELECT * FROM feeds WHERE category='other' AND enabled=1 LIMIT 10").fetchall()

        for feed in pending:
            try:
                resp = requests.get(feed['url'], timeout=6, headers={'User-Agent': USER_AGENT})
                if resp.status_code != 200:
                    continue
                d = feedparser.parse(resp.content)
                if not d.entries:
                    continue

                feed_title = d.feed.get('title') or feed['name']
                feed_desc = d.feed.get('description', '')
                cat, score = smart_classify(feed_title, feed_desc, d.entries)

                if cat != 'other' and score >= 3:
                    with get_db() as conn:
                        conn.execute("UPDATE feeds SET category=?, name=? WHERE id=?", (cat, feed_title[:60], feed['id']))
                        conn.commit()
                    print(f"[Classify] Promoted '{feed['name']}' to '{cat}' (score: {score})")
            except Exception:
                continue
    except Exception as e:
        print(f"[Classify] Error: {e}")


# --- WORKER LOOP ---
def update_all_categories():
    print(f"[{datetime.now()}] Running full category cache refresh...")
    with get_db() as conn:
        cats = [row[0] for row in conn.execute("SELECT DISTINCT category FROM feeds WHERE enabled=1").fetchall()]

    discovery_pool = []
    for cat in cats:
        try:
            articles = fetch_category(cat)
            if articles:
                discovery_pool.extend(articles[:4])
            time.sleep(0.2)
        except Exception as e:
            print(f"[Worker] Error updating {cat}: {e}")

    if discovery_pool:
        try:
            discover_feeds(discovery_pool)
            classify_pending_feeds()
        except Exception as e:
            print(f"[Worker] Discovery cycle error: {e}")


def worker_thread():
    while True:
        try:
            time.sleep(1)
            init_db()

            # Fast priority load for instant user response
            priority_cats = ['tech', 'edan', 'ai', 'world', 'science', 'business']
            for cat in priority_cats:
                try:
                    fetch_category(cat)
                except Exception as e:
                    print(f"[Init] Priority category {cat} failed: {e}")

            # Run full category update
            update_all_categories()

            schedule.clear()
            schedule.every(15).minutes.do(update_all_categories)

            while True:
                schedule.run_pending()
                time.sleep(5)
        except Exception as e:
            print(f"[WorkerCRASH] Background worker crashed: {e}. Restarting in 10s...")
            time.sleep(10)


# --- ROUTES ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)


@app.route('/api/news')
def api_news():
    category = request.args.get('category', 'tech').strip().lower()

    # 1. Try Redis cache
    if cache:
        try:
            data = cache.get(f"news:{category}")
            if data:
                return jsonify(json.loads(data))
        except Exception as e:
            print(f"[API] Redis get error: {e}")

    # 2. Try persistent SQLite cache fallback
    try:
        with get_db() as conn:
            row = conn.execute("SELECT data FROM articles_cache WHERE category=?", (category,)).fetchone()
            if row and row['data']:
                return jsonify(json.loads(row['data']))
    except Exception as e:
        print(f"[API] SQLite cache error: {e}")

    # 3. Synchronous on-demand fetch if still empty (ensures user NEVER sees SILENCE)
    try:
        articles = fetch_category(category)
        if articles:
            return jsonify(articles)
    except Exception as e:
        print(f"[API] On-demand fetch failed for {category}: {e}")

    return jsonify([])


@app.route('/api/health')
def health():
    redis_ok = False
    if cache:
        try:
            redis_ok = bool(cache.ping())
        except Exception:
            redis_ok = False
    return jsonify({
        'status': 'healthy',
        'redis': redis_ok,
        'timestamp': int(time.time())
    })


if __name__ == '__main__':
    t = threading.Thread(target=worker_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5051)
