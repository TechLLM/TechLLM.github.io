# DiffSentinel — State-Change Grading for AI Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 에이전트의 작업을 파일 및 데이터의 실제 변경 사항을 확인하여 평가합니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

DiffSentinel은 워크스페이스에서 실제 작업을 수행하는 AI 에이전트 및 자동화 워크플로우를 평가하기 위한 제안된 평가 도구 키트입니다. 최종 작성된 응답만 판단하는 대신 실행 후 남겨진 관찰 가능한 변경 사항을 검사합니다.

이는 그럴듯한 답변이 완료된 작업과 같지 않기 때문에 중요합니다. 에이전트는 계획을 설명하고, 성공을 주장하거나, 편집 내용을 요약할 수 있지만, 신뢰할 수 있는 시스템은 증거가 필요합니다: 생성된 파일, 업데이트된 기록, 추가된 인용문, 제거된 아티팩트 및 작성된 작업 로그.

DiffSentinel은 실행 전후의 워크스페이스를 비교하고, 기대 규칙을 적용하고, 결정론적인 평가 보고서를 생성합니다. 결과는 CI, 벤치마크 제품군, 회귀 테스트 및 반복적인 에이전트 개발에 사용될 수 있습니다.

**누구를 위한 건가요.** DiffSentinel은 LLM 에이전트, RAG 워크플로우, 코딩 도우미, 문서 편집 에이전트, 위키 유지 관리 에이전트, 연구 조수 및 성공이 단일 자연어 답변이 아닌 지속적인 상태 변화에 달려 있는 자동화 시스템을 구축하거나 평가하는 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/diffsentinel-state-change-grading-for-ai-agents
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "pass": true,
  "score": 1.0,
  "earned_points": 13,
  "max_score": 13,
  "summary": {
    "passed": 13,
    "failed": 0,
    "warnings": 0
  },
  "checks": [
    {
      "id": "required_files:report.md",
      "kind": "required_files",
      "target": "report.md",
      "status": "pass",
      "detail": "File exists in after snapshot."
    },
    {
      "id": "created_files:report.md",
      "kind": "created_files",
      "target": "report.md",
      "status": "pass",
      "detail": "File was created.",
      "expected": "absent before and present after",
      "observed": true
    },
    {
      "id": "created_files:logs/task.log",
      "kind": "created_files",
      "target": "logs/task.log",
      "status": "pass",
      "detail": "File was created.",
      "expected": "absent before and present after",
      "observed": true
    },
    {
      "id": "deleted_files:draft.txt",
      "kind": "deleted_files",
      "target": "draft.txt",
      "status": "pass",
      "detail": "File was deleted.",
      "expected": "present before and absent after",
      "observed": true
    },
    {
      "id": "modified_files:data.json",
      "kind": "modified_files",
      "target": "data.json",
      "status": "pass",
      "detail": "File content changed.",
      "expected": true,
      "observed": true
    },
    {
      "id": "forbidden_changes:notes.md",
      "kind": "forbidden_changes",
      "target": "notes.md",
      "status": "pass",
      "detail": "File did not change.",
      "expected": false,
      "observed": false
    },
    {
      "id": "content_contains:report.md contains 'Summary: Work completed.'",
      "kind": "content_contains",
      "target": "report.md contains 'Summary: Work completed.'",
      "status": "pass",
      "detail": "Required string found.",
      "expected": "Summary: Work completed."
    },
    {
      "id": "content_contains:report.md contains '[source:A]'",
      "kind": "content_contains",
      "target": "report.md contai
… (+1781 chars truncated)
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
mkdir -p ~/.claude/skills/diffsentinel-state-change-grading-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-change-grading-for-ai-agents/* ~/.claude/skills/diffsentinel-state-change-grading-for-ai-agents/

# 프로젝트 로컬
mkdir -p .claude/skills/diffsentinel-state-change-grading-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-change-grading-for-ai-agents/* .claude/skills/diffsentinel-state-change-grading-for-ai-agents/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/diffsentinel-state-change-grading-for-ai-agents
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/diffsentinel-state-change-grading-for-ai-agents/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--before BEFORE] [--after AFTER] [--expect EXPECT]
              [--output OUTPUT] [--threshold THRESHOLD] [--selftest]

DiffSentinel grades observable before-and-after workspace state changes.

options:
  -h, --help            show this help message and exit
  --before BEFORE       Directory snapshot before the agent ran
  --after AFTER         Directory snapshot after the agent ran
  --expect EXPECT       Expectation YAML or JSON file. Defaults to
                        DIFFSENTINEL_EXPECTATIONS.
  --output OUTPUT       Optional report output path. Defaults to
                        DIFFSENTINEL_OUTPUT.
  --threshold THRESHOLD
                        Minimum score needed to pass. Defaults to
                        DIFFSENTINEL_SCORE_THRESHOLD or 1.0.
  --selftest            Run built-in sample data with no API key and print the
                        report
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 완료된 에이전트 실행에 대한 전후 워크스페이스 스냅샷을 캡처하거나 수신합니다.
- 필요한 파일, 삭제된 파일, 수정된 파일, 금지된 변경, 인용문, 작업 로그 및 생성된 아티팩트를 정의하는 기대 규칙을 읽습니다.
- 필요한 텍스트, 인용 표시 및 요청된 작업이 완료되었음을 나타내는 기타 증거에 대해 파일 내용을 확인합니다.
- 예상된 필드 추가, 제거 및 값 변경과 같은 구조화된 아티팩트(예: JSON 레코드)를 검증합니다.
- 자동화된 평가 파이프라인에 대해 통과, 실패, 경고 및 점수 세부 정보가 포함된 기계 판독 가능한 평가 보고서를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 에이전트가 작업이 완료되었다고 했음에도 불구하고 평가 보고서가 실패합니다. | DiffSentinel은 에이전트의 최종 메시지가 아닌 관찰 가능한 상태 변화를 평가합니다. 전후 상태에 예상된 파일, 편집, 인용문 또는 구조화된 업데이트가 없었습니다. | 에이전트 워크플로우를 업데이트하여 필요한 아티팩트를 작성하거나, 예상 규칙을 조정하여 의도한 작업 결과와 일치시킵니다. |
| 평가 대상이 아닌 파일이 변경된 것으로 보고됩니다. | 작업 공간 비교에는 예상 규칙에 포함되지 않은 우발적이거나 관련 없는 수정이 포함됩니다. | 평가되는 작업 공간을 좁히고, 예상되는 보조 파일에 대한 명시적인 허용을 추가하거나, 워크플로우가 관련 없는 아티팩트를 작성하지 않도록 합니다. |
| 생성된 JSON 아티팩트에 대한 구조화된 검증이 실패합니다. | 아티팩트가 존재하지만, 필드, 값 또는 제거가 예상된 상태 변경 규칙과 일치하지 않습니다. | 에이전트가 필요한 구조를 일관되게 작성하고, 예상 규칙이 의도한 최종 스키마 및 값을 설명하는지 확인합니다. |

## 자주 묻는 질문

**DiffSentinel은 최종 답변을 평가하는 것과 어떻게 다른가요?**

에이전트 실행의 지속적인 효과를 평가합니다. 최종 답변은 유창하지만 부정확할 수 있습니다. DiffSentinel은 실행 후 예상된 파일, 내용, 인용문, 로그 및 구조화된 업데이트가 실제로 존재하는지 확인합니다.

**이 도구는 어떤 종류의 작업에 가장 적합한가요?**

올바름이 예상된 변경 집합인 워크플로우 벤치마크에 가장 적합합니다. 예를 들어, 문서 편집, 위키 유지 관리, JSON 레코드 업데이트, 연구 아티팩트 생성, 코드 수정 또는 출력된 결과물 생성 등이 있습니다.

**DiffSentinel을 CI에 사용할 수 있나요?**

네. 평가 모델은 결정론적이고 기계 판독 가능한 보고서를 생성하고, 벤치마크 및 회귀 실행에 대해 CI 친화적인 통과 또는 실패 결과를 생성하도록 설계되었습니다.

**DiffSentinel은 산문 품질을 결정하나요?**

그 자체로는 아닙니다. 핵심 목적은 상태 변경 검증입니다. 필요한 텍스트 또는 인용문이 나타나는지 확인할 수 있지만, 질적 작문 평가는 별도로 계층화될 수 있습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/diffsentinel-state-change-grading-for-ai-agents/` 또는 `.claude/skills/diffsentinel-state-change-grading-for-ai-agents/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
