#!/usr/bin/env python3
# generate_poems.py

import os
import sys
import frontmatter
import markdown
import re
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

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
poem_root = Path(POEM_DIR)

for path in sorted(poem_root.rglob('*.md')):
    rel = path.relative_to(poem_root)          
    rel_str = rel.as_posix()                   
    slug_default = rel.with_suffix('').as_posix()
    slug_default = re.sub(r'.*[\\/]', '', slug_default) 

    try:
        post = frontmatter.load(str(path))
    except Exception as e:
        print(f"⚠️  Skipping {rel_str}: failed to parse front-matter ({e})", file=sys.stderr)
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
        lines = [ln.rstrip('\n') for ln in s.splitlines()]
        if not lines:
            continue

        stanza_lines = []    
        stanza_html_lines = []

        for ln in lines:
            stanza_lines.append(ln)
            line_html = markdown.markdown(ln, extensions=['extra'])

            m = re.match(r'^\s*<p>(.*)</p>\s*$', line_html, flags=re.S) 
            if m:
                inner = m.group(1)
                stanza_html_lines.append({'tag': 'p', 'content': inner})
            else:
                stanza_html_lines.append({'tag': None, 'content': line_html})

        stanzas.append(stanza_lines)
        stanzas_html.append(stanza_html_lines)

    # Convert whole body to HTML as a fallback (you used this earlier)
    html = markdown.markdown(body, extensions=['nl2br'])

    # default_title based on filename (same behavior as before)
    default_title = path.stem.replace('-', ' ').replace('_', ' ').title()
    title = meta.get('title', default_title)
    slug  = meta.get('slug', slug_default)
    author = meta.get('author', 'Anonymous')

    poems.append({
        'title':        title,
        'slug':         slug,
        'author':       author,
        'stanzas':      stanzas,
        'stanzas_html': stanzas_html,
        'html':         html,         
        'source_path':  rel_str         
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