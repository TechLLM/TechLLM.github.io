#!/usr/bin/env python3
"""Sync a Hugo post (and its images) to the Obsidian vault."""
import sys, re, shutil
from pathlib import Path

SITE_ROOT = Path(__file__).parent.parent
STATIC_IMAGES = SITE_ROOT / "static" / "images"
OBSIDIAN_ROOT = Path("/Users/noah/Noah-Wiki/Noah-Wiki")
VAULT_BLOG = OBSIDIAN_ROOT / "30-blog" / "techllm"
VAULT_IMAGES = VAULT_BLOG / "images"

def normalize_image_path(path: str) -> str:
    return path.split("#", 1)[0].split("?", 1)[0]

def collect_images(text: str) -> list[str]:
    patterns = [
        r'image:\s*["\']?(/images/[^"\'\s]+)["\']?',
        r'!\[[^\]]*\]\((/images/[^)\s]+)[^)]*\)',
        r'{{<\s*figure\b[^>]*\bsrc=["\'](/images/[^"\']+)["\'][^>]*>}}',
    ]
    images = []
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            img = normalize_image_path(match.group(1)).removeprefix("/images/")
            if img not in seen:
                seen.add(img)
                images.append(img)
    return images

def sync(post_path: str):
    src = Path(post_path)
    if not src.exists():
        print(f"ERROR: {src} not found")
        sys.exit(1)

    text = src.read_text()

    # Collect referenced images
    images = collect_images(text)

    # Copy images
    VAULT_IMAGES.mkdir(parents=True, exist_ok=True)
    for img in images:
        src_img = STATIC_IMAGES / img
        dst_img = VAULT_IMAGES / Path(img).name
        if src_img.exists():
            shutil.copy2(src_img, dst_img)
            print(f"  image: {dst_img.name}")
        else:
            print(f"  WARN: image not found: {src_img}")

    # Convert /images/... → images/... for Obsidian relative links
    obsidian_text = re.sub(r'(/images/)', 'images/', text)

    # Write post
    dst_post = VAULT_BLOG / src.name
    dst_post.write_text(obsidian_text)
    print(f"OK  synced → {dst_post}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sync_hugo_to_obsidian.py <post.md>")
        sys.exit(1)
    sync(sys.argv[1])
