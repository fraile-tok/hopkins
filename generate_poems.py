#!/usr/bin/env python3
# generate_poems.py

import os
import sys
import frontmatter
import markdown
import re
from jinja2 import Environment, FileSystemLoader

# 1) Configuration
POEM_DIR = '_poems'       # where .md files live
OUT_DIR  = 'poems'           # where to dump .html output
TEMPLATE_DIR = '_templates'

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Load Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

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

    # Normalize line endings
    body = body.replace('\r\n', '\n').replace('\r', '\n').strip()

    # Stanza-gathering (what is separated at least by one blank line)
    stanza_texts = re.split(r'\n\s*\n+', body) if body else []

    stanzas = []
    stanzas_html = []
    for s in stanza_texts:
        # keep leading spaces (use rstrip to remove trailing accidental spaces)
        lines = [ln.rstrip('\n') for ln in s.splitlines()]
        if not lines:
            continue

        stanza_lines = []       # raw lines (optional)
        stanza_html_lines = []

        for ln in lines:
            stanza_lines.append(ln)
            line_html = markdown.markdown(ln, extensions=['extra'])

            m = re.match(r'^\s*<p>(.*)</p>\s*$', line_html, flags=re.S) # to strip leading/trailing <p> tags
            if m:
                inner = m.group(1)
                stanza_html_lines.append({'tag': 'p', 'content': inner})
            else:
                # we keep the rest of the tags
                stanza_html_lines.append({'tag': None, 'content': line_html})

        stanzas.append(stanza_lines)
        stanzas_html.append(stanza_html_lines)

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
         'stanzas': stanzas,
        'stanzas_html': stanzas_html
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