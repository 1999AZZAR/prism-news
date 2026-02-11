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
    document.querySelectorAll('.neo-m3-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetBtn = document.getElementById(`btn-${catKey}`);
    if (targetBtn) targetBtn.classList.add('active');

    // Update Hero Title & Label
    const catLabel = document.getElementById('category-label');
    const titleMap = {
        'tech': 'Technological Frontier',
        'edan': 'Madness Unleashed',
        'ai': 'Neural Synthetics',
        'design': 'Visual Engineering',
        'science': 'Quantum Horizons',
        'world': 'Global Context',
        'business': 'Market Logic',
        'gaming': 'Interactive Realities',
        'other': 'Raw Signals',
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
    
    feed.style.display = 'none';
    loader.style.display = 'flex';

    try {
        const response = await fetch(`/api/news?category=${catKey}&t=${Date.now()}`);
        const stories = await response.json();

        // Clear feed
        feed.innerHTML = '';
        
        // Hide Loader
        loader.style.display = 'none';

        if (!stories || stories.length === 0) {
            feed.innerHTML = `
                <div class="col-span-full neo-m3-card p-24 text-center bg-white">
                    <h3 class="font-black text-6xl uppercase tracking-tighter mb-4 text-black">SILENCE</h3>
                    <p class="font-mono text-xs font-black uppercase tracking-widest text-slate-400">Zero data received from current uplink: ${catKey}</p>
                </div>
            `;
            feed.style.display = 'grid';
            return;
        }

        stories.forEach((story, index) => {
            const card = createCard(story, index);
            feed.appendChild(card);
        });

        // Show grid
        feed.style.display = 'grid';

    } catch (e) {
        console.error(e);
        loader.innerHTML = '<div class="neo-m3-card p-10 bg-red-600 text-white font-black text-2xl uppercase">Critical Uplink Failure.</div>';
    } finally {
        isLoading = false;
    }
}

function createCard(story, index) {
    const div = document.createElement('div');
    div.className = 'neo-m3-card flex flex-col justify-between overflow-hidden group';
    
    const time = new Date(story.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(story.time * 1000).toLocaleDateString([], { month: 'short', day: 'numeric' });
    
    // Verge-style Tonal Accents
    const accents = ['#ff00ff', '#3b82f6', '#22c55e', '#f97316', '#a855f7'];
    const accent = accents[index % accents.length];

    div.innerHTML = `
        <div class="p-8">
            <div class="flex justify-between items-center mb-8">
                <div class="flex items-center gap-4">
                    <span class="flex items-center justify-center w-12 h-12 border-4 border-black text-black text-xl font-black rounded-2xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]" style="background-color: ${accent}">
                        ${index + 1}
                    </span>
                    <div class="flex flex-col">
                        <p class="text-[10px] font-black uppercase tracking-widest text-slate-400">${story.source_name || 'Hacker News'}</p>
                        <p class="text-[10px] font-bold text-black uppercase opacity-40">${date}</p>
                    </div>
                </div>
                <div class="font-mono text-[10px] font-bold bg-black text-white px-3 py-1.5 rounded-lg">
                    ${time}
                </div>
            </div>
            
            <h3 class="text-3xl font-black leading-[1.1] mb-8 text-black group-hover:text-hybrid-primary transition-colors duration-300 tracking-tight">
                <a href="${story.url}" target="_blank" class="focus:outline-none">
                    ${story.title}
                </a>
            </h3>
            
            <div class="flex items-center gap-2">
                <span class="verge-label text-[9px]">Uplink</span>
                <p class="font-mono text-[10px] font-black uppercase tracking-tight text-slate-500">
                    ${story.domain}
                </p>
            </div>
        </div>

        <div class="bg-slate-50 p-6 border-t-4 border-black flex items-center justify-between">
            <div class="flex gap-8">
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase text-slate-400 tracking-widest mb-1">Signal By</span>
                    <span class="text-xs font-black text-black truncate max-w-[120px]">${story.author}</span>
                </div>
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase text-slate-400 tracking-widest mb-1">Magnitude</span>
                    <span class="text-xs font-black text-hybrid-primary">${formatScore(story.score)}</span>
                </div>
            </div>
            
            <a href="${story.commentsUrl}" target="_blank" class="w-14 h-14 bg-white border-4 border-black flex items-center justify-center text-black hover:bg-black hover:text-white transition-all rounded-2xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-none active:translate-x-1 active:translate-y-1">
                <i class="fa-solid fa-comment-dots text-2xl"></i>
            </a>
        </div>
    `;
    return div;
}

function formatScore(score) {
    if (score >= 1000) return (score / 1000).toFixed(1) + 'k';
    return score;
}
