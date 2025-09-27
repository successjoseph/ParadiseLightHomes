from flask import Flask, render_template, request, redirect, url_for, flash, session
import json, os, uuid
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"

# Upload config
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_POSTS = os.path.join('static', 'data', 'posts.json')
DATA_VERIFIER = os.path.join('static', 'data', 'verifier.json')

# Helpers
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
    # return web path (use with <img src="{{ cover }}"> )
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

# Basic site routes (unchanged behavior)
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

# VERIFIER: uses `editors` list from verifier.json
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

# SETTINGS: editor-only (simple auth: must be logged-in user via session)
@app.route('/settings')
def settings():
    if not session.get('user'):
        flash('You must log in first.', 'warning')
        return redirect(url_for('verifier'))

    posts = load_json(DATA_POSTS)
    projects = posts.get('projects', [])
    blog = posts.get('blog', [])

    return render_template('settings.html', user=session.get('user'), projects=projects, blog=blog)

# Update an existing project
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

if __name__ == '__main__':
    app.run(debug=True)
