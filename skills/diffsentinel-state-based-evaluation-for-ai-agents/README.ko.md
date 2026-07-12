# DiffSentinel — State-Based Evaluation for AI Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> AI 에 평가할 때는 그들의 주장보다는 변화한 내용을 기준으로 하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

DiffSentinel은 실제 작업 공간 내에서 작동하는 AI 에이전트를 위한 오픈 소스 평가 툴킷으로 제안된 것입니다. 에이전트를 최종 메시지로 판단하는 대신, 에이전트가 만든 관찰 가능한 변화를 검사합니다: 무엇이 생성, 편집, 삭제, 연결, 참조, 접근되었거나 그대로 남아있는지.

이는 에이전트 평가에서 흔히 발생하는 문제를 해결합니다: 세련된 요약은 불완전한 작업, 누락된 인용, 안전하지 않은 접근 또는 잘못된 구조를 숨길 수 있습니다. DiffSentinel은 작업 공간의 차이(diff)와 도구 추적을 진실의 원천으로 취급하여, 평가를 코드 리뷰, 감사 로깅 및 재현 가능한 검증에 더 가깝게 만듭니다.

그 결과는 CI 시스템, 벤치마크 도구, 회귀 테스트, 대시보드 또는 인간 검토자가 사용할 수 있는 구조화된 보고서입니다.

**누구를 위한 건가요.** DiffSentinel은 저장소, 문서 시스템, 지식 기반 및 최종 상태의 품질이 최종 응답의 표현보다 더 중요한 기타 구조화된 작업 공간에서 작동하는 AI 에이전트를 구축, 테스트 또는 감사하는 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/diffsentinel-state-based-evaluation-for-ai-agents
python scripts/run.py --selftest
```

**예상 출력:**

```text
{"evidence": {"changed_paths": ["docs/faq.md", "docs/guide.md"], "policy": {"allow_shell_without_approval": true, "fail_below_score": 80, "forbidden_path_patterns": ["../", "~", ".env", "secrets/", "private/"], "protected_paths": []}}, "findings": [], "graph": {"added_links": [{"source": "docs/faq.md", "target": "docs/guide.md"}], "orphaned_nodes": [], "removed_links": [], "unresolved_references": []}, "schema_version": "diffsentinel-report-v1", "state_diff": {"created": ["docs/faq.md"], "deleted": [], "modified": ["docs/guide.md"], "renamed": [], "unchanged": ["docs/index.md"]}, "summary": {"counts": {"created": 1, "deleted": 0, "modified": 1, "renamed": 0, "unchanged": 1, "violations": 0}, "graph_score": 100, "overall_score": 100, "state_score": 100, "status": "pass", "trace_score": 100}, "trace": {"actions": {"read": 1, "shell": 1, "write": 2}, "events": 4, "external_accesses": [], "paths_accessed": ["docs/faq.md", "docs/guide.md", "docs/index.md"], "shell_commands": ["python scripts/test.py"], "tools": {"read_file": 1, "shell": 1, "write_file": 2}}, "violations": []}
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
mkdir -p ~/.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-based-evaluation-for-ai-agents/* ~/.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/

# 프로젝트 로컬
mkdir -p .claude/skills/diffsentinel-state-based-evaluation-for-ai-agents
cp -r /tmp/techllm-skills/skills/diffsentinel-state-based-evaluation-for-ai-agents/* .claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/diffsentinel-state-based-evaluation-for-ai-agents
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/diffsentinel-state-based-evaluation-for-ai-agents/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--before BEFORE] [--after AFTER] [--trace TRACE]
              [--config CONFIG] [--output OUTPUT] [--pretty] [--selftest]

Evaluate AI agent workspace state diffs and JSONL tool traces.

options:
  -h, --help       show this help message and exit
  --before BEFORE  Before snapshot JSON file or directory
  --after AFTER    After snapshot JSON file or directory
  --trace TRACE    JSONL tool trace file
  --config CONFIG  Optional JSON config file
  --output OUTPUT  Write report JSON to this file
  --pretty         Print indented JSON output
  --selftest       Run built-in sample data with no API key or external
                   service
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 이전 스냅샷과 이후 스냅샷을 비교하여 생성, 수정, 삭제, 이름 변경 및 변경되지 않은 파일을 식별합니다.
- JSONL 도구 추적을 분석하여 읽기, 쓰기, API 호출, 셸 활동 및 외부 접근을 검사합니다.
- 허용되지 않은 영역, 누락된 승인, 안전하지 않은 쓰기 및 예기치 않은 부작용과 같은 작업 공간 정책을 확인합니다.
- 그래프 및 참조 무결성을 평가하며, 추가된 링크, 제거된 링크, 고아 노드, 해결되지 않은 참조 및 인용 누락을 포함합니다.
- 점수, 위반, 증거, 심각도 및 기계가 읽을 수 있는 결과를 포함하는 결정론적 JSON 결과를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 보고서에 예상된 변경에 대한 증거가 누락되었다고 표시됩니다. | 작업 공간은 변경되었지만, 사용 가능한 추적 또는 스냅샷에 변경이 발생한 이유를 증명할 수 있는 충분한 정보가 포함되어 있지 않습니다. | 평가가 완전한 이전 및 이후 상태 데이터와 에이전트 실행을 위한 전체 도구 추적을 포함하는지 확인하세요. |
| 요약으로는 작업이 통과했지만 DiffSentinel에서는 실패합니다. | 에이전트의 최종 응답은 성공을 설명했지만, 작업 공간 상태에 필요한 변경 사항이 포함되어 있지 않거나 참조가 보존되지 않았습니다. | 보고된 결과를 검토하고 작업 기준 또는 에이전트 동작을 업데이트하여 성공이 실제 작업 공간 상태에 반영되도록 하세요. |
| 작업과 관련이 없어 보이는 파일에 대한 정책 위반이 나타납니다. | 에이전트가 예상된 작업 경계 외부 영역에 접근하거나 수정했습니다. | 허용된 작업 공간 범위를 좁히고, 작업 경계를 명확히 하거나, 광범위한 접근에 대해 명시적인 승인을 요구하세요. |

## 자주 묻는 질문

**왜 최종 텍스트가 아니라 상태를 평가하나요?**

최종 텍스트는 에이전트가 옳게 들리도록 만들기 쉽습니다. 상태 기반 평가는 약속된 작업이 실제로 이루어졌는지, 그리고 작업 공간 규칙을 준수했는지 여부를 확인합니다.

**DiffSentinel을 CI에서 사용할 수 있나요?**

네. 구조화된 JSON 출력은 자동화된 파이프라인, 대시보드, 벤치마크 도구 모음 및 장기적인 회귀 추적에 맞게 설계되었습니다.

**이것은 코드 에이전트에만 해당되나요?**

아니요. 문서 에이전트, 지식 기반 에이전트, 연구 조수 및 구조화된 작업 공간 콘텐츠를 변경하는 모든 에이전트에게 유용합니다.

**이것이 일반적인 diff 도구와 다른 점은 무엇인가요?**

일반적인 diff는 무엇이 변경되었는지를 보여줍니다. DiffSentinel은 작업 기준, 도구 활동, 작업 공간 정책, 그래프 무결성 및 필요한 증거에 대해 이러한 변경 사항을 해석합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/` 또는 `.claude/skills/diffsentinel-state-based-evaluation-for-ai-agents/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
