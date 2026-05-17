---
title: "로봇이 인간관계를 이해하는 시대 — ARIS: Social Robots를 위한 관계 지능 시스템"
date: 2026-05-17T13:15:00+09:00
draft: false
description: "Monash大学 연구팀이 로봇이 사용자 간의 사회적 관계를 지식 그래프로建模하고 추적하는 ARIS 시스템을 개발했다. Pepper 로봇 기반 사용자 연구(N=23)에서 기존 LLM 대비 인지력, 생명성, 유사인간성, 호감도 모두 유의미하게 향상."
cover:
  image: "/images/aris-cover.png"
  alt: "ARIS - Agentic and Relationship Intelligence System for Social Robots"
tags:
  - AI
  - Robotics
  - SocialRobots
  - ARIS
  - LLM
  - RAG
  - HumanRobotInteraction
  - MonashUniversity
categories:
  - AI Research
  - Robotics

---

로봇이 내 대화를 듣고, 내가 누구와 무슨 관계인지 기억하고, 그걸 바탕으로 더 자연스럽게 대화하는 시대다.

Monash University 연구팀이 그걸 실제로 만들어냈다. 이름하여 **ARIS** — Agentic and Relationship Intelligence System. 소셜 로봇을 위한 관계 지능 프레임워크다.

---

## 문제가 뭐였나

기존 소셜 로봇은 크게 두 가지로 한계가 있었다.

**첫째, 관계 추론의 부재.** 로봇은 당신과 대화할 수는 있지만, 당신이 누구와 어떤 관계인지 모른다. 가족이야, 동료야, 연인인가? 이런 사회적 맥락을 파악하지 못하니까 대화의 깊이가 자연스럽게 제한된다.

**둘째, 장기 대화의 한계.** 대화가 길어질수록 LLM은 과거 컨텍스트를 놓치거나 응답 지연이 늘어난다. 수천 번의 교환이 이어지는 밀집적 대화에 대응하기 어렵다.

ARIS는 이 두 문제에 동시에 덤볐다.

---

## ARIS는 어떻게 풀었나

핵심은 세 가지 아키텍처가 조화를 이루는 구조다.

### 1. Social World Model — 지식 그래프로 관계를建模

로봇이 만나는 사람을 **노드**로, 사람 간 관계를 **엣지**로 표현한다. 대화를 통해 "철수와 영희는 부부야", "영희는 간호사야" 같은 정보를 추출하면 그대로 그래프에 저장된다.

다음에 영희가 다시 방문하면, 로봇은 이름만으로 이전 대화를 꺼내올 수 있다. 한번도 만난 적 없는 사람에 대해서는 유사 이름 매칭(Levenshtein 거리)으로 기존 노드와 통합한다.

### 2. RAG 기반 대화 파이프라인 — 천 건의 대화도 버티는检索

대화 히스토리가 길어질수록 일반 LLM은 성능이 저하된다. ARIS는 **하이브리드 의미 검색 + 최근성 인식** 방식으로 대화를 효율적으로 검색한다. 응답 지연은 낮게 유지하면서도 수천 차레의 교환에서 맥락적 관련성을 보장한다.

### 3. 모듈형 에이전트 아키텍처

음성(Vision), 시각(Whisper-large-v3),的身体 조작을 **구조적 API**로 조율한다. Reasoner가 사용자의 의도를 파악하고, Executor가 적절한 API를 선택해 로봇이 움직이든 말하든 반응한다.

사용된 기술 스택:
- **음성 인식:** Whisper-large-v3
- **추론/LLM:** Grok 2
- **시각:** Grok-2-Vision
- **임베딩:** OpenAI Embeddings
- **그래프 DB:** Neo4j
- **로봇:** Pepper v1.8

---

##Pepper로 실험, 결과는?

Pepper 로봇을实际的 대인 대화 환경에 놓고, 일반 LLM 베이스라인과 비교하는 사용자 연구를 진행했다 (N=23).

결과는 명확했다.

| 지표 | 효과 크기 (Cohen's d) |
|------|----------------------|
| 인지된 지능 (Perceived Intelligence) | 0.74 |
| 생명성 (Animacy) | 0.70 |
| 유사인간성 (Anthropomorphism) | **1.05** |
| 호감도 (Likeability) | 0.46 |

유사인간성이 **d=1.05**로 가장 큰 효과를 보였다. 기존 LLM만 쓴 로봇에 비해 ARIS 기반 Pepper가 "거의 사람처럼" 느껴졌다는 뜻이다.

---

## 우리 시스템에 적용하면 좋은 점

ARIS의思路가 흥미로운 이유는 두 가지다.

**1. 관계 데이터의価値.** chatbot이나 AI 어시스턴트도 결국 "누구와 대화하느냐"에 따라 접대의 방식이 달라져야 한다. 사용자 간 관계를knowledge graph로建模하는思路는客服, 멘탈 케어, 교육 같은 분야にも適用可能다.

**2. RAG의 확장 가능성.** 천 건이든 천만 건이든 컨텍스트를 효율적으로检索하는 메커니즘은 모든 장기 대화 AI 시스템에 필요하다. ARIS의 하이브리드 검색 방식은这方面的実装参考가 될 수 있다.

---

## 마무리

로봇이 단순히 명령을 수행하는 시대는 지났다. ARIS가 보여준 건, **로봇이 사회적 관계를 이해하고 추적할 수 있다면 사람과 의외로 자연스러운 대화가 가능하다는 것**이다.

연구는 오픈소스로公开发표될 예정이라, 관심 있는 분들은 지켜보면 좋겠다.

---

원문 : <a href="https://arxiv.org/abs/2605.00943">ARIS: Agentic and Relationship Intelligence System for Social Robots</a>
