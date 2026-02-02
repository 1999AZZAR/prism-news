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
from urllib.parse import urlparse
from datetime import datetime

app = flask.Flask(__name__, static_folder='.')

# --- CONFIG ---
CACHE_DURATION = 600
HN_API = 'https://hacker-news.firebaseio.com/v0'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
DB_FILE = 'prism.db'

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
                ('9to5Mac', 'https://9to5mac.com/feed/', 'tech', 'rss'),
                ('Android Authority', 'https://www.androidauthority.com/feed/', 'tech', 'rss'),
                ('GSMArena', 'https://www.gsmarena.com/rss-news-reviews.php3', 'tech', 'rss'),
                ('Mashable', 'https://mashable.com/feeds/rss/all', 'tech', 'rss'),
                
                # AI (Mixed sources as specific AI RSS is rare in general lists, using Tech subsets + specialized)
                ('MIT Tech Review (AI)', 'https://www.technologyreview.com/feed/', 'ai', 'rss'), # General feed, often high AI content
                ('VentureBeat (AI)', 'https://venturebeat.com/category/ai/feed/', 'ai', 'rss'),
                ('Google AI Blog', 'http://feeds.feedburner.com/blogspot/gJZg', 'ai', 'rss'),
                ('OpenAI Blog', 'https://openai.com/blog/rss.xml', 'ai', 'rss'),
                
                # DESIGN
                ('Smashing Magazine', 'https://www.smashingmagazine.com/feed/', 'design', 'rss'),
                ('Design Milk', 'https://design-milk.com/feed/', 'design', 'rss'),
                ('Creative Bloq', 'https://www.creativebloq.com/feed', 'design', 'rss'),
                ('Abduzeedo', 'https://abduzeedo.com/feed.xml', 'design', 'rss'),
                ('A List Apart', 'https://alistapart.com/main/feed', 'design', 'rss'),
                
                # WORLD
                ('BBC News (World)', 'http://feeds.bbci.co.uk/news/world/rss.xml', 'world', 'rss'),
                ('The Guardian (World)', 'https://www.theguardian.com/world/rss', 'world', 'rss'),
                ('Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml', 'world', 'rss'),
                ('Reuters (World)', 'https://www.reutersagency.com/feed/?best-topics=world&post_type=best', 'world', 'rss'), # Reuters RSS is tricky, using agency feed or alternatives
                ('NPR News', 'https://feeds.npr.org/1001/rss.xml', 'world', 'rss'),
                ('Associated Press', 'https://apnews.com/hub/ap-top-news.rss', 'world', 'rss'), # Often unofficial
                ('CNN (Top Stories)', 'http://rss.cnn.com/rss/edition.rss', 'world', 'rss'),

                # SCIENCE
                ('Science Daily', 'https://www.sciencedaily.com/rss/all.xml', 'science', 'rss'),
                ('Scientific American', 'http://rss.sciam.com/ScientificAmerican-Global', 'science', 'rss'),
                ('Nature', 'http://www.nature.com/nature/current_issue/rss', 'science', 'rss'),
                ('New Scientist', 'https://www.newscientist.com/feed/home/', 'science', 'rss'),
                ('NASA Breaking News', 'https://www.nasa.gov/rss/dyn/breaking_news.rss', 'science', 'rss'),
                ('National Geographic', 'https://www.nationalgeographic.com/ngm/index.xml', 'science', 'rss'), # Often unstable, but worth a try

                # BUSINESS
                ('Forbes', 'https://www.forbes.com/most-popular/feed/', 'business', 'rss'),
                ('Fortune', 'https://fortune.com/feed', 'business', 'rss'),
                ('Bloomberg', 'https://feeds.bloomberg.com/markets/news.rss', 'business', 'rss'),
                ('Business Insider', 'https://feeds.businessinsider.com/custom/type/top-stories', 'business', 'rss'),
                ('Economist', 'https://www.economist.com/sections/business-finance/rss.xml', 'business', 'rss'),
                ('Harvard Business Review', 'https://feeds.hbr.org/harvardbusiness', 'business', 'rss'),

                # GAMING
                ('Polygon', 'https://www.polygon.com/rss/index.xml', 'gaming', 'rss'),
                ('Kotaku', 'https://kotaku.com/rss', 'gaming', 'rss'),
                ('GameSpot', 'https://www.gamespot.com/feeds/news/', 'gaming', 'rss'),
                ('IGN', 'http://feeds.ign.com/ign/news', 'gaming', 'rss'),
                ('Eurogamer', 'https://www.eurogamer.net/?format=rss', 'gaming', 'rss'),
                ('PC Gamer', 'https://www.pcgamer.com/rss', 'gaming', 'rss'),

                # ENTERTAINMENT (Movies/TV)
                ('Variety', 'https://variety.com/feed/', 'entertainment', 'rss'),
                ('The Hollywood Reporter', 'https://deadline.com/feed/', 'entertainment', 'rss'),
                ('Screen Rant', 'https://screenrant.com/feed/', 'entertainment', 'rss'),
                ('IndieWire', 'https://www.indiewire.com/feed/', 'entertainment', 'rss'),

                # MUSIC
                ('Pitchfork', 'https://pitchfork.com/feed/feed-news/rss', 'music', 'rss'),
                ('Rolling Stone', 'https://www.rollingstone.com/music/music-news/feed/', 'music', 'rss'),
                ('Billboard', 'https://www.billboard.com/feed/', 'music', 'rss'),
                ('NME', 'https://www.nme.com/feed', 'music', 'rss'),

                # SPORTS
                ('ESPN', 'https://www.espn.com/espn/rss/news', 'sports', 'rss'),
                ('Yahoo Sports', 'https://sports.yahoo.com/rss/', 'sports', 'rss'),
                ('Bleacher Report', 'https://bleacherreport.com/articles/feed', 'sports', 'rss'),
                ('CBS Sports', 'https://sports.cbsimg.net/rss/headlines.xml', 'sports', 'rss'),

                # FOOD
                ('Serious Eats', 'https://feeds.feedburner.com/seriouseatsfeaturesvideos', 'food', 'rss'),
                ('Eater', 'https://www.eater.com/rss/index.xml', 'food', 'rss'),
                ('Bon Appétit', 'https://www.bonappetit.com/feed/latest', 'food', 'rss'),
                ('Food & Wine', 'https://www.foodandwine.com/feed', 'food', 'rss'),

                # TRAVEL
                ('Lonely Planet', 'https://www.lonelyplanet.com/news/rss.xml', 'travel', 'rss'),
                ('Nomadic Matt', 'https://www.nomadicmatt.com/feed/', 'travel', 'rss'),
                ('Travel + Leisure', 'https://www.travelandleisure.com/feed', 'travel', 'rss'),
                ('Skift', 'https://skift.com/feed/', 'travel', 'rss'),

                # HEALTH
                ('Healthline', 'https://www.healthline.com/rss', 'health', 'rss'),
                ('Medical News Today', 'https://www.medicalnewstoday.com/feed', 'health', 'rss'),
                ('Psychology Today', 'https://www.psychologytoday.com/us/feed/news', 'health', 'rss')
            ]
            conn.executemany('INSERT INTO feeds (name, url, category, type) VALUES (?, ?, ?, ?)', seeds)
            conn.commit()

# --- HELPERS ---
def get_domain(url):
    try:
        return urlparse(url).hostname.replace('www.', '')
    except:
        return 'Self'

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
                if item:
                    stories.append({
                        'title': item.get('title'),
                        'url': item.get('url', f'https://news.ycombinator.com/item?id={id}'),
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
        for entry in d.entries[:15]:
            link = entry.link
            title = entry.title
            
            # Basic validation
            if not title or not link:
                continue

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
        return items
    except Exception as e:
        print(f"RSS Error ({url}): {e}")
        return []

# --- BACKGROUND WORKER ---
def update_cache():
    print(f"[{datetime.now()}] Starting cache update...")
    with get_db() as conn:
        cats = conn.execute("SELECT DISTINCT category FROM feeds WHERE enabled=1").fetchall()
        
        for row in cats:
            cat = row['category']
            feeds = conn.execute("SELECT * FROM feeds WHERE category=? AND enabled=1", (cat,)).fetchall()
            
            aggregated_news = []
            
            for feed in feeds:
                print(f"Fetching {feed['name']} ({cat})...")
                if feed['type'] == 'hn':
                    aggregated_news.extend(fetch_hn())
                else:
                    aggregated_news.extend(fetch_rss(feed['url'], feed['name']))
            
            # Sort by time desc
            aggregated_news.sort(key=lambda x: x['time'], reverse=True)
            
            # Store in Redis
            try:
                cache.set(f"news:{cat}", json.dumps(aggregated_news))
                print(f"Cached {len(aggregated_news)} items for {cat}")
            except Exception as e:
                print(f"Redis Error: {e}")

def worker_thread():
    # Initial run
    time.sleep(5) 
    init_db()
    update_cache()
    
    schedule.every(10).minutes.do(update_cache)
    
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
