import os
import re
import json
from datetime import datetime

CONTENT_DIR = 'src/content'
PROJECTS_DIR = 'src/projects'


def slugify(filename):
    name = filename.rsplit('.', 1)[0]
    return re.sub(r'^\d+-', '', name)


def parse_sections(body_text):
    pattern = r'\*\*(.+?)\*\*\s*\n+(.*?)(?=\n\*\*|\Z)'
    matches = re.findall(pattern, body_text, re.DOTALL)
    return [{'heading': h.strip(), 'text': ' '.join(t.strip().split())} for h, t in matches]


def parse_period_end(period, status):
    """
    Returns a [year, month] sort key representing the end of the project's period.
    Ongoing projects (status=ongoing, or a period ending in 'Present') always sort
    as the most recent — they get a far-future key so they float to the top.
    """
    if status == 'ongoing' or 'present' in period.lower():
        return [9999, 12]

    # Take the piece after the last dash (en dash, em dash, or hyphen)
    parts = re.split(r'[\u2013\u2014-]', period)
    end_str = parts[-1].strip() if parts else period.strip()

    for fmt in ('%b %Y', '%B %Y'):
        try:
            dt = datetime.strptime(end_str, fmt)
            return [dt.year, dt.month]
        except ValueError:
            continue

    # Unparseable PERIOD — sort last rather than crashing the build
    return [0, 0]


def parse_txt(raw, fallback_index):
    header_part, _, body_part = raw.partition('\n---\n')
    fields = {}
    highlights = []
    collaborators = []
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
        if line.upper().startswith('COLLABORATORS:'):
            i += 1
            while i < len(lines) and lines[i].strip().startswith('-'):
                collaborators.append(lines[i].strip().lstrip('-').strip())
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

    status = fields.get('STATUS', 'completed').lower()
    period = fields.get('PERIOD', '')

    return {
        'title': fields.get('TITLE', ''),
        'img': fields.get('IMAGE', ''),
        'summary': fields.get('SUMMARY', ''),
        'period': period,
        'status': status,
        'actions': actions,
        'tags': tags,
        'highlights': highlights,
        'collaborators': collaborators,
        'body': parse_sections(body_part),
        'sort_key': parse_period_end(period, status),
        # kept as a stable tiebreaker for projects with identical/missing periods
        'fallback_index': fallback_index,
    }


def run():
    if not os.path.exists(CONTENT_DIR):
        print("No src/content/ directory — nothing to do.")
        return

    os.makedirs(PROJECTS_DIR, exist_ok=True)

    print("📝 Formatting project content...")
    txt_files = sorted(f for f in os.listdir(CONTENT_DIR) if f.endswith('.txt'))
    for index, content_file in enumerate(txt_files):
        slug = slugify(content_file)
        raw = open(os.path.join(CONTENT_DIR, content_file), 'r', encoding='utf-8').read()
        data = parse_txt(raw, index)

        if not data['body']:
            print(f"  ⚠️  No **Heading** sections found in {content_file}")
            continue
        if not data['title']:
            print(f"  ⚠️  No TITLE field in {content_file} — skipping")
            continue
        if not data['img']:
            print(f"  ⚠️  No IMAGE field in {content_file} — card image will be blank")

        out_path = os.path.join(PROJECTS_DIR, f'{slug}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {content_file} → {out_path}")

    print("✅ Content formatting complete")


if __name__ == '__main__':
    run()