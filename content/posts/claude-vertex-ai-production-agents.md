---
title: "프로덕션 AI 에이전트를 만드는 Google Cloud 스택: ADK, MCP, Agent Engine, A2A"
date: 2026-05-01T17:20:00+09:00
draft: false
description: "Anthropic Claude on Vertex AI 워크숍 영상을 바탕으로, 프로토타입 에이전트를 운영 가능한 프로덕션 시스템으로 만들기 위한 Google Cloud 에이전트 스택을 정리한다."
cover:
  image: "/images/vertex-ai-agent-stack-hero.png"
  alt: "Production AI Agent Stack illustration"
  caption: "Source: Ionuț Dogariu / YouTube"
tags:
  - Claude
  - VertexAI
  - GoogleCloud
  - ADK
  - MCP
  - AgentEngine
  - A2A
  - AIAgent
  - ProductionAI
categories:
  - AI Agent
  - 기술 인사이트
---

출처: Ionuț Dogariu YouTube  
문서유형: 영상 해설  
#Claude #VertexAI #ADK #MCP #AgentEngine #A2A

## 핵심 요약

이 영상은 **Claude를 Vertex AI 위에서 사용해 프로덕션 AI 에이전트를 만드는 방법**을 다룹니다. 단순히 에이전트를 만드는 법이 아니라, 프로토타입을 실제 운영 환경에 올릴 때 필요한 스택을 설명합니다.

핵심 메시지는 분명합니다. 에이전트 개발의 어려움은 모델 호출이 아니라 **표준화, 도구 연결, 에이전트 간 통신, 배포, 관측 가능성, 거버넌스**에 있습니다. Google Cloud는 이를 위해 ADK, MCP, Agent Engine, A2A라는 네 가지 축을 제시합니다.

![Vertex AI Agent Stack](/images/vertex-ai-agent-stack-hero.png)

## 기: 에이전트 프로토타입은 쉽지만, 운영은 어렵다

AI 에이전트로 멋진 데모를 만드는 일은 점점 쉬워졌습니다. 하지만 데모가 마음에 들어도 실제 서비스로 올리는 순간 문제가 시작됩니다.

영상에서는 프로덕션화가 어려운 이유를 세 가지로 정리합니다.

- 에이전트 프레임워크와 도구 생태계가 너무 파편화되어 있습니다.
- 서로 다른 프레임워크로 만든 에이전트끼리 통신시키기 어렵습니다.
- 배포 후 모니터링, 로깅, 평가, 거버넌스를 직접 챙겨야 합니다.

즉 에이전트 제품화는 “모델이 똑똑한가”보다 “운영 가능한 시스템인가”의 문제로 넘어갑니다.

## 승: Google Cloud의 4단 에이전트 스택

Google Cloud가 제시하는 스택은 네 가지입니다.

1. **ADK, Agent Development Kit**  
   코드 중심으로 에이전트를 만들고 평가하고 배포하기 위한 프레임워크입니다.

2. **MCP, Model Context Protocol**  
   에이전트가 도구와 컨텍스트를 표준 방식으로 소비하도록 해줍니다.

3. **Vertex AI Agent Engine**  
   에이전트를 관리형 서비스로 배포하고, 로깅·모니터링·평가를 붙이는 운영 레이어입니다.

4. **A2A, Agent-to-Agent Protocol**  
   서로 다른 프레임워크로 만든 에이전트가 공통 언어로 협업하게 하는 프로토콜입니다.

이 네 가지가 합쳐지면 에이전트는 데모가 아니라 운영 가능한 애플리케이션 구조에 가까워집니다.

## 전: ADK와 MCP로 에이전트를 조립한다

영상의 데모는 생일 파티 플래너 에이전트로 시작합니다. ADK에서 에이전트를 만들려면 기본적으로 세 가지 파일이 필요합니다.

- `agent.py`: 에이전트 로직
- `.env`: 환경 변수
- `__init__.py`: 파이썬 패키지 초기화

ADK는 LLM Agent, Tool, Runner, Session 같은 개념을 제공합니다. Runner는 에이전트 실행과 세션 상태를 관리하고, CLI와 웹 UI를 통해 에이전트를 테스트할 수 있습니다.

![ADK MCP Orchestrator](/images/adk-mcp-orchestrator.svg)

여기서 MCP가 중요해집니다. 예를 들어 생일 파티 아이디어를 제안하는 에이전트에 캘린더 일정을 잡는 기능을 붙이고 싶다면, MCP 서버를 도구처럼 연결할 수 있습니다. 영상에서는 MCP 서버를 ADK 도구로 변환해 Calendar Agent가 사용할 수 있게 만듭니다.

이후 Orchestrator Agent가 Birthday Agent와 Calendar Agent를 도구처럼 받아, 사용자의 요청을 적절한 에이전트로 라우팅합니다. 멀티 에이전트 시스템을 작은 코드 변경으로 구성하는 방식입니다.

## 결: Agent Engine과 A2A가 운영의 핵심이다

로컬에서 에이전트를 만드는 것과 운영 환경에 올리는 것은 다릅니다. 직접 하려면 FastAPI나 Django로 감싸고, 컨테이너를 만들고, 클라우드 런타임을 구성하고, 로깅과 모니터링을 붙여야 합니다.

Vertex AI Agent Engine은 이 복잡도를 줄입니다. `agent_engine.create` 같은 방식으로 에이전트를 배포하고, 쿼리 수, 응답 지연 시간, CPU·메모리, 세션 정보를 관리형 UI에서 볼 수 있게 합니다.

![Agent Engine Observability](/images/agent-engine-observability.svg)

A2A는 그 다음 단계입니다. 앞으로는 하나의 프레임워크로 만든 에이전트만 쓰지 않을 가능성이 큽니다. LangGraph, LangChain, ADK, 사내 프레임워크로 만든 에이전트가 함께 일해야 합니다. A2A는 이들이 서로의 기능을 설명하고, 요청과 응답을 주고받는 공통 언어가 됩니다.

## 핵심 인사이트

### 1. 에이전트 제품화의 병목은 모델이 아니라 운영이다

프롬프트와 모델 호출만으로는 부족합니다. 실제 서비스에는 로깅, 모니터링, 평가, 권한, 세션, 배포, 확장성이 필요합니다.

### 2. ADK는 에이전트 개발을 소프트웨어 엔지니어링에 가깝게 만든다

파일 구조, Runner, Session, CLI, Web UI를 통해 에이전트를 반복 개발할 수 있습니다. 이는 노트북 데모보다 훨씬 운영 친화적인 접근입니다.

### 3. MCP는 도구 연결의 표준화 계층이다

에이전트가 외부 도구를 쓸 때마다 커스텀 wrapper를 만들면 유지보수가 어려워집니다. MCP를 쓰면 도구와 컨텍스트 연결 방식을 표준화할 수 있습니다.

### 4. Agent Engine은 배포 이후의 문제를 다룬다

운영에서 중요한 것은 “배포됐다”가 아니라 “관측되고, 평가되고, 개선될 수 있다”입니다. Agent Engine은 이 지점을 플랫폼 레벨에서 처리하려는 시도입니다.

### 5. A2A는 멀티 에이전트 시대의 공통 언어다

서로 다른 프레임워크로 만든 에이전트가 함께 일하려면 공통 프로토콜이 필요합니다. A2A는 에이전트의 기능을 명함처럼 설명하고, 요청과 응답을 주고받는 구조를 제공합니다.

## 실무적으로 볼 포인트

이 영상은 Claude on Vertex AI 워크숍이지만, 핵심은 특정 클라우드에만 묶이지 않습니다. 모든 프로덕션 에이전트 시스템에 공통으로 적용됩니다.

- 에이전트 개발 프레임워크가 필요합니다.
- 도구 연결은 표준화되어야 합니다.
- 에이전트 간 통신 프로토콜이 필요합니다.
- 배포 이후 관측 가능성과 평가 루프가 있어야 합니다.
- 운영 환경에서는 거버넌스와 보안이 필수입니다.

결국 좋은 에이전트 시스템은 “모델 + 프롬프트”가 아니라 **개발 키트 + 프로토콜 + 배포 엔진 + 관측 가능성**의 조합입니다.

## 마무리

에이전트 개발의 다음 단계는 더 멋진 데모가 아닙니다. 데모를 운영 가능한 시스템으로 바꾸는 일입니다.

이 영상이 보여주는 Google Cloud의 방향은 분명합니다. ADK로 만들고, MCP로 도구를 연결하고, Agent Engine으로 배포·관측하고, A2A로 다른 에이전트와 협업하게 만드는 것입니다.

앞으로 에이전트 경쟁력은 모델 선택만으로 결정되지 않을 것입니다. 누가 더 빨리, 더 안전하게, 더 관측 가능한 운영 구조를 만들 수 있는지가 중요해집니다.

원문 : <a href="https://www.youtube.com/watch?v=X0ASQC5AfpI">Anthropic Just Taught How to Build Production AI Agents in 30 Minutes</a>
