let currentCategory = 'tech';
let isLoading = false;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadCategory('tech');
});

async function loadCategory(catKey) {
    if (isLoading && currentCategory === catKey) return;
    
    currentCategory = catKey;
    isLoading = true;

    // Update UI Nav
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active-nav');
    });
    document.getElementById(`btn-${catKey}`).classList.add('active-nav');

    // Show Loader
    const feed = document.getElementById('news-feed');
    feed.innerHTML = '';
    
    document.getElementById('loading').style.display = 'block';

    try {
        const response = await fetch(`/api/news?category=${catKey}`);
        const stories = await response.json();

        document.getElementById('loading').style.display = 'none';

        if (!stories || stories.length === 0) {
            feed.innerHTML = '<div class="text-center text-slate-500 py-10">No stories found.</div>';
            return;
        }

        stories.forEach((story, index) => {
            const card = createCard(story, index);
            feed.appendChild(card);
        });

    } catch (e) {
        console.error(e);
        document.getElementById('loading').innerHTML = '<p class="text-red-400">Connection Error.</p>';
    } finally {
        isLoading = false;
    }
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
