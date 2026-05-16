---
title: "좋은 AI 에이전트를 만드는 5가지 실전 원칙"
date: 2026-05-01T10:15:00+09:00
draft: false
description: "Google Developers Blog의 Agent Bake-Off 사례를 바탕으로, 프로덕션급 AI 에이전트를 만들 때 필요한 멀티 에이전트 구조, 모듈성, 멀티모달, 오픈 프로토콜, 결정론적 실행 원칙을 정리한다."
cover:
  image: "/images/google-agent-bakeoff-ai-agents-cover.jpg"
  alt: "Google Agent Bake-Off AI agents cover"
  caption: "Source: Google Developers Blog"
tags:
  - AIAgent
  - MultiAgent
  - GoogleCloud
  - AgentEngineering
  - ADK
  - MCP
categories:
  - AI Agent
  - 기술 인사이트

---

출처: Google Developers Blog  
문서유형: 번역·해설  
#AIAgent #MultiAgent #AgentEngineering #GoogleCloud

## 핵심 요약

Google Developers Blog가 공개한 Agent Bake-Off 사례에서 가장 흥미로운 지점은 분명합니다. 이제 AI 에이전트 개발의 핵심은 “프롬프트를 얼마나 잘 쓰느냐”가 아닙니다. 실제 서비스로 버티는 구조를 만들 수 있느냐입니다.

좋은 데모는 한 번 멋지게 작동하면 됩니다. 하지만 프로덕션 에이전트는 반복 실행, 예외 처리, 외부 시스템 연동, 비용, 지연 시간, 검증 가능성까지 견뎌야 합니다.

![Google Agent Bake-Off 대표 이미지](/images/google-agent-bakeoff-ai-agents-cover.jpg)

## 1. 하나의 거대한 에이전트로 만들지 말 것

복잡한 일을 하나의 LLM에게 전부 맡기면 금방 흔들립니다. 의도 파악, DB 조회, 계산, 응답 스타일 조정까지 한 번에 처리하게 만들면 환각과 지연 시간이 늘어납니다.

Google이 강조한 첫 번째 원칙은 **멀티 에이전트 워크플로우**입니다. 기능별로 작은 에이전트를 나누고, 상위 supervisor agent가 흐름을 조율하는 방식입니다.

![멀티 에이전트 워크플로우 아키텍처](/images/google-agent-bakeoff-multi-agent-workflow.jpg)

이 구조는 마이크로서비스와 비슷합니다. 특정 모델을 바꾸거나 데이터베이스 스키마를 수정해야 할 때 전체 시스템을 건드리지 않고 일부 에이전트만 교체할 수 있습니다.

## 2. 오늘 만든 에이전트 하네스는 내일 버릴 수 있어야 한다

AI 모델은 너무 빠르게 좋아지고 있습니다. 예전에는 여러 단계의 agent harness가 필요했던 작업이, 몇 주 뒤에는 새 모델의 단일 프롬프트로 해결될 수 있습니다.

그래서 에이전트 구조는 영구적인 성이 아니라 교체 가능한 부품처럼 설계해야 합니다. 복잡한 파이프라인을 만들더라도, 모델 성능이 따라잡는 순간 해당 코드를 과감히 제거할 수 있어야 합니다.

![에이전트 하네스 다이어그램](/images/google-agent-bakeoff-agent-harness.jpg)

핵심은 모듈성입니다. 오래 붙잡는 코드가 아니라, 빨리 교체할 수 있는 코드가 좋은 에이전트 아키텍처가 됩니다.

## 3. 멀티모달은 부가기능이 아니다

현실의 문제는 텍스트만으로 끝나지 않습니다. 이커머스 추천, 가상 착용, 현장 점검, 문서 분석 같은 작업에서는 이미지와 음성, 화면 맥락이 결과 품질을 크게 좌우합니다.

“파란 청바지를 입어보세요”라는 텍스트 추천보다, 실제 사용자 사진과 상품 이미지를 반영한 시각적 결과물이 훨씬 강력합니다.

![멀티모달 프롬프트와 이미지 입력 비교](/images/google-agent-bakeoff-multimodal.jpg)

앞으로의 에이전트는 텍스트 챗봇에 이미지 기능을 덧붙이는 방식이 아니라, 처음부터 멀티모달 입력과 출력을 기본 전제로 설계되어야 합니다.

## 4. MCP, A2A 같은 오픈 프로토콜을 이해해야 한다

기업 시스템과 연결되는 순간, 에이전트 개발은 단순한 API 호출 문제가 아닙니다. 내부 도구, 원격 에이전트, 결제, 재고, 권한, UI 렌더링까지 연결해야 합니다.

이때 모든 연동을 직접 wrapper로 만들면 시스템은 금방 깨지기 쉬워집니다. Google 글은 MCP, A2A, UCP, AP2, A2UI, AG-UI 같은 오픈 프로토콜을 적극적으로 이해하고 활용해야 한다고 말합니다.

![AI 에이전트 프로토콜 가이드](/images/google-agent-bakeoff-agent-protocols.png)

표준화된 프로토콜을 쓰면 에이전트가 도구를 발견하고, 다른 에이전트와 통신하고, 구조화된 payload로 안정적으로 작업할 수 있습니다. 커스텀 접착 코드를 줄이는 것이 곧 운영 안정성입니다.

## 5. LLM은 추론하고, 실행은 결정론적 코드가 해야 한다

가장 중요한 원칙은 이것입니다. LLM에게 계산이나 금융 거래 실행을 직접 맡기면 안 됩니다.

LLM은 의도를 파악하고 필요한 변수를 추출하는 데 강합니다. 하지만 이자 계산, DB 쓰기, 결제 처리처럼 정확성이 필요한 일은 전통적인 코드가 해야 합니다.

![LLM 추론과 결정론적 코드 실행 구조](/images/google-agent-bakeoff-strict-schema.jpg)

좋은 패턴은 단순합니다. LLM의 출력을 JSON schema나 Pydantic 같은 엄격한 구조로 검증하고, 통과한 값만 Python 함수나 SQL 쿼리에 넘기는 것입니다.

즉, **AI는 생각하고 코드는 실행한다**는 경계를 지켜야 합니다.

## 실무자가 볼 포인트

이 글의 핵심은 “프롬프트보다 엔지니어링”입니다.

프로덕션급 AI 에이전트는 멋진 God Prompt로 만들어지지 않습니다. 작게 나눈 에이전트, 교체 가능한 하네스, 멀티모달 기본 설계, 오픈 프로토콜, 엄격한 schema 검증이 합쳐져야 합니다.

AI 에이전트를 만든다는 것은 더 이상 챗봇을 하나 붙이는 일이 아닙니다. 작은 소프트웨어 시스템을 설계하는 일에 가깝습니다.

그리고 그 시스템에서 LLM은 전부를 대신하는 마법 상자가 아니라, 잘 정의된 역할을 맡은 하나의 강력한 컴포넌트가 되어야 합니다.

원문 : <a href="https://developers.googleblog.com/build-better-ai-agents-5-developer-tips-from-the-agent-bake-off/">Build Better AI Agents: 5 Developer Tips from the Agent Bake-Off</a>
