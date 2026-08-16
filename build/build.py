import os
import shutil

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

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

def build_page(base, nav, footer, title, content, sidebar_links):
    sidebar = make_sidebar(sidebar_links)
    html = base.replace('{{TITLE}}', title)
    html = html.replace('{{NAV}}', nav)
    html = html.replace('{{FOOTER}}', footer)
    html = html.replace('{{SIDEBAR}}', sidebar)
    html = html.replace('{{CONTENT}}', content)
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
    about_links = [('intro', 'Introduction'), ('expertise', 'Technical Expertise'), ('approach', 'Engineering Philosophy')]
    write_file('dist/index.html', build_page(base, nav, footer, 'About & Skills', read_file('src/pages/about.html'), about_links))
    print("  + dist/index.html")

    # 2. Portfolio
    projects_dir = 'src/projects'
    cards = []
    if os.path.exists(projects_dir):
        for f in sorted(os.listdir(projects_dir)):
            if f.endswith('.html'):
                cards.append(read_file(os.path.join(projects_dir, f)))

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
