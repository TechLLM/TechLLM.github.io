#!/usr/bin/env python3
"""Validate a Hugo post before publishing."""
import sys, re, os
from pathlib import Path
from datetime import datetime, timezone

SITE_ROOT = Path(__file__).parent.parent
POSTS_DIR = SITE_ROOT / "content" / "posts"
IMAGES_DIR = SITE_ROOT / "static" / "images"

def check(post_path: str):
    path = Path(post_path)
    errors = []
    warnings = []

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    text = path.read_text()

    # Frontmatter present
    if not text.startswith("---"):
        errors.append("No frontmatter found")

    # Required fields
    for field in ["title:", "date:", "draft:", "description:"]:
        if field not in text:
            errors.append(f"Missing frontmatter field: {field}")

    # draft: false
    if "draft: true" in text:
        warnings.append("draft is true — post will not be published")

    # Date not in future (UTC)
    date_match = re.search(r"date:\s*(.+)", text)
    if date_match:
        raw = date_match.group(1).strip()
        try:
            from datetime import datetime
            import email.utils
            # Parse ISO 8601
            raw_clean = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw_clean)
            now_utc = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt > now_utc:
                errors.append(f"Post date {dt.isoformat()} is in the future (UTC now: {now_utc.isoformat()}) — Hugo will exclude it")
        except Exception as e:
            warnings.append(f"Could not parse date '{raw}': {e}")

    # Cover image exists
    img_match = re.search(r'image:\s*"(/images/[^"]+)"', text)
    if img_match:
        img_rel = img_match.group(1).lstrip("/")
        img_abs = SITE_ROOT / "static" / img_rel
        if not img_abs.exists():
            errors.append(f"Cover image not found: {img_abs}")
    else:
        warnings.append("No cover image defined")

    # Body images exist
    for m in re.finditer(r'!\[.*?\]\((/images/[^)]+)\)', text):
        img_rel = m.group(1).lstrip("/")
        img_abs = SITE_ROOT / "static" / img_rel
        if not img_abs.exists():
            errors.append(f"Body image not found: {img_abs}")

    # Report
    ok = len(errors) == 0
    print(f"{'OK' if ok else 'FAIL'}  {path.name}")
    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"  WARN:  {w}")

    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_hugo_post.py <post.md>")
        sys.exit(1)
    check(sys.argv[1])
