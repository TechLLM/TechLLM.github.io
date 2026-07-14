# ParallaxPack — Hub-Bias-Resistant Evidence Retrieval

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 그래프 기반 RAG를 위한 균형 잡히고 설명 가능한 증거 검색.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

ParallaxPack는 그래프 검색 후보들을 균형 잡히고 검사 가능한 증거 묶음으로 변환하는 오픈소스 Python 라이브러리이자 CLI로 제안되었습니다. 이는 후보 생성과 프롬프트 구성 사이에서 정책 계층 역할을 하며, 기존의 벡터 데이터베이스와 그래프 엔진을 보완합니다.

ParallaxPack는 허브 편향(hub bias) 문제를 해결합니다. 연결성이 높은 노드들이 광범위한 배경 자료로 최근접 이웃 검색 결과를 압도하면서, 최근의 메모, 롱테일 증거, 관련성 있는 먼 커뮤니티들이 묻히게 됩니다. ParallaxPack는 의미적 관련성, 역허브 차수, 커뮤니티 다양성, 최신성, 출처 완전성, 메타데이터 품질을 활용해 증거를 재정렬하고 선택합니다.

**누구를 위한 건가요.** ParallaxPack는 그래프 기반 RAG, 지식 어시스턴트, 연구 도구, 그리고 다양한 증거, 신뢰할 수 있는 출처 정보, 재현 가능한 선택, 그리고 변경되지 않은 최근접 이웃 기준선과의 명확한 비교가 필요한 운영 검색 시스템을 구축하는 팀에 유용합니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "query": "What recent checkout failures, rollback actions, and customer impact evidence should operators review?",
  "as_of": "2026-01-15",
  "configuration": {
    "top_k": 4,
    "per_community_cap": 2,
    "min_communities": 3,
    "effective_min_communities": 3,
    "redundancy_weight": 0.08,
    "weights": {
      "semantic_relevance": 0.45,
      "inverse_degree": 0.2,
      "recency": 0.15,
      "source_completeness": 0.1,
      "metadata_quality": 0.1
    }
  },
  "summary": {
    "candidate_count": 6,
    "selected_count": 4,
    "excluded_count": 2
  },
  "baseline_comparison": {
    "baseline_policy": "semantic relevance descending, note ID tie-break",
    "hub_degree_threshold": 3.157379,
    "baseline": {
      "selected_ids": [
        "general-platform",
        "architecture-overview",
        "checkout-incident",
        "rollback-runbook"
      ],
      "metrics": {
        "community_count": 2,
        "community_coverage": 0.5,
        "hub_concentration": 0.25,
        "average_degree": 2.0,
        "average_freshness": 0.592399,
        "provenance_coverage": 0.75
      }
    },
    "parallaxpack": {
      "selected_ids": [
        "checkout-incident",
        "security-advisory",
        "customer-impact",
        "rollback-runbook"
      ],
      "metrics": {
        "community_count": 3,
        "community_coverage": 0.75,
        "hub_concentration": 0.0,
        "average_degree": 1.0,
        "average_freshness": 0.989196,
        "provenance_coverage": 1.0
      }
    },
    "delta": {
      "community_count": 1,
      "community_coverage": 0.25,
      "hub_concentration": -0.25,
      "average_degree": -1.0,
      "average_freshness": 0.396797,
      "provenance_coverage": 0.25
    }
  },
  "results": [
    {
      "rank": 1,
      "id": "checkout-incident",
      "title": "Checkout API timeout incident",
      "community": "operations",
      "updated_at": "2026-01-12",
      "degree": 1,
      "score": 0.870963,
      "score_compo
… (+5863 chars truncated)
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
mkdir -p ~/.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
cp -r /tmp/techllm-skills/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/* ~/.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/

# 프로젝트 로컬
mkdir -p .claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
cp -r /tmp/techllm-skills/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/* .claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/parallaxpack-hub-bias-resistant-evidence-retrieval
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/parallaxpack-hub-bias-resistant-evidence-retrieval/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] (--input INPUT | --selftest) [--format FORMAT]
              [--output OUTPUT] [--force] [--top-k TOP_K]
              [--per-community-cap PER_COMMUNITY_CAP]
              [--min-communities MIN_COMMUNITIES]

Rerank graph candidates into a hub-resistant evidence pack.

options:
  -h, --help            show this help message and exit
  --input INPUT         Path to an input JSON file
  --selftest            Run the built-in offline deterministic sample
  --format FORMAT       Output format: json, markdown, or both (default: json)
  --output OUTPUT       Write output to this file instead of stdout
  --force               Allow --output to overwrite an existing file
  --top-k TOP_K         Override the number of selected notes
  --per-community-cap PER_COMMUNITY_CAP
                        Override the maximum notes per community
  --min-communities MIN_COMMUNITIES
                        Override the minimum community coverage target
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 지식 그래프, 메모 메타데이터, 자연어 쿼리, 그리고 기존 검색 시스템의 후보들을 입력받습니다.
- 의미적 관련성, 역차수, 최신성, 출처 가용성, 메타데이터 품질을 종합한 점수를 계산합니다.
- 허브 노드를 자동으로 제외하지 않으면서, 커뮤니티 한도, 커버리지 목표, 중복 페널티를 사용해 다양한 증거 묶음을 선택합니다.
- 점수 구성 요소, 출처 정보, 커뮤니티 할당을 포함해 각 후보가 선택, 감점, 또는 제외된 이유를 설명합니다.
- LLM에 바로 쓸 수 있는 Markdown, 기계 판독 가능한 JSON, 또는 둘 다를 생성하며, 커버리지, 허브 집중도, 최신성, 출처에 대한 기준선 비교를 함께 제공합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 결과가 여전히 허브 노드에 의해 지배됩니다. | 역차수의 영향력이 의미적 관련성에 비해 너무 약하거나, 커뮤니티 제약 조건이 너무 느슨할 수 있습니다. | 역차수 점수의 영향력을 높이고, 커뮤니티별 한도를 더 엄격하게 조정한 다음, 증거 묶음을 기준선과 비교하기 전에 점수 설명을 검토하세요. |
| 관련 증거가 최종 묶음에서 누락되었습니다. | 후보 생성기가 해당 증거를 애초에 검색하지 않았거나, 다양성 및 중복 규칙이 너무 공격적으로 필터링하고 있을 수 있습니다. | 해당 증거가 입력 후보에 포함되어 있는지 확인하고, 필요 시 상류 검색 범위를 넓힌 뒤 커버리지, 한도, 중복 설정을 조정하세요. |
| 최신성 또는 출처 점수가 예상보다 낮습니다. | 메모의 타임스탬프, 출처 참조, 메타데이터 필드가 누락되었거나, 일관성이 없거나, 유효하지 않을 수 있습니다. | 재정렬 전에 메타데이터를 정규화하고, 각 메모에 유효한 날짜, 출처 세부 정보, 커뮤니티 할당, 출처 가용성 정보가 모두 포함되어 있는지 확인하세요. |
| 반복 실행해도 선택 결과가 달라집니다. | 후보 정렬, 그래프 상태, 메타데이터, 또는 동점 처리 방식이 실행 간에 달라질 수 있습니다. | 입력과 구성을 고정된 상태로 유지하고, 결정론적인 동점 처리를 사용하며, 비교를 위해 구조화된 점수 설명을 보관하세요. |

## 자주 묻는 질문

**ParallaxPack가 벡터 데이터베이스나 그래프 엔진을 대체하나요?**

아닙니다. ParallaxPack는 기존 검색 인프라에서 생성된 후보들을 재정렬하고 선택할 뿐이며, 프롬프트 구성 전의 정책 계층 역할을 합니다.

**허브 인지 재정렬은 연결성이 높은 노드를 제거하나요?**

아닙니다. 허브 노드는 관련성이 있을 때 자격을 유지하지만, 그 연결성이 더 이상 불균형한 영향을 주지는 않습니다.

**왜 Markdown과 JSON을 모두 지원하나요?**

Markdown은 LLM 컨텍스트와 사람의 검토에 직접 사용하기에 편리하고, JSON은 평가, 자동화, 감사, 그리고 다운스트림 시스템과의 통합을 지원합니다.

**팀은 재정렬이 도움이 되는지 어떻게 평가할 수 있나요?**

커뮤니티 커버리지, 허브 집중도, 최신성, 출처 완전성, 그리고 작업별 답변 품질을 기준으로, 증거 묶음을 수정되지 않은 최근접 이웃 기준선과 비교해 보세요.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/` 또는 `.claude/skills/parallaxpack-hub-bias-resistant-evidence-retrieval/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
