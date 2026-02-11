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

    // Update Nav Pills (Desktop & Mobile)
    document.querySelectorAll('.nav-pill').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const desktopBtn = document.getElementById(`btn-${catKey}`);
    const mobileBtn = document.getElementById(`m-btn-${catKey}`);
    
    if (desktopBtn) desktopBtn.classList.add('active');
    if (mobileBtn) mobileBtn.classList.add('active');

    // Update Hero Title
    const titleMap = {
        'tech': 'Technological Frontier',
        'ai': 'Neural Synthetics',
        'design': 'Visual Engineering',
        'science': 'Quantum Horizons',
        'world': 'Global Context',
        'business': 'Market Logic',
        'gaming': 'Interactive Realities',
        'other': 'The Signal',
        'entertainment': 'Media Stream',
        'music': 'Sonic Architecture',
        'sports': 'Performance Metrics',
        'food': 'Culinary Synthesis',
        'health': 'Biological Core'
    };
    
    const titleEl = document.getElementById('category-title');
    if (titleEl) {
        titleEl.textContent = titleMap[catKey] || 'Intelligence Feed';
    }

    // Show Loader & Hide Feed
    const feed = document.getElementById('news-feed');
    const loader = document.getElementById('loading');
    
    feed.classList.add('opacity-0');
    loader.classList.remove('hidden');
    loader.classList.add('flex');

    try {
        const response = await fetch(`/api/news?category=${catKey}`);
        const stories = await response.json();

        // Clear feed
        feed.innerHTML = '';
        
        // Hide Loader
        loader.classList.add('hidden');
        loader.classList.remove('flex');

        if (!stories || stories.length === 0) {
            feed.innerHTML = '<div class="col-span-full text-center text-slate-500 py-20 font-mono tracking-widest uppercase text-xs">No signals received.</div>';
            feed.classList.remove('opacity-0');
            return;
        }

        stories.forEach((story, index) => {
            const card = createCard(story, index);
            feed.appendChild(card);
        });

        // Trigger fade in
        setTimeout(() => {
            feed.classList.remove('opacity-0');
        }, 100);

    } catch (e) {
        console.error(e);
        loader.innerHTML = '<p class="text-red-400 font-mono uppercase text-xs tracking-widest">Initialization Failed. Check Uplink.</p>';
    } finally {
        isLoading = false;
    }
}

function createCard(story, index) {
    const div = document.createElement('div');
    div.className = 'glass-card rounded-[2.5rem] p-8 relative group flex flex-col justify-between overflow-hidden';
    
    const time = new Date(story.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = new Date(story.time * 1000).toLocaleDateString([], { month: 'short', day: 'numeric' });
    
    // Modern gradients for numbers
    const gradients = [
        'from-accent-primary to-accent-secondary',
        'from-accent-secondary to-accent-tertiary',
        'from-accent-tertiary to-accent-primary',
        'from-m3-primary to-accent-secondary'
    ];
    const accentGradient = gradients[index % gradients.length];

    div.innerHTML = `
        <!-- Background Glow -->
        <div class="absolute -right-10 -top-10 w-32 h-32 bg-accent-primary/5 blur-3xl group-hover:bg-accent-primary/10 transition-colors duration-500"></div>
        
        <div class="relative z-10">
            <div class="flex justify-between items-center mb-6">
                <div class="flex items-center gap-3">
                    <span class="flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br ${accentGradient} text-void text-sm font-black shadow-xl shadow-accent-primary/10">
                        ${index + 1}
                    </span>
                    <div>
                        <p class="text-[10px] font-bold uppercase tracking-widest text-slate-500">${story.source_name || 'Hacker News'}</p>
                        <p class="text-[10px] font-medium text-slate-400 opacity-60">${date}</p>
                    </div>
                </div>
                <div class="text-[10px] font-mono font-bold text-accent-primary bg-accent-primary/10 px-3 py-1.5 rounded-full border border-accent-primary/20">
                    <i class="fa-regular fa-clock mr-1"></i> ${time}
                </div>
            </div>
            
            <h3 class="text-2xl font-bold leading-[1.3] mb-6 text-slate-100 group-hover:text-white transition-colors">
                <a href="${story.url}" target="_blank" class="focus:outline-none decoration-accent-primary/30 decoration-2 hover:underline underline-offset-8 transition-all">
                    ${story.title}
                </a>
            </h3>
            
            <div class="flex items-center gap-2 mb-8">
                <div class="w-2 h-2 rounded-full bg-accent-secondary"></div>
                <p class="text-xs text-slate-400 font-medium">
                    via <span class="text-slate-300 font-bold tracking-tight">${story.domain}</span>
                </p>
            </div>
        </div>

        <div class="relative z-10 flex items-center justify-between pt-6 border-t border-white/5">
            <div class="flex items-center gap-6">
                <div class="flex flex-col">
                    <span class="text-[9px] uppercase tracking-tighter text-slate-500 font-bold mb-0.5">Author</span>
                    <span class="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                         ${story.author}
                    </span>
                </div>
                <div class="flex flex-col">
                    <span class="text-[9px] uppercase tracking-tighter text-slate-500 font-bold mb-0.5">Weight</span>
                    <span class="text-xs font-bold text-accent-tertiary">
                        ${formatScore(story.score)}
                    </span>
                </div>
            </div>
            
            <a href="${story.commentsUrl}" target="_blank" class="w-10 h-10 rounded-2xl bg-white/5 flex items-center justify-center text-slate-400 hover:bg-accent-primary hover:text-void transition-all duration-300 group/btn shadow-inner">
                <i class="fa-solid fa-comment-dots text-lg group-hover/btn:scale-110 transition-transform"></i>
            </a>
        </div>
    `;
    return div;
}

function formatScore(score) {
    if (score >= 1000) return (score / 1000).toFixed(1) + 'k';
    return score;
}
