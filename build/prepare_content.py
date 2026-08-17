import os
import re
import json
from datetime import datetime

CONTENT_DIR = 'src/content'
PROJECTS_DIR = 'src/projects'
ASSETS_PROJECTS_DIR = 'src/assets/projects'
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')


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


def resolve_image(image_field, slug):
    """
    Resolve the IMAGE field into an actual file path under src/assets/projects/.

    - If IMAGE points to a file that literally exists (old-style full path,
      e.g. 'assets/projects/campusai.jpg'), it's used as-is — fully backward
      compatible with existing .txt files.
    - Otherwise, IMAGE (or the slug, if IMAGE is blank) is treated as a
      basename hint: any extension or directory the user included is
      stripped, and the assets folder is searched case-insensitively for a
      file whose name (minus extension) matches.

    Returns (img_path, warning_or_None).
    """
    if image_field and os.path.isfile(image_field):
        return image_field, None

    search_name = os.path.splitext(os.path.basename(image_field))[0] if image_field else slug

    if not os.path.isdir(ASSETS_PROJECTS_DIR):
        return '', f"assets folder '{ASSETS_PROJECTS_DIR}' not found"

    matches = sorted(
        fname for fname in os.listdir(ASSETS_PROJECTS_DIR)
        if os.path.splitext(fname)[1].lower() in IMAGE_EXTENSIONS
        and os.path.splitext(fname)[0].lower() == search_name.lower()
    )

    if not matches:
        return '', f"no image matching '{search_name}' found in {ASSETS_PROJECTS_DIR}"

    chosen = matches[0]
    warning = None
    if len(matches) > 1:
        warning = f"multiple images match '{search_name}' ({', '.join(matches)}) — using {chosen}"

    return f'{ASSETS_PROJECTS_DIR}/{chosen}'.replace('src/', '', 1), warning


def parse_txt(raw, fallback_index, slug):
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
    img, img_warning = resolve_image(fields.get('IMAGE', ''), slug)

    return {
        'title': fields.get('TITLE', ''),
        'img': img,
        'img_warning': img_warning,
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
        data = parse_txt(raw, index, slug)

        if not data['body']:
            print(f"  ⚠️  No **Heading** sections found in {content_file}")
            continue
        if not data['title']:
            print(f"  ⚠️  No TITLE field in {content_file} — skipping")
            continue
        if not data['img']:
            print(f"  ⚠️  No image found for {content_file} — card image will be blank")
        elif data.get('img_warning'):
            print(f"  ⚠️  {content_file}: {data['img_warning']}")

        data.pop('img_warning', None)

        out_path = os.path.join(PROJECTS_DIR, f'{slug}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {content_file} → {out_path}")

    print("✅ Content formatting complete")


if __name__ == '__main__':
    run()