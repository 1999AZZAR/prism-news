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
from urllib.parse import urlparse, urljoin
from datetime import datetime
from bs4 import BeautifulSoup

app = flask.Flask(__name__, static_folder='.')

# --- CONFIG ---
CACHE_DURATION = 600
HN_API = 'https://hacker-news.firebaseio.com/v0'
USER_AGENT = 'Mozilla/5.0 (compatible; PrismBot/1.0; +http://prism.glassgallery.my.id)'
DB_FILE = 'prism.db'

# --- CLASSIFICATION KEYWORDS ---
CATEGORY_KEYWORDS = {
    'tech': ['software', 'linux', 'apple', 'google', 'microsoft', 'code', 'app', 'iphone', 'android', 'crypto', 'data', 'cyber', 'robot'],
    'ai': ['ai', 'gpt', 'llm', 'machine learning', 'neural', 'openai', 'deepmind', 'algorithm', 'intelligence'],
    'gaming': ['game', 'nintendo', 'xbox', 'ps5', 'playstation', 'steam', 'esports', 'zelda', 'mario', 'rpg', 'fps'],
    'science': ['space', 'nasa', 'research', 'study', 'physics', 'biology', 'climate', 'planet', 'quantum', 'lab'],
    'business': ['stock', 'market', 'ceo', 'revenue', 'economy', 'bank', 'invest', 'trade', 'startup', 'ipo'],
    'music': ['song', 'album', 'tour', 'band', 'artist', 'concert', 'track', 'remix', 'vinyl'],
    'sports': ['score', 'team', 'league', 'cup', 'nba', 'nfl', 'football', 'soccer', 'cricket', 'champion', 'match'],
    'food': ['recipe', 'cook', 'delicious', 'restaurant', 'taste', 'dinner', 'lunch', 'breakfast', 'chef', 'baking'],
    'entertainment': ['movie', 'film', 'series', 'netflix', 'hollywood', 'actor', 'drama', 'cinema', 'show', 'trailer'],
    'health': ['health', 'diet', 'wellness', 'disease', 'medical', 'therapy', 'mental', 'fitness', 'doctor', 'virus']
}

# --- REDIS ---
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
cache = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

# --- DATABASE ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Remove old DB if exists to ensure fresh seed
    if not os.path.exists(DB_FILE):
        print("Creating new database...")
    
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'rss',
                enabled INTEGER DEFAULT 1
            )
        ''')
        
        # Check if empty, then seed
        cur = conn.execute('SELECT count(*) FROM feeds')
        if cur.fetchone()[0] == 0:
            print("Seeding DB with Awesome-RSS feeds...")
            seeds = [
                # TECH
                ('Hacker News', 'https://hacker-news.firebaseio.com/v0', 'tech', 'hn'),
                ('The Verge', 'https://www.theverge.com/rss/index.xml', 'tech', 'rss'),
                ('Wired', 'https://www.wired.com/feed/rss', 'tech', 'rss'),
                ('TechCrunch', 'https://techcrunch.com/feed/', 'tech', 'rss'),
                ('Ars Technica', 'https://feeds.arstechnica.com/arstechnica/index', 'tech', 'rss'),
                ('Engadget', 'https://www.engadget.com/rss.xml', 'tech', 'rss'),
                
                # AI
                ('MIT Tech Review (AI)', 'https://www.technologyreview.com/feed/', 'ai', 'rss'),
                ('VentureBeat (AI)', 'https://venturebeat.com/category/ai/feed/', 'ai', 'rss'),
                ('Google AI Blog', 'http://feeds.feedburner.com/blogspot/gJZg', 'ai', 'rss'),
                
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

                # BUSINESS
                ('Forbes', 'https://www.forbes.com/most-popular/feed/', 'business', 'rss'),
                ('Fortune', 'https://fortune.com/feed', 'business', 'rss'),
                ('Bloomberg', 'https://feeds.bloomberg.com/markets/news.rss', 'business', 'rss'),

                # GAMING
                ('Polygon', 'https://www.polygon.com/rss/index.xml', 'gaming', 'rss'),
                ('Kotaku', 'https://kotaku.com/rss', 'gaming', 'rss'),
                ('Eurogamer', 'https://www.eurogamer.net/?format=rss', 'gaming', 'rss'),

                # OTHERS
                ('Variety', 'https://variety.com/feed/', 'entertainment', 'rss'),
                ('Pitchfork', 'https://pitchfork.com/feed/feed-news/rss', 'music', 'rss'),
                ('ESPN', 'https://www.espn.com/espn/rss/news', 'sports', 'rss'),
                ('Eater', 'https://www.eater.com/rss/index.xml', 'food', 'rss'),
                ('Lonely Planet', 'https://www.lonelyplanet.com/news/rss.xml', 'travel', 'rss'),
                ('Healthline', 'https://www.healthline.com/rss', 'health', 'rss')
            ]
            conn.executemany('INSERT INTO feeds (name, url, category, type) VALUES (?, ?, ?, ?)', seeds)
            conn.commit()

# --- HELPERS ---
def get_domain(url):
    try:
        return urlparse(url).hostname.replace('www.', '')
    except:
        return 'Self'

def find_rss_link(html, base_url):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 1. Look for standard link tags
        link = soup.find('link', type='application/rss+xml')
        if link: return urljoin(base_url, link.get('href'))
        
        link = soup.find('link', type='application/atom+xml')
        if link: return urljoin(base_url, link.get('href'))
        
        return None
    except:
        return None

def score_category(text):
    text = text.lower()
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for k in keywords:
            if k in text:
                scores[cat] += 1
    
    # Get winner
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] > 0:
        return best_cat, scores[best_cat]
    return 'other', 0

# --- FETCHERS ---
def fetch_hn():
    try:
        r = requests.get(f'{HN_API}/topstories.json', timeout=5)
        ids = r.json()[:30]
        stories = []
        for id in ids:
            item_r = requests.get(f'{HN_API}/item/{id}.json', timeout=2)
            if item_r.status_code == 200:
                item = item_r.json()
                if item and 'url' in item:
                    stories.append({
                        'title': item.get('title'),
                        'url': item.get('url'),
                        'score': item.get('score', 0),
                        'author': item.get('by', 'unknown'),
                        'time': item.get('time', time.time()),
                        'domain': get_domain(item.get('url')),
                        'commentsUrl': f'https://news.ycombinator.com/item?id={id}',
                        'id': str(id),
                        'source_name': 'Hacker News'
                    })
        return stories
    except Exception as e:
        print(f"HN Error: {e}")
        return []

def fetch_rss(url, source_name):
    try:
        d = feedparser.parse(url, agent=USER_AGENT)
        items = []
        full_text_for_scoring = ""
        
        for entry in d.entries[:15]:
            link = entry.link
            title = entry.title
            if not title or not link: continue
            
            full_text_for_scoring += f"{title} "

            items.append({
                'title': title,
                'url': link,
                'score': 0,
                'author': entry.get('author', d.feed.get('title', source_name)),
                'time': time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else time.time(),
                'domain': get_domain(link),
                'commentsUrl': link,
                'id': entry.id if hasattr(entry, 'id') else link,
                'source_name': source_name
            })
            
        return items, full_text_for_scoring
    except Exception as e:
        print(f"RSS Error ({url}): {e}")
        return [], ""

# --- DISCOVERY ENGINE ---
def discover_feeds(articles):
    # Take 3 random articles from domains we DON'T have
    candidates = []
    
    with get_db() as conn:
        known_urls = [row['url'] for row in conn.execute("SELECT url FROM feeds").fetchall()]
        # Simple domain extraction from known RSS urls is hard, so we just check DB logic later
    
    # We want to find NEW domains. 
    # This is a basic implementation: check 2 random articles per cycle
    import random
    if len(articles) > 2:
        targets = random.sample(articles, 2)
    else:
        targets = articles

    for t in targets:
        domain = t['domain']
        if domain == 'Self' or 'github' in domain or 'youtube' in domain: continue
        
        try:
            # Check if we already have this domain in our DB (fuzzy match)
            # This prevents re-scanning TechCrunch if we already have TechCrunch RSS
            # For V1, we just scan.
            
            print(f"🕵️ DISCOVERY: Scanning {t['url']} for feeds...")
            r = requests.get(t['url'], timeout=5, headers={'User-Agent': USER_AGENT})
            if r.status_code != 200: continue
            
            feed_url = find_rss_link(r.text, t['url'])
            
            if feed_url:
                print(f"✅ FOUND FEED: {feed_url}")
                
                # Check if exists
                with get_db() as conn:
                    exists = conn.execute("SELECT 1 FROM feeds WHERE url=?", (feed_url,)).fetchone()
                    if not exists:
                        # Insert as 'other'
                        conn.execute("INSERT INTO feeds (name, url, category, type) VALUES (?, ?, ?, ?)",
                                     (domain, feed_url, 'other', 'rss'))
                        conn.commit()
                        print("Saved to DB as 'other'")
        except Exception as e:
            print(f"Discovery failed for {t['url']}: {e}")

def classify_pending_feeds():
    with get_db() as conn:
        # Find feeds in 'other'
        pending = conn.execute("SELECT * FROM feeds WHERE category='other'").fetchall()
        
        for feed in pending:
            print(f"🧠 CLASSIFYING: {feed['name']}...")
            items, full_text = fetch_rss(feed['url'], feed['name'])
            
            if not full_text: continue
            
            cat, score = score_category(full_text)
            
            if score > 2: # Threshold
                print(f"🎉 PROMOTED {feed['name']} to {cat} (Score: {score})")
                conn.execute("UPDATE feeds SET category=? WHERE id=?", (cat, feed['id']))
                conn.commit()
            else:
                print(f"⚠️ Could not classify {feed['name']} (Best: {cat} with score {score})")

# --- BACKGROUND WORKER ---
def update_cache():
    print(f"[{datetime.now()}] Starting cache update...")
    all_articles_for_discovery = []
    
    with get_db() as conn:
        cats = conn.execute("SELECT DISTINCT category FROM feeds WHERE enabled=1").fetchall()
        
        for row in cats:
            cat = row['category']
            feeds = conn.execute("SELECT * FROM feeds WHERE category=? AND enabled=1", (cat,)).fetchall()
            
            aggregated_news = []
            
            for feed in feeds:
                # fetch_rss now returns tuple (items, text)
                if feed['type'] == 'hn':
                    items = fetch_hn()
                else:
                    items, _ = fetch_rss(feed['url'], feed['name'])
                
                aggregated_news.extend(items)
            
            # Sort by time desc
            aggregated_news.sort(key=lambda x: x['time'], reverse=True)
            
            # Cap at 150 items to stay relevant
            aggregated_news = aggregated_news[:150]
            
            # Keep for discovery
            if cat == 'tech': # Mostly discover from Tech
                all_articles_for_discovery.extend(aggregated_news)
            
            # Store in Redis
            try:
                cache.set(f"news:{cat}", json.dumps(aggregated_news))
            except Exception as e:
                print(f"Redis Error: {e}")

    # Run AI Engines
    discover_feeds(all_articles_for_discovery)
    classify_pending_feeds()

def worker_thread():
    time.sleep(5) 
    init_db()
    update_cache()
    
    schedule.every(15).minutes.do(update_cache)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- ROUTES ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/news')
def api_news():
    category = request.args.get('category', 'tech')
    try:
        data = cache.get(f"news:{category}")
        if data:
            return jsonify(json.loads(data))
    except:
        pass
    return jsonify([])

# --- START ---
if __name__ == '__main__':
    t = threading.Thread(target=worker_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5051)
