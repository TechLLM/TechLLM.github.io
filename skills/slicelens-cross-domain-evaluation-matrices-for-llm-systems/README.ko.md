# SliceLens — Cross-Domain Evaluation Matrices for LLM Systems

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> LLM 시스템이 평균적으로 잘하는 부분이 아닌 일반화 실패 지점을 찾으세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

SliceLens는 일반적인 평가 CSV 파일을 LLM, RAG 및 에이전트 시스템의 진단 성능 매트릭스로 변환하기 위한 제안된 오픈 소스 CLI 도구입니다. 이는 결과가 도메인, 질문 유형, 문서 유형, 모달리티 및 견고성 조건에 따라 어떻게 달라지는지 이해해야 하는 팀을 위해 설계되었습니다.

대부분의 평가 요약은 모든 것을 하나의 평균 점수로 압축합니다. 이는 심각한 실패를 숨길 수 있습니다: 시스템이 전반적으로 개선된 것처럼 보이지만 법률 문서, 모호한 질문, 누락된 메타데이터 또는 도메인 외 입력에 대한 성능이 악화될 수 있습니다. SliceLens는 이러한 취약한 부분을 눈에 띄게 만듭니다.

목표는 벤치마크 보고서를 리더보드가 아닌 엔지니어링 진단으로 취급하는 것입니다. SliceLens는 평균 성능, 최악의 부분 성능, 도메인 격차, 누락된 필드 또는 손상 하에서의 성능 저하, 소스에서 대상까지의 전이 패턴을 강조하는 보고서를 생성하여 모델 카드, 풀 리퀘스트, 릴리스 노트 및 회귀 검토에 사용할 수 있습니다.

**누구를 위한 건가요.** SliceLens는 LLM 시스템이 어디에서 작동하는지, 어디에서 실패하는지, 그리고 보고된 개선이 실제로 일반화되는지 여부에 대한 더 명확한 증거가 필요한 ML 엔지니어, 평가 팀, RAG 빌더, 에이전트 개발자, 기술 작가 및 오픈 소스 유지 관리자를 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
python scripts/run.py --selftest
```

**예상 출력:**

```text
# SliceLens Evaluation Report

## Summary

| Metric | Value |
| --- | --- |
| Rows | 12 |
| Overall mean | 0.653 |
| Score column | score |
| Worst-slice min count | 2 |

## Worst Slice

| Dimension | Value | Mean | Count |
| --- | --- | --- | --- |
| condition | missing_metadata | 0.413 | 3 |

## Source-to-Target Transfer Matrix

| source_domain \ target_domain | finance | legal | medical |
| --- | --- | --- | --- |
| finance | 0.895 (n=2) | 0.580 (n=1) | 0.390 (n=1) |
| legal | 0.620 (n=1) | 0.800 (n=2) | 0.440 (n=1) |
| medical | 0.410 (n=1) | 0.550 (n=1) | 0.730 (n=2) |

## Domain Gaps

| Source domain | In-domain mean | In n | Out-domain mean | Out n | Gap |
| --- | --- | --- | --- | --- | --- |
| finance | 0.895 | 2 | 0.485 | 2 | 0.410 |
| legal | 0.800 | 2 | 0.530 | 2 | 0.270 |
| medical | 0.730 | 2 | 0.480 | 2 | 0.250 |

## Slice Tables

### condition

| Value | Mean | Count |
| --- | --- | --- |
| missing_metadata | 0.413 | 3 |
| format_shift | 0.610 | 3 |
| clean | 0.795 | 6 |

### document_type

| Value | Mean | Count |
| --- | --- | --- |
| (missing) | 0.410 | 1 |
| csv | 0.627 | 3 |
| pdf | 0.667 | 7 |
| html | 0.880 | 1 |

### modality

| Value | Mean | Count |
| --- | --- | --- |
| image | 0.600 | 1 |
| text | 0.658 | 11 |

### question_type

| Value | Mean | Count |
| --- | --- | --- |
| ambiguous | 0.460 | 4 |
| comparison | 0.613 | 4 |
| fact | 0.888 | 4 |

### source_domain

| Value | Mean | Count |
| --- | --- | --- |
| medical | 0.605 | 4 |
| legal | 0.665 | 4 |
| finance | 0.690 | 4 |

### target_domain

| Value | Mean | Count |
| --- | --- | --- |
| medical | 0.573 | 4 |
| legal | 0.683 | 4 |
| finance | 0.705 | 4 |

## Missing-Field Degradation

| Field | Present mean | Present n | Missing mean | Missing n | Degradation |
| --- | --- | --- | --- | --- | --- |
| source_domain | 0.653 | 12 | n/a | 0 | n/a |
| target_domain | 0.653 | 12 | n/a | 0 | n/a |
| question_type | 0.653 | 12 | n/a | 0 | n/a |
| document_type | 0.675 | 11 | 0.410 | 1 | 0.
… (+90 chars truncated)
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
mkdir -p ~/.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
cp -r /tmp/techllm-skills/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/* ~/.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/

# 프로젝트 로컬
mkdir -p .claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
cp -r /tmp/techllm-skills/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/* .claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT]
              [--score-column SCORE_COLUMN] [--source-column SOURCE_COLUMN]
              [--target-column TARGET_COLUMN] [--slice-columns SLICE_COLUMNS]
              [--min-count MIN_COUNT] [--precision PRECISION] [--json]
              [--selftest]

Generate cross-domain SliceLens evaluation matrices from a CSV file. Runs a
built-in no-key self-test when --selftest is provided or no input is set.

options:
  -h, --help            show this help message and exit
  --input INPUT         Evaluation CSV path. Defaults to SLICELENS_INPUT, then
                        built-in sample for self-test.
  --output OUTPUT       Markdown report path. Defaults to stdout or
                        SLICELENS_OUTPUT.
  --score-column SCORE_COLUMN
                        Numeric score column. Default: score.
  --source-column SOURCE_COLUMN
                        Source-domain column. Default: source_domain.
  --target-column TARGET_COLUMN
                        Target-domain column. Default: target_domain.
  --slice-columns SLICE_COLUMNS
                        Comma-separated optional categorical columns. Default:
                        question_type,document_type,modality,condition.
  --min-count MIN_COUNT
                        Minimum rows for worst-slice eligibility. Default: 2.
  --precision PRECISION
                        Decimal places for numeric output. Default: 3.
  --json                Emit the raw analysis dictionary as deterministic JSON
                        instead of Markdown.
  --selftest            Run on built-in sample data without any API key or
                        external service.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 기존의 평가 내보내기 파일을 CSV 형식으로 읽어들이므로 팀에서 현재의 벤치마크 또는 회귀 파이프라인의 결과를 사용할 수 있습니다.
- 결과를 소스 도메인, 대상 도메인, 질문 유형, 문서 유형, 모달리티 및 견고성 조건과 같은 통제된 부분으로 그룹화합니다.
- 평균 점수, 최악의 부분 점수, 도메인 격차, 누락된 필드에서의 성능 저하 및 소스에서 대상까지의 전이 패턴을 포함한 진단 메트릭을 계산합니다.
- 부분화된 결과를 성능 매트릭스로 변환하여 일반화 실패를 보다 쉽게 검사하고 비교할 수 있도록 합니다.
- 엔지니어링 검토, 모델 문서화 및 릴리스 아티팩트에 적합한 정제된 Markdown 형식의 서술을 내보냅니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 보고서가 실패를 명확하게 설명하기에는 너무 광범위해 보입니다. | 입력 데이터에 도메인, 질문 유형, 문서 유형 또는 조건을 분리하기에 충분한 부분 열이 포함되지 않았을 수 있습니다. | SliceLens가 의미 있는 그룹 간의 성능을 비교할 수 있도록 평가 내보내기에 관련 메타데이터 열을 추가하세요. |
| 시스템이 평균 점수에서는 강하지만 보고서에서는 약하게 나타납니다. | 평균이 도메인 또는 조건에 걸친 불균일한 성능을 숨기고 있습니다. | 최악의 부분, 도메인 격차 및 전이 매트릭스 섹션을 사용하여 성능이 저하되는 특정 분포를 식별하세요. |
| 누락된 필드 또는 손상 분석이 비어 있습니다. | 평가 데이터에 누락된 메타데이터, 손상된 입력 또는 기타 견고성 조건에 대해 행을 레이블링하지 않았습니다. | 보고서를 생성하기 전에 영향을 받는 예제에 명시적 조건 레이블을 추가하세요. |

## 자주 묻는 질문

**SliceLens가 제 기존 평가 파이프라인을 대체할 수 있나요?**

아니오. SliceLens는 기존 평가 실행 후에 사용되도록 설계되었습니다. 내보내기 결과를 소비하고 이를 교차 도메인 진단 보고서로 변환합니다.

**왜 평균 정확도나 적중률만 보고하지 않나요?**

평균은 유용하지만 불완전합니다. 드물고 어렵거나 도메인 외 사례에서의 회귀를 숨길 수 있습니다. SliceLens는 평균치를 유지하면서 시스템이 일반화하지 못하는 부분을 보여줍니다.

**이것을 RAG 평가에 사용할 수 있나요?**

예. SliceLens는 특히 RAG 시스템에 유용합니다. 문서 유형, 도메인, 질문 유형, 메타데이터 품질 및 입력 손상에 따라 검색 및 답변 품질이 달라지기 때문입니다.

**이것이 에이전트 또는 라우터 평가에 도움이 될 수 있나요?**

예. 에이전트 라우팅 및 도구 선택 시스템은 집계에서는 정확해 보이지만 특정 도메인 또는 입력 형식에서는 실패할 수 있습니다. SliceLens는 이러한 패턴을 노출하도록 설계되었습니다.

**SliceLens는 어떤 종류의 출력을 생성하나요?**

슬라이스 수준의 성능, 약한 분포, 도메인 격차, 견고성 저하 및 전이 매트릭스를 요약하는 Markdown 보고서를 생성하며, 이는 검토 및 문서화에 적합한 형식입니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/` 또는 `.claude/skills/slicelens-cross-domain-evaluation-matrices-for-llm-systems/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
