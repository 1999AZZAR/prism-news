import flask
from flask import request, jsonify, send_from_directory
import requests
import feedparser
import time
import json
import os
import redis
from urllib.parse import urlparse

app = flask.Flask(__name__, static_folder='.')

# --- CONFIG ---
CACHE_DURATION = 600  # 10 minutes
HN_API = 'https://hacker-news.firebaseio.com/v0'
REDDIT_API = 'https://www.reddit.com'
USER_AGENT = 'Mozilla/5.0 (compatible; PrismBot/1.0; +http://prism.glassgallery.my.id)'

# --- REDIS SETUP ---
# Connect to redis service defined in docker-compose
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
cache = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

# --- HELPERS ---
def get_domain(url):
    try:
        return urlparse(url).hostname.replace('www.', '')
    except:
        return 'Self'

def get_cached(key):
    try:
        data = cache.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis Read Error: {e}")
    return None

def set_cached(key, data):
    try:
        cache.setex(key, CACHE_DURATION, json.dumps(data))
    except Exception as e:
        print(f"Redis Write Error: {e}")

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
                        'id': id
                    })
        return stories
    except Exception as e:
        print(f"HN Error: {e}")
        return []

def fetch_rss(url):
    try:
        d = feedparser.parse(url, agent=USER_AGENT)
        items = []
        for entry in d.entries[:25]:
            link = entry.link
            items.append({
                'title': entry.title,
                'url': link,
                'score': 0,
                'author': entry.get('author', d.feed.get('title', 'Unknown')),
                'time': time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else time.time(),
                'domain': get_domain(link),
                'commentsUrl': link,
                'id': entry.id if hasattr(entry, 'id') else link
            })
        return items
    except Exception as e:
        print(f"RSS Error ({url}): {e}")
        return []

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
    
    # Try cache first
    cached_data = get_cached(category)
    if cached_data:
        return jsonify(cached_data)

    # Fetch fresh
    data = []
    if category == 'tech':
        data = fetch_hn()
    elif category == 'verge':
        data = fetch_rss('https://www.theverge.com/rss/index.xml')
    elif category == 'wired':
        data = fetch_rss('https://www.wired.com/feed/rss')
    elif category == 'techcrunch':
        data = fetch_rss('https://techcrunch.com/feed/')
    elif category == 'ars':
        data = fetch_rss('https://feeds.arstechnica.com/arstechnica/index')
    elif category == 'engadget':
        data = fetch_rss('https://www.engadget.com/rss.xml')
    elif category == 'ai':
        data = fetch_rss('https://www.reddit.com/r/ArtificialIntelligence/.rss')
    elif category == 'design':
        data = fetch_rss('https://www.reddit.com/r/Design/.rss')
    elif category == 'world':
        data = fetch_rss('https://www.reddit.com/r/worldnews/.rss')
    elif category == 'science':
        data = fetch_rss('https://www.reddit.com/r/science/.rss')
    elif category == 'business':
        data = fetch_rss('https://www.reddit.com/r/economics/.rss')
    elif category == 'gaming':
        data = fetch_rss('https://www.reddit.com/r/Games/.rss')
    
    # Save to cache
    if data:
        set_cached(category, data)
        
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
