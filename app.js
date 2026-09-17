let currentCategory = "tech";
let isLoading = false;
let currentStories = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 21;

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

// --- BACK TO TOP (BTT) SCROLL CONTROLLER ---
const bttBtn = document.getElementById("btt-btn");
window.addEventListener("scroll", () => {
    if (window.scrollY > 300) {
        bttBtn?.classList.add("visible");
    } else {
        bttBtn?.classList.remove("visible");
    }
}, { passive: true });

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadCategory(catKey, force = false) {
    if (!force && isLoading && currentCategory === catKey) return;

    currentCategory = catKey;
    isLoading = true;
    currentPage = 1;
    currentStories = [];
    syncCategoryMeta(catKey);
    syncNav(catKey);

    const feed = document.getElementById("news-feed");
    const loader = document.getElementById("loading");
    const pagination = document.getElementById("pagination-wrap");

    if (pagination) pagination.style.display = "none";
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
            if (pagination) pagination.style.display = "none";
            return;
        }

        currentStories = stories;
        renderCurrentPage();
    } catch (error) {
        console.error(error);
        loader.innerHTML = `
            <div class="archive-loader-panel">
                <p class="archive-meta">SYSTEM NOTICE</p>
                <p>Archive stream temporarily unavailable.</p>
            </div>
        `;
        if (pagination) pagination.style.display = "none";
    } finally {
        isLoading = false;
    }
}

function renderCurrentPage() {
    const feed = document.getElementById("news-feed");
    const pagination = document.getElementById("pagination-wrap");
    feed.innerHTML = "";

    const totalItems = currentStories.length;
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

    if (currentPage > totalPages) currentPage = totalPages || 1;
    if (currentPage < 1) currentPage = 1;

    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, totalItems);
    const pageStories = currentStories.slice(startIndex, endIndex);

    pageStories.forEach((story, i) => {
        feed.appendChild(createCard(story, startIndex + i));
    });
    feed.style.display = "grid";

    // Pagination controls: only render when total records exceed 21 items
    if (totalItems > ITEMS_PER_PAGE && pagination) {
        renderPaginationControls(pagination, currentPage, totalPages, totalItems);
        pagination.style.display = "flex";
    } else if (pagination) {
        pagination.style.display = "none";
    }
}

function renderPaginationControls(container, page, totalPages, totalItems) {
    let pagesHtml = "";

    // Previous Button
    const prevDisabled = page <= 1 ? "disabled" : "";
    pagesHtml += `<button class="archive-page-btn" ${prevDisabled} onclick="goToPage(${page - 1})" aria-label="Previous page">[ PREV ]</button>`;

    // Numeric Buttons
    for (let p = 1; p <= totalPages; p++) {
        const activeClass = p === page ? "active" : "";
        pagesHtml += `<button class="archive-page-btn ${activeClass}" onclick="goToPage(${p})" aria-label="Page ${p}">[ ${String(p).padStart(2, "0")} ]</button>`;
    }

    // Next Button
    const nextDisabled = page >= totalPages ? "disabled" : "";
    pagesHtml += `<button class="archive-page-btn" ${nextDisabled} onclick="goToPage(${page + 1})" aria-label="Next page">[ NEXT ]</button>`;

    container.innerHTML = `
        <p class="archive-pagination-info">PAGE ${String(page).padStart(2, "0")} OF ${String(totalPages).padStart(2, "0")} &bull; TOTAL ${totalItems} RECORDS</p>
        <div class="archive-pagination">
            ${pagesHtml}
        </div>
    `;
}

function goToPage(page) {
    const totalPages = Math.ceil(currentStories.length / ITEMS_PER_PAGE);
    if (page < 1 || page > totalPages || page === currentPage) return;
    currentPage = page;
    renderCurrentPage();

    const hero = document.querySelector(".archive-hero");
    if (hero) {
        hero.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
        window.scrollTo({ top: 0, behavior: "smooth" });
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
    const specimenSVG = generateSpecimenSVG(`${safeTitle}|${safeDomain}|${index}`);

    const visualHtml = story.image ?
        `<img src="${safeUrlOrFallback(story.image)}" alt="${safeTitle}" class="archive-img" loading="lazy" onerror="this.onerror=null; this.parentElement.innerHTML=\`${specimenSVG.replace(/"/g, '&quot;')}\`;" />` :
        specimenSVG;

    card.innerHTML = `
        <div class="archive-visual" aria-hidden="true">
            ${visualHtml}
        </div>

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
            <a class="archive-comments" href="${safeCommentsUrl}" target="_blank" rel="noopener noreferrer">READ_MORE</a>
        </footer>
    `;

    return card;
}

function generateSpecimenSVG(input) {
    const seed = getSeed(input);
    const lineA = pickColor(seed);
    const lineB = pickColor(seed >> 3);
    const lineC = pickColor(seed >> 5);

    const m1 = (seed % 9) + 3;
    const n1 = ((seed % 40) / 20) + 0.7;
    const n2 = ((seed >> 2) % 90) / 10 + 1;
    const n3 = ((seed >> 4) % 90) / 10 + 1;
    const m2 = ((seed >> 6) % 7) + 2;

    let layers = "";
    for (let i = 1; i <= 4; i += 1) {
        const scale = 10 + i * 7.5;
        const rotation = (seed % 360) + i * 18;
        const opacity = (0.35 - i * 0.05).toFixed(2);
        layers += `<path d="${generatePath(60, 40, scale, [m1, n1, n2, n3])}" fill="none" stroke="${lineA}" stroke-width="0.6" opacity="${opacity}" transform="rotate(${rotation} 60 40)" />`;
        if (i % 2 === 0) {
            layers += `<path d="${generatePath(60, 40, scale * 0.75, [m2, 2, 1, 1])}" fill="none" stroke="${lineB}" stroke-width="0.45" opacity="0.2" transform="rotate(${-rotation} 60 40)" stroke-dasharray="1.4 2.2" />`;
        }
    }

    let nodes = "";
    const orbitCount = (seed % 4) + 3;
    for (let i = 0; i < orbitCount; i += 1) {
        const angle = (i * (360 / orbitCount) + (seed % 80)) * (Math.PI / 180);
        const ox = 60 + 24 * Math.cos(angle);
        const oy = 40 + 24 * Math.sin(angle);
        nodes += `<circle cx="${ox.toFixed(2)}" cy="${oy.toFixed(2)}" r="1.1" fill="none" stroke="${lineC}" stroke-width="0.5" opacity="0.4" />`;
        nodes += `<line x1="60" y1="40" x2="${ox.toFixed(2)}" y2="${oy.toFixed(2)}" stroke="${lineC}" stroke-width="0.35" opacity="0.2" stroke-dasharray="1 1.8" />`;
    }

    return `
        <svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
            <rect width="120" height="80" fill="transparent"></rect>
            <g opacity="0.28">
                <line x1="0" y1="40" x2="120" y2="40" stroke="${lineC}" stroke-width="0.35" />
                <line x1="60" y1="0" x2="60" y2="80" stroke="${lineC}" stroke-width="0.35" />
                <circle cx="60" cy="40" r="33" fill="none" stroke="${lineC}" stroke-width="0.35" stroke-dasharray="1.2 2.4" />
            </g>
            <g>${layers}${nodes}</g>
            <text x="4" y="75" font-size="4.2" font-family="JetBrains Mono, monospace" fill="${lineC}" opacity="0.65">SPEC ${String(seed % 99999).padStart(5, "0")}</text>
        </svg>
    `;
}

function getSeed(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i += 1) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
        hash |= 0;
    }
    return Math.abs(hash);
}

function pickColor(seed) {
    const palette = ["#8B1A1A", "#7A7068", "#2A2520", "#6B5E52"];
    return palette[Math.abs(seed) % palette.length];
}

function superformula(theta, m, n1, n2, n3, a = 1, b = 1) {
    const t1 = Math.pow(Math.abs(Math.cos((m * theta) / 4) / a), n2);
    const t2 = Math.pow(Math.abs(Math.sin((m * theta) / 4) / b), n3);
    return Math.pow(t1 + t2, -1 / n1);
}

function generatePath(cx, cy, scale, params) {
    const steps = 120;
    const points = [];
    for (let i = 0; i <= steps; i += 1) {
        const theta = (i * Math.PI * 2) / steps;
        const r = superformula(theta, ...params);
        const x = cx + r * scale * Math.cos(theta);
        const y = cy + r * scale * Math.sin(theta);
        points.push(`${x.toFixed(2)},${y.toFixed(2)}`);
    }
    return `M ${points.join(" L ")} Z`;
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
