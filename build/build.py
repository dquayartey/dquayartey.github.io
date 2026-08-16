import os
import shutil

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def build_site():
    print("🚀 Starting build process...")

    # Clean and re-create output directory
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist')

    # Copy assets folder
    if os.path.exists('src/assets'):
        shutil.copytree('src/assets', 'dist/assets')
        print("📦 Assets successfully copied to dist/assets")

    # Load shell templates and partials
    base_template = read_file('src/template/base.html')
    nav_partial = read_file('src/partials/nav.html')
    footer_partial = read_file('src/partials/footer.html')

    # 1. Build Index / About Page (dist/index.html)
    about_content = read_file('src/pages/about.html')
    index_html = base_template.replace('{{TITLE}}', 'About & Skills')
    index_html = index_html.replace('{{NAV}}', nav_partial)
    index_html = index_html.replace('{{FOOTER}}', footer_partial)
    index_html = index_html.replace('{{CONTENT}}', about_content)
    write_file('dist/index.html', index_html)
    print("  + Generated dist/index.html (About & Skills)")

    # 2. Build Portfolio Page (dist/portfolio.html)
    portfolio_intro = read_file('src/pages/portfolio-intro.html')
    projects_dir = 'src/projects'
    project_cards = []

    if os.path.exists(projects_dir):
        project_files = sorted(os.listdir(projects_dir))
        for filename in project_files:
            if filename.endswith('.html'):
                file_path = os.path.join(projects_dir, filename)
                project_cards.append(read_file(file_path))

    all_projects_html = "\n".join(project_cards)
    portfolio_content = portfolio_intro.replace('{{PROJECT_CARDS}}', all_projects_html)

    portfolio_html = base_template.replace('{{TITLE}}', 'Portfolio')
    portfolio_html = portfolio_html.replace('{{NAV}}', nav_partial)
    portfolio_html = portfolio_html.replace('{{FOOTER}}', footer_partial)
    portfolio_html = portfolio_html.replace('{{CONTENT}}', portfolio_content)
    write_file('dist/portfolio.html', portfolio_html)
    print("  + Generated dist/portfolio.html (Portfolio Vertical List)")

    # 3. Build Contact Page (dist/contact.html)
    contact_content = read_file('src/pages/contact.html')
    contact_html = base_template.replace('{{TITLE}}', 'Contact')
    contact_html = contact_html.replace('{{NAV}}', nav_partial)
    contact_html = contact_html.replace('{{FOOTER}}', footer_partial)
    contact_html = contact_html.replace('{{CONTENT}}', contact_content)
    write_file('dist/contact.html', contact_html)
    print("  + Generated dist/contact.html (Contact Links)")

    print("✅ Build complete! Static site generated in dist/")

if __name__ == '__main__':
    build_site()
