# ContextTrellis — Hub-Aware Context Budget Compressor

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 중요한 꼬리표시 노드를 잃지 않으면서 컴팩트한 LLM 컨텍스트 번들을 구축하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

ContextTrellis는 대규모 Markdown 지식 저장소를 LLM을 위한 고신호 컨텍스트 번들로 변환하는 오픈 소스 라이브러리와 CLI를 제안합니다.

이는 에이전트 시스템에서 흔히 발생하는 검색 문제를 해결합니다: 중앙 허브 노트는 종종 프롬프트 예산의 대부분을 소비하는 반면, 정확한 실행 세부 사항이 포함된 작은 노드들은 제외됩니다. 간과된 노드들은 API 동작, 폴링 규칙, 드라이 런 결과, 명령어 특성 또는 에이전트의 성공 여부를 결정하는 제약 조건을 포함할 수 있습니다.

ContextTrellis는 광범위한 지도를 유지하면서 운영상의 세부 사항을 묻히지 않도록 합니다. 그것은 높은 연결성을 가진 허브 노드를 짧은 방향성 요약으로 압축하고, 실행에 중점을 둔 긴 꼬리 노드를 가능한 한 원래 형태로 보존합니다.

**누구를 위한 건가요.** ContextTrellis는 대규모 Markdown 또는 Obsidian 스타일의 저장소를 유지하고 LLM 워크플로우를 위한 신뢰할 수 있고 감사 가능한 컨텍스트 패키지가 필요한 개발자, 에이전트 빌더, 기술 작가 및 지식 관리 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/contexttrellis-hub-aware-context-budget-compressor
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "bundle_version": "0.1",
  "mode": "selftest",
  "input": "built-in-sample",
  "budget": {
    "requested_tokens": 900,
    "reserve_tokens": 100,
    "available_tokens": 800,
    "used_tokens": 269
  },
  "graph": {
    "notes": 5,
    "edges": 4,
    "hubs": [
      "Architecture.md"
    ],
    "long_tail": [
      "API Polling.md",
      "CLI Commands.md",
      "Dry Run Log.md",
      "Error Handling.md"
    ]
  },
  "items": [
    {
      "id": "Architecture.md",
      "path": "Architecture.md",
      "role": "hub_summary",
      "tokens": 39,
      "centrality": 1.0,
      "execution_score": 2.55,
      "reason": "high-centrality orientation note; compressed",
      "content": "# Architecture Hub\nPurpose: ContextTrellis builds prompt bundles from [[API Polling]], [[CLI Commands]], and [[Dry Run Log]].\nLinks: API Polling.md, CLI Commands.md, Dry Run Log.md, Error Handling.md\nTags: architecture, index"
    },
    {
      "id": "API Polling.md",
      "path": "API Polling.md",
      "role": "preserved_detail",
      "tokens": 65,
      "centrality": 0.25,
      "execution_score": 12.7,
      "reason": "execution-heavy long-tail note; preserved",
      "content": "# API Polling\n\nTags: #api #execution\n\nUse this when a job returns `queued` or `running`.\nPoll `GET /v1/jobs/{job_id}` every 5 seconds until status becomes `succeeded` or `failed`.\nDo not poll faster than once per second.\n\n```bash\ncurl -s \"$BASE_URL/v1/jobs/$JOB_ID\"\n```\n\nIf the API returns 429, wait 30 seconds before retrying."
    },
    {
      "id": "CLI Commands.md",
      "path": "CLI Commands.md",
      "role": "preserved_detail",
      "tokens": 47,
      "centrality": 0.25,
      "execution_score": 6.05,
      "reason": "execution-heavy long-tail note; preserved",
      "content": "# CLI Commands\n\nTags: #cli #execution\n\nRun the compressor locally before calling an LLM:\n\n```bash\npython scripts/run.py --input examples/vault --budget 620 --reserve 80\n```\n\nUse `--format 
… (+2119 chars truncated)
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
mkdir -p ~/.claude/skills/contexttrellis-hub-aware-context-budget-compressor
cp -r /tmp/techllm-skills/skills/contexttrellis-hub-aware-context-budget-compressor/* ~/.claude/skills/contexttrellis-hub-aware-context-budget-compressor/

# 프로젝트 로컬
mkdir -p .claude/skills/contexttrellis-hub-aware-context-budget-compressor
cp -r /tmp/techllm-skills/skills/contexttrellis-hub-aware-context-budget-compressor/* .claude/skills/contexttrellis-hub-aware-context-budget-compressor/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/contexttrellis-hub-aware-context-budget-compressor
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/contexttrellis-hub-aware-context-budget-compressor/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--selftest] [--budget BUDGET]
              [--reserve RESERVE] [--format {json,markdown}]
              [--min-execution-score MIN_EXECUTION_SCORE]
              [--hub-summary-tokens HUB_SUMMARY_TOKENS]
              [--max-note-tokens MAX_NOTE_TOKENS]

Build a hub-aware, budgeted LLM context bundle from Markdown notes.

options:
  -h, --help            show this help message and exit
  --input INPUT         Markdown file or folder. Omit for built-in sample
                        data.
  --selftest            Run on built-in sample data with no API key or
                        external services.
  --budget BUDGET       Requested token budget before reserve. Env:
                        CONTEXTTRELLIS_BUDGET.
  --reserve RESERVE     Tokens to reserve for the caller's surrounding prompt.
                        Env: CONTEXTTRELLIS_RESERVE_TOKENS.
  --format {json,markdown}
                        Output format. Env: CONTEXTTRELLIS_OUTPUT_FORMAT.
  --min-execution-score MIN_EXECUTION_SCORE
  --hub-summary-tokens HUB_SUMMARY_TOKENS
  --max-note-tokens MAX_NOTE_TOKENS
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- Markdown 노트, 링크, 태그, 제목, 머리말 및 관련 개념을 지식 그래프로 구문 분석합니다.
- 노트를 그래프 중심성, 실행 신호 및 예상 토큰 비용에 따라 점수를 매깁니다.
- 너무 중심이 되는 허브 노드를 압축하여 간결한 방향성 블록으로 만들고, 그것들이 프롬프트를 지배하지 않도록 합니다.
- 명령어, API 세부 사항, 오류, 절차, 상태 전환 또는 운영 제약 조건을 포함하는 낮은 중심성 노드를 보존합니다.
- 투명한 포함 결정과 구성 가능한 토큰 예약을 사용하여 결정론적인 컨텍스트 번들을 구성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 번들에 여전히 중요한 운영 노트가 누락되어 있습니다. | 실행 신호 점수가 저장소의 언어 또는 구조에 맞게 조정되지 않았을 수 있습니다. | 실행 신호 구성을 조정하여 플래너가 노트에서 사용되는 용어, 제목, 코드 패턴 및 절차 표시자를 인식하도록 합니다. |
| 번들이 너무 추상적이거나 요약이 너무 많습니다. | 토큰 예산이 너무 적거나, 허브 압축이 작업에 비해 너무 공격적일 수 있습니다. | 사용 가능한 예산을 늘리고, 예약을 줄이거나, 더 상세하게 유지해야 하는 노트의 압축 설정을 완화합니다. |
| 허브 노드가 너무 장황하게 포함되어 있습니다. | 노드에 강력한 실행 신호와 높은 중심성이 모두 포함되어 있어 운영상 중요하게 취급될 수 있습니다. | 포함 이유를 검토하고 중심성 압축과 실행 보존 간의 균형을 조정합니다. |

## 자주 묻는 질문

**ContextTrellis는 Obsidian 저장소에만 사용할 수 있나요?**

아니요. Obsidian 스타일의 Markdown 폴더, 위키 링크 및 머리말과 잘 작동하도록 설계되었지만, 기본적인 그래프 기반 예산 접근 방식은 다른 Markdown 지식 기반에도 적용할 수 있습니다.

**벡터 검색을 대체하나요?**

꼭 그런 것은 아닙니다. ContextTrellis는 검색 전이나 검색과 함께 사용할 수 있습니다. 그것의 초점은 예산 할당에 있습니다: 후보 지식이 확보된 후 무엇을 요약하고, 보존하고, 생략할지 결정하는 것입니다.

**왜 그냥 모든 것을 요약하지 않나요?**

균일한 요약은 에이전트가 올바르게 행동하는 데 필요한 정확한 세부 사항을 제거할 수 있습니다. ContextTrellis는 방향성과 실행을 다르게 취급하여 광범위한 허브 자료를 압축하면서 운영상의 세부 사항을 포함하는 노트를 보존합니다.

**에이전트 프레임워크 내에서 사용할 수 있나요?**

네. 제안된 설계는 독립형 CLI 워크플로우와 에이전트 프레임워크, 검색 파이프라인 및 지식 관리 도구에 대한 Python 라이브러리 통합을 모두 지원합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/contexttrellis-hub-aware-context-budget-compressor/` 또는 `.claude/skills/contexttrellis-hub-aware-context-budget-compressor/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
