# TraceTrellis — Evidence-First RAG Gate Evaluation

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> RAG 게이트를 평가할 때는 답변만이 아니라 증거를 확인하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

TraceTrellis는 RAG 시스템이 파이프라인을 통해 올바른 증거를 전달하는지 테스트하기 위한 오픈 소스 평가 도구입니다. 최종 응답만을 판단하는 대신, 그 응답 뒤에 숨겨진 실행 경로를 검사합니다: 검색 흔적, 선택된 문서, 작업 로그, 변경된 아티팩트 및 서비스 수준의 결과입니다.

이는 많은 RAG 평가가 시스템이 잘못된 소스를 사용했거나 필수 증거를 생략했거나 관련성 없는 문맥이 관련성 게이트를 통과했음에도 불구하고 그럴듯한 텍스트에 보상을 주기 때문에 중요합니다. TraceTrellis는 목표를 답변 다듬기에서 관찰 가능한 증거 처리로 이동시켜, 실패를 더 쉽게 진단하고 재현할 수 있게 합니다.

이 도구는 오프라인 CLI 워크플로우를 중심으로 설계되었으며, 구조화된 검색, 작업 및 데이터 정확도 점수와 실패 설명을 생성합니다. 선택적으로 LLM 판정 결과를 추가 신호로 추가할 수 있지만, 결정론적 증거 검사는 핵심 평가 계층으로 남아 있습니다.

**누구를 위한 건가요.** TraceTrellis는 CI, 오프라인 환경 및 개인 정보 보호 설정에서 작동하는 반복 가능한 평가가 필요한 RAG 애플리케이션, 에이전트 검색 시스템, 관련성 게이트, 증거 라우터 및 벤치마크 제품군을 구축하는 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/tracetrellis-evidence-first-rag-gate-evaluation
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "tool": "rag-evidence-grader",
  "version": "0.1.0",
  "summary": {
    "cases": 1,
    "passed": 1,
    "failed": 0,
    "pass_rate": 1.0,
    "average_scores": {
      "retrieval": 1.0,
      "action": 1.0,
      "data_accuracy": 1.0,
      "overall": 1.0
    }
  },
  "cases": [
    {
      "run_id": "refund-window",
      "passed": true,
      "scores": {
        "retrieval": 1.0,
        "action": 1.0,
        "data_accuracy": 1.0,
        "overall": 1.0
      },
      "documents": {
        "selected": [
          "policy/refunds-2026",
          "faq/refunds"
        ],
        "required_found": [
          "policy/refunds-2026"
        ],
        "required_missing": [],
        "optional_found": [
          "faq/refunds"
        ],
        "forbidden_found": []
      },
      "actions": {
        "observed": [
          {
            "type": "retrieve",
            "target": "policy/refunds-2026"
          },
          {
            "type": "cite",
            "target": "policy/refunds-2026"
          }
        ],
        "required_found": [
          {
            "type": "retrieve",
            "target": "policy/refunds-2026"
          },
          {
            "type": "cite",
            "target": "policy/refunds-2026"
          }
        ],
        "required_missing": []
      },
      "facts": {
        "matched": {
          "refund_window_days": 30,
          "region": "US"
        },
        "mismatched": {},
        "missing": []
      },
      "answer": null,
      "llm_judge": null,
      "failures": []
    }
  ]
}
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
mkdir -p ~/.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/tracetrellis-evidence-first-rag-gate-evaluation/* ~/.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/

# 프로젝트 로컬
mkdir -p .claude/skills/tracetrellis-evidence-first-rag-gate-evaluation
cp -r /tmp/techllm-skills/skills/tracetrellis-evidence-first-rag-gate-evaluation/* .claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/tracetrellis-evidence-first-rag-gate-evaluation
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/tracetrellis-evidence-first-rag-gate-evaluation/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: rag-evidence-grader [-h] [--traces TRACES] [--manifest MANIFEST]
                           [--answers ANSWERS]
                           [--llm-judge-json LLM_JUDGE_JSON]
                           [--threshold THRESHOLD] [--format {json,csv}]
                           [--output OUTPUT] [--selftest] [--version]

Offline evidence-first grader for RAG retrieval gates and traces.

options:
  -h, --help            show this help message and exit
  --traces TRACES       Path to JSONL trace records.
  --manifest MANIFEST   Path to expected evidence manifest JSON.
  --answers ANSWERS     Optional JSON or JSONL final-answer records.
  --llm-judge-json LLM_JUDGE_JSON
                        Optional JSON or JSONL judge records; can also use
                        TRACE_TRELLIS_LLM_JUDGE_PATH.
  --threshold THRESHOLD
                        Overall pass threshold from 0 to 1. Defaults to
                        RAG_EVIDENCE_GRADER_THRESHOLD or 0.8.
  --format {json,csv}   Output format. Defaults to json.
  --output OUTPUT       Optional output file path.
  --selftest            Run the built-in offline sample with no API key.
  --version             show program's version number and exit
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- RAG 또는 에이전트 검색 실행에 의해 생성된 표준 JSONL 흔적을 읽습니다.
- 검색된 증거와 선택된 증거를 예상 증거 매니페스트와 비교합니다.
- 검색 동작, 다운스트림 작업 및 데이터 정확도를 별도의 채널로 점수화합니다.
- 필수, 선택 및 금지된 증거 처리 실패를 설명과 함께 플래그로 표시합니다.
- LLM 판정 출력을 결정론적 검사를 대체하지 않고 병합할 수 있습니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 최종 답변이 올바르게 보이지만 실행 점수가 낮습니다. | 답변은 그럴듯할 수 있지만, 흔적은 필수 증거가 누락되었거나 지원되지 않는 문맥이 있거나 잘못된 문서가 선택되었음을 보여줍니다. | 실패 설명을 검토하고 검색 게이트, 증거 매니페스트 또는 흔적 계측을 업데이트하여 필수 증거가 관찰 가능하도록 합니다. |
| 도메인이나 코퍼스에 따라 점수가 다릅니다. | 관련성 게이트가 특정 문서 구조, 어휘 또는 증거 밀도 패턴에 맞춰 조정되었을 수 있습니다. | 도메인 균형 평가 세트를 사용하고 코퍼스별로 점수 채널을 비교하여 검색 정책 변경이 필요한 부분을 식별합니다. |
| 작업 또는 데이터 정확도 점수가 불완전합니다. | 흔적에는 검색 이벤트가 포함될 수 있지만 작업 로그, 아티팩트 변경 또는 구조화된 결과 데이터가 생략될 수 있습니다. | 계측을 확장하여 다운스트림 작업 및 생성된 아티팩트가 흔적에 캡처되도록 합니다. |

## 자주 묻는 질문

**TraceTrellis에 LLM 판정이 필요한가요?**

아니오. 핵심 점수는 결정론적이며 완전히 오프라인으로 실행할 수 있습니다. LLM 판정 출력은 선택 사항이며 추가 신호로 취급됩니다.

**이것이 최종 답변 평가와 다른 점은 무엇인가요?**

최종 답변 평가는 응답이 옳게 들리는지 묻습니다. TraceTrellis는 시스템이 올바른 증거를 선택하고, 라우팅하고, 사용하여 답변을 생성했는지 묻습니다.

**CI에서 사용할 수 있나요?**

예. 설계는 JSONL 입력, 구조화된 JSON 또는 CSV 출력, 결정론적 점수 및 회귀 테스트 워크플로우에 적합한 실패 설명을 선호합니다.

**어떤 종류의 RAG 시스템을 위한 것인가요?**

관련성 게이트, Gate2 스타일 필터, 도메인 간 검색 정책, 에이전트 검색 파이프라인 및 증거 라우팅 계층에 특히 유용합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/` 또는 `.claude/skills/tracetrellis-evidence-first-rag-gate-evaluation/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
