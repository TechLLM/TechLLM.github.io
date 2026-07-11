# RiftLens — Domain Collapse Maps for RAG Evaluation

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> RAG 시스템이 조용히 실패하는 소스 도메인을 찾아보세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

RiftLens는 소스 도메인별로 검색 증강 생성 시스템을 평가하기 위한 제안된 명령줄 벤치마크입니다. 하나의 통합된 점수가 아닌 방식으로 평가합니다.

혼합된 지식 기반에는 종종 메모, 위키 페이지, API 참조, 연구 요약, 티켓 및 정책 문서가 포함됩니다. 집계된 관련성 메트릭은 시스템이 실제로보다 더 건강해 보이게 만들면서 특정 문서 유형의 심각한 실패를 숨길 수 있습니다.

RiftLens는 이러한 숨겨진 실패를 검토 가능한 Markdown 보고서로 전환합니다. 이를 통해 팀은 어떤 도메인이 개선되었는지, 어떤 도메인이 악화되었는지, 그리고 검색 또는 재순위 변경이 실제로 제공하는 지식 기반 전체에 걸쳐 일반화되는지 여부를 확인할 수 있습니다.

**누구를 위한 건가요.** RiftLens는 검색기, 재순위기, 관련성 게이트 또는 지식 기반 인덱싱 파이프라인에 대한 변경 사항을 배포하기 전에 더 명확한 회귀 신호를 필요로 하는 RAG 빌더, 평가 엔지니어, AI 플랫폼 팀 및 기술 검토자를 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/riftlens-domain-collapse-maps-for-rag-evaluation
python scripts/run.py --selftest
```

**예상 출력:**

```text
# RiftLens Domain Collapse Report

- Threshold: `0.60`
- Top K: `all`
- Queries: `3`
- Retrieved items: `8`
- Overall hit rate: `75.0%`
- Overall false pass rate: `50.0%`
- Overall false reject rate: `25.0%`
- Worst-domain gap: `100.0 pp`
- Worst domain: `api_reference`

| Domain | Coverage | Hit rate | False pass | False reject | Relevant | Passed |
|---|---:|---:|---:|---:|---:|---:|
| api_reference | 66.7% | 0.0% | 0.0% | 100.0% | 1 | 0 |
| notes | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |
| tickets | 66.7% | 100.0% | 0.0% | 0.0% | 1 | 1 |
| wiki | 66.7% | 100.0% | 100.0% | 0.0% | 1 | 2 |

## Flags

- Collapse: `api_reference` trails the best domain by `100.0 pp`.
- Risk: `api_reference` has high false reject rate (`100.0%`).
- Risk: `notes` has high false pass rate (`100.0%`).
- Risk: `wiki` has high false pass rate (`100.0%`).
```

## 요구 사항

| Key | Value |
|---|---|
| 파이썬 | 3.9+ |
| 의존성 | 파이썬 표준 라이브러리만 |
| API 키 | 필요 없음 |

## 📦 설치

**1) Claude Code / OpenClaw 스킬로**

```bash
# 개인용 (모든 프로젝트에서 사용)
git clone https://github.com/TechLLM/TechLLM.github.io /tmp/techllm-skills
mkdir -p ~/.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation
cp -r /tmp/techllm-skills/skills/riftlens-domain-collapse-maps-for-rag-evaluation/* ~/.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/

# 프로젝트 로컬
mkdir -p .claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation
cp -r /tmp/techllm-skills/skills/riftlens-domain-collapse-maps-for-rag-evaluation/* .claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/riftlens-domain-collapse-maps-for-rag-evaluation
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/riftlens-domain-collapse-maps-for-rag-evaluation/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT] [--threshold THRESHOLD]
              [--top-k TOP_K] [--selftest]

Generate domain-split RAG retrieval diagnostics as Markdown.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        JSONL retrieval log. If omitted, RiftLens uses built-
                        in sample data.
  --output OUTPUT, -o OUTPUT
                        Optional Markdown output path. Defaults to stdout.
  --threshold THRESHOLD
                        Score threshold for pass/fail. Defaults to
                        RIFTLENS_THRESHOLD or 0.60.
  --top-k TOP_K         Evaluate only the first K retrieved documents per
                        query. Defaults to RIFTLENS_TOP_K or all.
  --selftest            Run on built-in sample data. This is also the default
                        when --input is omitted.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 일반적인 JSONL 입력에서 쿼리, 답변 및 검색 기록을 읽습니다.
- 검색된 문서의 도메인 태그를 사용하여 소스 유형별로 평가를 분할합니다.
- 적중률, 잘못된 통과율, 잘못된 거부율 및 커버리지와 같은 도메인별 진단을 계산합니다.
- 평균이 강하더라도 국부적인 회귀를 숨기지 않도록 최악의 도메인 격차를 강조합니다.
- 풀 리퀘스트, 감사, 실험 노트 및 릴리스 게이트에 대한 Markdown 보고서를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 보고서에 도메인이 누락되었습니다. | 해당 도메인의 검색된 문서에 태그가 지정되지 않았거나 평가된 레코드에 해당 도메인이 포함되지 않았습니다. | 검색된 각 문서에 일관된 도메인 태그가 있는지, 그리고 평가 입력에 누락된 도메인의 예제가 포함되어 있는지 확인하세요. |
| 전체 점수는 개선되었지만 한 도메인의 점수가 훨씬 더 나빠 보입니다. | 변경 사항이 일반적이거나 쉬운 도메인을 개선하면서 규모가 작거나 더 어려운 소스 유형의 성능을 저하시킬 수 있습니다. | 변경 사항을 배포하기 전에 영향을 받는 도메인을 별도로 검토하고 해당 분할의 예를 이전 실행과 비교하세요. |
| 잘못된 통과율과 잘못된 거부율이 예상과 다르게 보입니다. | 관련성 임계값이 평가 중인 검색기, 재순위기 또는 게이트의 점수 척도 또는 동작과 일치하지 않을 수 있습니다. | 임계값의 의미를 확인하고 의도한 통과 또는 거부 결정을 반영하는 컷오프를 선택하세요. |

## 자주 묻는 질문

**왜 도메인별로 평가하는 대신 하나의 관련성 점수를 사용하나요?**

단일 점수는 불균등한 동작을 숨길 수 있습니다. 도메인 수준 평가는 시스템이 사용자가 실제로 검색하는 다양한 종류의 콘텐츠에 걸쳐 작동하는지 여부를 보여줍니다.

**RiftLens는 어떤 종류의 도메인을 비교할 수 있나요?**

검색 데이터에 태그를 지정할 수 있는 모든 소스 유형, 메모, 위키 노드, 티켓, 연구 요약, API 문서, 정책 문서 및 내부 문서를 포함합니다.

**RiftLens는 기존 RAG 메트릭을 대체하기 위한 것인가요?**

아니오. 이는 집계 메트릭에 분할 수준 진단 및 최악의 도메인 회귀 신호를 추가하여 보완합니다.

**보고서는 어디에서 사용되나요?**

Markdown 보고서는 평가 검토, 풀 리퀘스트, 릴리스 게이트, 감사 및 실험 노트를 위해 설계되었습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/` 또는 `.claude/skills/riftlens-domain-collapse-maps-for-rag-evaluation/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
