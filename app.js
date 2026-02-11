let currentCategory = 'tech';
let isLoading = false;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadCategory('tech');
});

async function loadCategory(catKey, force = false) {
    if (!force && isLoading && currentCategory === catKey) return;
    
    currentCategory = catKey;
    isLoading = true;

    // Update Nav Buttons
    document.querySelectorAll('.neo-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetBtn = document.getElementById(`btn-${catKey}`);
    if (targetBtn) targetBtn.classList.add('active');

    // Update Marquee & Labels
    const marqueeCat = document.getElementById('marquee-cat');
    if (marqueeCat) marqueeCat.textContent = catKey.toUpperCase();
    
    const catLabel = document.getElementById('category-label');
    const titleMap = {
        'tech': 'Technological Frontier',
        'ai': 'Neural Synthetics',
        'design': 'Visual Engineering',
        'science': 'Quantum Horizons',
        'world': 'Global Context',
        'business': 'Market Logic',
        'gaming': 'Interactive Realities',
        'other': 'Raw Signal',
        'entertainment': 'Media Stream',
        'music': 'Sonic Architecture',
        'sports': 'Performance Metrics',
        'food': 'Culinary Synthesis',
        'health': 'Biological Core'
    };
    if (catLabel) catLabel.textContent = titleMap[catKey] || 'Intelligence Feed';

    // Show Loader & Hide Feed
    const feed = document.getElementById('news-feed');
    const loader = document.getElementById('loading');
    
    feed.style.visibility = 'hidden';
    loader.classList.remove('hidden');

    try {
        const response = await fetch(`/api/news?category=${catKey}`);
        const stories = await response.json();

        // Clear feed
        feed.innerHTML = '';
        
        // Hide Loader
        loader.classList.add('hidden');

        if (!stories || stories.length === 0) {
            feed.innerHTML = '<div class="col-span-full bg-white neo-border p-20 text-center font-mega font-black text-4xl uppercase text-black">Zero Signals Received.</div>';
            feed.style.visibility = 'visible';
            return;
        }

        stories.forEach((story, index) => {
            const card = createCard(story, index);
            feed.appendChild(card);
        });

        // Ensure visible
        feed.style.visibility = 'visible';

    } catch (e) {
        console.error(e);
        loader.innerHTML = '<div class="bg-red-500 text-white neo-border p-10 font-mega font-black text-3xl">UPLINK FAILURE. CHECK NETWORK.</div>';
    } finally {
        isLoading = false;
    }
}

function createCard(story, index) {
    const div = document.createElement('div');
    div.className = 'neo-card p-0 flex flex-col justify-between overflow-hidden group';
    
    const time = new Date(story.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(story.time * 1000).toLocaleDateString([], { month: 'short', day: 'numeric' });
    
    // Clash colors based on index
    const accentColors = ['bg-neo-pink', 'bg-neo-blue', 'bg-neo-green', 'bg-neo-orange', 'bg-neo-purple'];
    const accent = accentColors[index % accentColors.length];

    div.innerHTML = `
        <div class="p-8 bg-white">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-4">
                    <span class="inline-flex items-center justify-center w-12 h-12 neo-border ${accent} text-black text-xl font-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                        ${index + 1}
                    </span>
                    <div>
                        <p class="text-xs font-black uppercase tracking-tighter text-black">${story.source_name || 'Hacker News'}</p>
                        <p class="text-[10px] font-bold opacity-50 uppercase text-black">${date}</p>
                    </div>
                </div>
                <div class="font-mono text-xs font-black bg-black text-white px-3 py-1 neo-border">
                    ${time}
                </div>
            </div>
            
            <h3 class="text-2xl font-black leading-tight mb-6 group-hover:underline decoration-4 underline-offset-4 text-black">
                <a href="${story.url}" target="_blank" class="focus:outline-none">
                    ${story.title}
                </a>
            </h3>
            
            <div class="inline-block bg-neo-white neo-border px-3 py-1 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                <p class="text-[10px] font-black uppercase text-black">
                    DOMAIN: <span class="text-neo-blue">${story.domain}</span>
                </p>
            </div>
        </div>

        <div class="bg-black text-white p-6 border-t-4 border-black flex items-center justify-between">
            <div class="flex gap-6">
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase text-neo-yellow opacity-80">Author</span>
                    <span class="text-xs font-black tracking-tight truncate max-w-[100px]">${story.author}</span>
                </div>
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase text-neo-yellow opacity-80">Score</span>
                    <span class="text-xs font-black">${formatScore(story.score)}</span>
                </div>
            </div>
            
            <a href="${story.commentsUrl}" target="_blank" class="w-12 h-12 bg-white neo-border flex items-center justify-center text-black hover:bg-neo-yellow transition-colors shadow-[4px_4px_0px_0px_rgba(255,255,255,0.2)] active:shadow-none">
                <i class="fa-solid fa-comment-dots text-xl"></i>
            </a>
        </div>
    `;
    return div;
}

function formatScore(score) {
    if (score >= 1000) return (score / 1000).toFixed(1) + 'k';
    return score;
}
