---
title: "LLM을 활용한 세계 사건 예측: Mantic의 최신 연구"
date: 2026-05-13T09:00:00+09:00
description: "Mantic가 gpt-oss-120b를 RL fine-tuning하여 세계 사건 예측 성능을 대폭 향상시킨 연구를 분석합니다."
author: "TechLLM"
tags: ["LLM", "예측", "RL fine-tuning", "Mantic", "Metaculus"]
categories: ["기술 분석", "인공지능"]
image: "/images/llm-world-events-prediction-cover.jpg"
---

## LLM을 활용한 세계 사건 예측: Mantic의 최신 연구

2026년 3월 19일, Thinking Machines Lab의 Scott Jeen과 Matthew Aitchison이 Mantic와 협력한 연구를 발표했습니다. 이 연구는 **gpt-oss-120b를 RL fine-tuning하여 세계 사건 예측 성능을 대폭 향상**시킨 결과를 담고 있습니다.

### 배경: AI 예측 시스템의 급성장

AI 예측 시스템이 슈퍼포레캐스터 수준의 정확도에 근접하고 있습니다. Metaculus Cup 대회에서 최고의 AI 시스템들이 톱 프로 포레캐스터들을 제치고 있습니다.

기존의 최선의 방법론은 Gemini 3나 GPT-5 같은 오프더쉘 LLM을 사용하는 것이었습니다. 하지만 이 모델들은 예측 특화로 훈련되지 않았습니다. Mantic는 이 문제를 해결하기 위해 **예측 특화 fine-tuning**을 시도했습니다.

### 핵심 기법: RL Fine-tuning

#### 데이터셋
- ~10,000개의 이진형 질문: "[사건]이 [날짜] 이전에 일어날까?"
- 2024년 8월부터 2025년 12월까지의 질문들
- 모델의 지식 컷오프는 이 기간 이전

#### 학습 방법
- 정책 기울기 알고리즘 (GRPO-style advantage normalization)
- Brier score를 보상 함수로 사용 (안정성이 log score보다 우수)
- 배치 크기 64, 그룹 크기 8
- Tinker 플랫폼에서 실험 실행

### 결과: gpt-oss-120b 성능 향상

| 설정 | Baseline Score |
|------|---------------|
| 초기 (fine-tuning 전) | 38.6 |
| fine-tuning 후 | 45.8 |
| 프론티어 LLM 평균 | ~45 |

fine-tuning 후 점수는 38.6에서 45.8로 향상되어, Gemini 3 Pro와 거의 동등한 수준에 도달했습니다.

### 두 단계 아키텍처

Mantic의 예측 시스템은 두 단계로 구성됩니다:

1. **Research Phase (연구 단계)**
   - Deep research agents가 관련 정보 수집
   - 예: "2026년 이전에 미국이 베네수엘라를 공격할까?" 질문에 대해 군사 배치, 트럼프 대통령 발언, 베네수엘라 경제 상황 등 수집

2. **Prediction Phase (예측 단계)**
   - Mixture model을 활용한 확률 분포 출력
   - LLM이 다양한 시나리오를 포착하는 구성요소 선택
   - 최종 예측은 가중 조합

### 앙상블 예측의 핵심

**Wisdom of the Crowd 효과**: 여러 모델의 예측을 조합하면 개별 모델보다 우수한 결과를 얻습니다.

최적의 5-샘플 앙상블:
- fine-tuned gpt-oss-120b: 40%
- Gemini 3 Pro: 20%
- GPT-5: 20%
- Grok 4: 20%

Grok 4와 fine-tuned gpt-oss-120b가 가장 대체 불가능한 모델로, 이 둘의 예측이 기존 모델들과 낮은 상관관계를 보여 앙상블 다양성을 크게 증가시킵니다.

### 우리 시스템에 적용하면 좋은 점

#### 1. RL Fine-tuning의 활용
- gpt-oss-120b처럼 오픈소스 모델을 fine-tuning하면 비용 효율적
- Tinker 같은 플랫폼을 활용하면 대규모 학습 가능

#### 2. 두 단계 아키텍처
- Research + Prediction 분리로 예측 품질 향상
- 컨텍스트 수집 자동화로 인간 개입 최소화

#### 3. 앙상블 예측 전략
- 다양한 모델의 조합으로 예측 정확도 향상
- 상관관계가 낮은 모델 선택이 핵심

### 향후 전망

Mantic는 다음 방향을 탐색 중입니다:
- 더 큰 모델 훈련 (Kimi K2.5 등)
- 수치형 질문 확장 (경제 지표, 선거 결과 등)
- 정보 검색을 포함한 in-loop 학습

이 연구는 "AI를 잘 쓰는 사람은 프롬프트보다 업무 구조를 먼저 짠다"는 원칙과 완벽히 일치합니다. 세계 사건 예측이라는 구체적인 업무 목표를 명확히 하고, 그에 맞는 아키텍처와 학습 방법을 설계한 것이 핵심입니다.

---

**원문**: [Training LLMs to Predict World Events (Guest Post with Mantic) - Thinking Machines Lab](https://thinkingmachines.ai/news/training-llms-to-predict-world-events/)