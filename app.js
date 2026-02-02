const HN_API = 'https://hacker-news.firebaseio.com/v0';
const REDDIT_API = 'https://www.reddit.com';

const CATEGORIES = {
    tech: { name: 'Tech', type: 'hn', state: { ids: [], index: 0 } },
    ai: { name: 'AI', type: 'reddit', endpoint: 'r/ArtificialIntelligence', state: { after: null } },
    design: { name: 'Design', type: 'reddit', endpoint: 'r/Design', state: { after: null } },
    world: { name: 'World', type: 'reddit', endpoint: 'r/worldnews', state: { after: null } },
    science: { name: 'Science', type: 'reddit', endpoint: 'r/science', state: { after: null } },
    space: { name: 'Space', type: 'reddit', endpoint: 'r/space', state: { after: null } },
    business: { name: 'Business', type: 'reddit', endpoint: 'r/economics', state: { after: null } },
    gaming: { name: 'Gaming', type: 'reddit', endpoint: 'r/Games', state: { after: null } }
};

let currentCategory = 'tech';
let isLoading = false;
let hasMore = true;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadCategory('tech');
    window.addEventListener('scroll', handleScroll);
});

async function loadCategory(catKey) {
    if (isLoading && currentCategory === catKey) return;
    
    currentCategory = catKey;
    isLoading = false;
    hasMore = true;

    // Reset State
    Object.keys(CATEGORIES).forEach(k => {
        CATEGORIES[k].state = { ids: [], index: 0, after: null };
    });

    // Update UI Nav
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active-nav');
    });
    document.getElementById(`btn-${catKey}`).classList.add('active-nav');

    // Clear Feed
    const feed = document.getElementById('news-feed');
    feed.innerHTML = '';
    
    // Show Top Loader
    document.getElementById('loading').style.display = 'block';
    
    // Initial fetch
    await loadMore();
    
    // Hide Top Loader
    document.getElementById('loading').style.display = 'none';
}

async function loadMore() {
    if (isLoading || !hasMore) return;
    isLoading = true;

    const loader = document.getElementById('infinite-loader');
    loader.classList.remove('hidden');

    try {
        const config = CATEGORIES[currentCategory];
        let stories = [];

        if (config.type === 'hn') {
            stories = await fetchHN(config);
        } else if (config.type === 'reddit') {
            stories = await fetchReddit(config);
        }

        if (stories.length === 0) {
            hasMore = false;
            loader.classList.add('hidden');
            return;
        }

        const feed = document.getElementById('news-feed');
        // Calculate offset for animation delay based on existing items
        const currentCount = feed.children.length;

        stories.forEach((story, index) => {
            const card = createCard(story, index + currentCount); // Pass total index for color cycling
            feed.appendChild(card);
        });

    } catch (e) {
        console.error(e);
    } finally {
        isLoading = false;
        loader.classList.add('hidden');
    }
}

async function fetchHN(config) {
    // If we haven't fetched the IDs yet, get them
    if (config.state.ids.length === 0) {
        const response = await fetch(`${HN_API}/topstories.json`);
        config.state.ids = await response.json();
    }

    const start = config.state.index;
    const end = start + 12;
    const batchIds = config.state.ids.slice(start, end);

    if (batchIds.length === 0) return [];

    config.state.index = end; // Advance cursor

    const promises = batchIds.map(id => fetch(`${HN_API}/item/${id}.json`).then(r => r.json()));
    const raw = await Promise.all(promises);
    
    return raw.filter(item => item).map(item => ({
        title: item.title,
        url: item.url || `https://news.ycombinator.com/item?id=${item.id}`,
        score: item.score,
        author: item.by,
        time: item.time,
        domain: getDomain(item.url),
        commentsUrl: `https://news.ycombinator.com/item?id=${item.id}`,
        id: item.id
    }));
}

async function fetchReddit(config) {
    let url = `${REDDIT_API}/${config.endpoint}/hot.json?limit=15`;
    if (config.state.after) {
        url += `&after=${config.state.after}`;
    }

    const response = await fetch(url);
    const data = await response.json();
    
    // Update 'after' token for next page
    config.state.after = data.data.after;
    if (!config.state.after) hasMore = false;

    return data.data.children
        .filter(child => !child.data.stickied) 
        .map(child => {
            const item = child.data;
            return {
                title: item.title,
                url: item.url,
                score: item.score,
                author: item.author,
                time: item.created_utc,
                domain: item.domain,
                commentsUrl: `https://www.reddit.com${item.permalink}`,
                id: item.id
            };
        });
}

function handleScroll() {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    
    // Load more when user is 300px from the bottom
    if (scrollTop + clientHeight >= scrollHeight - 300) {
        loadMore();
    }
}

function getDomain(url) {
    if (!url) return 'Self';
    try {
        return new URL(url).hostname.replace('www.', '');
    } catch(e) { return 'Self'; }
}

function createCard(story, index) {
    const div = document.createElement('div');
    div.className = 'glass glass-card rounded-3xl p-6 relative group transition-all duration-500 opacity-0 translate-y-4';
    
    // Animate in
    requestAnimationFrame(() => {
        div.classList.remove('opacity-0', 'translate-y-4');
    });
    
    const time = new Date(story.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Colors based on index
    const colors = ['bg-pastel-purple', 'bg-pastel-blue', 'bg-pastel-pink', 'bg-pastel-green'];
    const accentColor = colors[index % colors.length];

    div.innerHTML = `
        <div class="flex flex-col h-full justify-between">
            <div>
                <div class="flex justify-between items-start mb-4">
                    <span class="inline-flex items-center justify-center w-8 h-8 rounded-full ${accentColor} text-dark text-xs font-bold shadow-lg shadow-white/5">
                        ${index + 1}
                    </span>
                    <span class="text-xs font-mono text-slate-400 bg-white/5 px-2 py-1 rounded-lg border border-white/5">
                        <i class="fa-regular fa-clock mr-1"></i> ${time}
                    </span>
                </div>
                
                <h2 class="text-xl font-bold leading-tight mb-3 text-slate-100 group-hover:text-pastel-purple transition-colors">
                    <a href="${story.url}" target="_blank" class="focus:outline-none">
                        ${story.title}
                        <span class="absolute inset-0"></span>
                    </a>
                </h2>
                
                <p class="text-sm text-slate-400 mb-4 line-clamp-2 font-light">
                    From <span class="text-slate-300 font-medium">${story.domain}</span>
                </p>
            </div>

            <div class="flex items-center justify-between pt-4 border-t border-white/10 mt-2 text-xs text-slate-400">
                <div class="flex items-center gap-3">
                    <span class="flex items-center hover:text-pastel-pink transition-colors z-10">
                        <i class="fa-solid fa-heart mr-1.5 text-slate-600 group-hover:text-pastel-pink transition-colors"></i> ${formatScore(story.score)}
                    </span>
                    <span class="flex items-center hover:text-pastel-blue transition-colors z-10">
                        <i class="fa-solid fa-user mr-1.5 text-slate-600 group-hover:text-pastel-blue transition-colors"></i> ${story.author}
                    </span>
                </div>
                <a href="${story.commentsUrl}" target="_blank" class="z-10 text-slate-500 hover:text-white transition-colors">
                    <i class="fa-solid fa-comment-dots text-lg"></i>
                </a>
            </div>
        </div>
    `;
    return div;
}

function formatScore(score) {
    if (score >= 1000) return (score / 1000).toFixed(1) + 'k';
    return score;
}