# Tracewright — Execution-Evidence Grader Scaffolding for AI Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 에이전트 워크플로우를 위한 결정론적 실행 증거 평가기

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

Tracewright는 AI 에이전트가 작업을 완료한 방식, 즉 반환된 답변이 아닌 실행 증거를 평가하는 평가기를 구축하기 위한 제안된 오픈 소스 CLI입니다. 파일, 변경 사항, 도구 추적, 로그 및 최종 출력을 포함한 실행 증거에 중점을 둡니다.

이 도구는 팀이 에이전트 작업을 반복 가능한 검사로 전환할 수 있도록 도와줍니다. 처음부터 맞춤형 평가기를 작성하는 대신, 작업 작성자는 간결한 YAML 또는 JSON 사양으로 예상되는 증거를 설명하고, Tracewright는 샘플 테스트와 함께 실행 가능한 Python 평가기를 생성합니다.

Tracewright는 모델 기반 판단을 보완하여 에이전트가 남긴 아티팩트에 대한 결정론적 검사를 추가합니다. 이는 감사가 중요한 실용적인 개발, 문서화, 데이터 및 작업 공간 자동화 작업에 사용됩니다.

**누구를 위한 건가요.** Tracewright는 로컬 하니스, 회귀 테스트 모음, CI 또는 내부 평가에서 실제 에이전트 작업에 대한 일관된 평가를 필요로 하는 유지보수자, 벤치마크 작성자, 에이전트 플랫폼 팀 및 개발자 도구 빌더를 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "task_id": "sample-agent-edit",
  "passed": true,
  "score": 1.0,
  "summary": {
    "passed": 13,
    "failed": 0,
    "total": 13
  },
  "checks": [
    {
      "id": "file.required:src/feature.py",
      "category": "files",
      "passed": true,
      "message": "Required file exists: src/feature.py"
    },
    {
      "id": "file.forbidden:secrets.txt",
      "category": "files",
      "passed": true,
      "message": "Forbidden file absent: secrets.txt"
    },
    {
      "id": "edit.expected:src/feature.py",
      "category": "diff",
      "passed": true,
      "message": "Expected edit observed: src/feature.py"
    },
    {
      "id": "edit.forbidden:config/prod.env",
      "category": "diff",
      "passed": true,
      "message": "Forbidden edit absent: config/prod.env"
    },
    {
      "id": "trace.required:1",
      "category": "trace",
      "passed": true,
      "message": "Required trace event observed: {'type': 'read', 'path': 'src/feature.py'}"
    },
    {
      "id": "trace.required:2",
      "category": "trace",
      "passed": true,
      "message": "Required trace event observed: {'type': 'write', 'path': 'src/feature.py'}"
    },
    {
      "id": "trace.required:3",
      "category": "trace",
      "passed": true,
      "message": "Required trace event observed: {'type': 'command', 'pattern': 'python\\\\s+scripts/test.py'}"
    },
    {
      "id": "trace.forbidden:1",
      "category": "trace",
      "passed": true,
      "message": "Forbidden trace event absent: {'type': 'api_call', 'pattern': 'production'}"
    },
    {
      "id": "diff.required_pattern:1",
      "category": "diff",
      "passed": true,
      "message": "Required diff pattern matched: \\+def calculate_total"
    },
    {
      "id": "diff.forbidden_pattern:1",
      "category": "diff",
      "passed": true,
      "message": "Forbidden diff pattern absent: API_KEY|password"
    },
    {
      "id": "output.must_contain:1",
      "category": "output",
      "passed"
… (+413 chars truncated)
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
mkdir -p ~/.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
cp -r /tmp/techllm-skills/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/* ~/.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/

# 프로젝트 로컬
mkdir -p .claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
cp -r /tmp/techllm-skills/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/* .claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--selftest] [--spec SPEC] [--workspace WORKSPACE]
              [--trace TRACE] [--diff DIFF] [--output OUTPUT] [--audit AUDIT]
              [--scaffold] [--out OUT] [--format {json}]

Grade execution evidence or scaffold a deterministic Tracewright grader.

options:
  -h, --help            show this help message and exit
  --selftest            Run built-in sample data with no API key.
  --spec SPEC           Path to a JSON or simple YAML Tracewright spec. Can
                        also be set with TRACEWRIGHT_SPEC.
  --workspace WORKSPACE
                        Workspace directory after the agent run.
  --trace TRACE         JSONL tool trace file.
  --diff DIFF           Unified diff file.
  --output OUTPUT       Final answer or task output text file.
  --audit AUDIT         Audit log text file.
  --scaffold            Generate a standalone grader and sample fixtures.
  --out OUT             Output directory for --scaffold.
  --format {json}       Output format. TRACEWRIGHT_OUTPUT_FORMAT may also be
                        used.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 작업 작성자는 간결한 YAML 또는 JSON 사양에 예상되는 실행 증거를 설명합니다.
- Tracewright는 작업 공간 상태, 도구 추적, 변경 사항, 로그 및 최종 출력을 검사하는 Python 평가기를 구축합니다.
- 생성된 평가기는 필요한 파일, 예상된 편집, 금지된 수정, 필요한 도구 활동 및 금지된 패턴을 검증할 수 있습니다.
- 유지보수자가 평가기를 환경에 맞게 조정할 수 있도록 통과, 실패 및 경계 사례 테스트를 제공합니다.
- 팀은 모델 기반 평가와 함께 평가기를 사용하여 누락된 증거, 안전하지 않은 부작용 및 검증할 수 없는 작업 완료를 포착할 수 있습니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 최종 답변이 올바르게 보이지만 평가기가 실패합니다. | Tracewright는 실행 증거를 평가하므로 에이전트가 필요한 파일을 검사하지 않고, 예상된 편집을 수행하지 않거나 필요한 감사 추적을 남기지 않고도 허용 가능한 텍스트를 생성했을 수 있습니다. | 작업 사양과 캡처된 아티팩트를 검토하세요. 에이전트 워크플로우를 업데이트하여 필요한 증거를 생성하거나 증거 요구 사항이 너무 엄격했다면 사양을 수정하세요. |
| 추적 검사가 캡처된 도구 활동과 일치하지 않습니다. | 추적 형식, 이벤트 이름 또는 기록된 필드가 사양에서 예상하는 것과 다를 수 있습니다. | 사양을 실제 구조화된 추적 스키마와 정렬하고, 추적 어설션을 우발적인 형식이 아닌 안정적인 증거에 집중하세요. |
| 변경 패턴 검사가 시끄럽거나 부서지기 쉽습니다. | 정규 표현식이 너무 광범위하거나 너무 좁거나, 실행 간에 변경되는 형식에 연결될 수 있습니다. | 의미 있는 행동 변화를 포착하는 패턴을 선호하고, 필요한 편집을 금지된 부작용과 분리하여 실패를 더 쉽게 진단하세요. |

## 자주 묻는 질문

**Tracewright가 인간 또는 모델 기반 판단을 대체합니까?**

아니오. Tracewright는 실행 아티팩트에 대한 결정론적 검사로 이러한 접근 방식을 보완하도록 설계되었습니다. 에이전트가 허용 가능한 프로세스를 따르고 검증 가능한 증거를 생성했는지 여부를 판단하는 데 도움이 됩니다.

**Tracewright는 어떤 종류의 작업을 평가할 수 있습니까?**

코드 변경, 문서 편집, 데이터 변환, 작업 공간 자동화, API 상호 작용 및 감사된 명령 또는 도구 사용과 같이 검사 가능한 아티팩트를 남기는 에이전트 작업에 사용됩니다.

**왜 일반적인 평가기 대신 평가기를 생성합니까?**

에이전트 작업에는 종종 작업별 증거 요구 사항이 있습니다. 생성된 평가기를 통해 각 작업은 자체 예상 파일, 허용된 변경, 금지된 부작용, 추적 요구 사항 및 출력 어설션을 정의할 수 있으며, 동시에 공통 구조를 공유할 수 있습니다.

**팀이 생성된 평가기를 조정할 수 있습니까?**

예. 스캐폴드는 읽고 편집할 수 있도록 설계되었으므로 유지보수자는 검사를 확장하고, 하니스와 통합하거나, CI 및 벤치마크 워크플로우에 맞게 테스트를 조정할 수 있습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/` 또는 `.claude/skills/tracewright-execution-evidence-grader-scaffolding-for-ai-age/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
