---
title: "Gemini Enterprise Agent Platform: 구글이 보는 엔터프라이즈 에이전트의 다음 단계"
date: 2026-04-30T23:20:00+09:00
draft: false
description: "Google Cloud가 공개한 Gemini Enterprise Agent Platform의 핵심 기능과 기업용 AI 에이전트 플랫폼 경쟁의 의미를 정리한다."
cover:
  image: "/images/google-gemini-enterprise-agent-platform-cover.jpg"
  alt: "Gemini Enterprise Agent Platform 대표 이미지"
  caption: "Source: Google Cloud"
tags:
  - GoogleCloud
  - GeminiEnterprise
  - AIAgent
  - VertexAI
  - AgentPlatform
  - EnterpriseAI
categories:
  - AI Agent
  - 기술 인사이트

---

출처: Google Cloud  
문서유형: 번역·해설  
#GoogleCloud #GeminiEnterprise #AIAgent #VertexAI

## 핵심 요약

Google Cloud가 **Gemini Enterprise Agent Platform**을 공개했습니다. 기존 Vertex AI의 모델 선택·모델 구축·에이전트 구축 기능을 기반으로, 에이전트 통합, DevOps, 오케스트레이션, 보안, 거버넌스까지 하나의 플랫폼으로 묶겠다는 방향입니다.

![Gemini Enterprise Agent Platform 대표 이미지](/images/google-gemini-enterprise-agent-platform-cover.jpg)

## Vertex AI에서 Agent Platform으로

이번 발표의 핵심은 단순한 새 기능 추가가 아닙니다. Google은 앞으로 Vertex AI 서비스와 로드맵 진화를 독립 서비스가 아니라 Agent Platform을 통해 제공하겠다고 밝혔습니다. 기업용 AI 개발의 중심축을 “모델 개발”에서 “운영 가능한 에이전트 플랫폼”으로 옮기는 선언에 가깝습니다.

Agent Platform은 Gemini 3.1 Pro, Gemini 3.1 Flash Image, Lyria 3, Gemma 4 같은 구글 모델뿐 아니라 Claude Opus, Sonnet, Haiku 같은 서드파티 모델도 Model Garden을 통해 다룰 수 있게 합니다. 기업 입장에서는 특정 모델 하나에 묶이지 않고 작업별로 맞는 모델을 고르는 구조가 중요해졌습니다.

## Build, Scale, Govern, Optimize

Google은 Agent Platform의 역할을 네 가지로 설명합니다. 만들고(Build), 확장하고(Scale), 통제하고(Govern), 최적화하는(Optimize) 것입니다.

Build 영역에서는 Agent Studio와 ADK가 중심입니다. Agent Studio는 낮은 코드로 에이전트를 만들고, 더 깊은 커스터마이징이 필요하면 ADK로 가져갈 수 있습니다. ADK는 그래프 기반 sub-agent 구조를 지원해 복잡한 문제를 여러 에이전트가 나눠 처리할 수 있게 합니다.

![Gemini Enterprise Agent Platform의 에이전트 구축 흐름](/images/google-gemini-enterprise-agent-platform-build.jpg)

Scale 영역에서는 Agent Runtime, 장기 실행 에이전트, Agent Sandbox, Agent Memory Bank가 눈에 띕니다. 특히 며칠 동안 상태를 유지하는 long-running agent와 장기 기억을 다루는 Memory Bank는 기업 업무 자동화에서 중요한 기능입니다. 단발성 챗봇이 아니라, 상태를 유지하며 업무 흐름을 이어가는 에이전트를 겨냥한 셈입니다.

## 기업용 에이전트에서 거버넌스가 중심이 되는 이유

에이전트가 실제 업무 시스템과 연결되면 가장 중요한 문제는 “무엇을 할 수 있는가”보다 “누가, 어떤 권한으로, 어떤 기록을 남기며 실행하는가”입니다. Google은 Agent Identity, Agent Registry, Agent Gateway를 통해 에이전트마다 추적 가능한 정체성과 중앙 통제 구조를 제공하겠다고 설명합니다.

또 Agent Simulation, Agent Evaluation, Agent Observability로 실행 trace와 reasoning 흐름을 볼 수 있게 합니다. 에이전트가 실패했을 때 단순히 “모델이 틀렸다”로 끝나는 것이 아니라, 어떤 도구를 호출했고 어떤 판단 경로를 거쳤는지 추적할 수 있어야 운영이 가능합니다.

![Gemini Enterprise Agent Platform의 거버넌스와 운영 구조](/images/google-gemini-enterprise-agent-platform-govern.jpg)

## 실무자가 볼 포인트

이번 발표에서 가장 중요한 메시지는 기업용 에이전트가 더 이상 데모 수준의 챗봇으로 머물 수 없다는 점입니다. 실제 업무에 들어가려면 모델, 도구, 메모리, 권한, 실행 환경, 관찰 가능성, 평가가 함께 묶여야 합니다.

특히 기업은 세 가지를 먼저 봐야 합니다. 첫째, 에이전트가 접근할 수 있는 시스템과 데이터 범위입니다. 둘째, 장기 실행과 메모리 저장이 필요한 업무인지입니다. 셋째, 실패했을 때 원인을 추적하고 권한을 회수할 수 있는 운영 구조입니다.

## 정리

Gemini Enterprise Agent Platform은 구글이 엔터프라이즈 AI 경쟁을 모델 단위가 아니라 플랫폼 단위로 보고 있다는 신호입니다. 앞으로 기업용 AI의 차이는 “어떤 모델을 썼나”보다 “에이전트를 얼마나 안전하게 만들고, 배포하고, 관찰하고, 개선할 수 있나”에서 갈릴 가능성이 큽니다.

원문 : <a href="https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform">Introducing Gemini Enterprise Agent Platform</a>
