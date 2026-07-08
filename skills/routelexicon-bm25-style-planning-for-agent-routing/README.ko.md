# RouteLexicon — BM25-Style Planning for Agent Routing

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 다중 에이전트 시스템을 위한 투명한 BM25 스타일 라우팅 계획입니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

RouteLexicon은 다중 에이전트 시스템을 위한 제안된 오픈 소스 라우팅 계층입니다. 사용자의 요청과 에이전트의 매니페스트를 구체적인 어휘적 증거(키워드, 희귀 용어, 동의어, 배제어, 제약 조건, 가중치 및 하위 쿼리)로 구성된 명시적 라우팅 계획으로 변환합니다.

RouteLexicon은 언어 모델에게 모호한 의도만으로 에이전트를 선택하도록 요구하는 대신, 매칭 과정을 검사 가능하게 만듭니다. 왜 에이전트가 매칭되었는지, 어떤 단서가 중요한지, 어떤 유사한 에이전트가 배제되었는지, 그리고 요청이 전문화된 에이전트 간에 어떻게 분할될 수 있는지를 보여줍니다.

이 프로젝트는 일반 JSON 매니페스트와 Python 표준 라이브러리와 함께 작동하는 경량 CLI 및 라이브러리로 설계되었습니다. 그 출력은 기계가 읽을 수 있는 JSON이며, 로깅, 테스트, 검토 또는 LLM 기반 오케스트레이션 계층으로 전달될 수 있습니다.

**누구를 위한 건가요.** RouteLexicon은 에이전트 라우터, 오케스트레이션 계층, 내부 자동화 시스템 및 평가 도구를 구축하는 개발자를 위한 것입니다. 여기서 에이전트 선택은 투명하고 테스트 가능하며 단일 불투명한 모델 결정보다 디버깅이 쉬워야 합니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/routelexicon-bm25-style-planning-for-agent-routing
python scripts/run.py --selftest
```

**예상 출력:**

```text
{"version": "0.1.0", "request": "Research competitors and summarize current market evidence", "query_terms": ["competitors", "current", "evidence", "market", "research", "summarize"], "idf": {"agent_count": 3, "average_document_length": 35.67}, "ranked_agents": [{"agent_id": "research-agent", "name": "Research Agent", "score": 7.6549, "matched_terms": [{"term": "competitors", "idf": 0.9808, "tf": 2}, {"term": "current", "idf": 0.9808, "tf": 1}, {"term": "evidence", "idf": 0.9808, "tf": 3}, {"term": "research", "idf": 0.9808, "tf": 6}, {"term": "market", "idf": 0.47, "tf": 3}], "rare_terms": [{"term": "competitors", "idf": 0.9808}, {"term": "current", "idf": 0.9808}, {"term": "evidence", "idf": 0.9808}, {"term": "research", "idf": 0.9808}, {"term": "market", "idf": 0.47}], "excluded_by": [], "weights": {"bm25": 6.5055, "keyword_boost": 1.1494, "exclusion_penalty": 0.0, "final": 7.6549}, "rationale": "Matched competitors, current, evidence, market, research; rare clues: competitors, current, evidence."}, {"agent_id": "finance-agent", "name": "Finance Agent", "score": 0.9685, "matched_terms": [{"term": "market", "idf": 0.47, "tf": 3}], "rare_terms": [{"term": "market", "idf": 0.47}], "excluded_by": [], "weights": {"bm25": 0.804, "keyword_boost": 0.1645, "exclusion_penalty": 0.0, "final": 0.9685}, "rationale": "Matched market; rare clues: market."}, {"agent_id": "coding-agent", "name": "Coding Agent", "score": -1.5, "matched_terms": [], "rare_terms": [], "excluded_by": ["market"], "weights": {"bm25": 0.0, "keyword_boost": 0.0, "exclusion_penalty": 1.5, "final": -1.5}, "rationale": "Penalized because the request contains exclusion terms: market."}], "routing_plan": {"selected_agent_ids": ["research-agent", "finance-agent"], "decomposed_subqueries": [{"id": "q1", "text": "Research competitors", "terms": ["competitors", "research"], "candidate_agent_ids": ["research-agent"]}, {"id": "q2", "text": "summarize current market evidence", "terms": ["current", "evidence", "market
… (+151 chars truncated)
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
mkdir -p ~/.claude/skills/routelexicon-bm25-style-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routelexicon-bm25-style-planning-for-agent-routing/* ~/.claude/skills/routelexicon-bm25-style-planning-for-agent-routing/

# 프로젝트 로컬
mkdir -p .claude/skills/routelexicon-bm25-style-planning-for-agent-routing
cp -r /tmp/techllm-skills/skills/routelexicon-bm25-style-planning-for-agent-routing/* .claude/skills/routelexicon-bm25-style-planning-for-agent-routing/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/routelexicon-bm25-style-planning-for-agent-routing
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/routelexicon-bm25-style-planning-for-agent-routing/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--manifest MANIFEST] [--query QUERY]
              [--query-file QUERY_FILE] [--top-k TOP_K] [--k1 K1] [--b B]
              [--output OUTPUT] [--pretty] [--selftest]

Create BM25-style routing plans from a user request and JSON agent manifest.

options:
  -h, --help            show this help message and exit
  --manifest MANIFEST   Path to a JSON manifest with an agents array.
  --query QUERY         Request text to route.
  --query-file QUERY_FILE
                        Path to a UTF-8 text file containing the request.
  --top-k TOP_K         Number of selected agents to return.
  --k1 K1               BM25 term saturation parameter.
  --b B                 BM25 document-length normalization parameter.
  --output OUTPUT       Write the JSON result to this file instead of stdout.
  --pretty              Pretty-print JSON output.
  --selftest            Run on built-in sample data without API keys.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 각 에이전트의 기능을 설명하는 일반 JSON 에이전트 매니페스트를 읽습니다.
- 표준 라이브러리 토크나이저로 에이전트 설명과 사용자 요청을 토큰화합니다.
- 말뭉치 수준의 IDF 점수를 계산하여 희귀하고 구체적인 용어가 더 많은 라우팅 가중치를 갖도록 합니다.
- 키워드, 희귀 용어, 배제어, 가중치 및 하위 쿼리로 구성된 BM25 스타일 라우팅 계획을 작성합니다.
- 순위가 매겨진 후보 에이전트를 구조화된 점수 세부 정보와 사람이 읽을 수 있는 근거와 함께 반환합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 잘못된 에이전트가 상위에 랭크됩니다. | 에이전트 매니페스트에 요청과 어휘적으로 일치하지만 올바른 기능을 나타내지 않는 광범위하거나 중복된 언어가 포함되어 있을 수 있습니다. | 매니페스트 설명을 강화하고, 더 구체적인 기능 용어를 추가하고, 유사하지만 잘못된 매치를 위한 배제 용어를 정의하세요. |
| 여러 에이전트가 매우 유사한 점수를 받습니다. | 그들의 매니페스트가 유사한 어휘를 사용하거나 충분히 구별되는 용어 없이 인접한 책임을 설명할 가능성이 높습니다. | 각 매니페스트에 더 명확한 기능 경계, 희귀한 도메인 용어 및 작업별 제약 조건을 추가하세요. |
| 관련 에이전트가 상위 결과에 나타나지 않습니다. | 요청과 에이전트 매니페스트가 동일한 개념에 대해 다른 용어를 사용할 수 있습니다. | 매니페스트에 동의어나 대체 문구를 추가하여 계획자가 요청 언어를 에이전트의 기능과 연결할 수 있도록 하세요. |

## 자주 묻는 질문

**RouteLexicon이 LLM 라우터의 대체품인가요?**

꼭 그런 것은 아닙니다. RouteLexicon은 자체적으로 어휘 라우팅을 위해 사용되거나, LLM 라우터 앞에 배치되어 명시적 증거, 후보 순위, 배제 및 하위 쿼리를 제공할 수 있습니다.

**왜 에이전트 라우팅에 BM25 스타일 계획을 사용하나요?**

BM25 스타일 점수는 구체적이고 희귀한 용어를 보상하고 어휘적 증거를 명시적으로 만듭니다. 이는 라우팅이 직접적인 자연어 분류 단계보다 검사, 테스트 및 디버깅이 더 쉬워지게 합니다.

**RouteLexicon이 외부 종속성을 요구하나요?**

제안된 핵심은 Python 표준 라이브러리, 일반 JSON 매니페스트 및 간단한 토크나이저 및 IDF 논리를 중심으로 설계되어 경량이고 통합이 용이합니다.

**라우팅 출력에는 무엇이 포함되나요?**

출력에는 순위가 매겨진 에이전트, 점수 세부 정보, 일치하는 용어, 희귀한 단서, 배제, 가중치, 하위 쿼리 및 하위 시스템이 검사하거나 기록할 수 있는 근거가 포함됩니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/routelexicon-bm25-style-planning-for-agent-routing/` 또는 `.claude/skills/routelexicon-bm25-style-planning-for-agent-routing/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
