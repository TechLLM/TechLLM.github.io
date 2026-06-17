---
title: "허깅페이스 ARD 공개 — 에이전트가 도구를 직접 검색하는 시대"
date: 2026-06-18T02:28:00+09:00
draft: false
description: "허깅페이스가 마이크로소프트·구글·고대디와 함께 만든 ARD(Agentic Resource Discovery) 초안이 공개됐습니다. 도구를 미리 설치하지 않아도 에이전트가 런타임에 직접 찾아 호출할 수 있게 해주는 표준입니다. ai-catalog.json과 검색 REST API라는 두 축이 어떻게 동작하는지, hf discover 명령으로 실제로 어떻게 써보는지 정리했습니다."
cover:
  image: "/images/huggingface-ard-agentic-resource-discovery/huggingface-ard-agentic-resource-discovery-cover.png"
  alt: "에이전트가 여러 도구 카탈로그 사이를 가로질러 필요한 스킬을 직접 골라내는 일러스트"
  caption: ""
tags: ["허깅페이스", "ARD", "에이전트", "MCP", "AI-Agent", "툴디스커버리", "Open-Standard", "Skills"]
categories: ["AI-LLM"]
---

## 개요

지금까지 에이전트에게 도구를 붙이는 방식은 늘 **"먼저 설치하고 나중에 부른다"** 였습니다. 개발자가 설정 파일에 URL을 박아 넣고, 사용자가 플러그인 메뉴에서 일일이 연결해 주고, 그 결과를 모두 LLM의 컨텍스트 창에 욱여넣어 모델이 알아서 고르게 하는 구조였죠.

2026년 6월 17일 허깅페이스가 공개한 **ARD(Agentic Resource Discovery)** 초안은 이 흐름을 통째로 뒤집는 시도입니다. 마이크로소프트, 구글, 고대디, 허깅페이스가 함께 만든 오픈 표준으로, 에이전트가 **런타임에 직접 도구를 검색하고 호출**할 수 있게 발견 계층을 따로 떼어냈습니다.

## 핵심 요약

- ARD는 마이크로소프트·구글·고대디·허깅페이스가 공동으로 만든 **오픈 표준 초안**입니다(2026-06-17 공개).
- 도구 선택을 **LLM 바깥으로 끌어내** 별도 검색 시스템에 맡깁니다. 컨텍스트 창에 도구 설명을 잔뜩 붓던 관행을 끝내자는 제안입니다.
- 표준은 두 부분으로 이뤄집니다. **정적 매니페스트(`ai-catalog.json`)** 와 **동적 레지스트리 REST API(`POST /search`)**.
- 허깅페이스의 **Discover Tool**이 ARD의 레퍼런스 구현으로 먼저 공개됐고, MCP 서버·Skills·Spaces를 한 곳에서 검색합니다.
- `hf discover search "원하는 작업"` 한 줄이면 적합한 스킬이나 MCP 서버를 자연어로 바로 찾을 수 있습니다.

## 본문

### 발견 문제 — 왜 새 표준이 필요한가

기존 에이전트 생태계의 가장 큰 병목은 **"도구가 너무 많다"** 가 아니라 **"도구를 어떻게 찾아 붙이느냐"** 였습니다. 정적인 설정 파일에 URL을 박아두면 새 도구가 생길 때마다 사람이 끼어들어야 하고, 도구 설명을 컨텍스트에 잔뜩 부어 넣어 모델에게 골라 쓰게 하면 토큰 비용이 빠르게 불어납니다.

ARD가 제안하는 길은 단순합니다. 도구 선택을 LLM이 아닌 **별도의 검색 시스템**에 맡기는 겁니다. 발행자 신원, 대표 질의, 컴플라이언스 증명, 태그처럼 더 풍부한 신호로 능력을 색인하고, 자연어 검색을 위한 REST 엔드포인트를 노출합니다. 에이전트는 그때그때 필요한 의도(intent)로 후보를 추려 호출하면 됩니다.

### 두 가지 축 — 매니페스트와 검색 API

ARD는 두 갈래로 동작합니다.

첫째는 **정적 매니페스트**입니다. 발행자가 자기 도메인의 `well-known` 경로에 `ai-catalog.json`을 올려두면, 누구나 그 URL만 보고 능력 목록을 가져갈 수 있습니다. 허깅페이스의 경우 `https://huggingface.co/.well-known/ai-catalog.json` 한 줄이 시작점입니다.

둘째는 **동적 레지스트리 API**입니다. `POST /search` 한 엔드포인트로 자연어 질의를 던지면, 매체 타입(media type)별로 결과가 랭킹돼 돌아옵니다. 매체 타입은 사실상 "이 카탈로그가 무엇을 다루느냐"를 결정합니다.

- `application/ai-skill` (기본): Space의 `agents.md`를 감싼 `SKILL.md`
- `application/mcp-server+json`: MCP 서버 카탈로그 엔트리
- `application/vnd.huggingface.space+json`: Space 원본 메타데이터

매체 타입을 갈아끼우면 같은 엔드포인트가 스킬 카탈로그였다가, MCP 디렉터리였다가, Space 검색기로 변신합니다.

### 허깅페이스 Discover Tool — 첫 번째 실전

레퍼런스 구현인 **Hugging Face Discover Tool**은 Hub에 올라간 Spaces 가운데 Agent Skills가 붙은 것들을 묶어 검색해 줍니다. 두 가지 필터만 기본으로 둡니다.

1. 런타임 상태가 `RUNNING` 인 Space만 노출
2. 응답 매체 타입은 요청에 따라 결정

CLI로는 다음처럼 부릅니다.

```bash
# 허깅페이스 CLI 설치
uv tool install huggingface_hub

# 언어 모델 파인튜닝에 쓸 자원을 찾는다
hf discover search "Fine tune a language model"

# 이미지를 만들 MCP 서버를 찾는다
hf discover search "Generate an image" --json --kind mcp

# 다른 레지스트리도 같은 명령으로
hf discover search "Purchase aeroplane tickets" --registry-url <카탈로그-URL>
```

REST를 직접 부르고 싶다면 이렇게 보내면 됩니다.

```bash
curl -s https://huggingface-hf-discover.hf.space/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "text": "fine tune a sentence transformer",
      "filter": { "type": ["application/ai-skill"] }
    },
    "pageSize": 5
  }'
```

MCP 클라이언트를 그대로 붙이고 싶으면 `https://huggingface-hf-discover.hf.space/mcp`에 연결합니다. MCP 서버를 검색하는 MCP 서버라는 재미있는 구조죠.

### 설계의 결 — 프로토콜 위에 또 다른 프로토콜이 아니다

ARD가 신경 쓴 부분은 "MCP·Skills 같은 기존 포맷을 새 표준으로 갈아치우지 않는다"입니다.

- **프로토콜 무관**: 매체 타입으로 결과를 가르기 때문에 어떤 아티팩트 프로토콜이라도 같은 봉투(envelope)에 담깁니다.
- **연합(federation) 기본 지원**: 모드는 `auto`·`referrals`·`none`. 한 레지스트리가 다른 레지스트리의 결과를 함께 보여줄 수 있습니다.
- **표준 HTTP REST**: 특수 SDK가 필요하지 않습니다. 어떤 클라이언트도 직접 붙일 수 있습니다.
- **기존 포맷 위에 얹기**: MCP와 Skills를 감싸기만 하지 새 프로토콜을 강요하지 않습니다.

앞으로 사용자·조직 프로필 위에 정적 `ai-catalog.json`을 둘 수 있도록 확장할 계획이라, Space를 운영하는 누구나 같은 `well-known` URI 약속으로 자기 카탈로그를 광고할 수 있게 됩니다.

## 실무자가 볼 핵심 포인트

- **컨텍스트 비용을 줄여야 하는 팀**: 도구 카드를 컨텍스트에 모두 넣지 말고, `POST /search`로 그때그때 후보 3~5개만 끌어오는 구조를 시험해 볼 가치가 있습니다.
- **사내 도구 카탈로그를 가진 곳**: `ai-catalog.json`을 자기 도메인 `well-known` 경로에 올려두는 것만으로도 외부 에이전트가 자사 도구를 찾아 쓰게 만들 수 있습니다. 사내용 MCP 디렉터리가 있다면 연합(federation)으로 묶기 좋습니다.
- **MCP·Skill 둘 다 쓰는 팀**: 매체 타입을 바꿔 같은 검색기를 양쪽에 그대로 써먹을 수 있습니다. 검색 인프라를 한 번만 만들어 두면 됩니다.
- **에이전트 워크플로 설계자**: "필요할 때 찾아 붙이는" 동적 도구 바인딩 패턴을 가정하고 흐름을 다시 그려보면, 사용자가 플러그인 메뉴를 일일이 켜는 단계를 통째로 들어낼 수 있습니다.
- **표준 자체가 아직 초안**: 사양은 `agenticresourcediscovery.org`, 레퍼런스 코드는 `github.com/huggingface/hf-discover`에 있습니다. 의견을 보태고 싶다면 지금이 가장 좋은 타이밍입니다.

## 원문 출처

[원문 보기](https://huggingface.co/blog/agentic-resource-discovery-launch) — Ben Burtenshaw, Shaun Smith / Hugging Face Blog, 2026-06-17
