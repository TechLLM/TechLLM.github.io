#!/usr/bin/env python3
"""
techllm 블로그 포스트 품질 검증 스크립트.

기본 검증 (소스 없이도 동작):
  - frontmatter 필수 필드: title, date, draft, description, tags
  - 한국어 문자 수 >= 1,500자 (SKILL.md 목표치 ~2,500 한국어 문자 기준)
  - H2 섹션 >= 3개
  - 본문 내 원문 출처 라인(italic markdown link) 존재

원문 텍스트가 함께 주어지면 (--source) gnomon TranslationGate로:
  - 길이 비율 (0.4~3.5배)
  - 고유명사 보존 (도메인별 화이트리스트 + 자동 추출)
  - 종합 품질 점수

사용법:
  python3 validate_blog_quality.py --post content/posts/foo.md
  python3 validate_blog_quality.py --post content/posts/foo.md --source /tmp/source.txt

종료 코드:
  0 = PASS
  1 = FAIL
"""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FRONTMATTER = ["title:", "date:", "draft:", "description:", "tags:"]
MIN_KOREAN_CHARS = 1500
TARGET_KOREAN_CHARS = 2500
MIN_H2_COUNT = 3

def extract_proper_nouns_from_source(source_path: str, top_n: int = 8) -> list:
    """Extract likely proper nouns from source text.

    Strategy: multi-word capitalized phrases are highly reliable proper nouns.
    Single capitalized tokens are accepted only if they appear ≥3 times AND
    never appear lowercased in the text (filters sentence-starting common words).
    """
    text = Path(source_path).read_text(encoding="utf-8", errors="ignore")
    candidates = {}

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


def extract_body(note: str) -> str:
    return re.sub(r"^---.*?---\s*", "", note, flags=re.DOTALL).strip()


def count_korean_chars(text: str) -> int:
    return len(re.findall(r"[가-힣]", text))


def check(post_path: str, source_path: str = "") -> dict:
    note = Path(post_path).read_text(encoding="utf-8")
    results = {}

    missing = [f for f in REQUIRED_FRONTMATTER if f not in note]
    results["frontmatter_complete"] = len(missing) == 0
    results["missing_fields"] = missing

    body = extract_body(note)
    body_len = len(body)
    korean_len = count_korean_chars(body)
    results["body_length"] = body_len
    results["korean_char_count"] = korean_len
    results["body_length_pass"] = korean_len >= MIN_KOREAN_CHARS
    results["target_reached"] = korean_len >= TARGET_KOREAN_CHARS

    h2_count = len(re.findall(r"^## .+", note, re.MULTILINE))
    results["h2_count"] = h2_count
    results["section_structure_pass"] = h2_count >= MIN_H2_COUNT

    source_line = re.search(r"\*원문:\s*\[[^\]]+\]\(https?://[^\)]+\)", body)
    results["source_attribution_pass"] = source_line is not None

    gate_result = None
    if source_path and Path(source_path).exists():
        try:
            import sys as _sys
            _gnomon_site = "/Users/noah/.local/share/uv/tools/gnomon/lib/python3.12/site-packages"
            if _gnomon_site not in _sys.path:
                _sys.path.insert(0, _gnomon_site)
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
        results["frontmatter_complete"],
        results["body_length_pass"],
        results["section_structure_pass"],
        results["source_attribution_pass"],
    ])
    final_pass = basic_pass and (gate_result.get("passed") if gate_result and "passed" in gate_result else True)

    fix_hints = []
    if missing:
        fix_hints.append(f"frontmatter 누락 필드: {', '.join(missing)}")
    if not results["body_length_pass"]:
        fix_hints.append(f"한국어 분량 부족 ({korean_len}자, 최소 {MIN_KOREAN_CHARS}자 / 목표 {TARGET_KOREAN_CHARS}자)")
    elif not results["target_reached"]:
        fix_hints.append(f"한국어 분량은 통과했지만 목표치({TARGET_KOREAN_CHARS}자) 미달 — 현재 {korean_len}자")
    if not results["section_structure_pass"]:
        fix_hints.append(f"H2 섹션 부족 ({h2_count}개, 최소 {MIN_H2_COUNT}개 필요)")
    if not results["source_attribution_pass"]:
        fix_hints.append("본문 끝에 '*원문: [제목](URL)' 형식의 출처 라인 누락")
    if gate_result and not gate_result.get("passed") and "details" in gate_result:
        d = gate_result["details"]
        if d.get("length_ratio", {}).get("ratio", 1) < 0.4:
            fix_hints.append("번역/요약 분량이 원문 대비 너무 짧음")
        missing_nouns = d.get("proper_nouns", {}).get("missing", [])
        if missing_nouns:
            fix_hints.append(f"고유명사 누락: {', '.join(missing_nouns)}")

    return {
        "passed": final_pass,
        "verdict": "PASS ✅" if final_pass else "FAIL ❌",
        "checks": results,
        "gate": gate_result,
        "fix_hints": fix_hints,
    }


def main():
    parser = argparse.ArgumentParser(description="techllm 블로그 포스트 품질 검증")
    parser.add_argument("--post", required=True, help="블로그 포스트 마크다운 경로")
    parser.add_argument("--source", default="", help="원문 텍스트 파일 경로 (선택)")
    args = parser.parse_args()

    result = check(args.post, args.source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
