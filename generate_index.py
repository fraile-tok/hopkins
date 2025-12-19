#!/usr/bin/env python3
# generate_index.py

import os
import sys
import frontmatter
import markdown
import re
from jinja2 import Environment, FileSystemLoader
from itertools import groupby
from unicodedata import normalize

# ─── CONFIG ───────────────────────────────────────────────
POEM_DIR     = '_poems'      # where .md files live
HTML_DIR     = 'poems'       # where to dump .html files
TEMPLATE_DIR = '_templates'  # Jinja2 templates
INDEX_NAME   = 'index.html'  # output filename

_num_re = re.compile(r'(\d+)')

def natural_key(s: str):
    if not s:
        return []
    s = s.strip().lower()
    parts = _num_re.split(s)
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.strip())
    return key

# Make slugs
def slugify_lastname(name: str) -> str:
    """Make a safe slug from the author's last name (ASCII, lower, hyphens)."""
    s = (name or 'Anonymous').strip()
    # remove common suffixes like "Jr." "II"
    s = re.sub(r',?\s*(jr|sr|ii|iii|iv|v)\.?$', '', s, flags=re.I).strip()
    parts = re.split(r'\s+', s)
    last = parts[-1] if parts else 'anonymous'
    last = normalize("NFKD", last).encode("ascii", "ignore").decode("ascii")
    last = re.sub(r'[^a-z0-9]+', '-', last.lower()).strip('-')
    return last or 'anonymous'


# Ensure output directory exists
os.makedirs(HTML_DIR, exist_ok=True)

# Set up Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True
)

# ─── COLLECT POEMS ────────────────────────────────────────
poems = []
for fname in sorted(os.listdir(POEM_DIR)):
    if not fname.lower().endswith('.md'):
        continue

    full = os.path.join(POEM_DIR, fname)
    try:
        post = frontmatter.load(full)
    except Exception as e:
        print(f"⚠️ Skipping {fname}: {e}", file=sys.stderr)
        continue

    meta = post.metadata or {}
    # Normalize/fallbacks
    base = os.path.splitext(fname)[0]
    default_title = base.replace('-', ' ').replace('_', ' ').title()
    title  = meta.get('title', default_title)
    slug   = meta.get('slug', base)
    author = meta.get('author', 'Anonymous')

    poems.append({
        'title':  title,
        'slug':   slug,
        'author': author,
    })

if not poems:
    print("❌ No poems found!", file=sys.stderr)
    sys.exit(1)

# ─── SORT & GROUP BY AUTHOR ───────────────────────────────
# sort by normalized author name so groupby works correctly
poems.sort(key=lambda p: (p.get('author') or '').strip().lower())

authors_map = {}
for author_key, items in groupby(poems, key=lambda p: (p.get('author') or '').strip()):
    group_list = sorted(list(items), key=lambda p: natural_key(p.get('title') or ''))
    display_author = group_list[0].get('author') if group_list and group_list[0].get('author') else 'Anonymous'
    authors_map[display_author] = group_list

used_slugs = set()
authors_list = []

for name in sorted(authors_map.keys(), key=lambda s: s.lower()):
    base = slugify_lastname(name)
    candidate = base

    # try initials if simple last-name collides
    if candidate in used_slugs:
        initials = ''.join([part[0].lower() for part in name.split() if part])
        if initials:
            candidate = f"{base}-{initials}"
        else:
            candidate = f"{base}-a"

    orig = candidate
    i = 1
    while candidate in used_slugs:
        candidate = f"{orig}-{i}"
        i += 1

    used_slugs.add(candidate)

    authors_list.append({
        'author': name,
        'author_slug': candidate,
        'count': len(authors_map[name]),
        'poems': authors_map[name]
    })

# ─── RENDER INDEX ─────────────────────────────────────────
try:
    tpl_index = env.get_template('index.html')   # ensure _templates/index.html exists
except Exception as e:
    print(f"❌ Could not load template 'index.html' from '{TEMPLATE_DIR}': {e}", file=sys.stderr)
    print("Available templates:", env.list_templates(), file=sys.stderr)
    sys.exit(1)

index_out = tpl_index.render(authors=authors_list)

with open(INDEX_NAME, 'w', encoding='utf-8') as f:
    f.write(index_out)
print(f"✔️  Wrote {INDEX_NAME} with {len(authors_list)} authors.")
print(f"Total poem count: {poem_count}.")
