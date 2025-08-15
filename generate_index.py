#!/usr/bin/env python3
# generate_index.py

import os
import sys
import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

# 1) Configuration
POEM_DIR = '_poems'       # where your .md files live
HTML_DIR  = 'poems'           # where to dump .html output
TEMPLATE_DIR = '_templates'
INDEX_NAME = 'index.html'

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

def _lastname(author):
    a = (author or '').strip()
    return a.split()[-1].lower() if a else ''

poems.sort(key=lambda p: (_lastname(p.get('author')), (p.get('author') or '').lower()))

if not poems:
    print("❌  No poems found in", POEM_DIR, file=sys.stderr)
    sys.exit(1)


tpl = env.get_template('index.html')
output = tpl.render(poems=poems)

out_path = os.path.join(INDEX_NAME)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f"✔️ Wrote {out_path}")