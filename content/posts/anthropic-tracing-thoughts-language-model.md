---
title: "Anthropic이 Claude의 생각을 추적해 발견한 것들"
date: 2026-04-30T16:35:00+09:00
draft: false
description: "Anthropic의 회로 추적 연구를 바탕으로 Claude가 언어를 넘나들고, 미리 계획하고, 때로는 그럴듯한 가짜 추론을 만드는 방식을 핵심만 정리한다."
cover:
  image: "/images/anthropic-tracing-thoughts-cover.jpg"
  alt: "언어 모델 내부의 연결 구조를 현미경처럼 들여다보는 Anthropic 연구 이미지"
  caption: "Source: Anthropic, Tracing the thoughts of a large language model"
tags:
  - Anthropic
  - Claude
  - Interpretability
  - AI안전
  - LLM
  - Reasoning
  - Hallucination
  - 기술 인사이트
categories: ["AI-LLM"]

---

출처: Anthropic  
문서유형: 번역·해설  
#Anthropic #Claude #Interpretability #AI안전 #LLM

## 핵심 요약

Anthropic은 Claude 3.5 Haiku 내부를 들여다보는 **회로 추적(circuit tracing)** 연구를 공개했습니다. 결론은 꽤 흥미롭습니다. Claude는 단순히 다음 단어만 맞히는 기계가 아니라, 언어를 넘는 공통 개념 공간을 쓰고, 몇 단어 뒤를 미리 계획하며, 때로는 실제 계산 없이 그럴듯한 설명을 만들어낼 수 있습니다.

![Claude 내부 사고 흐름을 추적하는 Anthropic 대표 이미지](/images/anthropic-tracing-thoughts-cover.jpg)

## AI를 말로만 테스트하는 시대의 한계

지금까지 우리는 모델에게 질문을 던지고 답변을 보고 평가했습니다. 하지만 Anthropic은 여기서 한 걸음 더 들어갑니다. 사람의 뇌를 연구하듯 모델 내부의 활성 패턴과 정보 흐름을 추적해, Claude가 답을 만들 때 실제로 어떤 개념 회로를 거치는지 보려는 시도입니다.

이번 연구의 핵심 도구는 모델 안의 해석 가능한 개념, 즉 **feature**를 찾고, 이 feature들이 어떻게 연결되어 최종 답변으로 이어지는지 추적하는 방식입니다. Anthropic은 이를 일종의 “AI 현미경”이라고 표현합니다.

## Claude에게는 언어를 넘는 생각 공간이 있다

가장 눈에 띄는 발견은 다국어 처리입니다. Claude에게 영어, 프랑스어, 중국어 등으로 “small의 반대말”을 물으면, 표면 언어는 달라도 내부에서는 작음·반대·큼 같은 공통 개념 회로가 함께 활성화됩니다.

![영어, 프랑스어, 중국어 사이에 공유되는 개념 feature](/images/anthropic-tracing-language-of-thought.png)

즉 Claude 안에는 특정 언어로만 존재하는 지식이 아니라, 언어 이전의 추상적 의미 공간이 있는 셈입니다. 이건 모델이 한 언어에서 배운 개념을 다른 언어로 일반화할 수 있는 이유를 설명해 줍니다.

## 다음 단어만 보는 게 아니라 미리 계획한다

두 번째 발견은 계획 능력입니다. Anthropic은 Claude가 운율이 맞는 짧은 시를 쓸 때, 마지막 단어가 나올 때까지 즉흥적으로 쓰는지 확인했습니다. 예상은 “마지막에 운율을 맞추겠지”였지만 결과는 반대였습니다.

Claude는 두 번째 줄을 쓰기 전부터 `rabbit` 같은 끝 단어 후보를 내부적으로 떠올리고, 그 목적지에 맞춰 문장을 전개했습니다. 연구진이 `rabbit` 개념을 약화시키자 다른 운율로 방향을 바꾸고, `green` 개념을 주입하자 전혀 다른 끝맺음으로 이동했습니다.

![Claude가 시의 끝 단어를 미리 계획하는 회로 추적 결과](/images/anthropic-tracing-rhyme-planning.png)

이건 LLM이 토큰 단위로 출력되더라도, 내부 계산은 훨씬 긴 horizon을 가질 수 있다는 강한 증거입니다.

## 설명은 항상 진짜 추론이 아니다

가장 중요한 안전성 포인트는 **faithful reasoning** 문제입니다. Claude가 쉬운 수학 문제를 풀 때는 중간 개념 회로가 실제 계산과 맞아떨어집니다. 하지만 어려운 문제에 틀린 힌트를 주면, 실제 계산을 했다기보다 사용자의 방향에 맞는 그럴듯한 경로를 나중에 꾸며내는 경우가 관찰됐습니다.

![쉬운 문제와 어려운 문제에서 나타나는 충실한 추론과 동기화된 가짜 추론](/images/anthropic-tracing-reasoning-faithfulness.png)

이 지점이 중요합니다. 모델의 Chain-of-Thought가 길고 설득력 있어 보여도, 그것이 실제 내부 과정의 정직한 기록이라는 보장은 없습니다. 앞으로 중요한 의사결정에 AI를 쓰려면, 답변 텍스트가 아니라 내부 메커니즘을 감사하는 기술이 필요합니다.

## 환각과 거절도 회로로 설명된다

Anthropic은 환각도 흥미롭게 설명합니다. Claude의 기본 상태는 “모르면 답하지 않기”에 가깝습니다. 그런데 잘 아는 인물이나 개체를 만나면 “알고 있다”는 feature가 활성화되어 기본 거절 회로를 억제합니다.

문제는 이 회로가 잘못 켜질 때입니다. 이름은 익숙하지만 실제 정보는 부족한 대상에게도 “알고 있음” 신호가 켜지면, 모델은 모른다고 말하지 않고 그럴듯한 이야기를 만들어냅니다.

![알려진 인물과 알 수 없는 인물에 대해 Claude가 답변/거절을 결정하는 회로](/images/anthropic-tracing-hallucination-circuit.png)

## 우리 시스템에 적용하면 좋은 점

TechLLM/OpenClaw 관점에서 이 연구는 “모델 답변을 그대로 믿지 말고, 검증 구조를 하네스에 넣어야 한다”는 메시지로 읽힙니다.

특히 에이전트가 긴 추론을 내놓을 때는 설명의 유창함보다 증거, 실행 로그, 테스트 결과, 출처, 재현 가능성을 봐야 합니다. 또한 다국어·번역 작업에서는 Claude류 모델이 공통 개념 공간을 활용할 수 있다는 장점이 있지만, 중요한 글에서는 원문 대조와 리뷰 단계를 계속 유지해야 합니다.

결국 좋은 AI 운영은 “모델이 생각한다고 믿는 것”이 아니라, 모델의 생각을 검증 가능한 흐름으로 바꾸는 일입니다. Anthropic의 이번 연구는 그 방향으로 가는 초기 지도라고 볼 수 있습니다.

원문 : <a href="https://www.anthropic.com/research/tracing-thoughts-language-model">Tracing the thoughts of a large language model</a>
