// small helper to escape user content (prevent accidental XSS)
function escapeHtml(str) {
  if (!str && str !== 0) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function loadContent() {
  try {
    const resp = await fetch("/static/data/posts.json", { cache: "no-cache" });
    if (!resp.ok)
      throw new Error("Failed to load /data/posts.json: " + resp.status);
    const data = await resp.json();
    renderProjects(Array.isArray(data.projects) ? data.projects : []);
    renderBlog(Array.isArray(data.blog) ? data.blog : []);
  } catch (err) {
    console.error(err);
    document.getElementById("projects-grid").innerHTML =
      '<div class="col-span-full text-red-600">Could not load projects.</div>';
    document.getElementById("blog-grid").innerHTML =
      '<div class="col-span-full text-red-600">Could not load blog posts.</div>';
  }
}

function renderProjects(items) {
  const container = document.getElementById("projects-grid");
  if (!items || items.length === 0) {
    container.innerHTML =
      '<div class="col-span-full text-gray-500">No projects found.</div>';
    return;
  }
  container.innerHTML = items
    .map((p) => {
      const sold = p.is_sold ? "sold-out" : "";
      const coming = p.is_coming ? "coming-soon" : "";
      const soldClass = sold || coming ? sold + " " + coming : "";
      const cover = p.cover || "img/placeholder.png";
      const header = escapeHtml(p.header || p.title || "");
      const sub = escapeHtml(p.subheader || "");
      const excerpt = escapeHtml(p.excerpt || "");
      const link = p.link || "/projects/" + (p.slug || "");
      return `
          <div class="card">
            <h3 class="text-xl font-semibold mb-2">${header}</h3>
            <div class=" ${soldClass}"><img src="${escapeHtml(
        cover
      )}" alt="${escapeHtml(
        p.title || ""
      )}" loading="lazy" class="w-full h-48 object-cover rounded mb-3" /></div>
            <h4 class="text-sm font-semibold mb-1">${sub}</h4>
            <p class="">${excerpt}</p>
            <a href="${escapeHtml(
              link
            )}" class="mt-3 inline-block text-green-700 font-semibold hover:underline">View Project →</a>
          </div>
        `;
    })
    .join("");
}

function renderBlog(items) {
  const container = document.getElementById("blog-grid");
  if (!items || items.length === 0) {
    container.innerHTML =
      '<div class=" text-gray-500">No blog posts found.</div>';
    return;
  }
  container.innerHTML = items
    .map((p) => {
      const cover =
        p.cover && p.cover.trim() ? p.cover : "static/img/placeholder.png";
      const title = escapeHtml(p.title || p.header || "");
      const excerpt = escapeHtml(p.excerpt || "");
      const link = p.link || "/projects/" + (p.slug || "") + ".html";
      return ` <a href="${escapeHtml(link)}">
  <article class="blog-card" >
    <img  src="${escapeHtml(
      cover
    )}" alt="${title}" loading="lazy" class="w-full h-48 object-cover" />
    <div class="p-4">
      <h3 class="text-lg font-semibold mb-2">${title}</h3>
      <p class="mb-4 text-gray-600">${excerpt}</p>
      <a href="${escapeHtml(
        link
      )}" class="text-green-700 font-semibold items-end hover:underline">Read More →</a>
    </div>
  </article>
  </a>
`;
    })
    .join("");
}
const carousel = document.getElementById("blog-carousel");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");

const card = document.querySelector(".card");
const cardStyle = card ? window.getComputedStyle(card) : null;
const gap = cardStyle ? parseInt(cardStyle.marginRight) || 0 : 16; // handle gap if using margin
const cardWidth = card ? card.offsetWidth + gap : 300;

let autoScroll;

// Clone first 3 cards for seamless loop
function cloneCards() {
  const cards = Array.from(carousel.children);
  cards.slice(0, 3).forEach((c) => {
    const clone = c.cloneNode(true);
    carousel.appendChild(clone);
  });
}
cloneCards();

// Next button → move 1 card
nextBtn.addEventListener("click", () => {
  carousel.scrollBy({ left: cardWidth, behavior: "smooth" });
  resetAutoScroll();
});

// Prev button → move 1 card back
prevBtn.addEventListener("click", () => {
  carousel.scrollBy({ left: -cardWidth, behavior: "smooth" });
  resetAutoScroll();
});

// Auto-scroll → 1 card per iteration
function startAutoScroll() {
  autoScroll = setInterval(() => {
    carousel.scrollBy({ left: 1, behavior: "smooth" });

    // If we've hit the cloned section → snap back invisibly
    if (
      carousel.scrollLeft >=
      carousel.scrollWidth - carousel.clientWidth - cardWidth
    ) {
      setTimeout(() => {
        carousel.scrollTo({ left: 0, behavior: "instant" });
      }, 600); // wait for smooth scroll animation
    }
  }, 10000);
}

function resetAutoScroll() {
  clearInterval(autoScroll);
  startAutoScroll();
}

startAutoScroll();

document.addEventListener("DOMContentLoaded", () => {
  loadContent();
  // cookie banner demo
  document.getElementById("accept-cookies")?.addEventListener("click", () => {
    document.getElementById("cookie-banner").classList.add("hidden");
  });
});
