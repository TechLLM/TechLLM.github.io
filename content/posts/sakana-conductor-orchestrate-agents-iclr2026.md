---
title: "Sakana AI Conductor: 7B 모델이 GPT-5·Claude·Gemini를 지휘한다"
date: 2026-05-04T11:00:00+09:00
draft: false
description: "Sakana AI가 ICLR 2026에서 발표한 Conductor는 7B RL 모델이 자연어 워크플로우로 프론티어 AI들을 오케스트레이션한다. LiveCodeBench 83.9%, GPQA-Diamond 87.5% 달성."
cover:
  image: "/images/sakana-conductor-cover.svg"
  alt: "Sakana AI Conductor multi-agent orchestration diagram"
  caption: "Conductor는 7B 파라미터 모델로 GPT-5, Gemini, Claude 등 프론티어 모델을 지휘한다"
tags:
  - SakanaAI
  - MultiAgent
  - Conductor
  - Orchestration
  - ICLR2026
  - ReinforcementLearning
  - LLM
categories:
  - AI Research
summary: "Sakana AI의 Conductor는 7B RL 모델이 자연어로 다중 AI 에이전트를 동적 오케스트레이션하는 시스템이다. 단순 질문엔 단일 모델, 복잡한 코딩엔 플래너-코더-검증기 파이프라인을 자율 구성한다."
---

## 핵심 요약

Sakana AI가 ICLR 2026에 발표한 **Conductor**는 7B 파라미터 모델이 강화학습으로 훈련돼 GPT-5, Gemini, Claude 등 프론티어 AI들을 **자연어 워크플로우**로 지휘하는 멀티에이전트 오케스트레이터다. 고정된 파이프라인 없이 문제 난이도에 따라 에이전트 구성을 동적으로 결정하며, LiveCodeBench **83.9%**, GPQA-Diamond **87.5%**로 개별 워커 모델과 기존 멀티에이전트 베이스라인을 모두 능가했다.

---

## 문제 의식: 왜 오케스트레이터가 필요한가

멀티에이전트 시스템의 기존 접근은 두 가지 문제를 갖고 있었다.

첫째, **고정 워크플로우**다. "Agent A → Agent B → Agent C" 같은 하드코딩된 파이프라인은 문제 유형이 달라지면 비효율이 발생한다. 쉬운 질문에도 불필요하게 여러 모델을 호출하는 낭비가 생긴다.

둘째, **수동 프롬프트 엔지니어링**이다. 각 에이전트에 어떤 서브태스크를 어떻게 지시할지를 사람이 설계해야 한다. 이는 확장성의 병목이 된다.

Conductor는 이 두 문제를 동시에 해결한다. 오케스트레이터 자체를 **학습 가능한 모델**로 만들고, 지시문을 자연어로 동적 생성하게 한 것이다.

---

## Conductor 작동 원리

Conductor가 하는 일은 세 가지다.

**① 에이전트 선택:** 워커 풀(GPT-5, Gemini, Claude, 오픈소스 모델 등)에서 해당 태스크에 맞는 모델을 선택한다.

**② 서브태스크 지시:** 선택한 에이전트에게 전달할 구체적인 프롬프트를 생성한다. Conductor가 일종의 **전문가 프롬프트 엔지니어** 역할을 맡는다.

**③ 컨텍스트 관리:** 어떤 정보를 어떤 에이전트에게 전달할지 결정해 불필요한 컨텍스트 오염을 막는다.

이 세 단계가 자연어 워크플로우로 출력되고, 워커들이 순차적·병렬적으로 실행된다.

---

## 핵심 특징: 두 가지 창발적 행동

### 적응형 파이프라인 구성

실험에서 Conductor는 문제 난이도에 따라 전략을 스스로 조정했다.

> *"For simple factual questions, it just queries one model. But for hard coding problems, it autonomously spins up a whole pipeline of planners, coders, and verifiers."*

단순 사실 질문엔 단일 모델 호출로 끝내고, 어려운 코딩 문제엔 **플래너 → 코더 → 검증기** 파이프라인을 자율 구성한다. 고정 워크플로우 없이 태스크 복잡도에 비례한 컴퓨팅 배분이 가능해진 것이다.

### 재귀적 테스트타임 스케일링

Conductor는 워커 풀에 **자기 자신을 포함시킬 수 있다**. 즉, 오케스트레이터가 워커로도 동작하는 재귀 구조다. 이를 통해:
- 이전 에이전트의 출력을 검토하고 오류를 탐지
- 교정 워크플로우를 추가로 생성

테스트타임에 컴퓨팅을 더 투입할수록 성능이 올라가는 **스케일링 특성**이 확인됐다.

---

## 성능

| 벤치마크 | Conductor | 개별 최강 모델 | Mixture-of-Agents |
|----------|-----------|---------------|-------------------|
| LiveCodeBench | **83.9%** | 낮음 | 낮음 |
| GPQA-Diamond | **87.5%** | 낮음 | 낮음 |

논문은 Conductor가 개별 워커 모델과 Mixture-of-Agents 등 기존 멀티에이전트 베이스라인을 **더 낮은 컴퓨팅 비용으로** 능가한다고 보고한다.

---

## Fugu: Sakana의 상용 멀티에이전트 시스템

Conductor는 Sakana AI가 새롭게 공개한 멀티에이전트 시스템 **Fugu**의 핵심 기반이다. 이번 연구는 ICLR 2026에서 발표됐으며 arXiv(2512.04388)에서 전문을 볼 수 있다.

---

## 시사점

Conductor가 보여준 것은 단순한 성능 수치 이상이다. **"더 큰 단일 모델"이 아닌 "더 똑똑한 조율자"** 방향으로 AI 시스템 설계 패러다임이 이동하고 있음을 보여준다. 7B 모델이 수백억 파라미터 프론티어 모델들을 지휘해 더 나은 결과를 만들어낼 수 있다는 것은, 오케스트레이션 능력 자체가 독립적인 고부가가치 역량임을 시사한다.

에이전트 시대의 경쟁은 더 큰 모델이 아니라 더 잘 지휘하는 모델에서 갈릴 수도 있다.

---

**원문:** [Learning to Orchestrate Agents in Natural Language with the Conductor](https://sakana.ai/learning-to-orchestrate/) — Sakana AI, 2026.04.27  
**논문:** arXiv:2512.04388 · ICLR 2026
