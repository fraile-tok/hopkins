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
POEM_DIR     = '_poems'      # source markdown
POEMS_HTML   = 'poems'       # where individual poem .html live (unchanged)
TEMPLATE_DIR = '_templates'  # your templates
TEMPLATE_NAME= 'author.html' # template for author pages
OUT_DIR      = 'authors'     # where to dump .html output

# helper: slugify using only the last name
def slugify_lastname(name: str) -> str:
    # remove trailing suffixes like "Jr." / "II", then take last token
    s = (name or 'Anonymous').strip()
    s = re.sub(r',?\s*(jr|sr|ii|iii|iv|v)\.?$', '', s, flags=re.I).strip()
    parts = re.split(r'\s+', s)
    last = parts[-1] if parts else 'anonymous'

    # normalize accents and produce safe slug
    last = normalize("NFKD", last).encode("ascii", "ignore").decode("ascii")
    last = re.sub(r'[^a-z0-9]+', '-', last.lower()).strip('-')
    return last or 'anonymous'

_num_re = re.compile(r'(\d+)')

# Natural Key
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

# ─── COLLECT POEMS ────────────────────────────────────────
# Setup Jinja
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

try:
    tpl = env.get_template(TEMPLATE_NAME)
except Exception as e:
    print(f"❌ Could not load template '{TEMPLATE_NAME}' from '{TEMPLATE_DIR}': {e}", file=sys.stderr)
    print("Available templates:", env.list_templates(), file=sys.stderr)
    sys.exit(1)

# Delete existing output files
for fname in os.listdir(OUT_DIR):
    path = os.path.join(OUT_DIR, fname)
    if fname.lower().endswith('.html'):
        if os.path.isfile(path):
            try:
                os.remove(path)
                print("Deleted", path)
            except Exception as e:
                print("Failed to delete", path, ":", e)

# Collect all poems
poems = []
for fname in sorted(os.listdir(POEM_DIR)):
    if not fname.lower().endswith('.md'):
        continue

    path = os.path.join(POEM_DIR, fname)
    try:
        post = frontmatter.load(path)
    except Exception as e:
        print(f"⚠️  Skipping {fname}: failed to parse front-matter ({e})", file=sys.stderr)
        continue

    meta = post.metadata or {}
    body = post.content or ''

    # Derive defaults
    base = os.path.splitext(fname)[0]
    default_title = base.replace('-', ' ').replace('_', ' ').title()
    title = meta.get('title', default_title)
    slug  = meta.get('slug', base)
    author = meta.get('author', 'Anonymous')

    author_slug = slugify_lastname(author)

    poems.append({
        'title':   title,
        'slug':    slug,
        'author':  author,
        'author_slug': author_slug
    })

if not poems:
    print("❌  No poems found in", POEM_DIR, file=sys.stderr)
    sys.exit(1)

# Group by author
poems.sort(key=lambda p: ((p.get('author')) or '').strip().lower())

groups = []
for author_key, items in groupby(poems, key=lambda p: (p.get('author') or '').strip()):
    # sort poems for this author by title (case-insensitive)
    group_list = sorted(list(items), key=lambda p: natural_key(p.get('title') or ''))

    display_author = group_list[0].get('author') if group_list and group_list[0].get('author') else 'Anonymous'
    author_slug = group_list[0]['author_slug']

    groups.append({
        'author': display_author,
        'author_slug': author_slug,
        'poems': group_list
    })

# Render author pages
for g in groups:
    out_path = os.path.join(OUT_DIR, f"{g['author_slug']}.html")
    rendered = tpl.render(author=g['author'], poems=g['poems'], author_slug=g['author_slug'])
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(rendered)
        print(f"✔️  Wrote {out_path}")

print(f"✔️  Wrote {len(groups)} author pages")