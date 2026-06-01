#!/usr/bin/env python3
"""Hugo 블로그 포스트 통합 검증 (기술 + 품질).

기존 두 스크립트(validate_hugo_post.py + validate_blog_quality.py)를 단일 진입점으로 통합.

기술 검증:
  - frontmatter 필수 필드(title/date/draft/description/tags)
  - draft 상태
  - date UTC 미래 아님 (Hugo는 미래 날짜 포스트 제외 → 404)
  - cover image 파일 존재
  - 본문 이미지 파일 존재 (Markdown 이미지 + Hugo figure shortcode)
  - (옵션 --public-url) 공개 페이지와 공개 이미지 URL 200 확인

품질 검증:
  - 한국어 문자 ≥ 1,500자 (기본 목표 2,000자)
  - H2 섹션 ≥ 3개
  - 본문에 원문 출처 라인 존재
  - (옵션 --source) gnomon TranslationGate: 길이 비율, 고유명사 보존

사용법:
  /opt/homebrew/bin/python3 /Users/noah/.openclaw/workspace-techllm/scripts/validate_blog.py --post content/posts/foo.md
  /opt/homebrew/bin/python3 /Users/noah/.openclaw/workspace-techllm/scripts/validate_blog.py --post content/posts/foo.md --source /tmp/source.txt

종료 코드: 0=PASS, 1=FAIL
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SITE_ROOT = Path(__file__).parent.parent

REQUIRED_FRONTMATTER = ["title:", "date:", "draft:", "description:", "tags:"]
MIN_KOREAN_CHARS = 1500
TARGET_KOREAN_CHARS = 2000
MIN_H2_COUNT = 3


class ImageSrcParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attrs_dict = dict(attrs)
        src = attrs_dict.get("src")
        if src:
            self.image_srcs.append(src)


def extract_body(note: str) -> str:
    return re.sub(r"^---.*?---\s*", "", note, flags=re.DOTALL).strip()


def count_korean_chars(text: str) -> int:
    return len(re.findall(r"[가-힣]", text))


def normalize_image_path(path: str) -> str:
    return path.split("#", 1)[0].split("?", 1)[0]


def extract_local_image_paths(text: str) -> list[str]:
    """Return /images/... references from frontmatter, Markdown, and Hugo shortcodes."""
    patterns = [
        r'image:\s*["\']?(/images/[^"\'\s]+)["\']?',
        r'!\[[^\]]*\]\((/images/[^)\s]+)[^)]*\)',
        r'{{<\s*figure\b[^>]*\bsrc=["\'](/images/[^"\']+)["\'][^>]*>}}',
    ]
    images: list[str] = []
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            img = normalize_image_path(match.group(1))
            if img not in seen:
                seen.add(img)
                images.append(img)
    return images


def check_local_image_exists(image_path: str) -> str | None:
    img_rel = image_path.lstrip("/")
    img_abs = SITE_ROOT / "static" / img_rel
    if not img_abs.exists():
        return str(img_abs)
    return None


def check_tech(post_path: Path, text: str) -> dict:
    errors = []
    warnings = []

    if not text.startswith("---"):
        errors.append("No frontmatter found")

    for field in REQUIRED_FRONTMATTER:
        if field not in text:
            errors.append(f"Missing frontmatter field: {field}")

    if "draft: true" in text:
        warnings.append("draft is true — post will not be published")

    date_match = re.search(r"date:\s*(.+)", text)
    if date_match:
        raw = date_match.group(1).strip()
        try:
            raw_clean = raw.replace("Z", "+00:00")
            dt = datetime.fromisoformat(raw_clean)
            now_utc = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt > now_utc:
                errors.append(
                    f"Post date {dt.isoformat()} is in the future "
                    f"(UTC now: {now_utc.isoformat()}) — Hugo will exclude it"
                )
        except Exception as e:
            warnings.append(f"Could not parse date '{raw}': {e}")

    cover_match = re.search(r'image:\s*["\']?(/images/[^"\'\s]+)["\']?', text)
    if cover_match:
        missing = check_local_image_exists(normalize_image_path(cover_match.group(1)))
        if missing:
            errors.append(f"Cover image not found: {missing}")
    else:
        warnings.append("No cover image defined")

    for image_path in extract_local_image_paths(extract_body(text)):
        missing = check_local_image_exists(image_path)
        if missing:
            errors.append(f"Body image not found: {missing}")

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


def fetch_url_status(url: str) -> tuple[int | None, str]:
    try:
        req = Request(url, headers={"User-Agent": "techllm-blog-validator/1.0"})
        with urlopen(req, timeout=15) as response:
            response.read(512)
            return response.status, ""
    except Exception as e:
        return None, str(e)


def check_public_url(public_url: str) -> dict:
    errors = []
    warnings = []
    page_status, page_error = fetch_url_status(public_url)
    if page_status != 200:
        errors.append(f"Public page not reachable: {public_url} ({page_error or page_status})")
        return {"passed": False, "errors": errors, "warnings": warnings, "images": []}

    try:
        req = Request(public_url, headers={"User-Agent": "techllm-blog-validator/1.0"})
        with urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        errors.append(f"Could not fetch public HTML: {e}")
        return {"passed": False, "errors": errors, "warnings": warnings, "images": []}

    parser = ImageSrcParser()
    parser.feed(html)

    image_urls = []
    seen = set()
    for src in parser.image_srcs:
        absolute = urljoin(public_url, src)
        parsed = urlparse(absolute)
        if "/images/" not in parsed.path:
            continue
        normalized = absolute.split("#", 1)[0].split("?", 1)[0]
        if normalized not in seen:
            seen.add(normalized)
            image_urls.append(normalized)

    if not image_urls:
        warnings.append("No public /images/ <img> tags found")

    image_results = []
    for image_url in image_urls:
        status, error = fetch_url_status(image_url)
        image_results.append({"url": image_url, "status": status, "error": error})
        if status != 200:
            errors.append(f"Public image not reachable: {image_url} ({error or status})")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "images": image_results,
    }


def extract_proper_nouns_from_source(source_path: str, top_n: int = 8) -> list:
    """Extract likely proper nouns from source text."""
    text = Path(source_path).read_text(encoding="utf-8", errors="ignore")
    candidates: dict[str, int] = {}

    for m in re.finditer(
        r"\b(?:[A-Z][A-Za-z]+(?:\s+(?:of|the|de|von|van)\s+)?(?:[A-Z][A-Za-z]+))(?:\s+[A-Z][A-Za-z]+){0,2}\b",
        text,
    ):
        phrase = m.group(0)
        candidates[phrase] = candidates.get(phrase, 0) + 1

    common_singletons = {
        "Cognitive", "University", "Journal", "Source", "Author", "Summary",
        "Image", "Tags", "About", "Abstract", "Editorial", "Notes", "Open",
        "Closed", "Featured", "Original", "Research", "Published", "Stronger",
        "Resilient", "Participants", "Bias", "Positive", "Negative", "Key",
        "Question", "Answered", "Title",
    }
    lower_tokens = set(re.findall(r"\b[a-z]{4,}\b", text))
    for m in re.finditer(r"\b[A-Z][A-Za-z]{3,}\b", text):
        token = m.group(0)
        if token.lower() in lower_tokens or token in common_singletons:
            continue
        candidates[token] = candidates.get(token, 0) + 1

    ranked = sorted(candidates.items(), key=lambda kv: -kv[1])
    return [name for name, count in ranked if count >= 2][:top_n]


def check_quality(note: str, source_path: str = "") -> dict:
    checks: dict = {}

    missing = [f for f in REQUIRED_FRONTMATTER if f not in note]
    checks["frontmatter_complete"] = len(missing) == 0
    checks["missing_fields"] = missing

    body = extract_body(note)
    korean_len = count_korean_chars(body)
    checks["body_length"] = len(body)
    checks["korean_char_count"] = korean_len
    checks["body_length_pass"] = korean_len >= MIN_KOREAN_CHARS
    checks["target_reached"] = korean_len >= TARGET_KOREAN_CHARS

    h2_count = len(re.findall(r"^## .+", note, re.MULTILINE))
    checks["h2_count"] = h2_count
    checks["section_structure_pass"] = h2_count >= MIN_H2_COUNT

    source_line = re.search(
        r"(?:\*{0,2}원문(?:\s*출처|\s*영상)?\s*:?\*{0,2}\s*)"
        r"(?:\[[^\]]+\]\(https?://[^\)]+\)|<a\s+href=[\"']https?://[^\"']+[\"'][^>]*>.+?</a>|https?://\S+)",
        body,
        re.IGNORECASE | re.DOTALL,
    )
    checks["source_attribution_pass"] = source_line is not None

    gate_result = None
    if source_path and Path(source_path).exists():
        try:
            _gnomon_site = "/Users/noah/.local/share/uv/tools/gnomon/lib/python3.12/site-packages"
            if _gnomon_site not in sys.path:
                sys.path.insert(0, _gnomon_site)
            from openclaw_gnomon.gates.translation_gate import TranslationGate
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_note = Path(tmpdir) / "post.md"
                tmp_note.write_text(note, encoding="utf-8")

                class Spec:
                    pass

                spec = Spec()
                spec.source_path = source_path
                spec.target_lang = "ko"
                spec.proper_nouns = extract_proper_nouns_from_source(source_path)
                spec.length_ratio_min = 0.4
                spec.length_ratio_max = 3.5

                gate = TranslationGate()
                gr = gate.evaluate(Path(tmpdir), spec)
                gate_result = {
                    "passed": gr.passed,
                    "score": round(gr.score, 1),
                    "details": gr.details,
                }
        except Exception as e:
            gate_result = {"error": str(e)}

    basic_pass = all([
        checks["frontmatter_complete"],
        checks["body_length_pass"],
        checks["section_structure_pass"],
        checks["source_attribution_pass"],
    ])
    gate_pass = gate_result.get("passed") if gate_result and "passed" in gate_result else True

    fix_hints = []
    if missing:
        fix_hints.append(f"frontmatter 누락 필드: {', '.join(missing)}")
    if not checks["body_length_pass"]:
        fix_hints.append(
            f"한국어 분량 부족 ({korean_len}자, 최소 {MIN_KOREAN_CHARS}자 / 기본 목표 {TARGET_KOREAN_CHARS}자)"
        )
    elif not checks["target_reached"]:
        fix_hints.append(
            f"한국어 분량은 통과했지만 기본 목표치({TARGET_KOREAN_CHARS}자) 미달 — 현재 {korean_len}자"
        )
    if not checks["section_structure_pass"]:
        fix_hints.append(f"H2 섹션 부족 ({h2_count}개, 최소 {MIN_H2_COUNT}개 필요)")
    if not checks["source_attribution_pass"]:
        fix_hints.append("본문 끝에 원문 출처 라인 누락")
    if gate_result and not gate_result.get("passed") and "details" in gate_result:
        d = gate_result["details"]
        if d.get("length_ratio", {}).get("ratio", 1) < 0.4:
            fix_hints.append("번역/요약 분량이 원문 대비 너무 짧음")
        missing_nouns = d.get("proper_nouns", {}).get("missing", [])
        if missing_nouns:
            fix_hints.append(f"고유명사 누락: {', '.join(missing_nouns)}")

    return {
        "passed": basic_pass and gate_pass,
        "checks": checks,
        "gate": gate_result,
        "fix_hints": fix_hints,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="techllm Hugo 블로그 통합 검증 (기술 + 품질)"
    )
    parser.add_argument("--post", required=True, help="블로그 포스트 마크다운 경로")
    parser.add_argument("--source", default="", help="원문 텍스트 파일 경로 (옵션)")
    parser.add_argument(
        "--tech-only",
        action="store_true",
        help="기술 검증만 실행 (frontmatter/date/이미지)",
    )
    parser.add_argument(
        "--quality-only",
        action="store_true",
        help="품질 검증만 실행 (분량/H2/출처/gnomon)",
    )
    parser.add_argument(
        "--public-url",
        default="",
        help="발행 후 공개 페이지 URL. HTML과 본문 이미지 URL 200 상태를 확인",
    )
    args = parser.parse_args()

    post_path = Path(args.post)
    if not post_path.exists():
        print(json.dumps({"passed": False, "error": f"File not found: {post_path}"}, ensure_ascii=False))
        return 1

    text = post_path.read_text(encoding="utf-8")

    result: dict = {"post": str(post_path)}

    if not args.quality_only:
        result["tech"] = check_tech(post_path, text)
    if not args.tech_only:
        result["quality"] = check_quality(text, args.source)
    if args.public_url:
        result["public"] = check_public_url(args.public_url)

    passed = True
    if "tech" in result:
        passed = passed and result["tech"]["passed"]
    if "quality" in result:
        passed = passed and result["quality"]["passed"]
    if "public" in result:
        passed = passed and result["public"]["passed"]
    result["passed"] = passed
    result["verdict"] = "PASS ✅" if passed else "FAIL ❌"

    fix_hints = []
    if "tech" in result and not result["tech"]["passed"]:
        fix_hints.extend(f"[tech] {e}" for e in result["tech"]["errors"])
    if "quality" in result:
        fix_hints.extend(f"[quality] {h}" for h in result["quality"]["fix_hints"])
    if "public" in result and not result["public"]["passed"]:
        fix_hints.extend(f"[public] {e}" for e in result["public"]["errors"])
    result["fix_hints"] = fix_hints

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
