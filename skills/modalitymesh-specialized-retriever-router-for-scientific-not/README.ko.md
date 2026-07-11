# ModalityMesh — Specialized Retriever Router for Scientific Notes

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 과학적 노트를 각 양식에 맞는 검색 전략으로 전달하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

ModalityMesh는 Markdown 기반의 지식에서 모달리티 인식 검색 매니페스트를 생성하기 위한 오픈 소스 CLI로 제안된 도구입니다. 이는 검색 시스템이 과학적 노트가 단순히 산문이 아니라 표, 공식, 코드, 인용문, 타임라인, 벤치마크 및 기타 구조화된 증거를 포함할 수 있음을 이해하도록 돕습니다.

대부분의 검색 파이프라인은 노트를 일반적인 텍스트 덩어리로 평면화하고 모든 것을 동일한 임베딩 또는 랭킹 모델을 통해 전송합니다. 이는 특히 최상의 일치가 숫자 비교, 기호 구조, 인용문 맥락 또는 시간적 순서에 의존할 때 중요한 신호를 놓칠 수 있습니다.

ModalityMesh는 노트를 스캔하고, 검색과 관련된 콘텐츠 패턴을 감지하며, 다운스트림 시스템이 각 파일, 섹션 또는 블록에 대해 더 나은 스코어링 파이프라인을 선택하는 데 사용할 수 있는 JSON 매니페스트를 생성합니다.

**누구를 위한 건가요.** ModalityMesh는 AI 연구 보조자, 과학적 노트 시스템, 에이전트 메모리 계층, 벡터 검색 워크플로 및 다양한 기술 자료를 통해 더 강력한 검색 및 랭킹이 필요한 RAG 파이프라인을 구축하는 사람들을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/modalitymesh-specialized-retriever-router-for-scientific-not
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "schema_version": "1.0",
  "generator": "modalitymesh",
  "policy": "balanced",
  "source_count": 1,
  "modalities": [
    "table",
    "formula",
    "code",
    "citation",
    "timeline",
    "benchmark"
  ],
  "files": [
    {
      "path": "scientific_notes.md",
      "tags": [
        "table",
        "formula",
        "code",
        "citation",
        "timeline",
        "benchmark"
      ],
      "recommended_scorers": [
        "bm25",
        "dense-semantic",
        "numeric-range",
        "table-structure",
        "symbolic-formula",
        "code-semantic",
        "citation-graph",
        "temporal-date",
        "benchmark-reranker"
      ],
      "evidence": [
        {
          "modality": "timeline",
          "block_type": "line",
          "line_start": 3,
          "line_end": 3,
          "reason": "Explicit calendar date",
          "snippet": "Observed on 2024-03-12 during instrument sweep."
        },
        {
          "modality": "formula",
          "block_type": "line",
          "line_start": 5,
          "line_end": 5,
          "reason": "Inline or display math marker",
          "snippet": "The transition estimate follows $T_c = 92K$ for sample A."
        },
        {
          "modality": "table",
          "block_type": "table",
          "line_start": 7,
          "line_end": 10,
          "reason": "Markdown table with header separator",
          "snippet": "| sample | Tc_K | resistance_ohm | | --- | ---: | ---: | | A | 92 | 0.02 | | B | 88 | 0.05 |"
        },
        {
          "modality": "code",
          "block_type": "code_fence",
          "line_start": 12,
          "line_end": 15,
          "reason": "Fenced code block (python)",
          "snippet": "```python def normalize(x): return x / max(x) ```"
        },
        {
          "modality": "citation",
          "block_type": "line",
          "line_start": 17,
          "line_end": 17,
          "reason": "Citation marker or DOI",
          "snippet":
… (+397 chars truncated)
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
mkdir -p ~/.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not
cp -r /tmp/techllm-skills/skills/modalitymesh-specialized-retriever-router-for-scientific-not/* ~/.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/

# 프로젝트 로컬
mkdir -p .claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not
cp -r /tmp/techllm-skills/skills/modalitymesh-specialized-retriever-router-for-scientific-not/* .claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/modalitymesh-specialized-retriever-router-for-scientific-not
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/modalitymesh-specialized-retriever-router-for-scientific-not/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [-o OUTPUT] [--policy {conservative,balanced,recall-heavy}]
              [--compact] [--selftest]
              [input_dir]

Build a modality-aware retrieval manifest from Markdown scientific notes.

positional arguments:
  input_dir             Markdown folder to scan. If omitted, the built-in
                        self-test sample is emitted.

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Write manifest JSON to this path. Defaults to
                        retrieval_manifest.json when scanning a folder.
  --policy {conservative,balanced,recall-heavy}
                        Routing policy. Defaults to MODALITYMESH_POLICY or
                        balanced.
  --compact             Emit compact single-line JSON instead of pretty-
                        printed JSON.
  --selftest            Run on built-in sample data with no API key and print
                        the manifest.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- Markdown 기반의 지식 베이스를 재귀적으로 스캔하고 결정론적인 매니페스트 데이터를 생성합니다.
- 표, 공식, 코드 블록, 인용문, 타임라인 및 벤치마크와 같은 구조화된 양식을 감지합니다.
- 파일, 섹션 또는 블록 수준에서 양식 태그 및 증거 메타데이터를 할당합니다.
- 어휘, 의미론적, 기호적, 수치적 및 시간적 전략을 포함한 각 양식에 적합한 스코어링 파이프라인을 추천합니다.
- 시스템이 보수적, 균형 잡힌 또는 검색 중심의 검색 동작을 선택할 수 있도록 라우팅 정책을 지원합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 매니페스트에 예상보다 적은 양식 태그가 포함되어 있습니다. | 노트가 일관성 없는 Markdown 서식이나 너무 모호하여 확신 있게 분류할 수 없는 패턴을 사용할 수 있습니다. | 표준 Markdown 표, 코드 블록, 명확한 인용 표시 및 일관된 날짜 또는 벤치마크 표기법을 사용하여 구조화된 콘텐츠를 더 명시적으로 만드세요. |
| 다운스트림 검색이 여전히 일반적인 산문 결과를 먼저 반환합니다. | 사용 중인 검색 또는 RAG 시스템이 매니페스트의 라우팅 권장 사항을 무시할 수 있습니다. | 매니페스트 태그 및 스코어링 권장 사항이 인덱싱 또는 쿼리 라우팅 중에 읽히고, 부수적인 아티팩트로만 생성되는 것이 아닌지 확인하세요. |
| 블록에 잘못된 양식 태그가 지정되었습니다. | 일부 과학적 노트 패턴이 겹치기 때문에 코드와 유사한 공식, 벤치마크 표 또는 인용문이 많은 산문과 같은 경우가 있습니다. | 라우팅 정책 설정 및 로컬 규칙을 사용하여 검색에 가장 중요한 양식으로 분류를 편향시키세요. |

## 자주 묻는 질문

**ModalityMesh가 벡터 데이터베이스 또는 임베딩 모델을 대체하나요?**

아니요. 이는 해당 시스템의 앞이나 옆에 위치하도록 설계되었습니다. 인덱싱 작업, 에이전트, 검색 서비스 또는 벡터 파이프라인이 적용할 검색 전략을 결정하는 데 도움이 되는 라우팅 메타데이터를 생성합니다.

**모든 노트를 하나의 강력한 모델로 임베딩하지 않는 이유는 무엇인가요?**

단일 임베딩 모델은 산문에 대해 잘 작동할 수 있지만, 과학적 노트는 종종 다른 처리가 필요한 구조화된 신호를 포함합니다. 수치적 벤치마크, 공식, 코드 및 타임라인은 결과를 정확하게 순위화하기 위해 특수한 스코어러가 필요할 수 있습니다.

**매니페스트에 무엇이 포함되나요?**

매니페스트에는 감지된 파일, 섹션 또는 블록에 대한 양식 태그, 증거 메타데이터 및 권장 스코어링 파이프라인이 포함됩니다. 이는 다운스트림 검색 시스템이 쉽게 사용할 수 있도록 설계되었습니다.

**이것을 과학적 노트 외에 사용할 수 있나요?**

네, 지식 베이스에 구조화된 Markdown 콘텐츠가 포함되어 있다면 가능합니다. 검색 품질이 표, 코드, 날짜, 인용문 또는 측정된 결과를 인식하는 데 달려 있을 때 특히 유용합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/` 또는 `.claude/skills/modalitymesh-specialized-retriever-router-for-scientific-not/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
