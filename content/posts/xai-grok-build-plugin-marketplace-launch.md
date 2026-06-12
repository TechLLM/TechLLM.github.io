---
title: "그록 빌드 플러그인 마켓플레이스 분해 — 디렉터리 한 줄로 끝나는 6종 통합"
date: 2026-06-12T21:59:00+09:00
draft: false
description: "xAI가 터미널 코딩 에이전트 그록 빌드에 플러그인 마켓플레이스를 열었습니다. 한 폴더에 스킬·커맨드·서브에이전트·훅·MCP·LSP 여섯 가지가 묶이고, 40자 SHA 핀으로 공급망 위험을 닫았습니다. MongoDB·Vercel·Sentry·Chrome DevTools·Cloudflare·Superpowers가 첫 라인업."
cover:
  image: "/images/xai-grok-build-plugin-marketplace-launch/xai-grok-build-plugin-marketplace-launch-cover.png"
  alt: "터미널 안에 떠 있는 그록 빌드 마켓플레이스 카드들을 손그림으로 표현한 일러스트"
  caption: "이미지 생성: TechLLM"
tags: ["xAI", "Grok Build", "Plugin Marketplace", "MCP", "코딩 에이전트", "공급망 보안", "Cloudflare", "MongoDB"]
categories: ["LLM-info"]
---

## 개요

xAI가 자사 터미널 코딩 에이전트 **그록 빌드(Grok Build)** 안에 플러그인 마켓플레이스를 열었습니다. 6월 11일 발표, 베타 단계입니다. 그동안 MCP 서버, 슬래시 커맨드, 훅, LSP 같은 부품은 각각 따로 손으로 엮어야 했는데, 이제는 카탈로그에서 하나 고르면 통째로 묶여 들어옵니다. 마켓플레이스 자체는 `xai-org/plugin-marketplace`라는 공개 깃허브 리포지터리고, 그록 빌드는 여기를 색인 삼아 진짜 플러그인 소스를 끌어옵니다. 단순한 "또 하나의 스토어"가 아니라, 에이전트 확장의 폴더 규약을 못 박아 둔 시도라는 점이 이번 발표의 핵심입니다.

## 핵심 요약

- **한 폴더 = 여섯 종류의 부품**. 스킬, 슬래시 커맨드, 서브에이전트, 훅, MCP 서버, LSP 서버. 각자 정해진 하위 디렉터리에 들어가고 `plugin.json`으로 묶입니다.
- **설치는 두 길**. 그록 빌드 안에서 `/marketplace`를 띄워 `i`키로 깔거나, 셸에서 `grok plugin install <name> --trust`. `--trust`는 "이 코드 실행 권한 줍니다"라는 명시적 동의 장치입니다.
- **공급망 핵심은 40자 SHA 핀**. 원격 플러그인은 전부 커밋 SHA에 고정되고, 클론 직후 `git rev-parse HEAD`로 한 번 더 검증합니다. 강제 푸시로 코드가 슬쩍 바뀌어도 잡힙니다.
- **1st-party / 3rd-party 분리 명시**. xAI가 만든 것과 외부 기여물을 카탈로그에서 분리해 두고, 외부 플러그인은 "AS-IS"라고 못 박았습니다.
- **카탈로그 진입은 PR 한 장**. `.grok-plugin/marketplace.json`에 항목을 추가해 PR을 보내면 됩니다. CI가 `--check`로 `plugin-index.json` 신선도까지 본 뒤 머지됩니다.
- **첫 라인업 6개**. MongoDB, Vercel, Sentry, Chrome DevTools, Cloudflare, Superpowers.
- **사용 조건은 유료 티어**. 그록 빌드 자체가 SuperGrok 또는 X Premium Plus 가입자에게만 열려 있습니다.

## 본문

### 한 플러그인 안에 무엇이 들어가는가

이번 마켓플레이스가 다른 'MCP 서버 모음'과 다른 지점이 여기서 갈립니다. 플러그인은 단순히 MCP 서버를 묶어 놓은 패키지가 아닙니다. 여섯 가지 부품이 한 디렉터리 안에 규약대로 자리 잡고, 필요한 것만 골라 담을 수 있게 돼 있습니다.

| 부품 | 위치 | 역할 |
|---|---|---|
| 스킬 | `skills/` | `SKILL.md`로 기술된 능력 |
| 슬래시 커맨드 | `commands/` | `/명령` 형태 단축 입력 |
| 서브에이전트 | `agents/` | 위임용 에이전트 정의 |
| 훅 | `hooks/hooks.json` | 라이프사이클 훅 |
| MCP 서버 | `.mcp.json` | MCP 서버 설정 |
| LSP 서버 | `.lsp.json` | 언어 서버 설정 |

선택 사항인 `plugin.json` 매니페스트로 메타데이터를 얹거나 경로를 재정의할 수 있습니다. 결과적으로 `grok plugin install mongodb` 한 줄이 셸 명령, 슬래시 커맨드, 자동 호출되는 훅, 그리고 백엔드 MCP 서버를 한 번에 다 깔아 줍니다. "한 줄짜리 통합"을 가능하게 만든 게 폴더 규약이라는 얘기입니다.

### 마켓플레이스의 동작 흐름

마켓플레이스는 디스커버리 레이어 역할만 합니다. `xai-org/plugin-marketplace` 리포지터리 안의 `marketplace.json`이 색인이고, 항목마다 진짜 플러그인이 사는 깃 URL과 커밋 SHA를 들고 있습니다.

```json
{
  "name": "my-plugin",
  "description": "What the plugin does.",
  "category": "development",
  "source": {
    "source": "url",
    "url": "https://github.com/my-org/my-plugin.git",
    "sha": "0000000000000000000000000000000000000000"
  },
  "homepage": "https://github.com/my-org/my-plugin",
  "keywords": ["my-plugin"]
}
```

PR로 항목을 추가하면 CI가 `python3 scripts/generate-plugin-index.py --check`로 `plugin-index.json`이 신선한지 검증합니다. 색인 파일을 손으로 고치는 건 금지고, 스크립트로 재생성해야 머지가 됩니다. 등록 자체는 가볍지만, 머지 게이트가 이 한 줄로 안전하게 작동합니다.

### SHA 핀의 의미

이번 설계에서 가장 영리한 부분은 SHA 핀입니다. 색인의 모든 원격 항목은 40자 소문자 커밋 해시에 고정돼 있습니다. 그록 빌드는 리포를 클론하고 나서 `git rev-parse HEAD == sha`를 한 번 더 확인합니다. 이 검증이 없다면 어떤 일이 가능할까요. 누군가 리포지터리 주인 자격을 탈취해 강제 푸시로 코드를 바꿔치기해도, 사용자는 영문도 모르고 새 코드를 받게 됩니다. SHA 핀은 그 경로를 설치 시점에 닫아 버립니다. 핀이 가리키는 커밋과 다른 게 들어오면 설치가 멈춥니다.

대신 xAI가 분명히 선을 그어 놓은 부분도 있습니다. "핀이 가리키는 커밋이 정확히 들어왔다"는 사실까지는 보장하지만, "그 커밋이 한 일이 안전하다"는 보장은 아닙니다. 1st-party와 3rd-party를 카탈로그에서 분리한 이유도 같습니다. 외부 플러그인은 검토 책임이 사용자에게 있고, "AS-IS"로 제공된다는 점을 약관에 명시했습니다.

### 첫 라인업 6개를 실제 시나리오로 보면

발표 시점의 라인업은 여섯 개입니다. 시나리오로 풀면 더 와 닿습니다.

- **MongoDB** — 쿼리가 느린 컬렉션을 발견한 데이터 엔지니어가 `grok plugin install mongodb` 후 "이 쿼리 인덱스 한번 점검해 줘"라고 시키는 흐름. 컬렉션 탐색, 쿼리 최적화, 메타데이터 관리 명령이 한 번에 들어옵니다.
- **Vercel** — 프런트엔드 개발자가 빌드 실패 상태를 셸에서 바로 확인하고, 도메인 설정까지 챙겨야 할 때 유용합니다.
- **Sentry** — 온콜이 새벽에 스택 트레이스를 받아들고 그록 빌드에 던지면, 함수 호출 그래프와 최근 릴리스 비교까지 같이 끌어옵니다.
- **Chrome DevTools** — 라이브 브라우저를 제어해 네트워크 요청을 들여다보고 성능 트레이스를 녹화합니다. 렌더링 회귀 추적 시 강력한 카드입니다.
- **Cloudflare** — Workers와 Durable Objects 같은 자원을 다루는 스킬들이 들어 있습니다.
- **Superpowers** — 에이전트 주도 워크플로를 묶어 놓은 패키지로, 다른 다섯 개와 결이 다른 메타 플러그인입니다.

요지는 단순합니다. 각자의 도구 안에서 일하던 흐름을 그록 빌드 한 화면으로 끌고 와서 에이전트에게 위임하기 좋게 만들었다는 것.

### 기존 MCP 통합과의 차이

기존 MCP 직접 통합 방식과 비교해 보면 차이가 또렷합니다.

| 항목 | 그록 빌드 마켓플레이스 | 직접 MCP 연결 |
|---|---|---|
| 묶음 단위 | 스킬·커맨드·에이전트·훅·MCP·LSP | MCP 서버만 |
| 탐색·설치 | 터미널 안에서 `/marketplace` | 수동 설정 편집 |
| 커밋 SHA 검증 | 설치 시 강제 | 기본 없음 |
| 공개 카탈로그 | PR 기반 오픈 카탈로그 | 별도 없음 |
| 업데이트 | `grok plugin` 흐름 | 수동 |

MCP는 어디까지나 한 종류의 부품이고, 마켓플레이스는 부품을 묶어 배포하는 상위 레이어라는 그림이 그려집니다.

## 실무자가 볼 핵심 포인트

- 자체 사내 에이전트를 굴리고 있다면, 이 폴더 규약을 그대로 베껴 와 사내 카탈로그를 만드는 게 가장 빠른 활용법입니다. `marketplace.json` 색인과 SHA 핀 검증만 흉내 내도 공급망 위험을 한 단계 낮춥니다.
- **3rd-party 플러그인 검증은 결국 우리 몫**. 핀은 "내려받은 커밋이 맞다"를 보장할 뿐입니다. 사내 도입 전엔 코드 리뷰와 권한 범위 확인 단계를 별도로 두는 게 안전합니다.
- 그록 빌드 라이선스가 유료 티어에 묶여 있어, 평가 단계에서는 다른 에이전트(예: Claude Code)로 같은 구조를 따라 해 보고 폴더 규약의 적합성만 검증하는 방법이 비용 효율적입니다.
- 마지막으로, `--trust` 플래그를 "당연한 기본값"으로 깔지 마세요. 플러그인은 코드와 시스템 데이터를 만질 수 있는 객체입니다. 사람이 한 번 확인해 주는 단계는 남겨 두는 게 좋습니다.

## 원문 출처

- [marktechpost — xAI Ships Grok Build Plugin Marketplace](https://www.marktechpost.com/2026/06/11/xai-ships-grok-build-plugin-marketplace-with-mongodb-vercel-sentry-chrome-devtools-cloudflare-and-superpowers-plugins-at-launch/)
- [xAI 공식 발표](https://x.ai/news/grok-plugin-marketplace)
- [xai-org/plugin-marketplace 깃허브](https://github.com/xai-org/plugin-marketplace)
