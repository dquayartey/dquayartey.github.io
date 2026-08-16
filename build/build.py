import os
import re
import json
import shutil

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def slugify(filename):
    name = filename.rsplit('.', 1)[0]
    return re.sub(r'^\d+-', '', name)

def extract_attr(html, name, quote):
    m = re.search(rf"data-{name}={quote}(.*?){quote}", html, re.DOTALL)
    return m.group(1) if m else ''

def parse_project(html):
    return {
        'title': extract_attr(html, 'title', '"'),
        'img': extract_attr(html, 'img', '"'),
        'actions': json.loads(extract_attr(html, 'actions', "'") or '[]'),
        'tags': json.loads(extract_attr(html, 'tags', "'") or '[]'),
        'body': json.loads(extract_attr(html, 'body', "'") or '[]'),
        'highlights': json.loads(extract_attr(html, 'highlights', "'") or '[]'),
    }

def make_card_link(html, slug):
    card = html.replace('<article class="project-card"', f'<a class="project-card" href="projects/{slug}.html"')
    card = re.sub(r'\s*tabindex="0"\s*role="button"\s*aria-label="([^"]*)"', r' aria-label="\1"', card)
    card = card.replace('</article>', '</a>')
    return card

def make_detail_content(data):
    actions_html = ''.join(
        f'<a href="{a["url"]}" target="_blank" class="modal-btn {"modal-btn-primary" if a.get("primary") else "modal-btn-secondary"}">'
        f'<i class="{a["icon"]}"></i> {a["label"]}</a>'
        for a in data['actions']
    )
    body_html = ''.join(f'<p>{p}</p>' for p in data['body'])
    highlights_html = ''.join(f'<li>{h}</li>' for h in data['highlights'])
    tags_html = ''.join(f'<span class="modal-tag">{t}</span>' for t in data['tags'])

    return f'''<article class="project-detail section-anchor" id="overview">
  <a href="../portfolio.html" class="back-link"><i class="fa-solid fa-arrow-left"></i> Back to Portfolio</a>
  <div class="detail-hero">
    <img src="../{data['img']}" alt="{data['title']}">
  </div>
  <h1 class="detail-title">{data['title']}</h1>
  {f'<div class="modal-actions">{actions_html}</div>' if actions_html else ''}
  <div class="modal-section">
    {body_html}
  </div>
  {f'<div class="modal-section"><div class="modal-section-title">Key Highlights</div><ul class="modal-highlights">{highlights_html}</ul></div>' if highlights_html else ''}
  {f'<div class="modal-section"><div class="modal-section-title">Tech Stack</div><div class="modal-tags">{tags_html}</div></div>' if tags_html else ''}
</article>'''

def make_sidebar(links):
    items = ''.join(f'<li><a href="#{id}">{label}</a></li>' for id, label in links)
    return f'''<aside class="sidebar" id="sidebar">
  <button class="sidebar-toggle" id="sidebarToggle">
    <i class="fa-solid fa-chevrons-left"></i>
    <span>On this page</span>
  </button>
  <div class="sidebar-content">
    <div class="sidebar-label">Navigation</div>
    <ul class="sidebar-nav">{items}</ul>
  </div>
</aside>'''

def build_page(base, nav, footer, title, content, sidebar_links, base_prefix=''):
    sidebar = make_sidebar(sidebar_links)
    html = base.replace('{{TITLE}}', title)
    html = html.replace('{{NAV}}', nav)
    html = html.replace('{{FOOTER}}', footer)
    html = html.replace('{{SIDEBAR}}', sidebar)
    html = html.replace('{{CONTENT}}', content)
    html = html.replace('{{BASE}}', base_prefix)  # catches tokens from base.html AND nav.html
    return html

def build_site():
    print("🚀 Starting build process...")

    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist')

    if os.path.exists('src/assets'):
        shutil.copytree('src/assets', 'dist/assets')
        print("📦 Assets copied to dist/assets")

    base = read_file('src/template/base.html')
    nav = read_file('src/partials/nav.html')
    footer = read_file('src/partials/footer.html')

    # 1. About / Index
    about_links = [('intro', 'Introduction'), ('bio', 'Background'), ('expertise', 'Technical Expertise'), ('approach', 'Engineering Philosophy')]
    write_file('dist/index.html', build_page(base, nav, footer, 'About', read_file('src/pages/about.html'), about_links))
    print("  + dist/index.html")

    # 2. Portfolio + individual project detail pages
    projects_dir = 'src/projects'
    cards = []
    if os.path.exists(projects_dir):
        for f in sorted(os.listdir(projects_dir)):
            if not f.endswith('.html'):
                continue
            raw = read_file(os.path.join(projects_dir, f))
            slug = slugify(f)
            data = parse_project(raw)

            cards.append(make_card_link(raw, slug))

            detail_content = make_detail_content(data)
            write_file(
                f'dist/projects/{slug}.html',
                build_page(base, nav, footer, data['title'], detail_content, [('overview', 'Overview')], base_prefix='../')
            )
            print(f"  + dist/projects/{slug}.html")

    intro = read_file('src/pages/portfolio-intro.html').replace('{{PROJECT_CARDS}}', '\n'.join(cards))
    portfolio_links = [('projects', 'Projects')]
    write_file('dist/portfolio.html', build_page(base, nav, footer, 'Portfolio', intro, portfolio_links))
    print("  + dist/portfolio.html")

    # 3. Contact
    contact_links = [('connect', 'Get in Touch')]
    write_file('dist/contact.html', build_page(base, nav, footer, 'Contact', read_file('src/pages/contact.html'), contact_links))
    print("  + dist/contact.html")

    print("✅ Build complete — dist/")

if __name__ == '__main__':
    build_site()