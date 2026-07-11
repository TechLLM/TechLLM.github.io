# TraceShepherd — Execution Evidence Grader for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> LLM 에의 작업을 검증하여 등급을 매깁니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

TraceShepherd는 LLM 에 실행 결과를 최종 채팅 응답 이상의 것으로 평가하는 로컬 우선 그레이더입니다. 이는 에이전트가 수행한 관찰 가능한 작업을 검사하며, 여기에는 검색된 증거, 파일 변경 사항, 생성된 아티팩트, 링크 업데이트 및 최종 작업 공간 상태가 포함됩니다.

이는 일반적인 평가 격차를 해결합니다: 에이전트는 검색, 편집, 생성 또는 검증 작업을 수행했다고 주장할 수 있지만, 일반적인 응답 점수 매기기는 이러한 부작용이 발생했음을 증명할 수 없습니다. TraceShepherd는 추적 이벤트, 파일 시스템 상태, 매니페스트 및 규칙 기반 요구 사항을 비교하여 결정론적인 통과/실패 보고서를 생성합니다.

로컬 파일, 결정론적 해싱, JSONL 추적 및 YAML 규칙을 사용하기 때문에 TraceShepherd는 외부 서비스에 의존하지 않고 개인 작업 흐름, 반복 가능한 벤치마크, CI 검사 및 회귀 테스트에 적합합니다.

**누구를 위한 건가요.** TraceShepherd는 코딩 에이전트, 연구 조수, 지식 기반 자동화, 워크플로우 에이전트 및 벤치마크 실행을 평가하는 팀과 개인을 위한 것입니다. 여기서 정확성은 세련된 산문이 아닌 감사 가능한 부작용에 따라 달라집니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/traceshepherd-execution-evidence-grader-for-llm-agents
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "errors": [],
  "evidence": {
    "missing_events": [],
    "required_events": [
      {
        "matched": true,
        "matched_event_index": 0,
        "rule": {
          "pattern": "project plan",
          "type": "search"
        }
      },
      {
        "matched": true,
        "matched_event_index": 1,
        "rule": {
          "path": "sources/project-plan.md",
          "type": "read"
        }
      },
      {
        "matched": true,
        "matched_event_index": 2,
        "rule": {
          "path": "docs/agent-report.md",
          "type": "write"
        }
      }
    ]
  },
  "files": [
    {
      "checks": [
        {
          "expected": true,
          "name": "exists",
          "pass": true
        },
        {
          "expected": 40,
          "name": "min_size",
          "pass": true
        },
        {
          "expected": "TraceShepherd demo report",
          "name": "contains",
          "pass": true
        },
        {
          "expected": "Evidence: project plan was read.",
          "name": "contains",
          "pass": true
        },
        {
          "expected": "Result: docs updated\\.",
          "name": "regex",
          "pass": true
        }
      ],
      "exists": true,
      "pass": true,
      "path": "docs/agent-report.md",
      "sha256": "52885658e8b360e25bcdb8f9d14195cc03469363ac7bdbc302630305dc9fabf0",
      "size_bytes": 82
    }
  ],
  "policy": {
    "changed_paths": [
      "docs/agent-report.md"
    ],
    "forbidden_modified_files": [],
    "unexpected_modified_files": []
  },
  "status": "pass",
  "summary": {
    "checks": 10,
    "failed": 0,
    "passed": 10
  },
  "tool": "traceshepherd",
  "version": "0.1.0"
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
mkdir -p ~/.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents
cp -r /tmp/techllm-skills/skills/traceshepherd-execution-evidence-grader-for-llm-agents/* ~/.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/

# 프로젝트 로컬
mkdir -p .claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents
cp -r /tmp/techllm-skills/skills/traceshepherd-execution-evidence-grader-for-llm-agents/* .claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/traceshepherd-execution-evidence-grader-for-llm-agents
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/traceshepherd-execution-evidence-grader-for-llm-agents/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--trace TRACE] [--manifest MANIFEST]
              [--workspace WORKSPACE] [--output OUTPUT] [--selftest]
              [--compact] [--version]

Grade LLM agent execution evidence from local trace JSONL and workspace files.

options:
  -h, --help            show this help message and exit
  --trace TRACE         Path to trace JSONL file.
  --manifest MANIFEST   Path to manifest YAML or JSON file.
  --workspace WORKSPACE
                        Workspace directory to inspect. Defaults to current
                        directory.
  --output OUTPUT       Optional path to write the JSON report.
  --selftest            Run a built-in deterministic sample with no API key or
                        external service.
  --compact             Emit compact one-line JSON.
  --version             show program's version number and exit
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 추적 JSONL 이벤트를 읽어 에이전트가 실제로 검색, 열기, 편집, 작성 또는 호출한 내용을 이해합니다.
- 최종 작업 공간을 선언된 매니페스트와 비교하여 예상된 아티팩트, 해시, 크기 및 콘텐츠 패턴을 확인합니다.
- 필요한 증거, 허용된 변경 사항, 금지된 경로, 정규식 어설션 및 감사 정책을 정의하는 YAML 규칙 팩을 적용합니다.
- 누락된 증거, 예상치 못한 파일, 금지된 수정 사항 및 예상 상태와 일치하지 않는 아티팩트를 표시합니다.
- CI 시스템, 대시보드 및 벤치마크 집계기에 의해 소비될 수 있는 결정론적인 JSON 보고서를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 보고서에 필요한 증거가 누락되었다고 나옵니다. | 에이전트가 보이는 작업을 완료했지만 규칙 팩에서 요구하는 추적 이벤트를 생성하지 않았을 수 있습니다. | 규칙 팩과 추적 로그를 함께 검토하세요. 규칙을 의도한 워크플로우에 맞게 조정하거나 에이전트 하네스를 업데이트하여 필요한 검색, 읽기, 편집 또는 쓰기가 기록되도록 합니다. |
| 예상된 아티팩트가 검증에 실패했습니다. | 파일이 누락되었거나, 너무 작거나, 예기치 않게 변경되었거나, 선언된 해시 또는 콘텐츠 패턴과 다를 수 있습니다. | 생성된 아티팩트와 매니페스트 기대치를 검사하세요. 아티팩트가 잘못된 경우 다시 생성하거나, 새로운 상태가 의도적으로 올바른 경우에만 매니페스트를 업데이트하세요. |
| 유효한 작업이 예기치 않은 파일 변경으로 보고되었습니다. | 허용된 경로 정책이 에이전트가 합법적으로 수행한 작업보다 좁을 수 있습니다. | 허용된 경로 또는 아티팩트 매니페스트를 확장하여 의도된 출력을 포함시키되, 관련 없는 작업 공간 영역은 금지된 상태로 유지하세요. |

## 자주 묻는 질문

**TraceShepherd는 최종 자연어 답변의 품질을 판단합니까?**

그렇지 않습니다. TraceShepherd는 주로 실행 증거와 최종 상태에 중점을 둡니다. 에이전트가 필요한 관찰 가능한 작업을 수행하고 예상된 아티팩트를 남겼는지 여부를 검증합니다.

**개인 정보 보호가 중요한 환경에서 실행할 수 있습니까?**

네. TraceShepherd는 파일, 해시, 추적 로그 및 규칙을 사용하여 로컬에서 작동하도록 설계되었으므로 평가를 외부 서비스로 전송할 필요가 없습니다.

**어떤 종류의 에이전트를 평가할 수 있습니까?**

검색, 파일 읽기, 코드 편집, 지식 기반 페이지 작성, 링크 업데이트 또는 구조화된 아티팩트 생성과 같은 감사 가능한 작업을 수행하는 에이전트를 평가할 수 있습니다.

**왜 규칙 팩을 사용합니까, 스냅샷만 사용하지 않고?**

스냅샷은 최종 상태를 보여주지만, 규칙 팩은 프로세스 증거를 요구할 수 있습니다. 예를 들어, 필요한 소스를 읽었는지 또는 승인된 영역만 수정했는지 확인할 수 있습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/` 또는 `.claude/skills/traceshepherd-execution-evidence-grader-for-llm-agents/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
