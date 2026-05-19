---
title: "Paperclip AI로 ‘제로 휴먼 컴퍼니’를 만드는 법: 기능, 설치, 운영 포인트 정리"
date: 2026-05-01T21:05:00+09:00
draft: false
description: "Metics Media의 Paperclip AI 튜토리얼 영상을 바탕으로, Paperclip이 무엇인지, 어떤 기능을 제공하는지, VPS·Docker·npx 기반 설치 방법과 운영 시 주의할 점을 정리한다."
cover:
  image: "/images/paperclip-ai-zero-human-company-cover.jpg"
  alt: "Paperclip AI Tutorial YouTube thumbnail"
  caption: "Source: Metics Media / YouTube"
tags:
  - PaperclipAI
  - AIAgent
  - ZeroHumanCompany
  - OpenClaw
  - ClaudeCode
  - Codex
  - Docker
  - VPS
  - AI Agent
  - AI 개발 & 인프라
categories: ["AI-LLM"]

---

출처: Metics Media YouTube  
문서유형: 영상 해설  
#PaperclipAI #AIAgent #ZeroHumanCompany #OpenClaw #ClaudeCode #Codex

## 핵심 요약

이 영상은 **Paperclip AI로 ‘제로 휴먼 컴퍼니’를 세팅하는 전 과정**을 보여줍니다. 여기서 말하는 제로 휴먼 컴퍼니는 사람이 완전히 사라진다는 뜻이라기보다, 사람이 매번 프롬프트를 던지는 방식에서 벗어나 **목표, 조직도, 예산, 업무 티켓, 승인 흐름을 가진 AI 에이전트 조직**을 운영한다는 뜻에 가깝습니다.

Paperclip은 단일 챗봇이나 코딩 에이전트가 아닙니다. 공식 설명처럼 “OpenClaw가 직원이라면, Paperclip은 회사”에 가깝습니다. Claude Code, Codex, OpenClaw, Cursor, Bash, HTTP webhook 같은 여러 실행 주체를 하나의 조직 안에 배치하고, CEO·CTO·마케터·리서처 같은 역할을 부여한 뒤, 목표를 향해 일하게 만드는 **AI 노동의 컨트롤 플레인**입니다.

![Paperclip AI Tutorial](/images/paperclip-ai-zero-human-company-cover.jpg)

## Paperclip이 해결하려는 문제

AI 에이전트를 몇 개만 써도 금방 문제가 생깁니다. Claude Code 탭은 여러 개 열려 있고, 어떤 에이전트가 어떤 작업을 맡았는지 흐려지고, 재부팅하면 맥락이 끊기고, 토큰 비용은 어디서 새는지 알기 어렵습니다.

Paperclip은 이 문제를 “회사 운영” 모델로 풀어냅니다. 사용자는 회사의 목표를 정하고, CEO 에이전트를 고용하고, CEO가 필요한 팀원을 제안하면 승인합니다. 각 작업은 티켓으로 남고, 에이전트의 판단·도구 호출·실행 로그가 추적됩니다. 즉, 단순히 AI에게 일을 시키는 도구가 아니라 **일을 배분하고, 감사하고, 예산을 통제하는 운영 계층**입니다.

## 핵심 기능 정리

Paperclip의 기능은 크게 여덟 가지로 볼 수 있습니다.

첫째, **Bring Your Own Agent**입니다. Paperclip은 특정 모델이나 에이전트 런타임에 묶이지 않습니다. Claude Code, OpenClaw, Codex, Cursor, Python 스크립트, shell command, HTTP bot처럼 heartbeat를 받을 수 있는 실행 주체라면 조직에 “고용”할 수 있습니다.

둘째, **조직도와 역할 관리**입니다. 에이전트는 그냥 프롬프트 묶음이 아니라 직책, 책임, 보고 라인, 예산을 가진 구성원으로 관리됩니다. CEO는 목표를 쪼개고, CTO나 마케팅 에이전트에게 일을 위임할 수 있습니다.

셋째, **목표 정렬**입니다. 모든 작업은 회사 목표, 프로젝트 목표, 에이전트 목표로 이어집니다. “무엇을 하라”만 전달하는 게 아니라 “왜 이 일을 하는지”까지 맥락으로 전달되기 때문에 장기 작업에서 방향을 잃을 가능성이 줄어듭니다.

넷째, **heartbeat 실행**입니다. 에이전트는 정해진 간격으로 깨어나 현재 업무를 확인하고, 필요한 작업을 수행하고, 로그를 남긴 뒤 다시 대기합니다. 영상에서는 CEO agent heartbeat, task assignment, dashboard log 확인 흐름이 핵심으로 다뤄집니다.

다섯째, **예산 통제**입니다. 에이전트별 월간 예산을 설정할 수 있고, 예산에 도달하면 자동으로 멈춥니다. 많은 에이전트가 병렬로 움직일수록 토큰 비용이 빠르게 커질 수 있기 때문에, 이 기능은 실험용 장난감과 실제 운영 도구를 가르는 중요한 지점입니다.

여섯째, **티켓과 감사 로그**입니다. Paperclip의 작업은 이슈·티켓 중심으로 남습니다. 누가 무엇을 지시했고, 어떤 도구를 호출했고, 어떤 판단을 했는지 추적할 수 있습니다. 실패한 작업을 디버깅할 때도 로그가 먼저 봐야 할 곳입니다.

일곱째, **거버넌스**입니다. 사용자는 일종의 이사회 역할을 합니다. 고용 요청을 승인하거나 거부하고, 전략을 검토하고, 에이전트를 일시정지하거나 종료할 수 있습니다. 자율성은 기본값이 아니라 사용자가 허용하는 권한입니다.

여덟째, **멀티 컴퍼니**입니다. 하나의 Paperclip 배포에서 여러 회사를 운영할 수 있고, 회사별 데이터는 분리됩니다. 콘텐츠 회사, 개발 에이전시, 리서치 팀, 세일즈 팀처럼 서로 다른 AI 조직을 한 컨트롤 플레인에서 다루는 구조입니다.

## 설치 방법: 가장 쉬운 경로

영상은 VPS에 Paperclip을 올려 24시간 동작하는 환경을 만드는 흐름을 중심으로 설명합니다. 가장 단순한 경로는 Hostinger 같은 VPS에서 Docker 템플릿을 사용해 Paperclip을 배포하는 방식입니다.

기본 흐름은 이렇습니다.

1. VPS를 준비합니다. 작은 실험은 2 vCPU, 4GB RAM, 50GB SSD 정도로 시작할 수 있습니다.
2. Docker 기반 Paperclip 템플릿 또는 Docker Compose로 애플리케이션을 배포합니다.
3. 브라우저에서 `http://서버IP:3100` 형태로 Paperclip dashboard에 접속합니다.
4. 관리자 계정을 만들고 첫 회사를 생성합니다.
5. 회사 목표를 입력하고 CEO 에이전트를 설정합니다.
6. 사용할 LLM 또는 에이전트 어댑터를 연결합니다.
7. Brave Search API, Resend email API 같은 외부 도구를 agent-level secret으로 등록합니다.
8. 이슈를 만들고 에이전트가 heartbeat를 통해 실제 작업을 수행하는지 확인합니다.

공식 quickstart를 쓰면 로컬에서도 시작할 수 있습니다.

```bash
npx paperclipai onboard --yes
```

인증이 필요한 사설 네트워크 모드로 시작하고 싶다면 bind preset을 명시할 수 있습니다.

```bash
npx paperclipai onboard --yes --bind lan
# 또는
npx paperclipai onboard --yes --bind tailnet
```

수동 개발 환경은 다음 흐름입니다.

```bash
git clone https://github.com/paperclipai/paperclip.git
cd paperclip
pnpm install
pnpm dev
```

요구 사항은 Node.js 20 이상, pnpm 9.15 이상입니다. 개발 서버는 기본적으로 `http://localhost:3100`에서 열리고, 로컬 모드에서는 embedded PostgreSQL과 로컬 데이터 파일을 사용합니다.

## 영상에서 특히 중요한 운영 포인트

영상의 실전 포인트는 설치 자체보다 **도구 연결과 운영 설계**에 있습니다. Paperclip은 설치만 한다고 바로 좋은 결과를 내지 않습니다. 회사 목표가 모호하면 CEO 에이전트도 모호한 계획을 세웁니다. 역할 설명이 약하면 마케팅 에이전트와 리서치 에이전트가 겹치는 일을 할 수 있습니다.

따라서 첫 실험은 작은 조직으로 시작하는 게 좋습니다. CEO 하나와 2~4개의 전문 에이전트 정도면 충분합니다. 예를 들어 “AI 뉴스레터를 매주 발행하는 회사”라면 CEO, Researcher, Writer, Editor, Distribution Manager 정도로 나눌 수 있습니다.

또 하나 중요한 점은 API 키 관리입니다. 영상에서는 Brave Search API와 Resend email API 연결이 언급됩니다. 검색 도구는 리서치 에이전트에게, 이메일 도구는 결과물 전송이나 알림 담당 에이전트에게 붙일 수 있습니다. 이때 키는 프롬프트에 직접 쓰는 것이 아니라 Paperclip의 secret/environment variable로 저장해야 합니다.

## 실무적으로 어떻게 써볼 만한가

Paperclip은 “AI 회사”라는 표현 때문에 과장처럼 보일 수 있지만, 실제로는 **반복 업무를 가진 팀 운영 도구**로 보면 더 현실적입니다.

예를 들어 콘텐츠 팀이라면 매일 AI/LLM 뉴스를 수집하고, 중요한 기사만 고르고, 초안을 만들고, 편집자가 검수하도록 티켓을 만들 수 있습니다. 개발 팀이라면 CEO가 제품 목표를 관리하고, CTO가 구현 작업을 쪼개고, Codex나 Claude Code 에이전트가 실제 코드를 작성하게 할 수 있습니다. 세일즈 팀이라면 리드 리서치, 이메일 초안 작성, 후속 일정 관리 같은 반복 업무를 역할별로 나눌 수 있습니다.

다만 완전 자동 실행보다 **승인 기반 반자동 운영**이 먼저입니다. 특히 외부 이메일 발송, 결제, 배포, 고객 응대처럼 사고가 날 수 있는 작업은 board approval을 거치게 해야 합니다. Paperclip의 강점은 사람을 없애는 데 있는 것이 아니라, 사람이 매번 붙잡고 있던 조율·감시·비용 통제를 시스템화하는 데 있습니다.

## 정리

Paperclip은 에이전트 시대의 “업무 관리 레이어”에 가깝습니다. 단일 AI에게 일을 시키는 단계를 지나, 여러 AI 에이전트를 조직으로 묶고 목표·역할·예산·승인·로그를 관리하려는 시도입니다.

영상에서 보여주는 설치 흐름은 비교적 단순합니다. VPS를 준비하고, Docker 또는 `npx paperclipai onboard --yes`로 배포하고, 첫 회사를 만들고, CEO 에이전트와 외부 API를 연결하면 됩니다. 하지만 진짜 핵심은 설치 이후입니다. 좋은 목표, 좁은 역할, 보수적인 예산, 촘촘한 로그 확인이 있어야 Paperclip은 “AI 자동화 장난감”이 아니라 실제 운영 도구가 됩니다.

원문 영상 : <a href="https://www.youtube.com/watch?v=XXplTbQR9to&t=36s">Paperclip AI Tutorial: How to Build a Zero-Human Company</a>  
참고 : <a href="https://paperclip.ing/">Paperclip 공식 사이트</a> / <a href="https://github.com/paperclipai/paperclip">Paperclip GitHub</a> / <a href="https://www.hostinger.com/tutorials/how-to-set-up-paperclip">Hostinger Paperclip setup guide</a>
