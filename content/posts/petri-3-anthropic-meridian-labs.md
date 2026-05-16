---
title: "Anthropic, 얼라인먼트 테스트 도구 Petri를 Meridian Labs에 기증 — 버전 3.0 핵심 정리"
date: 2026-05-15T21:15:00+09:00
draft: false
description: "Anthropic이 오픈소스 얼라인먼트 테스트 도구 Petri를 Meridian Labs에 기증하고 버전 3.0을 출시했다. 영국 AISI가 이미 활용 중이며, 중립적 AI 평가 생태계 구축의里程碑이다."
cover:
  image: /images/petri-3-anthropic-meridian-labs.png
  alt: "Petri 3.0 architecture showing auditor/target model separation and Bloom integration"
  caption: ""
tags:
  - AI
  - Alignment
  - Open Source
  - AI Safety
  - Petri
  - Anthropic
  - Meridian Labs
categories:
  - AI 안전 & 보안
  - LLM & 모델

---

## 핵심 요약

- Anthropic의 오픈소스 얼라인먼트 테스트 도구 **Petri**가 Meridian Labs로 이전되며 새로운 주인에게 건너갔다
- 버전 3.0의 핵심 변화 3가지: **적응성(분리 구조)** · **현실성(Dish 애드온)** · **심층성(Bloom 연동)**
- 영국 AI 보안연구소(AISI)가 이미 saboteur 평가 주요 수단으로 활용 중
- MCP/Linux Foundation 기증과 같은 구조 — 중립적 평가 생태계 구축 의도
- Petri 설치·사용 문서: `meridianlabs-ai.github.io/inspect_petri/`

---

## Petri란 무엇인가 — Claude를 시험하는 도구

Anthropic은 최근 자사의 핵심 AI 정렬 테스트 도구인 **Petri**를 Meridian Labs라는 비영리 기관에 기증했다. Petri는 Anthropic의 Fellows 프로그램에서 탄생하며, Claude 시리즈의 신뢰성을 검증하기 위해 만들어진 도구다. 이미 **Claude Sonnet 4.5부터 모든 Claude 모델**에 공식 적용되어 있다.

Petri의 동작 구조는 세 층으로 구성된다. **Auditor 모델**이 대상 모델의 행동을 평가하고, **Target 모델**이 실제 테스트 대상이 되며, **Judge 모델**이 최종 판정을 내린다. 이 구조를 통해 연구자들은 모델이 펼치는 의심스러운 행동 — 거짓말, 아부, 유해한 요청에 대한 순순한 협력 등 — 을 체계적으로 포착할 수 있다. Petri는 쉽게 말해 **AI 모델에 대한 감시 카메라** 역할을 하는 셈이다.

## 영국 AI Security Institute도 채택한 도구

이 도구가 단순한 사내 테스트 도구를 넘어서지 않은 이유는 분명하다. **영국 AI Security Institute(AISI)**가 이미 saboteur 평가를 위한 주요 수단으로 Petri를 활용하고 있다는 사실이다. 이는 [arxiv 논문](https://arxiv.org/abs/2604.00788으로도公开发표되었다.

외부 기관이 실제 평가에 채택했다는 것의 의미는 크다. 영국 정부 산하 기관이 채택했다는 사실 자체가 Petri의 신뢰성에 대한 업계의 인정이라 할 수 있다.

## Petri 3.0의 3대 변화 — 적응성·현실성·심층성

기부 소식과 함께 **버전 3.0**도 함께 출시됐다. 이번 업데이트는 세 가지 핵심 변화를 담고 있다.

### ① 적응성 — Auditor와 Target의 분리

기존 버전에서는 auditor와 target이 하나의 모델 안에서 함께 동작했다. 버전 3.0에서는 이 둘이 **별도의 컴포넌트로 분리**됐다. 덕분에 감사자와 대상 모델을 개별적으로 튜닝할 수 있게 되었다. 평가 대상과 평가자를 분리했다는 것은 곧 더 유연한 테스트 시나리오 구축이 가능해졌다는 의미다.

### ② 현실성 — "Dish" 애드온으로 실제 환경 재현

AI 평가의 가장 큰 문제는 **모델이 "테스트 중임을 감지"** 한다는 것이다. 모델이 자신의 평가받고 있음을 알아채면, 정상적인 반응 대신 평가자에게 잘 보이려는 행동을 보일 수 있다. 이것이 바로 정렬 테스트의 근본적 딜레마다.

Petri 3.0은 이 문제를 해결하기 위해 **Dish**라는 애드온을 도입했다. Dish는 실제 시스템 프롬프트와 실제 스캐폴드를 테스트 환경에 그대로 적용한다. 이를 통해 모델은 자신이 평가 중임을 인지하지 못한 채 실제와 동일한 조건에서 작동하게 된다. 비유하자면, 연습장 환경에서 연습하는 선수와 실제 경기장에서 경기에 임하는 선수의 차이와 같다. **실제 경기장**에서 해야 진짜 실력이 드러나는 것처럼, AI 모델도 실제 환경과 동일한 조건에서 평가받아야 한다.

### ③ 심층성 — Bloom 연동으로 더 깊은 분석

Petri는 넓은 범위의 행동을 스캐닝하는 데 강점이 있다. 반면 **Bloom**은 특정 행동에 대한 심층 평가에 초점을 맞춘다. Petri 3.0은 이 두 도구를 연동할 수 있게 되었으며, Petri가 포착한 이상 행동을 Bloom으로 넘겨 더 깊이 분석하는 **양방향 평가 체계**를 구현했다. 넓은 스캔과 심층 분석이 결합되면서 평가의 정밀도가 한 단계 끌어올려졌다.

## 왜 "비영리" 기관에 기부가 중요한가

Anthropic은 이번 Petri 기증 이전에도 **Model Context Protocol(MCP)**을 Linux Foundation에 기증한 바 있다. 이번 기증도 같은 맥락에서 이해할 수 있다.

핵심은 **중립성**이다. 만약 Petri가 Anthropic 단독으로 운영된다면, 평가 결과에 대해 "자사의 모델을 우호적으로 평가하고 있지 않은가"라는 편향 의심에서 자유로울 수 없다. 그러나 비영리 기관인 Meridian Labs로 이전되면, 결과는 특정 AI 기업에 종속되지 않은 **공인 검사소**의 판정으로 받아들여지게 된다.

Meridian Labs는 현재 Inspect, Scout 등 AI 평가 기술 스택을 구축하고 있다. Petri의 추가는 이 생태계에 핵심 인프라를填补하는 셈이다. 업계 전체가 신뢰할 수 있는 중립적 평가 기관으로 자리매jang하는 것이 목표이며, 이는 AI 안전 세상을 위한 **공공재**로서의 역할을 의미한다.

## VSS, 어디서 어떻게 쓰나

Petri 3.0과 Dish는 이미 Meridian Labs의 블로그를 통해详细介绍되었다. 직접 시도해보고 싶은 분은 아래 링크에서 설치 및 사용 문서를 확인할 수 있다.

> 📎 Meridian Labs — Petri & Inspect 문서  
> `meridianlabs-ai.github.io/inspect_petri/`

## 정리 — AI 안전성, 더 이상 "블랙 박스"가 아닌 개방형 인프라

Petri의 Meridian Labs 이전은 단순한 기부가 아니다. AI 안전성이라는 분야를 **민간 기업 차원에서 공공재화하는 전략적 선택**이다.

영국 AISI라는 국가 기관이 실제로 활용하고, 비영리 기관이 운영하며, 오픈소스로 공개되는 구조. 이것은 AI 평가 분야에 있어서 **MCP/Linux Foundation**과 같은 선례가 될 수 있다는 것을 의미한다. 더 이상 AI 모델의 안전성을 평가하는 일은 특정 기업의 비공개 테크닉에 의존하지 않아도 되는 시대가 되고 있는 것이다.

AI가 점점 더 많은 영역에 영향을 미치는 지금, 그 모델을 검증하는 도구까지 열려 있어야 한다. Petri는 바로 그 열린 인프라의 첫 번째 사례다.

---

## 실무자가 보는 핵심 포인트

1. **AI 평가도 "표준화" 시대**: Petri가 비영리 기관으로 이전된 것은 AI 안전성 테스트가 특정 기업 종속이 아닌 업계 공통 인프라로 전환되고 있다는 신호다. 실무에서 AI 시스템을 도입할 때 정렬 평가 기준을 스스로 확인하는 습관이 중요해졌다.
2. **"테스트 인지" 문제의 해결**: Dish 애드온은 단순한 기능이 아니라 AI 평가의 근본적 한계를 해결하는 접근이다. 실무에서도 AI 시스템을 평가할 때 "실제 환경과 동일한 조건"을 만드는 것이 얼마나 어려운지 알 수 있다.
3. **중립적 평가의 가치**: 특정 기업에서 운영하는 도구보다 비영리 기관의 도구가 더 신뢰받는 시대다. AI 솔루션을 도입할 때 어떤 평가 체계를 거쳤는지 확인하는 것도 선택 기준이 될 수 있다.

---

*원문: <a href="https://www.anthropic.com/research/donating-open-source-petri">Anthropic - Donating our open-source alignment tool</a>*