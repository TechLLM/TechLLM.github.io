# SurfacePilot — Failure-Surface Routing Profiler for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> LLM 에 실패하는 프로필을 식별한 후, 그 증거를 더 나은 라우팅 정책으로 전환합니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

SurfacePilot은 LLM 및 에이전트 시스템이 모델, 도구 및 보호 장치를 통해 작업을 어떻게 라우팅하는지 평가하기 위한 제안된 오픈 소스 CLI입니다. 이 프로젝트는 최종 답변이 올바르게 보이는지 여부로 라우터를 판단하는 것이 아니라 실행 증거에 중점을 둡니다.

이 프로젝트는 라우팅을 실패 표면 분류 문제로 취급합니다. 작업은 검색이 오래되었거나, 인용을 지원할 수 없거나, API 호출이 잘못되었거나, 파일 편집이 위험하거나, 계산이 신뢰할 수 없거나, 외부 상태 변경에 대한 검증이 더 필요할 때 실패할 수 있습니다.

SurfacePilot은 팀이 이러한 실패를 구조화된 통찰력으로 전환하는 데 도움을 줍니다. 이 도구는 추적 데이터와 작업 메타데이터를 수집하고, 실행 표면별로 성공/실패 보기를 구축하며, 반복되는 실패 패턴을 감지하고, 모델 선택, 도구 선택, 대체, 가드레일, 에스컬레이션 및 평가 범위를 알릴 수 있는 라우팅 정책 출력을 생성합니다.

**누구를 위한 건가요.** SurfacePilot은 실제 시스템에서 라우팅 결정이 실패하는 이유와 이러한 결정을 더 안전하고, 더 신뢰할 수 있으며, 테스트하기 쉽게 만드는 방법을 이해해야 하는 엔지니어, 평가 팀, AI 플랫폼 팀 및 에이전트 개발자를 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
python scripts/run.py --selftest
```

**예상 출력:**

```text
summary:
  events: 5
  passed: 1
  failed: 4
  failure_rate: 0.8
  surfaces:
    api_call:
      events: 1
      passed: 0
      failed: 1
      fail_rate: 1.0
    citation:
      events: 1
      passed: 0
      failed: 1
      fail_rate: 1.0
    file_edit:
      events: 1
      passed: 0
      failed: 1
      fail_rate: 1.0
    retrieval:
      events: 2
      passed: 1
      failed: 1
      fail_rate: 0.5
matrix:
  - task_type: "code_edit"
    model: "small-router"
    route: "edit_direct"
    tool: "filesystem"
    surface: "file_edit"
    signal: "unsafe_edit"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
  - task_type: "ops"
    model: "small-router"
    route: "api_direct"
    tool: "billing_api"
    surface: "api_call"
    signal: "malformed_api_call"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
  - task_type: "support_qa"
    model: "large-router"
    route: "rag_verified"
    tool: "retriever"
    surface: "retrieval"
    signal: "fresh_retrieval"
    events: 1
    passed: 1
    failed: 0
    fail_rate: 0.0
  - task_type: "support_qa"
    model: "small-router"
    route: "rag_fast"
    tool: "citation_checker"
    surface: "citation"
    signal: "unsupported_citation"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
  - task_type: "support_qa"
    model: "small-router"
    route: "rag_fast"
    tool: "retriever"
    surface: "retrieval"
    signal: "stale_retrieval"
    events: 1
    passed: 0
    failed: 1
    fail_rate: 1.0
patterns:
  - signal: "malformed_api_call"
    surface: "api_call"
    count: 1
    task_ids:
      - "task-004"
    routes:
      - "api_direct"
    tools:
      - "billing_api"
  - signal: "unsupported_citation"
    surface: "citation"
    count: 1
    task_ids:
      - "task-001"
    routes:
      - "rag_fast"
    tools:
      - "citation_checker"
  - signal: "unsafe_edit"
    surface: "file_edit"
    count: 1
    task_ids:
      - "task-003"
    routes:
      - "edit_direct"
    tools:
   
… (+2613 chars truncated)
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
mkdir -p ~/.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
cp -r /tmp/techllm-skills/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/* ~/.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/

# 프로젝트 로컬
mkdir -p .claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
cp -r /tmp/techllm-skills/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/* .claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT] [--format {yaml,json}]
              [--failure-threshold FAILURE_THRESHOLD]
              [--min-failures MIN_FAILURES] [--selftest] [--version]

Profile LLM agent failure surfaces from trace JSONL and export a routing
policy.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Trace JSONL input file.
  --output OUTPUT, -o OUTPUT
                        Write profile to this file.
  --format {yaml,json}  Output format. Default: yaml.
  --failure-threshold FAILURE_THRESHOLD
                        Minimum group failure rate for policy rules. Default:
                        env or 0.34.
  --min-failures MIN_FAILURES
                        Minimum failed events for patterns and policy rules.
                        Default: env or 1.
  --selftest            Run the built-in sample with assertions and print the
                        resulting profile.
  --version             show program's version number and exit

Environment: SURFACEPILOT_FAILURE_THRESHOLD and SURFACEPILOT_MIN_FAILURES may
set default thresholds.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 구조화된 에이전트 추적을 수집하며, 여기에는 실행, 도구 호출, 관찰, 평가자 결과 및 작업 메타데이터가 포함됩니다.
- 검색, 파일 편집, API 호출, 계산, 인용, 계획, 상태 변경 및 사용자 정의 범주와 같은 실행 표면 전반에 걸쳐 각 실행에 레이블을 지정합니다.
- 작업 유형, 모델, 도구, 경로, 표면 및 평가자 신호에 대한 성공/실패 매트릭스를 구축하여 약점을 숨기지 않고 볼 수 있도록 합니다.
- 오래된 검색, 안전하지 않은 편집, 잘못된 API 호출, 지원되지 않는 인용 및 신뢰할 수 없는 계산과 같은 반복되는 실패 패턴을 클러스터링합니다.
- YAML로 라우팅 정책을 내보내므로 결과를 모델 선택, 대체 동작, 가드레일, 에스컬레이션 규칙 및 평가 우선순위로 변환할 수 있습니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 프로파일러에 너무 많은 알 수 없거나 레이블이 없는 표면이 표시됩니다. | 추적에 SurfacePilot이 각 실패가 발생한 위치를 추론할 수 있는 충분한 구조화된 메타데이터가 포함되어 있지 않습니다. | 프로파일러가 증거를 올바른 실행 표면에 매핑할 수 있도록 더 명확한 작업 레이블, 도구 호출 주석, 평가자 신호 또는 사용자 정의 표면 레이블을 추가합니다. |
| 경로가 전반적으로는 정확해 보이지만 매트릭스에서는 여전히 위험해 보입니다. | 최종 답변이 성공한 경우에도 표면별 실패를 숨길 수 있으며, 특히 검색이 약하거나 인용이 누락되거나 도구 동작이 취약한 경우에도 에이전트가 성공할 때 그렇습니다. | 실패한 표면을 직접 검토하고 해당 표면에 대한 대상 라우팅 규칙, 가드레일, 대체 검사 또는 평가 사례를 추가합니다. |
| 실패 클러스터가 너무 광범위하여 조치를 취하기 어렵습니다. | 평가자 신호 또는 오류 범주가 너무 일반적이어서 관련 없는 실패가 함께 그룹화됩니다. | 더 구체적인 평가자 레이블과 메타데이터를 사용하여 반복되는 패턴을 실행 가능한 범주로 분리합니다. |

## 자주 묻는 질문

**SurfacePilot은 정확도 벤치마크인가요?**

꼭 그런 것은 아닙니다. 평가자 결과를 사용할 수 있지만, 주요 목적은 시스템이 최종 답안 점수로 축소되는 것이 아니라 실행 표면 전반에 걸쳐 라우팅이 성공하거나 실패하는 위치를 설명하는 것입니다.

**왜 실패 표면에 초점을 맞추나요, 작업이나 도구에만 초점을 맞추지 않고?**

동일한 작업이 다른 이유로 실패할 수 있기 때문입니다. 검색 집약적인 작업에 좋은 라우팅 결정은 파일 편집에는 안전하지 않거나, 계산에는 약하거나, 인용에 민감한 답변에는 불완전할 수 있습니다.

**내보낸 라우팅 정책은 무엇에 사용되나요?**

모델 선택, 도구 선택, 대체 라우팅, 가드레일, 에스컬레이션 경로 및 평가 범위를 안내하는 데 사용할 수 있습니다. 목표는 추적 증거를 개선하고 검증하기 쉬운 라우팅 동작으로 전환하는 것입니다.

**SurfacePilot에는 특정 에이전트 프레임워크가 필요한가요?**

개념은 프레임워크에 구애받지 않습니다. 추적 및 메타데이터 수집을 중심으로 설계되었으므로 구조화된 실행 증거를 내보낼 수 있는 모든 에이전트 시스템은 이를 채택할 수 있습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/` 또는 `.claude/skills/surfacepilot-failure-surface-routing-profiler-for-llm-agents/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
