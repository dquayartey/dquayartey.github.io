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
    return filename.rsplit('.', 1)[0]

def make_status_badge(status):
    if status == 'ongoing':
        return '<span class="status-badge status-ongoing"><span class="status-dot"></span> In Progress</span>'
    return ''

def make_card(template, data, slug):
    tags_html = ''.join(f'<span class="tag">{t}</span>' for t in data['tags'][:5])
    card = template
    card = card.replace('{{SLUG}}', slug)
    card = card.replace('{{TITLE}}', data['title'])
    card = card.replace('{{IMG}}', data['img'])
    card = card.replace('{{SUMMARY}}', data['summary'])
    card = card.replace('{{PERIOD}}', data['period'])
    card = card.replace('{{STATUS_BADGE}}', make_status_badge(data['status']))
    card = card.replace('{{TAGS_HTML}}', tags_html)
    return card

def make_detail_content(data):
    actions_html = ''.join(
        f'<a href="{a["url"]}" target="_blank" class="modal-btn {"modal-btn-primary" if a.get("primary") else "modal-btn-secondary"}">'
        f'<i class="{a["icon"]}"></i> {a["label"]}</a>'
        for a in data['actions']
    )
    body_html = ''.join(
        f'<h3 class="detail-section-heading">{p["heading"]}</h3><p>{p["text"]}</p>'
        for p in data['body']
    )
    highlights_html = ''.join(f'<li>{h}</li>' for h in data['highlights'])
    tags_html = ''.join(f'<span class="modal-tag">{t}</span>' for t in data['tags'])
    status_badge = make_status_badge(data['status'])
    period_html = f'<span class="detail-period">{data["period"]}</span>' if data['period'] else ''

    return f'''<article class="project-detail section-anchor" id="overview">
  <a href="../portfolio.html" class="back-link"><i class="fa-solid fa-arrow-left"></i> Back to Portfolio</a>
  <div class="detail-hero">
    <img src="../{data['img']}" alt="{data['title']}">
    {status_badge}
  </div>
  <div class="detail-title-row">
    <h1 class="detail-title">{data['title']}</h1>
    {period_html}
  </div>
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
    out = base.replace('{{TITLE}}', title)
    out = out.replace('{{NAV}}', nav)
    out = out.replace('{{FOOTER}}', footer)
    out = out.replace('{{SIDEBAR}}', sidebar)
    out = out.replace('{{CONTENT}}', content)
    out = out.replace('{{BASE}}', base_prefix)  # catches tokens from base.html AND nav.html
    return out

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
    card_template = read_file('src/template/project-card.html')
    cards = []
    if os.path.exists(projects_dir):
        json_files = [f for f in os.listdir(projects_dir) if f.endswith('.json')]
        json_files.sort(key=lambda f: json.load(open(os.path.join(projects_dir, f), encoding='utf-8'))['order'])

        for f in json_files:
            slug = slugify(f)
            with open(os.path.join(projects_dir, f), 'r', encoding='utf-8') as jf:
                data = json.load(jf)

            cards.append(make_card(card_template, data, slug))

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