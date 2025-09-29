from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
import json, os, uuid, re
from werkzeug.utils import secure_filename
from datetime import datetime
import markdown
from markupsafe import Markup, escape

app = Flask(__name__)
app.secret_key = "supersecret"

# Upload config
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB (bumped a bit)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_POSTS = os.path.join('static', 'data', 'posts.json')
DATA_VERIFIER = os.path.join('static', 'data', 'verifier.json')
DATA_PAGES = os.path.join('static', 'data', 'project_pages.json')

# --------------------
# Helpers
# --------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def save_uploaded_file(file):
    if not file:
        return None
    filename = file.filename
    if filename == '':
        return None
    if not allowed_file(filename):
        return None
    filename = secure_filename(filename)
    unique = f"{uuid.uuid4().hex}_{filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], unique)
    file.save(path)
    # return web path
    return os.path.join('static', 'uploads', unique).replace('\\', '/')

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def slugify(value):
    if not value:
        return ''
    s = value.strip().lower()
    s = re.sub(r'https?://', '', s)
    s = s.split('/')[-1]  # take last segment if a path
    s = re.sub(r'\.html$', '', s)
    s = re.sub(r'[^a-z0-9\-]+', '-', s)
    s = re.sub(r'\-+', '-', s)
    s = s.strip('-')
    return s or uuid.uuid4().hex[:8]

def ensure_project_slugs_and_save():
    posts = load_json(DATA_POSTS)
    changed = False
    projects = posts.get('projects', [])
    for p in projects:
        if not p.get('slug'):
            # try to derive from link then header/title
            link = p.get('link','')
            candidate = slugify(link) if link else ''
            if not candidate:
                candidate = slugify(p.get('title') or p.get('header') or '')
            p['slug'] = candidate
            changed = True
    if changed:
        posts['projects'] = projects
        write_json(DATA_POSTS, posts)

def get_project_by_slug(slug):
    posts = load_json(DATA_POSTS)
    for p in posts.get('projects', []):
        if p.get('slug') == slug:
            return p
        # fallback: if their link endswith slug.html
        link = p.get('link','')
        if link and slugify(link) == slug:
            return p
    return None

def get_page_by_project_id(project_id):
    pages = load_json(DATA_PAGES)
    for entry in pages.get('project_pages', []):
        if entry.get('project_id') == project_id:
            return entry
    return None

def save_or_update_page(entry):
    pages = load_json(DATA_PAGES)
    arr = pages.get('project_pages', [])
    for i, e in enumerate(arr):
        if e.get('project_id') == entry.get('project_id'):
            arr[i] = entry
            pages['project_pages'] = arr
            write_json(DATA_PAGES, pages)
            return
    arr.append(entry)
    pages['project_pages'] = arr
    write_json(DATA_PAGES, pages)

# --------------------
# Basic site routes
# --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    flash("Thanks for reaching out! We'll get back to you soon.", "success")
    return redirect(url_for('index') + '#contact')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    flash("You're now subscribed to our newsletter!", "success")
    return redirect(url_for('index') + '#footer')

# --------------------
# Verifier/login (editors)
# --------------------
@app.route('/verifier', methods=['GET', 'POST'])
def verifier():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        data = load_json(DATA_VERIFIER)
        for user in data.get('editors', []):
            if user.get('email') == email and user.get('password') == password:
                session['user'] = user.get('user')
                flash('Welcome, ' + user.get('user'), 'success')
                return redirect(url_for('settings'))

        flash('Invalid email or password', 'danger')
        return redirect(url_for('verifier'))

    return render_template('verifier.html')

# --------------------
# Settings / editor panel
# --------------------
@app.route('/settings')
def settings():
    if not session.get('user'):
        flash('You must log in first.', 'warning')
        return redirect(url_for('verifier'))

    # ensure slugs
    ensure_project_slugs_and_save()

    posts = load_json(DATA_POSTS)
    projects = posts.get('projects', [])
    blog = posts.get('blog', [])
    return render_template('settings.html', user=session.get('user'), projects=projects, blog=blog)

# --------------------
# Existing project/blog routes (add/update/delete) - unchanged
# (omitted in this block for brevity — keep your existing add/update/delete routes here)
# The content below assumes those functions already present in your app.py from earlier.
# --------------------

# We'll assume your previous routes (update_project/add_project/update_blog/add_blog/delete routes)
# are still in the file exactly as before. To avoid duplication here, keep them as they were.

# --------------------
# Media upload (AJAX)
# --------------------# Update an existing project
@app.route('/settings/update_project', methods=['POST'])
def update_project():
    if not session.get('user'):
        flash('Not authorized', 'danger')
        return redirect(url_for('verifier'))

    proj_id = request.form.get('id')
    if not proj_id:
        flash('Missing project id', 'danger')
        return redirect(url_for('settings'))

    posts = load_json(DATA_POSTS)
    for p in posts.get('projects', []):
        if p.get('id') == proj_id:
            p['title'] = request.form.get('title', p.get('title'))
            p['header'] = request.form.get('header', p.get('header'))
            p['subheader'] = request.form.get('subheader', p.get('subheader'))
            p['excerpt'] = request.form.get('excerpt', p.get('excerpt'))
            p['link'] = request.form.get('link', p.get('link'))

            p['published'] = True if request.form.get('published') == 'on' else False
            p['is_sold'] = True if request.form.get('is_sold') == 'on' else False
            p['is_coming'] = True if request.form.get('is_coming') == 'on' else False

            # cover upload
            file = request.files.get('cover')
            if file and file.filename:
                saved = save_uploaded_file(file)
                if saved:
                    p['cover'] = saved

            p['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            break

    write_json(DATA_POSTS, posts)
    flash('Project updated successfully', 'success')
    return redirect(url_for('settings'))

# Add new project
@app.route('/settings/add_project', methods=['POST'])
def add_project():
    if not session.get('user'):
        flash('Not authorized', 'danger')
        return redirect(url_for('verifier'))

    posts = load_json(DATA_POSTS)
    projects = posts.get('projects', [])

    title = request.form.get('title', 'Untitled Project')
    header = request.form.get('header', title)
    subheader = request.form.get('subheader', '')
    excerpt = request.form.get('excerpt', '')
    link = request.form.get('link', '')

    cover_file = request.files.get('cover')
    cover = None
    if cover_file and cover_file.filename:
        cover = save_uploaded_file(cover_file)

    new_proj = {
        'id': 'proj-' + uuid.uuid4().hex[:8],
        'title': title,
        'header': header,
        'subheader': subheader,
        'excerpt': excerpt,
        'cover': cover or 'static/img/placeholder.png',
        'published': True if request.form.get('published') == 'on' else False,
        'is_sold': True if request.form.get('is_sold') == 'on' else False,
        'is_coming': True if request.form.get('is_coming') == 'on' else False,
        'link': link or f"/projects/{title.replace(' ', '-').lower()}.html",
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'updated_at': datetime.utcnow().isoformat() + 'Z'
    }

    projects.append(new_proj)
    posts['projects'] = projects
    write_json(DATA_POSTS, posts)

    flash('Project added', 'success')
    return redirect(url_for('settings'))

# Update blog post
@app.route('/settings/update_blog', methods=['POST'])
def update_blog():
    if not session.get('user'):
        flash('Not authorized', 'danger')
        return redirect(url_for('verifier'))

    blog_id = request.form.get('id')
    if not blog_id:
        flash('Missing blog id', 'danger')
        return redirect(url_for('settings'))

    posts = load_json(DATA_POSTS)
    for b in posts.get('blog', []):
        if b.get('id') == blog_id:
            b['title'] = request.form.get('title', b.get('title'))
            b['header'] = request.form.get('header', b.get('header'))
            b['subheader'] = request.form.get('subheader', b.get('subheader'))
            b['excerpt'] = request.form.get('excerpt', b.get('excerpt'))
            b['slug'] = request.form.get('slug', b.get('slug'))
            b['published'] = True if request.form.get('published') == 'on' else False

            # save manual link if provided
            b['link'] = request.form.get('link', b.get('link'))

            file = request.files.get('cover')
            if file and file.filename:
                saved = save_uploaded_file(file)
                if saved:
                    b['cover'] = saved

            b['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            break

    write_json(DATA_POSTS, posts)
    flash('Blog post updated', 'success')
    return redirect(url_for('settings'))


# Add blog post
@app.route('/settings/add_blog', methods=['POST'])
def add_blog():
    if not session.get('user'):
        flash('Not authorized', 'danger')
        return redirect(url_for('verifier'))

    posts = load_json(DATA_POSTS)
    blog = posts.get('blog', [])

    title = request.form.get('title', 'Untitled')
    header = request.form.get('header', title)
    subheader = request.form.get('subheader', '')
    excerpt = request.form.get('excerpt', '')
    slug = request.form.get('slug', title.replace(' ', '-').lower())
    manual_link = request.form.get('link', '').strip()

    cover_file = request.files.get('cover')
    cover = None
    if cover_file and cover_file.filename:
        cover = save_uploaded_file(cover_file)

    link = manual_link if manual_link else f"/blog/{slug}.html"

    new_blog = {
        'id': 'blog-' + uuid.uuid4().hex[:8],
        'title': title,
        'header': header,
        'subheader': subheader,
        'excerpt': excerpt,
        'cover': cover or 'static/img/placeholder.png',
        'slug': slug,
        'tags': [],
        'published': True if request.form.get('published') == 'on' else False,
        'is_event': False,
        'status': 'draft' if not (request.form.get('published') == 'on') else 'published',
        'link': link,
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'updated_at': datetime.utcnow().isoformat() + 'Z'
    }

    blog.append(new_blog)
    posts['blog'] = blog
    write_json(DATA_POSTS, posts)

    flash('Blog post added', 'success')
    return redirect(url_for('settings'))

# Delete routes
@app.route('/settings/delete_project', methods=['POST'])
def delete_project():
    if not session.get('user'):
        flash('Not authorized', 'danger')
        return redirect(url_for('verifier'))

    proj_id = request.form.get('id')
    if not proj_id:
        flash('Missing project id', 'danger')
        return redirect(url_for('settings'))

    posts = load_json(DATA_POSTS)
    projects = posts.get('projects', [])
    for i, p in enumerate(projects):
        if p.get('id') == proj_id:
            cover = p.get('cover', '')
            # delete uploaded cover only if it's in uploads
            if cover and cover.startswith('static/uploads/'):
                try:
                    fp = os.path.normpath(os.path.join(os.getcwd(), cover))
                    if os.path.exists(fp):
                        os.remove(fp)
                except Exception:
                    pass
            projects.pop(i)
            posts['projects'] = projects
            write_json(DATA_POSTS, posts)
            flash('Project deleted', 'success')
            return redirect(url_for('settings'))

    flash('Project not found', 'danger')
    return redirect(url_for('settings'))

@app.route('/settings/delete_blog', methods=['POST'])
def delete_blog():
    if not session.get('user'):
        flash('Not authorized', 'danger')
        return redirect(url_for('verifier'))

    blog_id = request.form.get('id')
    if not blog_id:
        flash('Missing blog id', 'danger')
        return redirect(url_for('settings'))

    posts = load_json(DATA_POSTS)
    blog_list = posts.get('blog', [])
    for i, b in enumerate(blog_list):
        if b.get('id') == blog_id:
            cover = b.get('cover', '')
            if cover and cover.startswith('static/uploads/'):
                try:
                    fp = os.path.normpath(os.path.join(os.getcwd(), cover))
                    if os.path.exists(fp):
                        os.remove(fp)
                except Exception:
                    pass
            blog_list.pop(i)
            posts['blog'] = blog_list
            write_json(DATA_POSTS, posts)
            flash('Blog post deleted', 'success')
            return redirect(url_for('settings'))

    flash('Blog post not found', 'danger')
    return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('verifier'))

@app.route('/settings/upload_media', methods=['POST'])
def upload_media():
    if not session.get('user'):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    file = request.files.get('file')
    if not file:
        return jsonify({'ok': False, 'error': 'No file provided'}), 400

    saved = save_uploaded_file(file)
    if not saved:
        return jsonify({'ok': False, 'error': 'Invalid file or extension'}), 400

    return jsonify({'ok': True, 'url': saved})

# --------------------
# Page API: get/save/delete
# --------------------
@app.route('/settings/get_page', methods=['GET'])
def get_page():
    if not session.get('user'):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'ok': False, 'error': 'Missing project_id'}), 400

    entry = get_page_by_project_id(project_id)
    if not entry:
        return jsonify({'ok': True, 'page': None})
    return jsonify({'ok': True, 'page': entry})

@app.route('/settings/save_page', methods=['POST'])
def save_page():
    if not session.get('user'):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': 'Invalid JSON body'}), 400

    project_id = data.get('project_id')
    slug = data.get('slug', '').strip()
    title = data.get('title', '').strip()
    excerpt = data.get('excerpt', '').strip()
    sections = data.get('sections', [])

    if not project_id:
        return jsonify({'ok': False, 'error': 'Missing project_id'}), 400

    posts = load_json(DATA_POSTS)
    project = None
    for p in posts.get('projects', []):
        if p.get('id') == project_id:
            project = p
            break
    if not project:
        return jsonify({'ok': False, 'error': 'Project not found'}), 404

    # enforce/derive slug
    if not slug:
        slug = project.get('slug') or slugify(project.get('link') or project.get('title') or project.get('header'))

    # ensure sections have ids
    for s in sections:
        if not s.get('id'):
            s['id'] = 'sec-' + uuid.uuid4().hex[:8]

    now = datetime.utcnow().isoformat() + 'Z'
    entry = get_page_by_project_id(project_id)
    if entry:
        entry['slug'] = slug
        entry['title'] = title or entry.get('title') or project.get('title')
        entry['excerpt'] = excerpt or entry.get('excerpt') or project.get('excerpt')
        entry['sections'] = sections
        entry['updated_at'] = now
    else:
        entry = {
            'project_id': project_id,
            'slug': slug,
            'title': title or project.get('title'),
            'excerpt': excerpt or project.get('excerpt'),
            'sections': sections,
            'created_at': now,
            'updated_at': now
        }
    save_or_update_page(entry)

    # ensure the project's slug field is updated to this slug (so /projects/<slug>.html resolves)
    if project.get('slug') != slug:
        project['slug'] = slug
        # write back posts
        posts['projects'] = posts.get('projects', [])
        write_json(DATA_POSTS, posts)

    return jsonify({'ok': True, 'page_slug': slug})

@app.route('/settings/delete_page', methods=['POST'])
def delete_page():
    if not session.get('user'):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    data = request.get_json() or request.form
    project_id = data.get('project_id') or data.get('id')
    if not project_id:
        return jsonify({'ok': False, 'error': 'Missing project_id'}), 400

    pages = load_json(DATA_PAGES)
    arr = pages.get('project_pages', [])
    for i, e in enumerate(arr):
        if e.get('project_id') == project_id:
            # optionally delete uploaded files that are only referenced here (best-effort)
            secs = e.get('sections', [])
            for s in secs:
                # gather image urls
                if s.get('cover') and s['cover'].startswith('static/uploads/'):
                    try:
                        fp = os.path.normpath(os.path.join(os.getcwd(), s['cover']))
                        if os.path.exists(fp):
                            os.remove(fp)
                    except Exception:
                        pass
                if s.get('images'):
                    for im in s['images']:
                        src = im.get('src') if isinstance(im, dict) else im
                        if src and isinstance(src, str) and src.startswith('static/uploads/'):
                            try:
                                fp = os.path.normpath(os.path.join(os.getcwd(), src))
                                if os.path.exists(fp):
                                    os.remove(fp)
                            except Exception:
                                pass
            arr.pop(i)
            pages['project_pages'] = arr
            write_json(DATA_PAGES, pages)
            return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Page not found'}), 404

# --------------------
# Render dynamic project page
# --------------------
@app.route('/projects/<slug>.html')
def project_page(slug):
    project = get_project_by_slug(slug)
    if not project:
        abort(404)

    page = get_page_by_project_id(project.get('id'))
    sections = []
    if page:
        # convert markdown content to HTML for text sections
        for s in page.get('sections', []):
            scopy = dict(s)
            if 'content' in s and s.get('content'):
                html = markdown.markdown(s.get('content', ''), extensions=['extra'])
                scopy['html'] = Markup(html)
            # for safety, ensure strings are escaped where necessary in template too
            sections.append(scopy)
        page_title = page.get('title') or project.get('title')
        page_excerpt = page.get('excerpt') or project.get('excerpt')
    else:
        # fallback page derived from project basic info
        page_title = project.get('title')
        page_excerpt = project.get('excerpt')
        # create a simple hero section
        sections = [{
            'id': 'fallback-hero',
            'type': 'hero',
            'title': project.get('header') or project.get('title'),
            'subheader': project.get('subheader') or '',
            'cover': project.get('cover', '')
        }]

    return render_template('project_page.html', project=project, sections=sections, page_title=page_title, page_excerpt=page_excerpt)

# --------------------
# Run
# --------------------
if __name__ == '__main__':
    # ensure pages file exists
    if not os.path.exists(DATA_PAGES):
        write_json(DATA_PAGES, {'project_pages': []})
    app.run(debug=True)
