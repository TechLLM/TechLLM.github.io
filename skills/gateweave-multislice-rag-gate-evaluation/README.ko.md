# GateWeave — Multislice RAG Gate Evaluation

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 평균적인 지표가 숨기는 RAG 게이트 실패를 찾아내세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

GateWeave는 RAG 관련성 게이트가 현실적인 검색 조건에서 얼마나 일반화되는지 평가하기 위한 오픈 소스 벤치마크 CLI로 제안된 도구입니다. 이 도구는 팀들이 평균 적중률을 넘어서, 스코어러, 라우터 임계값 또는 재순위 지정기가 전반적으로는 잘 작동하지만 특정 부분에서 실패하는 부분을 보여줌으로써 도움을 줍니다.

이 프로젝트는 도메인 일반화 아이디어를 RAG 평가에 적용합니다. 모달리티 조합을 테스트하는 대신, GateWeave는 문서 필드, 누락된 증거, 손상된 메타데이터, 도메인 변화 및 문서 유형 그룹을 테스트합니다.

출력은 간결한 평가 매트릭스로, 프로덕션에 도달하기 전에 숨겨진 관련성 실패를 더 쉽게 검토, 비교 및 논의할 수 있도록 합니다.

**누구를 위한 건가요.** GateWeave는 프로덕션 RAG 시스템을 구축하는 팀을 위한 도구로, 특히 실제 검색 트래픽과 유사한 조건에서 관련성 게이트, 재순위 지정기 또는 라우팅 스코어러를 비교해야 하는 엔지니어, ML 실무자 및 기술 책임자에게 유용합니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/gateweave-multislice-rag-gate-evaluation
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "protocol": "gateweave-v0",
  "threshold": 0.5,
  "slice_columns": [
    "domain",
    "doc_type",
    "evidence_field"
  ],
  "missing_field_columns": [
    "evidence_field"
  ],
  "labels": {
    "rows": 8,
    "source": "builtin"
  },
  "scorers": [
    {
      "name": "baseline",
      "rows_evaluated": 8,
      "missing_predictions": 0,
      "extra_predictions": 0,
      "aggregate": {
        "count": 8,
        "tp": 2,
        "fp": 1,
        "fn": 2,
        "tn": 3,
        "precision": 0.666667,
        "recall": 0.5,
        "f1": 0.571429,
        "accuracy": 0.625
      },
      "slices": {
        "domain": [
          {
            "value": "legal",
            "metrics": {
              "count": 3,
              "tp": 1,
              "fp": 0,
              "fn": 0,
              "tn": 2,
              "precision": 1.0,
              "recall": 1.0,
              "f1": 1.0,
              "accuracy": 1.0
            }
          },
          {
            "value": "sales",
            "metrics": {
              "count": 2,
              "tp": 0,
              "fp": 0,
              "fn": 1,
              "tn": 1,
              "precision": 0.0,
              "recall": 0.0,
              "f1": 0.0,
              "accuracy": 0.5
            }
          },
          {
            "value": "support",
            "metrics": {
              "count": 3,
              "tp": 1,
              "fp": 1,
              "fn": 1,
              "tn": 0,
              "precision": 0.5,
              "recall": 0.5,
              "f1": 0.5,
              "accuracy": 0.333333
            }
          }
        ],
        "doc_type": [
          {
            "value": "case_study",
            "metrics": {
              "count": 2,
              "tp": 0,
              "fp": 0,
              "fn": 1,
              "tn": 1,
              "precision": 0.0,
              "recall": 0.0,
              "f1": 0.0,
              "accuracy": 0.5
            }
          },
      
… (+7694 chars truncated)
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
mkdir -p ~/.claude/skills/gateweave-multislice-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/gateweave-multislice-rag-gate-evaluation/* ~/.claude/skills/gateweave-multislice-rag-gate-evaluation/

# 프로젝트 로컬
mkdir -p .claude/skills/gateweave-multislice-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/gateweave-multislice-rag-gate-evaluation/* .claude/skills/gateweave-multislice-rag-gate-evaluation/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/gateweave-multislice-rag-gate-evaluation
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/gateweave-multislice-rag-gate-evaluation/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--labels LABELS] [--scorers SCORERS [SCORERS ...]]
              [--threshold THRESHOLD] [--slice-columns SLICE_COLUMNS]
              [--missing-field-columns MISSING_FIELD_COLUMNS]
              [--format {json,markdown}] [--output-json OUTPUT_JSON]
              [--output-md OUTPUT_MD]
              [--write-example-inputs WRITE_EXAMPLE_INPUTS] [--selftest]

Evaluate RAG relevance gates across aggregate, slice, and missing-field stress
metrics.

options:
  -h, --help            show this help message and exit
  --labels LABELS       Labeled CSV with qid, doc_id, label, and optional
                        slice columns.
  --scorers SCORERS [SCORERS ...]
                        One or more scorer CSV files with qid, doc_id, and
                        score or decision.
  --threshold THRESHOLD
                        Score threshold for positive predictions. Default:
                        0.5.
  --slice-columns SLICE_COLUMNS
                        Comma-separated slice columns. Default:
                        domain,doc_type,evidence_field.
  --missing-field-columns MISSING_FIELD_COLUMNS
                        Comma-separated columns for missing-field stress
                        tests.
  --format {json,markdown}
                        Format printed to stdout. Default: json.
  --output-json OUTPUT_JSON
                        Optional path for the JSON report.
  --output-md OUTPUT_MD
                        Optional path for the Markdown report.
  --write-example-inputs WRITE_EXAMPLE_INPUTS
                        Write sample CSV inputs to the given directory and
                        exit.
  --selftest            Run the built-in sample with no external files.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 레이블이 지정된 질문-질문-답변 데이터와 하나 이상의 스코어러 출력 테이블을 함께 입력받습니다.
- 예제를 도메인, 문서 유형, 증거 필드 및 사용자 정의 메타데이터 범주와 같은 통제된 부분으로 그룹화합니다.
- 각 스코어러에 대해 정밀도, 재현율, 누락된 필드 스트레스 동작 및 최악의 부분 성능을 측정합니다.
- 동일한 평가 프로토콜 하에 여러 게이트 또는 스코어러를 나란히 비교합니다.
- 실험 검토, CI 검사 및 풀 리퀘스트 논의를 위한 구조화된 읽기 쉬운 보고서를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 점수가 전반적으로는 강하지만 보고서의 한 부분에서 약합니다. | 게이트가 전체 데이터 세트에서는 일반적이지만 특정 부분에서는 신뢰할 수 없는 패턴에 과적합되었을 가능성이 높습니다. | 영향을 받는 부분을 검사하고, 그 뒤에 있는 예를 검토하며, 해당 검색 조건을 다루도록 스코어러, 임계값 또는 학습 데이터를 조정합니다. |
| 일부 부분이 비어있거나 예상보다 작게 나타납니다. | 입력 레이블 또는 메타데이터에 해당 부분을 형성하는 데 필요한 값이 누락되었을 수 있습니다. | 관련 열이 일관되게 채워져 있고, 빈 값이 의도적인 누락된 증거를 나타내는지, 아니면 주석 드리프트가 아닌지 확인합니다. |
| 두 스코어러 보고서를 비교하기 어렵습니다. | 스코어러 출력이 동일한 레이블이 지정된 예를 참조하지 않거나 일관되지 않은 식별자를 사용할 수 있습니다. | 각 스코어러 출력이 동일한 평가 세트에 맞는지 확인하고, 일치하는 예를 매칭하기 위해 안정적인 식별자를 사용합니다. |

## 자주 묻는 질문

**GateWeave가 종단 간 RAG 평가를 대체할 수 있나요?**

아니오. 이는 관련성 게이트, 재순위 지정기 및 라우팅 스코어러에 중점을 둡니다. 이는 답변 품질 및 사용자 지향 평가와 보완하여 검색 결정 계층이 얼마나 강력한지를 분리하여 평가합니다.

**왜 부분 기반 평가를 사용하나요, 하나의 집계 메트릭이 아닌?**

집계 메트릭은 시스템이 일반적인 경우에서는 잘 작동하지만 드문 도메인, 문서 유형, 메타데이터 패턴 또는 누락된 증거 상황에서는 성능이 나쁜 경우 심각한 실패를 숨길 수 있습니다.

**GateWeave가 여러 스코어러를 비교할 수 있나요?**

네. 이는 여러 관련성 게이트, 재순위 지정기 또는 라우터 스코어러를 동일한 레이블이 지정된 프로토콜 하에 비교하도록 설계되어 팀이 장단점을 명확하게 볼 수 있도록 합니다.

**GateWeave는 어떤 종류의 데이터를 기대하나요?**

이는 레이블이 지정된 예제와 스코어러 출력을 중심으로 한 CSV 우선 워크플로우로 설계되어 기존 주석 파이프라인, 오프라인 평가 내보내기 및 실험 로그와 호환됩니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/gateweave-multislice-rag-gate-evaluation/` 또는 `.claude/skills/gateweave-multislice-rag-gate-evaluation/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
