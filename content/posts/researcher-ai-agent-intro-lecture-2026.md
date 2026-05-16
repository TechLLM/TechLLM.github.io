---
title: "연구자를 위한 AI Agent 입문: 챗봇을 넘어 연구 워크플로우를 설계하는 법"
date: 2026-05-01T22:50:00+09:00
draft: false
description: "MahlerLab의 '연구자를 위한 AI Agent 입문 강의'를 바탕으로, AI Agent의 기본 구조, Claude Code·Agent.md·Skills·MCP, Context Engineering, 연구 자동화 전략과 실패 패턴을 정리한다."
cover:
  image: "/images/researcher-ai-agent-intro-2026-cover.jpg"
  alt: "연구자를 위한 AI Agent 입문 강의 YouTube thumbnail"
  caption: "Source: MahlerLab / YouTube"
tags:
  - AIAgent
  - ResearchWorkflow
  - ClaudeCode
  - MCP
  - ContextEngineering
  - AgentSkills
  - ResearchAutomation
categories:
  - AI Agent
  - 기술 인사이트

---

출처: MahlerLab YouTube  
문서유형: 영상 해설  
#AIAgent #ResearchWorkflow #ClaudeCode #MCP #ContextEngineering

## 핵심 요약

MahlerLab의 **“연구자를 위한 AI Agent 입문 강의”**는 연구자가 AI 에이전트를 어떻게 이해하고 활용해야 하는지 차분하게 정리한 강의입니다. 핵심은 “AI Agent가 더 똑똑한 챗봇인가?”가 아니라, **연구자가 AI를 대화 상대에서 작업 동료로 다루기 시작하면 무엇이 달라지는가**입니다.

기존 챗봇형 LLM 사용은 대부분 복사-붙여넣기 중심입니다. 자료를 붙이고, 답을 받고, 다시 다른 파일로 옮기고, 또 수정 요청을 합니다. 반면 AI Agent는 workspace 안에서 파일을 읽고 쓰고, 검색·코드 실행·API 호출 같은 도구를 사용하며, 목표를 향해 여러 단계를 수행합니다.

하지만 강의는 에이전트를 무조건 믿으라고 말하지 않습니다. 오히려 연구자는 더 중요해집니다. Agent가 빠르게 초안과 결과물을 만들수록, 인간 연구자는 **목표 설정, 맥락 설계, 비판적 검토, 최종 판단**을 더 잘해야 합니다.

![AI Agent 강의 썸네일](/images/researcher-ai-agent-intro-2026-cover.jpg)

## AI Agent란 무엇인가

강의에서 AI Agent는 목표가 주어지면 계획을 세우고, 메모리를 활용하고, 도구를 사용해 작업을 수행하는 LLM 기반 시스템으로 설명됩니다.

![LLM Agents](/images/researcher-agent-llm-agents.png)

Agent의 기본 요소는 다음과 같습니다.

- **Goal**: 무엇을 달성할 것인가
- **Planning**: 어떤 순서로 진행할 것인가
- **Memory**: 이전 작업과 맥락을 어떻게 유지할 것인가
- **Tools**: 검색, 코드 실행, 파일 조작, API 호출을 어떻게 사용할 것인가
- **Action / Observation loop**: 행동하고 결과를 관찰한 뒤 다음 행동을 정하는 반복 구조

이 구조 때문에 Agent는 단순 응답 생성기를 넘어, 작은 업무 단위를 실제로 처리하는 실행 시스템에 가까워집니다.

## 챗봇과 Agent의 차이

챗봇은 사용자가 질문하면 답합니다. 대화의 주도권은 대부분 사용자에게 있습니다. 사용자가 문서를 붙여 넣고, 요약을 요청하고, 다시 결과를 복사해 다른 작업으로 넘깁니다.

Agent는 다릅니다. 사용자가 목표를 주면 Agent는 작업을 쪼개고, 필요한 파일을 열고, 도구를 호출하고, 중간 결과를 확인하며, 다음 행동을 선택합니다.

![Chatbot vs Agent](/images/researcher-agent-chatbot-vs-agent.png)

연구 업무에서는 이 차이가 큽니다. 논문 조사, 데이터 정리, 코드 실행, 그림 변환, 보고서 초안 작성은 한 번의 질문으로 끝나지 않습니다. 여러 단계를 거쳐야 하므로 Agent형 워크플로우가 더 잘 맞습니다.

## Agentic workflow의 기본 구조

Agentic workflow는 보통 다음 루프를 따릅니다.

```text
Goal → Reason → Action → Observe → 다시 Reason → Finish
```

![Agentic workflow](/images/researcher-agent-workflow.png)

예를 들어 “최근 AI Agent 연구 동향을 정리해줘”라는 목표가 있으면 Agent는 검색하고, 자료를 고르고, 요약하고, 표를 만들고, 보고서를 작성합니다. 중요한 점은 이 모든 과정이 trace와 파일로 남아야 한다는 것입니다. 그래야 연구자가 검토하고, 잘못된 방향을 바로잡을 수 있습니다.

## Claude Code, Agent.md, Rules, Skills

강의는 Claude Code 같은 실제 도구와 함께 **Agent.md, Rules, Skills**의 중요성을 설명합니다.

- **Agent.md / AGENTS.md**: 프로젝트 안에서 Agent가 따라야 할 기본 지침
- **Rules**: 반복적으로 지켜야 할 원칙, 금지 사항, 출력 형식
- **Skills**: 특정 작업을 잘 수행하기 위한 절차화된 지식

연구 프로젝트에서는 특히 규칙이 중요합니다. 예를 들어 원문 논문 제목, DOI, URL은 임의로 바꾸지 말 것, 통계 결과는 원본 코드와 함께 저장할 것, 모르는 내용은 추측하지 말고 `[확인 필요]`로 표시할 것 같은 규칙이 필요합니다.

좋은 Agent 활용은 좋은 프롬프트 하나로 끝나지 않습니다. 좋은 폴더 구조, 좋은 규칙, 좋은 반복 절차가 함께 있어야 합니다.

## MCP는 왜 중요한가

MCP, Model Context Protocol은 Agent가 외부 도구와 데이터를 표준 방식으로 연결하도록 돕는 프로토콜입니다.

![MCP](/images/researcher-agent-mcp.png)

연구자 관점에서 MCP는 중요합니다. Agent가 PubMed, Google Drive, 로컬 파일, 실험 데이터베이스, 분석 스크립트 같은 도구에 접근할 수 있어야 실제 연구 업무를 도울 수 있기 때문입니다.

하지만 도구가 많아질수록 안전장치도 중요해집니다. 검색은 허용해도 원본 데이터 삭제는 막아야 하고, 초안 작성은 허용해도 외부 메일 발송은 승인 후 실행하게 해야 합니다.

## Vibe Research와 연구 폴더 설계

강의에서 말하는 Vibe Research는 AI와 함께 아이디어 탐색, 자료 수집, 초안 작성, 비판적 검토를 빠르게 반복하는 방식으로 볼 수 있습니다. 단, “느낌대로 연구한다”는 뜻은 아닙니다. Agent가 빠르게 생성한 가설과 초안을 인간 연구자가 구조화하고 검증하는 방식입니다.

이때 workspace 설계가 중요합니다. 추천 구조는 다음과 같습니다.

```text
project/
  data_inventory.md
  sources/
  notes/
  analysis/
  figures/
  drafts/
  reports/
  AGENTS.md
```

Agent가 어떤 파일을 읽고, 어디에 결과를 저장하고, 어떤 형식으로 보고해야 하는지 명확해야 합니다. 폴더 구조가 곧 Agent의 작업 환경입니다.

## Context Engineering

Context Engineering은 Agent에게 필요한 맥락을 적절한 시점에 적절한 형태로 제공하는 기술입니다. 단순히 프롬프트를 잘 쓰는 문제가 아닙니다. 프로젝트 파일, 규칙, 예시, 중간 산출물, 도구 설명을 어떻게 배치할지의 문제입니다.

![Context Engineering](/images/researcher-agent-context-engineering.png)

연구자는 다음 질문을 계속 던져야 합니다.

- Agent가 지금 이 작업을 하기 위해 반드시 알아야 하는 것은 무엇인가?
- 너무 많은 정보를 넣어 판단을 흐리게 만들고 있지는 않은가?
- 중간 결과가 다음 단계 Agent나 인간 연구자가 읽기 쉬운 구조로 남는가?

좋은 Context Engineering은 Agent의 성능을 끌어올리는 동시에, 사람이 검토할 수 있는 형태로 작업을 남기게 합니다.

## Agent의 실패 패턴

Agent는 반복 작업, 자료 수집, 초안 작성, 파일 정리, 형식 변환에 강합니다. 하지만 연구 질문의 타당성, 실험 설계의 근본적 결함, 데이터 해석의 책임 있는 판단은 여전히 약합니다.

특히 위험한 실패는 “그럴듯한데 틀린 결과”입니다. 논문 제목이나 DOI를 잘못 쓰거나, 통계 결과를 과장하거나, 존재하지 않는 근거를 자연스럽게 끼워 넣을 수 있습니다.

따라서 연구자는 Agent가 만든 결과를 최종 산출물로 바로 받아들이면 안 됩니다. Agent는 초안 생성과 탐색을 빠르게 해주는 도구이고, 최종 판단과 책임은 사람에게 남습니다.

## 연구자가 키워야 할 능력

이 강의가 강조하는 연구자의 능력은 다음과 같습니다.

1. 좋은 질문을 정의하는 능력
2. Agent가 일할 수 있는 workspace를 설계하는 능력
3. 규칙과 Skills를 문서화하는 능력
4. 여러 Agent의 결과를 비교하고 비판하는 능력
5. 자동화 가능한 작업과 인간 판단이 필요한 작업을 구분하는 능력
6. 발산된 아이디어를 논문, 실험 계획, 보고서로 수렴하는 능력

결국 AI Agent 시대의 연구자는 “AI를 잘 쓰는 사람”을 넘어 **AI가 일할 수 있는 연구 시스템을 설계하는 사람**이 되어야 합니다.

## 정리

이 강의는 AI Agent를 연구자의 생산성 도구로 소개하면서도, 동시에 그 한계를 분명히 짚습니다. Agent는 복잡한 연구 업무를 더 빠르게 탐색하고, 반복 작업을 줄이고, 초안을 만들고, 자동화 파이프라인을 구성하는 데 큰 도움을 줍니다.

하지만 좋은 결과는 Agent 혼자 만들지 않습니다. 연구자가 목표를 정하고, 맥락을 설계하고, 도구 권한을 관리하고, 결과를 비판적으로 검토할 때 Agent는 진짜 연구 동료가 됩니다.

원문 영상 : <a href="https://www.youtube.com/watch?v=tZ9KFQOA6NM&t=79s">연구자를 위한 AI Agent 입문 강의 (2026.4)</a>
