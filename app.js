let currentCategory = "tech";
let isLoading = false;

const categoryLabels = {
    tech: "Technological Frontier",
    edan: "Independent Archive / Edan",
    ai: "Neural Systems",
    design: "Design Canon",
    science: "Research Signals",
    world: "World Desk",
    business: "Market Ledger",
    gaming: "Interactive Media",
    entertainment: "Culture Desk",
    music: "Sound Studies",
    sports: "Sports Bulletin",
    food: "Food Notes",
    travel: "Travel Dispatch",
    health: "Health Review",
    other: "Open File"
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => loadCategory("tech", true));
} else {
    loadCategory("tech", true);
}

async function loadCategory(catKey, force = false) {
    if (!force && isLoading && currentCategory === catKey) return;

    currentCategory = catKey;
    isLoading = true;
    syncCategoryMeta(catKey);
    syncNav(catKey);

    const feed = document.getElementById("news-feed");
    const loader = document.getElementById("loading");
    loader.style.display = "grid";
    feed.style.display = "none";
    feed.innerHTML = "";

    try {
        const response = await fetch(`/api/news?category=${encodeURIComponent(catKey)}&t=${Date.now()}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const stories = await response.json();
        loader.style.display = "none";

        if (!Array.isArray(stories) || stories.length === 0) {
            feed.innerHTML = `
                <article class="archive-card archive-empty">
                    <p class="archive-meta">CATALOG STATUS</p>
                    <h3>No records available</h3>
                    <p class="archive-note">No entries were returned for <strong>${safeText(catKey)}</strong>.</p>
                </article>
            `;
            feed.style.display = "grid";
            return;
        }

        stories.forEach((story, index) => feed.appendChild(createCard(story, index)));
        feed.style.display = "grid";
    } catch (error) {
        console.error(error);
        loader.innerHTML = `
            <div class="archive-loader-panel">
                <p class="archive-meta">SYSTEM NOTICE</p>
                <p>Archive stream temporarily unavailable.</p>
            </div>
        `;
    } finally {
        isLoading = false;
    }
}

function syncNav(catKey) {
    document.querySelectorAll(".archive-nav-btn").forEach((button) => {
        button.classList.toggle("active", button.id === `btn-${catKey}`);
    });
}

function syncCategoryMeta(catKey) {
    const label = document.getElementById("category-label");
    const pageTitle = document.getElementById("hero-title");
    const value = categoryLabels[catKey] || "Open File";

    if (label) label.textContent = value;
    if (pageTitle) pageTitle.textContent = value;
}

function createCard(story, index) {
    const card = document.createElement("article");
    card.className = "archive-card";

    const published = new Date((story.time || 0) * 1000);
    const safeTitle = safeText(story.title || "Untitled record");
    const safeSource = safeText(story.source_name || story.domain || "Unknown Source");
    const safeAuthor = safeText(story.author || "Unknown");
    const safeDomain = safeText(story.domain || "n/a");
    const safeUrl = safeUrlOrFallback(story.url);
    const safeCommentsUrl = safeUrlOrFallback(story.commentsUrl);

    card.innerHTML = `
        <header class="archive-card-head">
            <p class="archive-meta">ENTRY ${String(index + 1).padStart(3, "0")}</p>
            <time class="archive-meta">${formatDate(published)} / ${formatTime(published)}</time>
        </header>

        <h3 class="archive-title">
            <a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${safeTitle}</a>
        </h3>

        <p class="archive-note">${safeSource}</p>

        <footer class="archive-card-foot">
            <dl>
                <div><dt>AUTHOR</dt><dd>${safeAuthor}</dd></div>
                <div><dt>SCORE</dt><dd>${formatScore(story.score)}</dd></div>
                <div><dt>DOMAIN</dt><dd>${safeDomain}</dd></div>
            </dl>
            <a class="archive-comments" href="${safeCommentsUrl}" target="_blank" rel="noopener noreferrer">COMMENTS</a>
        </footer>
    `;

    return card;
}

function formatScore(score) {
    const value = Number(score || 0);
    if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
    return `${value}`;
}

function formatDate(date) {
    if (Number.isNaN(date.getTime())) return "N/A";
    return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "2-digit" });
}

function formatTime(date) {
    if (Number.isNaN(date.getTime())) return "N/A";
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function safeText(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function safeUrlOrFallback(value) {
    try {
        const parsed = new URL(value);
        return parsed.href;
    } catch {
        return "#";
    }
}
