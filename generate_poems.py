#!/usr/bin/env python3
# generate_poems.py

import os
import sys
import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

# 1) Configuration
POEM_DIR = 'poems'       # where your .md files live
OUT_DIR  = '.'           # where to dump .html output
TEMPLATE_DIR = 'templates'

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Load Jinja2 environment
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True
)

# 2) Collect all poems
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

    # Convert Markdown to HTML
    html = markdown.markdown(body, extensions=['nl2br'])

    # Derive defaults
    base = os.path.splitext(fname)[0]
    default_title = base.replace('-', ' ').replace('_', ' ').title()
    title = meta.get('title', default_title)
    slug  = meta.get('slug', base)
    author = meta.get('author', 'Anonymous')

    poems.append({
        'title':   title,
        'slug':    slug,
        'author':  author,
        'content': html
    })

if not poems:
    print("❌  No poems found in", POEM_DIR, file=sys.stderr)
    sys.exit(1)

# 3) Render each poem page
tpl_poem = env.get_template('poem.html')
for p in poems:
    out_path = os.path.join(OUT_DIR, f"{p['slug']}.html")
    rendered = tpl_poem.render(poem=p, all_poems=poems)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(rendered)
    print(f"✔️  Wrote {out_path}")