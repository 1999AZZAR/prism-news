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

    // Update Labels
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
        'other': 'The Archive',
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
    
    feed.classList.add('opacity-0');
    loader.classList.remove('hidden');

    try {
        const response = await fetch(`/api/news?category=${catKey}&t=${Date.now()}`);
        const stories = await response.json();

        // Clear feed
        feed.innerHTML = '';
        
        // Hide Loader
        loader.classList.add('hidden');

        if (!stories || stories.length === 0) {
            feed.innerHTML = `
                <div class="col-span-full neo-m3-card p-20 text-center">
                    <h3 class="font-black text-4xl uppercase tracking-tighter mb-4">No Signals Detected</h3>
                    <p class="font-mono text-xs opacity-50 uppercase tracking-widest">Uplink sequence silent for category: ${catKey}</p>
                </div>
            `;
            feed.classList.remove('opacity-0');
            return;
        }

        stories.forEach((story, index) => {
            const card = createCard(story, index);
            feed.appendChild(card);
        });

        // Trigger fade in
        feed.classList.remove('opacity-0');

    } catch (e) {
        console.error(e);
        loader.innerHTML = '<div class="neo-m3-card p-10 bg-red-500 text-white font-black text-xl">UPLINK_FAILURE: CHECK GRID CONNECTION.</div>';
    } finally {
        isLoading = false;
    }
}

function createCard(story, index) {
    const div = document.createElement('div');
    div.className = 'neo-m3-card p-0 flex flex-col justify-between overflow-hidden group';
    
    const time = new Date(story.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(story.time * 1000).toLocaleDateString([], { month: 'short', day: 'numeric' });
    
    // Tonal Pastel Accents
    const accents = [
        'bg-hybrid-pastel-purple', 
        'bg-hybrid-pastel-blue', 
        'bg-hybrid-pastel-green', 
        'bg-hybrid-pastel-pink'
    ];
    const accent = accents[index % accents.length];

    div.innerHTML = `
        <div class="p-8">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-4">
                    <span class="inline-flex items-center justify-center w-12 h-12 neo-m3-border ${accent} text-black text-xl font-black">
                        ${index + 1}
                    </span>
                    <div>
                        <p class="text-[10px] font-black uppercase tracking-tighter text-slate-400">${story.source_name || 'Hacker News'}</p>
                        <p class="text-[10px] font-bold text-black uppercase opacity-60">${date}</p>
                    </div>
                </div>
                <div class="font-mono text-[9px] font-black bg-slate-100 text-black px-2 py-1 neo-m3-border rounded-lg border-2">
                    ${time}
                </div>
            </div>
            
            <h3 class="text-2xl font-black leading-tight mb-6 group-hover:text-hybrid-primary transition-colors duration-300">
                <a href="${story.url}" target="_blank" class="focus:outline-none">
                    ${story.title}
                </a>
            </h3>
            
            <div class="flex items-center gap-2 mb-2">
                <span class="verge-accent text-[9px]">Domain</span>
                <p class="font-mono text-[10px] font-black uppercase tracking-tight text-slate-400">
                    ${story.domain}
                </p>
            </div>
        </div>

        <div class="bg-slate-50 p-6 border-t-2 border-black flex items-center justify-between">
            <div class="flex gap-6">
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase opacity-40">Author</span>
                    <span class="text-xs font-black truncate max-w-[100px] text-slate-800">${story.author}</span>
                </div>
                <div class="flex flex-col">
                    <span class="text-[8px] font-black uppercase opacity-40">Weight</span>
                    <span class="text-xs font-bold text-hybrid-primary">${formatScore(story.score)}</span>
                </div>
            </div>
            
            <a href="${story.commentsUrl}" target="_blank" class="w-12 h-12 bg-white neo-m3-border border-2 flex items-center justify-center text-black hover:bg-black hover:text-white transition-all rounded-xl shadow-neo-sm hover:shadow-none active:translate-x-1 active:translate-y-1">
                <i class="fa-solid fa-comment-dots text-lg"></i>
            </a>
        </div>
    `;
    return div;
}

function formatScore(score) {
    if (score >= 1000) return (score / 1000).toFixed(1) + 'k';
    return score;
}
