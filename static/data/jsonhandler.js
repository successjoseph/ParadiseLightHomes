
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
        const resp = await fetch('/static/data/posts.json', {cache: 'no-cache'});
        if (!resp.ok) throw new Error('Failed to load /data/posts.json: ' + resp.status);
        const data = await resp.json();
        renderProjects(Array.isArray(data.projects) ? data.projects : []);
        renderBlog(Array.isArray(data.blog) ? data.blog : []);
      } catch (err) {
        console.error(err);
        document.getElementById('projects-grid').innerHTML = '<div class="col-span-full text-red-600">Could not load projects.</div>';
        document.getElementById('blog-grid').innerHTML = '<div class="col-span-full text-red-600">Could not load blog posts.</div>';
      }
    }

    function renderProjects(items) {
      const container = document.getElementById('projects-grid');
      if (!items || items.length === 0) {
        container.innerHTML = '<div class="col-span-full text-gray-500">No projects found.</div>';
        return;
      }
      container.innerHTML = items.map(p => {
        const sold = p.is_sold ? 'sold-out' : '';
        const coming = p.is_coming ? 'coming-soon' : '';
        const soldClass = sold || coming ? sold + ' ' + coming : '';
        const cover = p.cover || 'img/placeholder.png';
        const header = escapeHtml(p.header || p.title || '');
        const sub = escapeHtml(p.subheader || '');
        const excerpt = escapeHtml(p.excerpt || '');
        const link = p.link || ('/projects/' + (p.slug || ''));
        return `
          <div class="card">
            <h3 class="text-xl font-semibold mb-2">${header}</h3>
            <div class=" ${soldClass}"><img src="${escapeHtml(cover)}" alt="${escapeHtml(p.title || '')}" loading="lazy" class="w-full h-48 object-cover rounded mb-3" /></div>
            <h4 class="text-sm font-semibold mb-1">${sub}</h4>
            <p class="">${excerpt}</p>
            <a href="${escapeHtml(link)}" class="mt-3 inline-block text-green-700 font-semibold hover:underline">View Project →</a>
          </div>
        `;
      }).join('');
    }

    function renderBlog(items) {
      const container = document.getElementById('blog-grid');
      if (!items || items.length === 0) {
        container.innerHTML = '<div class="col-span-full text-gray-500">No blog posts found.</div>';
        return;
      }
      container.innerHTML = items.map(p => {
        const cover = p.cover || 'img/placeholder.png';
        const title = escapeHtml(p.title || p.header || '');
        const excerpt = escapeHtml(p.excerpt || '');
        const link = p.link || ('/blog/' + (p.slug || ''));
        return `
          <article class="card">
            <img src="${escapeHtml(cover)}" alt="${title}" loading="lazy" class="w-full h-48 object-cover rounded mb-4" />
            <h3 class="text-xl font-semibold mb-2">${title}</h3>
            <p class="mb-4">${excerpt}</p>
            <a href="${escapeHtml(link)}" class="text-green-700 font-semibold hover:underline">Read More →</a>
          </article>
        `;
      }).join('');
    }

    document.addEventListener('DOMContentLoaded', () => {
      loadContent();
      // cookie banner demo
      document.getElementById('accept-cookies')?.addEventListener('click', () => {
        document.getElementById('cookie-banner').classList.add('hidden');
      });
    });