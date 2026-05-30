---
title: "Hermes Agent의 Tool Search: MCP 툴셋을 컨텍스트 낭비 없이 쓰는 법"
date: 2026-05-30T20:32:00+09:00
draft: false
description: "Nous Research의 Hermes Agent가 공개한 Tool Search는 MCP 서버가 많을 때 모든 툴 스키마를 컨텍스트에 올리는 대신 필요한 툴만 검색해 로드하는 점진적 공개(progressive disclosure) 방식이다. BM25 검색으로 툴을 찾고 3개의 브리지 툴로 실행한다."
tags: ["Hermes", "MCP", "AI에이전트", "툴검색", "컨텍스트최적화"]
cover:
  image: /images/hermes-tool-search-progressive-disclosure-cover.png
  alt: "Hermes Agent Tool Search progressive disclosure"
---

## 개요

MCP 서버를 여러 개 붙이면 편리하지만, 대가가 있다. 툴마다 JSON 스키마가 있고, 그 스키마들이 매 턴마다 컨텍스트 윈도우를 잠식한다. MCP 서버 15개 이상이면 툴 스키마만으로 전체 컨텍스트의 10%를 훌쩍 넘길 수 있다. Nous Research의 Hermes Agent가 공개한 **Tool Search**는 이 문제를 점진적 공개(progressive disclosure) 방식으로 해결한다. 필요한 툴의 스키마만 그때그때 로드하는 구조다.

## 핵심 요약

- Tool Search가 활성화되면 지연된 툴들이 3개의 브리지 툴(`tool_search`, `tool_describe`, `tool_call`)로 대체된다
- 기본 auto 모드: 지연 가능한 툴 스키마가 컨텍스트의 10% 이상을 차지할 때만 활성화
- Hermes 내장 툴(terminal, read_file 등)은 지연 대상이 아니고 항상 직접 로드됨
- 검색은 BM25 기반, 히트 없으면 툴 이름 substring 매칭으로 폴백
- Anthropic 측정치: Opus 4에서 툴 검색 적용 시 49% → 74% 정확도 향상 (26%는 여전히 검색 실패)
- 카탈로그는 매 어셈블리마다 재빌드 — 세션 간 상태 없음

## 작동 방식

Tool Search가 활성화된 턴에서 모델은 지연된 툴들 대신 3개의 브리지 툴만 본다.

```
tool_search(query, limit?)  — 지연 툴 카탈로그 검색
tool_describe(name)          — 특정 툴의 전체 스키마 로드
tool_call(name, arguments)   — 지연 툴 호출
```

실제 상호작용은 이렇게 흐른다.

```
모델: tool_search("create a github issue")
  → { matches: [{ name: "mcp_github_create_issue", ... }] }

모델: tool_describe("mcp_github_create_issue")
  → { parameters: { type: "object", properties: { ... } } }

모델: tool_call("mcp_github_create_issue", { title: "...", body: "..." })
  → { ok: true, issue_number: 42 }
```

`tool_call`이 실행될 때 Hermes는 브리지를 벗겨내고 실제 툴을 직접 호출한 것과 동일하게 처리한다. 사전·사후 훅, 가드레일, 승인 프롬프트 모두 `tool_call`이 아닌 **실제 툴 이름**에 대해 실행된다. CLI와 게이트웨이의 활동 피드에서도 브리지가 아닌 실제 툴 이름이 표시된다.

## 언제 활성화되나

기본 auto 모드에서 Tool Search는 지연 가능한 툴 스키마가 **활성 모델 컨텍스트 윈도우의 10% 이상**을 차지할 때만 켜진다. 이 판단은 매 턴 툴 어레이가 빌드될 때마다 재평가된다.

- MCP 서버가 적고 컨텍스트가 긴 모델 → Tool Search 미활성화
- MCP 서버 15개 이상 → 활성화 시작
- 세션 중 MCP 서버를 제거 → 다음 어셈블리에서 직접 노출으로 복귀

## 설정

```yaml
tools:
  tool_search:
    enabled: auto          # auto (기본값), on, off
    threshold_pct: 10      # auto 모드 기준 컨텍스트 비율
    search_default_limit: 5
    max_search_limit: 20
```

| 키 | 기본값 | 의미 |
|----|--------|------|
| enabled | auto | auto: 임계값 초과 시 활성화 / on: 항상 활성화 / off: 비활성화 |
| threshold_pct | 10 | auto 모드 진입 기준 컨텍스트 비율 (0–100) |
| search_default_limit | 5 | limit 미지정 시 반환 결과 수 |
| max_search_limit | 20 | 모델이 요청할 수 있는 최대 결과 수 (1–50) |

레거시 boolean 형태도 지원한다: `tool_search: true`는 `{enabled: auto}`와 동일하다.

## 사용하지 말아야 할 때

Tool Search는 **3개의 브리지 툴 스키마(약 300 토큰)와 최소 1번의 추가 라운드 트립**을 고정 비용으로 낸다. 툴이 많고 매 턴 소수만 쓴다면 명확한 이득이지만, 툴이 적다면 오히려 오버헤드다. auto 기본값이 이 판단을 자동으로 처리한다. `enabled: on`으로 강제하면 소규모 툴셋에서 턴마다 소폭 비용이 발생한다.

## 사라지지 않는 트레이드오프

이 트레이드오프는 프롬프트 캐시 무결성 원칙에서 나오는 것으로 어떤 점진적 공개 설계에도 내재한다.

**콜드 툴의 추가 라운드 트립:** 처음 쓰는 지연 툴은 검색·로드에 1~2번의 추가 모델 호출이 필요하다. 정적 측면의 토큰 절약은 실재하지만, 일부는 런타임에 돌려준다.

**지연 스키마의 캐시 미혜택:** 로드된 `tool_describe` 결과는 대화 히스토리에 들어가 이후 턴에서는 캐시되지만, 시스템 프롬프트 캐시 접두사의 혜택은 받지 못한다.

**모델 품질 의존성:** Tool Search는 모델이 원하는 툴에 대해 적절한 검색 쿼리를 생성할 수 있다고 가정한다. 소형 모델은 이를 덜 잘한다. Anthropic 수치(Opus 4에서 49% → 74%)는 상승을 보여주지만 26%는 여전히 검색 실패다.

**툴셋 편집 시 캐시 무효화:** 세션 중 툴을 추가·제거하면 브리지 툴 설명(지연 툴 수 포함)과 카탈로그가 변경되어 프롬프트 캐시가 무효화된다.

## 구현 세부사항

- **검색:** BM25, 툴 이름+설명+파라미터 이름 토크나이즈 기반. BM25가 양수 점수 없으면 툴 이름 substring 매칭으로 폴백
- **카탈로그는 무상태:** 매 어셈블리마다 현재 툴 목록에서 재빌드 — 세션 키드 Map 없음. 저장된 카탈로그가 라이브 툴 레지스트리와 drift하는 버그 방지
- **세션 범위 격리:** 서브에이전트나 제한된 게이트웨이 세션은 브리지를 통해서도 부여받지 않은 툴을 발견하거나 호출할 수 없음
- **JS 샌드박스 없음:** 일부 구현이 제공하는 코드 모드 대신 단순한 structured tools 방식 채택

## 실무자가 볼 핵심 포인트

MCP 서버를 많이 붙이는 팀에게 Tool Search는 즉시 적용할 수 있는 컨텍스트 절약 수단이다. auto 모드가 기본값이라 설정 없이도 필요한 순간에 자동으로 켜진다.

26%의 검색 실패율은 무시할 수 없는 숫자다. 툴 이름과 설명을 검색 친화적으로 작성하는 것이 중요하다. "github_create_issue"보다 "create_github_issue_from_title_and_body"처럼 기능이 명확하게 드러나는 이름이 BM25 검색에서 더 잘 잡힌다.

콜드 툴의 추가 라운드 트립이 신경 쓰인다면, 자주 쓰는 툴을 Hermes 내장 도구로 승격시키거나 핵심 MCP 툴 수를 줄이는 방향이 현실적이다. auto 모드가 꺼질 만큼 툴 수가 적다면 오버헤드 자체가 없다.

## 원문 출처

*원문: [Tool Search | Hermes Agent](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-search) — Nous Research (2026)*
