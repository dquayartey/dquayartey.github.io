import os
import re
import json

CONTENT_DIR = 'src/content'
PROJECTS_DIR = 'src/projects'

def slugify(filename):
    name = filename.rsplit('.', 1)[0]
    return re.sub(r'^\d+-', '', name)

def parse_sections(body_text):
    pattern = r'\*\*(.+?)\*\*\s*\n+(.*?)(?=\n\*\*|\Z)'
    matches = re.findall(pattern, body_text, re.DOTALL)
    return [{'heading': h.strip(), 'text': ' '.join(t.strip().split())} for h, t in matches]

def parse_txt(raw, order):
    header_part, _, body_part = raw.partition('\n---\n')
    fields = {}
    highlights = []
    lines = header_part.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.upper().startswith('HIGHLIGHTS:'):
            i += 1
            while i < len(lines) and lines[i].strip().startswith('-'):
                highlights.append(lines[i].strip().lstrip('-').strip())
                i += 1
            continue
        m = re.match(r'^([A-Z_]+):\s*(.*)$', line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
        i += 1

    tags = [t.strip() for t in fields.get('TAGS', '').split(',') if t.strip()]

    actions = []
    if fields.get('DEMO_URL'):
        actions.append({'label': 'Live Demo', 'url': fields['DEMO_URL'],
                         'icon': 'fa-solid fa-arrow-up-right-from-square', 'primary': True})
    if fields.get('REPO_URL'):
        actions.append({'label': 'Repository', 'url': fields['REPO_URL'],
                         'icon': 'fa-brands fa-github', 'primary': False})

    return {
        'title': fields.get('TITLE', ''),
        'img': fields.get('IMAGE', ''),
        'summary': fields.get('SUMMARY', ''),
        'period': fields.get('PERIOD', ''),
        'status': fields.get('STATUS', 'completed').lower(),
        'actions': actions,
        'tags': tags,
        'highlights': highlights,
        'body': parse_sections(body_part),
        'order': order,
    }

def run():
    if not os.path.exists(CONTENT_DIR):
        print("No src/content/ directory — nothing to do.")
        return

    os.makedirs(PROJECTS_DIR, exist_ok=True)

    print("📝 Formatting project content...")
    txt_files = sorted(f for f in os.listdir(CONTENT_DIR) if f.endswith('.txt'))
    for order, content_file in enumerate(txt_files):
        slug = slugify(content_file)
        raw = open(os.path.join(CONTENT_DIR, content_file), 'r', encoding='utf-8').read()
        data = parse_txt(raw, order)

        if not data['body']:
            print(f"  ⚠️  No **Heading** sections found in {content_file}")
            continue
        if not data['title']:
            print(f"  ⚠️  No TITLE field in {content_file} — skipping")
            continue

        out_path = os.path.join(PROJECTS_DIR, f'{slug}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {content_file} → {out_path}")

    print("✅ Content formatting complete")

if __name__ == '__main__':
    run()