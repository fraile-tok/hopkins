#!/usr/bin/env python3
# generate_index.py

import os
import sys
import frontmatter
import markdown
import re
from jinja2 import Environment, FileSystemLoader
from itertools import groupby

# ─── CONFIG ───────────────────────────────────────────────
POEM_DIR     = '_poems'      # where your .md files live
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

# groupby requires adjacent items with same key, so sorting first is essential
groups = []
for author_key, items in groupby(poems, key=lambda p: (p.get('author') or '').strip()):
    # sort poems for this author by title (case-insensitive)
    group_list = sorted(list(items), key=lambda p: natural_key(p.get('title') or ''))

    # human-friendly display name (fallback to 'Anonymous')
    display_author = group_list[0].get('author') if group_list and group_list[0].get('author') else 'Anonymous'

    groups.append({
        'author': display_author,
        'poems':  group_list
    })

# ─── RENDER INDEX ─────────────────────────────────────────
tpl = env.get_template('index.html')
output = tpl.render(groups=groups)

out_path = os.path.join(INDEX_NAME)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"✔️ Wrote {out_path}")
