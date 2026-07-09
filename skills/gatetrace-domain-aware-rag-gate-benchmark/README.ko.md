# GateTrace — Domain-Aware RAG Gate Benchmark

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> RAG 관련성 게이트가 실패하는 위치를 노출합니다, 평균 점수만으로 평가하는 것이 아니라.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

GateTrace는 도메인 인식 세부 정보를 사용하여 RAG 관련성 게이트, 검색 에이전트 및 검색 계획 시스템을 평가하기 위한 제안된 벤치마킹 CLI입니다. 평가를 하나의 집계된 재현율 점수로 축소하는 대신, 문서 유형, 질문 패턴, 출처 범주, 전문 용어 및 도메인 태그에 따른 성능 변화를 보여줍니다.

이는 검색 시스템이 평균적으로는 강해 보이지만 가장 중요한 경우, 즉 드문 용어, 익숙하지 않은 도메인, 롱테일 의도, 희소한 증거 또는 지배적인 훈련 또는 테스트 예제와 유사하지 않은 문서에서 실패할 수 있기 때문에 중요합니다. GateTrace는 이러한 숨겨진 실패 모드를 프로덕션에 도달하기 전에 눈에 띄게 하도록 설계되었습니다.

이 도구는 간단한 구조화된 평가 데이터를 받아들이고 사람이 읽을 수 있는 보고서와 기계가 읽을 수 있는 보고서를 모두 생성하여 풀 리퀘스트 검토, 모델 카드, CI 게이트 및 평가 대시보드에 적합합니다.

**누구를 위한 건가요.** GateTrace는 RAG 시스템, 관련성 게이트, 검색 에이전트 및 검색 계획 워크플로를 구축, 테스트 또는 유지 관리하는 팀을 위한 것으로, 검색이 작동하는지 여부뿐만 아니라 어디에서 실패하고 왜 실패하는지를 이해해야 하는 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/gatetrace-domain-aware-rag-gate-benchmark
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "document_slices": {
    "doc_type": {
      "blog": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 0.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_document_count": 1
      },
      "chat": {
        "false_block_rate": 0.0,
        "false_pass_rate": 1.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_document_count": 1
      },
      "faq": {
        "false_block_rate": 0.0,
        "false_pass_rate": 1.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_document_count": 1
      },
      "guideline": {
        "false_block_rate": 1.0,
        "false_pass_rate": 0.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 0.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 1,
        "retrieved_document_count": 1
      },
      "incident_report": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 1.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 1.0,
        "gate_recall": 1.0,
        "relevant_retrieved_count": 1,
        "retrieved_document_count": 1
      },
      "manual": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 1.0,
        "gate_pass_rate": 1.0,
        "gate_precision": 1.0,
        "gate_recall": 1.0,
        "relevant_retrieved_count": 1,
        "retrieved_document_count": 1
      },
      "memo": {
        "false_block_rate": 0.0,
        "false_pass_rate": 0.0,
        "gate_f1": 0.0,
        "gate_pass_rate": 0.0,
        "gate_precision": 0.0,
        "gate_recall": 0.0,
        "relevant_retrieved_count": 0,
        "retrieved_d
… (+10547 chars truncated)
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
mkdir -p ~/.claude/skills/gatetrace-domain-aware-rag-gate-benchmark
cp -r /tmp/techllm-skills/skills/gatetrace-domain-aware-rag-gate-benchmark/* ~/.claude/skills/gatetrace-domain-aware-rag-gate-benchmark/

# 프로젝트 로컬
mkdir -p .claude/skills/gatetrace-domain-aware-rag-gate-benchmark
cp -r /tmp/techllm-skills/skills/gatetrace-domain-aware-rag-gate-benchmark/* .claude/skills/gatetrace-domain-aware-rag-gate-benchmark/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/gatetrace-domain-aware-rag-gate-benchmark
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/gatetrace-domain-aware-rag-gate-benchmark/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--format {json,markdown,both}]
              [--json-out JSON_OUT] [--markdown-out MARKDOWN_OUT]
              [--ood-tags OOD_TAGS] [--fail-under-recall FAIL_UNDER_RECALL]
              [--selftest]

Evaluate RAG retrieval and relevance-gate behavior with domain-aware slices.

options:
  -h, --help            show this help message and exit
  --input INPUT         JSONL input file. If omitted, built-in sample data is
                        used.
  --format {json,markdown,both}
                        Report format for stdout or output files.
  --json-out JSON_OUT   Write JSON report to this file.
  --markdown-out MARKDOWN_OUT
                        Write Markdown report to this file.
  --ood-tags OOD_TAGS   Comma-separated tags treated as OOD-like. Defaults to
                        GATETRACE_OOD_TAGS or built-ins.
  --fail-under-recall FAIL_UNDER_RECALL
                        Exit with code 2 if overall retrieval_recall is below
                        this threshold.
  --selftest            Run on built-in sample data and validate the resulting
                        report shape.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 도메인 태그, 문서 범주, 질문 유형, 출처 패밀리, 증거 밀도 및 사용자 정의 메타데이터에 따라 검색 및 게이트 메트릭을 슬라이스합니다.
- 검색 및 관련성 게이트 결정에 대해 재현율, 정밀도, F1 및 통과율 동작을 별도로 보고합니다.
- 관련 없는 컨텍스트가 통과되는 거짓 통과와 유용한 증거가 완성되기 전에 차단되는 거짓 차단을 강조합니다.
- 필요한 지원 문서가 쿼리에 대해 검색되지 않은 누락된 증거 사례를 식별합니다.
- 드문 용어, 익숙하지 않은 도메인 및 롱테일 의도와 같은 구성 가능한 태그를 사용하여 OOD와 같은 쿼리 그룹에 플래그를 지정합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 벤치마크가 전반적으로는 좋지만 도메인 슬라이스에서 성능이 약합니다. | 집계 메트릭은 특정 태그, 문서 유형 또는 쿼리 패턴에 집중된 실패를 숨길 수 있습니다. | 가장 약한 슬라이스를 먼저 검토하고 검색기나 게이트를 변경하기 전에 거짓 차단, 거짓 통과 및 누락된 증거 패턴을 비교하세요. |
| 일부 쿼리가 예기치 않게 누락된 증거 보고서에 나타납니다. | 해당 쿼리에 필요한 지원 증거가 검색되지 않았거나 입력 데이터에서 일관되게 레이블이 지정되지 않았습니다. | 평가 레이블이 필요한 증거를 명확하게 식별하는지 확인하고 도메인 메타데이터가 관련 레코드에 첨부되었는지 확인하세요. |
| OOD와 같은 보고서가 너무 시끄럽거나 너무 광범위합니다. | 드문 용어, 익숙하지 않은 도메인 또는 롱테일 의도를 식별하는 데 사용되는 태그가 데이터 세트에 너무 일반적일 수 있습니다. | 태그 정의를 구체화하여 의미 있는 위험 그룹을 포착하도록 합니다. |

## 자주 묻는 질문

**GateTrace가 표준 검색 메트릭을 대체합니까?**

아니오. 표준 메트릭을 보완하여 이러한 메트릭이 어디에서 나오고 어떤 도메인, 문서 유형 또는 증거 패턴이 성공 또는 실패를 주도하는지 보여줍니다.

**왜 관련성 게이트를 검색과 별도로 평가합니까?**

검색기가 유용한 증거를 찾을 수 있지만 게이트가 이를 차단하거나, 게이트가 관련 없는 컨텍스트를 통과시켜 나중에 생성기를 혼란스럽게 할 수 있습니다. 이러한 결정을 별도로 측정하면 실패 모드를 더 쉽게 진단할 수 있습니다.

**이것을 CI에서 사용할 수 있습니까?**

예. GateTrace는 자동화된 검사를 위한 기계가 읽을 수 있는 JSON과 검토자를 위한 Markdown 보고서를 생성하도록 설계되었습니다.

**어떤 종류의 시스템을 평가할 수 있습니까?**

쿼리, 검색된 문서, 레이블 및 메타데이터가 구조화된 평가 레코드로 표현될 수 있는 RAG 검색기, 관련성 게이트, 검색 에이전트 및 검색 계획 시스템용으로 설계되었습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/gatetrace-domain-aware-rag-gate-benchmark/` 또는 `.claude/skills/gatetrace-domain-aware-rag-gate-benchmark/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
