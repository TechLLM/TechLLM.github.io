# RouteGlyph — Verifiable BM25 Planning for Agent Routing

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 투명한 BM25 스타일의 라우팅 계획으로 에이전트 및 도구 선택을 지원합니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

RouteGlyph는 에이전트 및 도구 라우팅을 더 쉽게 검사, 테스트 및 신뢰할 수 있도록 설계된 오픈 소스 라우팅 계층입니다. 사용자의 요청과 도구 설명을 숨겨진 LLM 프롬프트 내부의 라우팅 결정 대신 명시적인 BM25 스타일의 후보 계획으로 변환합니다.

이 솔루션이 해결하는 문제는 라우팅 불투명성입니다. 많은 다중 에이전트 시스템에서 어떤 도구가 다른 도구보다 선택된 이유를 알기 어렵거나, 결정의 재현 가능성 여부, 또는 도구 설명의 변경이 행동에 어떻게 영향을 미쳤는지 파악하기 어렵습니다. RouteGlyph는 검토, 로깅, 버전 관리 및 회귀 테스트가 가능한 일반 소프트웨어처럼 구조화된 라우팅 표면을 만듭니다.

RouteGlyph는 LLM 라우터를 대체하지 않습니다. 생성적 결정이 이루어지기 전에 투명하고 순위가 매겨진 후보를 준비하므로, LLM, 규칙 엔진, 정책 계층 또는 오케스트레이터가 더 나은 증거를 가지고 최종 선택을 할 수 있습니다.

**누구를 위한 건가요.** RouteGlyph는 라우팅 실수가 비용이 많이 들거나 디버깅이 어렵거나 검토 대상인 다중 에이전트 시스템, 도구 사용 어시스턴트, RAG 파이프라인, 평가 도구 및 프로덕션 AI 워크플로를 구축하는 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "plan_version": "routeglyph.v1",
  "tokenizer": "routeglyph-tokenizer.v1",
  "query": "Route an agent request to build a local regression-testable BM25 router with no API key.",
  "query_terms": [
    "route",
    "agent",
    "request",
    "build",
    "local",
    "regression",
    "testable",
    "bm25",
    "router",
    "no",
    "api",
    "key"
  ],
  "required_constraints": [
    "code_required",
    "local_only",
    "regression_testable"
  ],
  "candidates": [
    {
      "rank": 1,
      "tool_id": "route_planner",
      "tool_name": "Route Planner",
      "score": 11.0619,
      "rare_terms": [
        "bm25",
        "route",
        "router",
        "routing",
        "tool"
      ],
      "matched_terms": [
        {
          "term": "agent",
          "query_weight": 1.0,
          "tool_tf": 2,
          "idf": 0.3567,
          "contribution": 0.4648
        },
        {
          "term": "bm25",
          "query_weight": 1.0,
          "tool_tf": 2,
          "idf": 1.204,
          "contribution": 1.5689
        },
        {
          "term": "idf",
          "query_weight": 0.65,
          "tool_tf": 1,
          "idf": 1.204,
          "contribution": 0.7244
        },
        {
          "term": "local",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 0.6931,
          "contribution": 0.6416
        },
        {
          "term": "orchestrator",
          "query_weight": 0.65,
          "tool_tf": 1,
          "idf": 1.204,
          "contribution": 0.7244
        },
        {
          "term": "regression",
          "query_weight": 1.0,
          "tool_tf": 2,
          "idf": 0.6931,
          "contribution": 0.9032
        },
        {
          "term": "route",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 1.204,
          "contribution": 1.1145
        },
        {
          "term": "router",
          "query_weight": 1.0,
          "tool_tf": 1,
          "idf": 1.204,
          "
… (+9902 chars truncated)
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
mkdir -p ~/.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/* ~/.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/

# 프로젝트 로컬
mkdir -p .claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/* .claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/routeglyph-verifiable-bm25-planning-for-agent-routing
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/routeglyph-verifiable-bm25-planning-for-agent-routing/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--query QUERY] [--query-file QUERY_FILE]
              [--catalog CATALOG] [--tool TOOL] [--limit LIMIT]
              [--min-score MIN_SCORE] [--pretty] [--selftest]

Generate deterministic BM25-style routing plans for agent/tool catalogs.

options:
  -h, --help            show this help message and exit
  --query QUERY         User request to route.
  --query-file QUERY_FILE
                        Text file containing the user request to route.
  --catalog CATALOG     Tool catalog as JSON or a small supported YAML subset.
  --tool TOOL           Inline tool as 'id|name|description' or
                        'id|name|description|keyword1,keyword2'. May be
                        repeated.
  --limit LIMIT         Maximum candidates to emit.
  --min-score MIN_SCORE
                        Drop candidates below this score.
  --pretty              Pretty-print JSON output.
  --selftest            Run on built-in sample data with no API key.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 사용자 요청과 도구 또는 에이전트 설명을 라우팅 신호로 토큰화합니다.
- BM25 스타일의 역문서 빈도 점수 계산으로 용어 중요성을 추정합니다.
- 각 후보 계획을 희귀 용어, 동의어, 제외어, 필요한 제약 조건, 점수 및 근거로 확장합니다.
- LLM 라우터, 정책 엔진 또는 오케스트레이터에 전달되기 전에 후보 도구 또는 에이전트의 순위를 지정합니다.
- 풀 리퀘스트에서 검토하고, 로그에 저장하고, 회귀 테스트에서 비교할 수 있는 구조화된 JSON 스냅샷을 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 잘못된 도구의 순위가 너무 높습니다. | 도구 설명에 광범위하거나 겹치는 용어가 포함되어 있어 관련이 없는 많은 요청에도 관련성이 있는 것처럼 보일 수 있습니다. | 더 구체적인 기능으로 설명을 구체화하고, 더 명확한 제외 사항을 추가하고, 주변 도구와 구별되는 고유한 용어를 포함하세요. |
| 후보 세트에서 관련 도구가 누락되었습니다. | 카탈로그 항목에 실제 사용자 요청에 사용되는 어휘가 포함되지 않았거나 필요한 제약 조건이 너무 좁을 수 있습니다. | 실제 사용자가 작업을 요청하는 방식과 일치하는 대표적인 동의어, 도메인 용어 및 제약 조건 용어를 추가하세요. |
| 카탈로그를 편집한 후 점수가 변경되었습니다. | IDF 스타일의 점수 계산은 전체 카탈로그에 따라 달라지므로 설명을 추가하거나 변경하면 후보 간의 용어 희귀성이 변경될 수 있습니다. | 생성된 계획 스냅샷을 검토하고 점수 변경을 다른 의도적인 행동 변경처럼 취급하세요. |

## 자주 묻는 질문

**RouteGlyph는 LLM 라우터인가요?**

아니오. RouteGlyph는 투명한 후보 생성 계층입니다. LLM 라우터, 규칙 엔진, 정책 계층 또는 오케스트레이터가 다운스트림에서 사용할 수 있는 검사 가능한 라우팅 계획을 생성합니다.

**에이전트 라우팅에 왜 BM25 스타일의 계획을 사용하나요?**

희소 검색은 고유한 용어, 제약 조건 및 긴 꼬리 쿼리와 일치시키는 데 능숙합니다. 이러한 속성은 어떤 도구나 에이전트가 요청에 적합할지 결정할 때 유용합니다.

**RouteGlyph가 라우팅을 결정론적으로 만들 수 있나요?**

후보 생성을 결정론적이고 재현 가능하게 만들 수 있습니다. 최종 라우팅 결정은 LLM에 전달되면 여전히 확률적일 수 있습니다.

**이것이 평가에 어떻게 도움이 되나요?**

RouteGlyph는 라우팅 계획, 점수 및 근거의 구조화된 스냅샷을 생성합니다. 이러한 스냅샷은 시간이 지나면서 비교하여 프롬프트, 도구 설명 또는 카탈로그 변경으로 인한 회귀를 포착할 수 있습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/` 또는 `.claude/skills/routeglyph-verifiable-bm25-planning-for-agent-routing/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
