---
title: "xAI, 그록 빌드에 플러그인 마켓플레이스를 붙였다 — 첫 라인업 6개와 새 보안 모델"
date: 2026-06-12T08:39:40+09:00
draft: false
description: "xAI가 터미널 코딩 에이전트 '그록 빌드'에 플러그인 마켓플레이스를 열었습니다. MongoDB·Vercel·Sentry·Chrome DevTools·Cloudflare·Superpowers가 첫 파트너이고, 모든 원격 플러그인은 40자 커밋 SHA로 고정됩니다."
cover:
  image: "/images/grok-build-plugin-marketplace-launch/grok-build-plugin-marketplace-launch-cover.png"
  alt: "그록 빌드의 /marketplace 화면을 캡처한 이미지. 라인업으로 올라온 플러그인 카드들이 나열돼 있다."
  caption: "이미지: marktechpost"
tags: ["xAI", "Grok", "Grok Build", "Plugin Marketplace", "MCP", "AI 에이전트", "코딩 에이전트", "Cloudflare", "MongoDB"]
categories: ["LLM-info"]
---

## 개요

xAI가 자사 터미널 코딩 에이전트인 **그록 빌드(Grok Build)** 안에 플러그인 마켓플레이스를 열었습니다. 발표는 2026년 6월 11일, 베타 단계입니다. 그동안은 MCP 서버, 슬래시 커맨드, 훅, LSP 같은 도구를 일일이 손으로 연결해 써야 했는데, 이제는 카탈로그에서 하나만 고르면 묶음으로 한꺼번에 들어옵니다. 카탈로그 첫 라인업은 MongoDB, Vercel, Sentry, Chrome DevTools, Cloudflare, 그리고 Superpowers 여섯 개. 안에서 어떤 게 어떻게 묶여 들어오는지, 왜 이걸 굳이 마켓플레이스 형태로 풀었는지 정리해 봅니다.

## 핵심 요약

- **하나로 묶이는 6가지 컴포넌트** — 스킬, 슬래시 커맨드, 서브에이전트, 훅, MCP 서버, LSP 서버. 한 플러그인 안에 이 여섯 종류가 폴더 규약대로 들어 있습니다.
- **설치는 두 가지 길** — `/marketplace`로 들어가 `i`키로 설치하거나, 셸에서 `grok plugin install <name> --trust`. `--trust` 플래그는 실행 권한을 명시적으로 넘기는 장치입니다.
- **공급망 보안의 핵심은 SHA 핀** — 모든 원격 플러그인은 40자 소문자 커밋 SHA에 고정되고, 그록 빌드가 클론 직후 `git rev-parse HEAD == sha`를 검증합니다. 강제 푸시로 코드가 슬쩍 바뀌어도 잡힙니다.
- **1st-party vs 3rd-party 명시 분리** — xAI가 직접 만든 플러그인은 따로 표기됩니다. 외부 플러그인은 검증 책임이 사용자에게 있다는 점도 약관에 못 박았습니다.
- **카탈로그 등록은 PR로** — `.grok-plugin/marketplace.json`에 PR을 보내면 됩니다. 커뮤니티 기여 진입 장벽이 낮은 편입니다.
- **접근 조건은 유료 구독** — 슈퍼그록(SuperGrok) 또는 X 프리미엄 플러스가 있어야 그록 빌드 자체를 쓸 수 있습니다.

## 본문

### 한 플러그인 안에 묶이는 것들

그록 빌드 플러그인은 디렉터리 규약을 그대로 따릅니다. 스킬은 `skills/` 아래, 커맨드는 `commands/`, 서브에이전트는 `agents/`, 훅은 `hooks/hooks.json`, MCP 서버 설정은 `.mcp.json`, LSP 서버 설정은 `.lsp.json` 식입니다. 메타데이터나 경로 오버라이드가 필요하면 `plugin.json` 매니페스트를 옵션으로 두면 됩니다.

이게 왜 의미가 있냐면, 그동안 같은 흐름을 만들려면 사용자가 직접 MCP 서버를 등록하고, 그 MCP를 호출할 슬래시 커맨드를 짜고, 그 커맨드를 자동으로 끼워 넣을 훅을 따로 세팅해야 했기 때문입니다. 플러그인 한 묶음이 들어오면 그 세 가지가 같은 폴더 구조 안에서 이미 연결돼 있습니다.

### 설치와 신뢰 모델

설치는 두 가지 경로입니다. 첫째, 그록 빌드 안에서 `/marketplace`를 치고 들어가 카탈로그를 둘러본 다음, 원하는 항목에 커서를 두고 `i`를 누르면 설치됩니다. 둘째, 셸에서 바로 `grok plugin install <name> --trust`. `--trust` 플래그가 필요한 이유는 분명합니다. 플러그인은 결국 코드를 실행하고 시스템 데이터에 접근하기 때문에, 신뢰를 명시적으로 부여하지 않으면 설치를 막아 둔 겁니다.

### SHA 핀 — 진짜 핵심

마켓플레이스 보안 모델의 중심은 **40자 커밋 SHA**입니다. 카탈로그 항목마다 소스 URL과 함께 정확한 커밋 SHA가 박혀 있고, 그록 빌드는 저장소를 클론한 직후 `git rev-parse HEAD`로 받은 값이 카탈로그에 적힌 SHA와 같은지 확인합니다. 같은 브랜치라도 강제 푸시가 한 번 들어가면 HEAD가 바뀌므로, 그 시점에서 설치가 거부됩니다. 저장소가 통째로 탈취되어도, 다시 PR을 받아 새 SHA로 카탈로그를 업데이트하지 않는 한 사용자에게 자동으로 새 코드가 들어가지 않습니다.

물론 SHA를 검증한다고 해서 **그 안에 든 코드가 안전하다**는 보장은 아닙니다. xAI도 이 점을 분명히 합니다. 1st-party 플러그인은 xAI가 직접 만들고 운영하지만, 3rd-party는 "있는 그대로(as-is)" 제공이고 동작도 검증하지 않습니다. 즉, SHA는 "코드가 도중에 바꿔치기 되지 않았다"만 보증하고, 코드 자체의 행동은 사용자가 판단해야 합니다.

### 첫 라인업 6종

런칭 시점 라인업은 자주 쓰는 클라우드·관측·브라우저 도구가 잘 섞여 있습니다.

- **MongoDB** — 컬렉션 탐색, 쿼리 최적화, 데이터 미리보기를 에이전트가 직접 수행
- **Vercel** — 배포 트리거, 빌드 상태 확인, 도메인 구성
- **Sentry** — 프로덕션 에러 추적, 스택트레이스 해석
- **Chrome DevTools** — 라이브 브라우저 제어, 성능 트레이스 기록, 네트워크 요청 검사
- **Cloudflare** — Workers, Durable Objects 등 엣지 서비스 관리
- **Superpowers** — 인기 있는 에이전트 워크플로 패키지

### 커뮤니티 등록 흐름

새 플러그인을 카탈로그에 넣으려면 `xai-org/plugin-marketplace` 저장소의 `.grok-plugin/marketplace.json`에 항목을 추가하는 PR을 보내면 됩니다. 원격 엔트리에는 이름·설명·카테고리·소스 URL·커밋 SHA·홈페이지·키워드가 들어갑니다. 그리고 `python3 scripts/generate-plugin-index.py`를 돌려 `plugin-index.json`을 다시 생성합니다. 이 인덱스가 실제 컴포넌트가 어디 들어 있는지 기록해 두는 매핑 파일입니다.

## 실무자가 볼 핵심 포인트

- **MCP 단독 등록이 줄어듭니다** — 지금까지 MCP 서버를 따로 정의하고 커맨드를 별도로 매핑하던 패턴이, 한 플러그인 묶음으로 자연스럽게 흡수됩니다. 같은 서비스에 대해 MCP 정의가 두 군데로 흩어지지 않게 정리해 두는 편이 좋습니다.
- **SHA 핀이 진짜 보안선** — 사내 플러그인을 만든다면 카탈로그 등록 시 반드시 정확한 커밋 SHA를 같이 박아두세요. 브랜치 이름만으로는 보호되지 않습니다.
- **`--trust` 플래그는 흔적이 남는 동의** — 자동화 스크립트로 설치를 돌릴 때 `--trust`를 무심코 박지 말고, 도입 검토 단계에서 별도 절차(코드 리뷰, 라이선스 확인)를 한 번 거치고 나서 통과시키는 흐름을 만들어 두는 편이 안전합니다.
- **3rd-party는 "as-is"라는 사실 잊지 말기** — 보안 검토는 결국 사용자 몫입니다. 사내 도입이라면 한 번이라도 코드를 훑고 들어가는 절차를 잡아두는 게 맞습니다.
- **베타 기간 가격 정책 확인** — 그록 빌드 자체가 슈퍼그록 또는 X 프리미엄 플러스 구독에 묶여 있습니다. 팀 단위 도입이라면 좌석 비용을 미리 계산해 두세요.

## 원문 출처

- Marktechpost — [xAI Ships Grok Build Plugin Marketplace With MongoDB, Vercel, Sentry, Chrome DevTools, Cloudflare, and Superpowers Plugins at Launch](https://www.marktechpost.com/2026/06/11/xai-ships-grok-build-plugin-marketplace-with-mongodb-vercel-sentry-chrome-devtools-cloudflare-and-superpowers-plugins-at-launch/)
- 공식 발표: [x.ai/news/grok-plugin-marketplace](https://x.ai/news/grok-plugin-marketplace)
- 카탈로그 저장소: [github.com/xai-org/plugin-marketplace](https://github.com/xai-org/plugin-marketplace)
