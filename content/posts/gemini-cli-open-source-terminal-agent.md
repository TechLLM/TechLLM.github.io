---
title: "Gemini CLI — 구글이 터미널에 Gemini를 직접 심었다"
description: "Google이 오픈소스로 공개한 Gemini CLI. 하루 1,000회 무료, 100만 토큰 컨텍스트, MCP 지원까지 — Claude Code의 강력한 경쟁자가 나타났다."
date: 2026-05-23T07:52:00+09:00
draft: false
tags: ["GeminiCLI", "AI에이전트", "터미널AI", "구글AI", "개발자도구", "MCP", "오픈소스"]
cover:
  image: /images/gemini-cli-open-source-terminal-agent-cover.png
  alt: "터미널 화면 속 Gemini CLI가 코드를 분석하는 장면"
---

## 개요

구글이 터미널용 AI 에이전트를 오픈소스로 공개했다. `gemini-cli`는 Gemini 모델을 터미널에서 직접 쓸 수 있게 해주는 에이전트로, 코드 이해·생성·자동화·MCP 연동까지 지원한다. 무료 티어는 분당 60회, 하루 1,000회 요청이 가능하고 100만 토큰 컨텍스트 윈도우를 제공한다. Claude Code와 직접 경쟁하는 포지셔닝이다.

---

## 핵심 요약

- **무료 티어**: Google 계정으로 로그인 시 분당 60회, 하루 1,000회 무료
- **모델**: Gemini 2.5 Flash/Pro, 100만 토큰 컨텍스트
- **설치**: `npx @google/gemini-cli` 또는 `brew install gemini-cli`
- **빌트인 도구**: Google Search 그라운딩, 파일 작업, 셸 명령, 웹 페치
- **확장성**: MCP(Model Context Protocol) 서버 지원
- **라이선스**: Apache 2.0 오픈소스
- **GitHub Action**: PR 리뷰, 이슈 트리아지 자동화 지원

---

## 본문

### Claude Code와 어깨를 나란히

지금 터미널 AI 에이전트 시장에는 세 플레이어가 있다. Anthropic의 Claude Code, GitHub Copilot CLI, 그리고 이제 Google의 Gemini CLI. 세 제품 모두 자연어로 코드를 이해하고 수정하며, 터미널 명령을 실행하고, 외부 도구와 연동한다.

Gemini CLI가 특이한 점은 **완전 오픈소스(Apache 2.0)** 라는 것이다. 소스코드가 공개돼 있고 누구나 포크하거나 기여할 수 있다. Claude Code와 Copilot이 프로프라이어터리 제품인 것과 대비된다.

### 무료 티어의 위력

Gemini CLI의 가장 강력한 무기는 무료 티어다. Google 계정으로 로그인하면 별도 결제 없이 분당 60회, 하루 1,000회 요청이 가능하다. Gemini API 키를 쓰면 무료 1,000회/일에 추가로 사용량 기반 유료 업그레이드도 된다.

기업 환경이라면 Vertex AI 연동으로 엔터프라이즈 보안·컴플라이언스 요건을 충족하면서 더 높은 한도를 쓸 수 있다.

### 설치 한 줄

```bash
# 설치 없이 바로 실행
npx @google/gemini-cli

# 전역 설치
npm install -g @google/gemini-cli

# macOS/Linux
brew install gemini-cli
```

실행 후 처음엔 Google 계정 로그인 또는 API 키 입력을 선택한다. 로그인하면 바로 쓸 수 있다.

### 핵심 기능

**코드 이해 및 생성**
대규모 코드베이스를 100만 토큰 컨텍스트로 한 번에 탐색하고 분석할 수 있다. PDF, 이미지, 스케치를 입력으로 앱을 생성하는 멀티모달 기능도 포함된다.

```bash
# 기존 프로젝트 분석
cd my-project && gemini
> 어제 들어간 변경 사항 전체 요약해줘

# 새 프로젝트 시작
cd new-project && gemini
> FAQ.md를 활용해 질문에 답하는 Discord 봇 만들어줘
```

**빌트인 도구**
- Google Search 그라운딩 — 실시간 정보를 쿼리에 반영
- 파일 시스템 작업 — 읽기/쓰기/편집
- 셸 명령 실행
- 웹 페치

**GEMINI.md — 프로젝트 컨텍스트 파일**
Claude Code의 CLAUDE.md처럼, 프로젝트 루트에 `GEMINI.md`를 두면 Gemini CLI가 매 세션 자동으로 참고한다. 코딩 컨벤션, 아키텍처 문서, 팀 규칙 등을 넣어두면 매번 설명할 필요가 없다.

**체크포인팅**
대화 세션을 저장하고 나중에 이어서 작업할 수 있다. 복잡한 리팩터링이나 장시간 디버깅 세션을 중단했다가 재개하는 데 유용하다.

**MCP 서버 연동**
`~/.gemini/settings.json`에 MCP 서버를 설정하면 GitHub, Slack 등 외부 도구를 Gemini CLI에서 직접 호출할 수 있다.

```text
> @github 내 열린 PR 목록 보여줘
> @slack 오늘 커밋 요약 보내줘
```

### 릴리즈 채널

| 채널 | 주기 | 특성 |
|------|------|------|
| `latest` (stable) | 매주 화요일 | 검증 완료, 운영 권장 |
| `preview` | 매주 화요일 | 미검증, 테스트용 |
| `nightly` | 매일 자정 | main 브랜치 스냅샷 |

### GitHub Action 연동

Gemini CLI는 GitHub Actions 워크플로우에서도 쓸 수 있다. PR 리뷰 자동화, 이슈 분류·우선순위화, `@gemini-cli` 멘션으로 온디맨드 도움 요청 등이 가능하다. CI/CD 파이프라인에 AI를 직접 녹여 넣는 방향이다.

### 비대화형(헤드리스) 모드

스크립트에서 쓸 때는 `-p` 플래그로 프롬프트를 바로 넘길 수 있다.

```bash
# 단순 텍스트 응답
gemini -p "이 코드베이스 아키텍처 설명해줘"

# JSON 구조화 출력
gemini -p "테스트 실행하고 배포해" --output-format json

# 실시간 스트리밍 (장시간 작업 모니터링)
gemini -p "테스트 실행하고 배포해" --output-format stream-json
```

---

## 실무자가 볼 핵심 포인트

1. **무료 1,000회/일은 개인 개발자에게 실질적으로 충분하다** — Claude Code 유료 구독($20/월)과 달리 Google 계정만 있으면 바로 쓸 수 있다. 사이드 프로젝트나 학습 용도로 진입 장벽이 매우 낮다.
2. **100만 토큰 컨텍스트가 핵심 차별화** — 대규모 모노레포나 레거시 코드베이스를 분석할 때 컨텍스트 제한이 없다시피 하다. 분할 로딩 없이 전체 코드베이스를 한 번에 넘길 수 있다.
3. **MCP 생태계 공유** — Claude Code와 Gemini CLI 모두 MCP를 지원하므로 같은 MCP 서버를 두 에이전트에서 재사용할 수 있다. MCP 도구 투자가 특정 벤더에 종속되지 않는다.
4. **오픈소스 포크 가능성** — Apache 2.0이므로 사내 보안 정책상 외부 AI 에이전트 사용이 제한된 환경에서도 자체 배포하거나 수정해 쓸 수 있다. 엔터프라이즈 셀프호스팅 시나리오가 현실적으로 열린다.

---

원문: <a href="https://github.com/google-gemini/gemini-cli">google-gemini/gemini-cli — GitHub</a>
