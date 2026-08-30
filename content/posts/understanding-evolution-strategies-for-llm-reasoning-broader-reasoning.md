---
title: "언어모델을 키우는 새로운 방법을 오래된 방법과 비교해, 더 다양한 풀이 길을 유지하면서 실력을 늘릴 수 있음을 보인 연구."
date: 2026-08-31T07:40:30+09:00
draft: false
description: "본 논문은 Evolution Strategies(ES)와 GRPO의 사후 학습 거동을 체계적으로 비교하여, ES가 GRPO의 엔트로피 붕괴 없이 Pass@1을 개선하면서도 더 넓은 Pass@K 추론 범위를 유지함을 이론적·실험적으로 입증한다. 또한 ES의 파라미터 변화는 기능적으로 희소하며, 대규모 모델일수록 더 작은 population size로 안정적 학습이 가능함을 보인다."
cover:
  image: "/images/understanding-evolution-strategies-for-llm-reasoning-broader-reasoning/_page_0_Figure_8.jpeg"
  alt: "세 가지 연구 질문(RQ1~3)과 주요 발견을 한눈에 보여주는 전체 구조도"
  caption: "논문 원문 발췌"
tags: ["Large Language Model / Post-Training", "논문 분석", "논문 리뷰", "Evolution Strategies", "GRPO", "Pass@K"]
categories: ["논문분석"]
---


언어모델을 키우는 새로운 방법을 오래된 방법과 비교해, 더 다양한 풀이 길을 유지하면서 실력을 늘릴 수 있음을 보인 연구.

**무엇이 문제였나** — 기존 강화학습 방식(GRPO)은 한 번에 한 길로만 정답을 맞추려다 보니 다양한 사고방식을 잃어버리는 문제가 있었다.
**어떻게 풀었나** — 진화전략(ES)이라는 무작위 방향 탐색 방식을 써서, 여러 갈래의 풀이를 동시에 시험하고 좋은 방향만 모아 학습시켰다.
**그래서 뭐가 좋아졌나** — 그 결과, 단발 정답률도 오르면서 여러 번 시도했을 때 정답을 찾을 확률도 더 좋아졌다.

> 여러 학생이 같은 문제에 각자 다른 풀이법으로 답안을 쓰고, 선생님이 점수가 높은 답안의 특징만 모아 다음 학습에 반영하는 것과 같다. 모든 답안이 비슷한 한 가지 스타일로 수렴하지 않기 때문에, 시험 문제가 살짝 달라져도 대응할 수 있는 다양한 실력이 유지된다.

## 논문 정보

Yunpeng Ba, Zhi Zheng, Yue Xie, Jiaqing Li et al. · Southern University of Science and Technology, NUS, Huawei Noah's Ark Lab, CityU HK, HIT Weihai · ICML 2026 (preprint) · 2026

## 왜 중요한가

AI가 한 번에 답을 맞히는 능력만 좋아지면, 결국 한 가지 패턴만 달달 외우는 학생이 된다. 여러 번 시도해 정답을 찾을 능력까지 유지하면, 실제 시험이나 코딩처럼 여러 시도가 허용되는 상황에서 훨씬 유리하다. 또한 학습 과정에서 원래 알고 있던 지식을 까먹지 않는지도 중요한데, 이 연구는 그 균형점을 잘 잡았다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Pass@32 평균 개선폭 (Hard Setting) | **+1.5%p** | Base Model(77.4) 대비 ES(78.9)의 평균 Pass@32 차이 (AIME24/25, AMC23, MATH500) |
| GRPO의 Pass@K 열화 빈도 | **83.3% (15/18)** | Easy Setting에서 GRPO가 Base Model 대비 Pass@16과 Pass@32에서 모두 열화한 비율 |
| ES 파라미터 드리프트 비율 | **40.7~44.1× (vs GRPO)** | 4개 모델에서 Full ES의 상대적 L2 거리가 GRPO 대비 몇 배인지를 나타냄 |
| Population size 절감 (1.5B+ 모델) | **4× (N=16 vs N** | Qwen2.5-1.5B/3B-Instruct에서 N=16이 N=64 대비 0.01 이내 보상 도달 (Table 6, update 300) |

## 어떻게 동작하나

본 연구는 LLM 추론 능력 사후 학습 패러다임으로 떠오른 Evolution Strategies(ES)와 주류 방법인 GRPO를 세 가지 질문으로 비교한다. 먼저 ES의 파라미터 perturbation이 Jensen-Shannon 다양도를 통해 Pass@K를 개선할 수 있음을 수학적으로 증명하고(Proposition 1), GSM8K(Easy) 및 DeepScaleR(Hard) 환경에서 4개 모델로 실증한다. 다음으로 ES의 전체 파라미터 드리프트가 GRPO 대비 40배 이상 크지만, 이는 작은 magnitude의 노이즈 이동이 누적된 결과이며 성능 기여는 큰 magnitude 업데이트의 sparse 부분집합에 집중됨을 보인다. 마지막으로 z-score 보상 정규화, 1-point estimator, 그리고 모델 스케일에 따른 population size 축소(N=16이면 1.5B+에서 N=64과 동등)라는 실전 가이드라인을 제시한다.

![세 가지 연구 질문(RQ1~3)과 주요 발견을 한눈에 보여주는 전체 구조도](/images/understanding-evolution-strategies-for-llm-reasoning-broader-reasoning/_page_0_Figure_8.jpeg)
*세 가지 연구 질문(RQ1~3)과 주요 발견을 한눈에 보여주는 전체 구조도*

ES vs GRPO 거동 비교, 파라미터 드리프트 vs 기능적 희소성, 정규화·population·estimator 선택의 세 축이 한 프레임에 정리되어 있다.

핵심 수식:

```
\hat{d}_{ES} = \frac{1}{N} \sum_{i=1}^{N} z_i \epsilon_i, \quad \theta^+ = \theta + \alpha \hat{d}_{ES}
```

\epsilon_i: 표준 정규 분포에서 추출한 i번째 perturbation 방향, z_i: 표준화된 보상(z-score), N: population 크기, \alpha: 업데이트 스케일, \theta/\theta^+: 업데이트 전/후 모델 파라미터

## 한계와 주의할 점

- ES는 한 업데이트당 N개의 forward pass가 필요하여 동일 연산 예산 대비 wall-clock 시간이 길어질 수 있다.
- Perturbation scale σ에 민감하며, 너무 작으면 지역 최적에 갇히고 너무 크면 발산한다.
- 본 연구는 1~2 에폭 단기 학습만 평가하여, 수 개월에 걸친 continual learning에서의 catastrophic forgetting 거동은 충분히 규명되지 않았다.
- 검증 가능한 보상(verifier reward)이 있는 추론 과제 위주로 평가되어, 보상이 희소하거나 연속적인 다른 도메인(예: 대화 생성)에는 일반화가 검증되지 않았다.
- Abdi et al.(2026)이 보고한 catastrophic forgetting과의 모순은 학습 데이터셋 크기와 과제 구성의 차이로 설명되지만, 어떤 조건에서 어느 결과가 나오는지에 대한 정량적 경계는 제시되지 않았다.
- 작은 모델(0.5B) + 작은 population(N=8, 16) 조합에서는 후기 업데이트에서 보상이 하락하여 안정적 개선이 어렵다(Table 6).
- z-score 정규화를 생략하면 reward-guided 최적화 효율이 떨어져 학습이 정체된다(Figure 1c, item 1).
- GSM8K와 같이 regenerated rollout이 필요한 환경에서 2-point ES는 paired evaluation의 공분산이 약해 분산 감소 이점이 사라진다(Appendix E, Table 13).
- 학습 분포와 다른 분포의 평가 프롬프트가 들어오면, ES의 population diversity 이점이 그대로 전달되지 않을 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 추론 fine-tuning 파이프라인에 ES→GRPO 순차 조합 도입

1단계에서 1-point ES를 1 epoch 적용해 population diversity를 확보하고(AIME24 Pass@16 60.3 → 70.6 같은 large-K 이점 유지), 2단계에서 GRPO로 Pass@1을 끌어올린다(Table 3 기준 ES→GRPO가 Hard Setting 평균 Pass@32 79.2로 최고치 도달). 적용 지점은 추론 모델 후속 학습 단계의 마지막 30~50% 구간이다. 동일 총 업데이트 예산 내에서 Pareto 전선을 확장할 수 있다.

**적용 지점** — 추론 LLM 후속 학습 파이프라인의 마지막 fine-tuning 단계

**기대 효과** — Hard Setting Pass@32 78.9(ES) → 79.2(ES→GRPO), Pass@1 49.9(ES) → 52.3(ES→GRPO) 동시 달성(Table 3 평균)

### z-score 보상 정규화를 GRPO/REINFORCE 계열 보상 가중치에 적용

논문 Section 5.1의 핵심 발견은 z-score 정규화 없이는 matched 1-point ES에서도 보상 가이드 최적화가 일관되게 저하된다는 점이다(RQ3, Figure 1c item 1). 적용 지점은 population 단위 보상 집계 직후, 가중치 계산 직전이다. 이는 GRPO의 group advantage 계산과 동일한 형태이며, reward 신호의 스케일 의존성을 제거해 학습 안정성을 개선한다.

**적용 지점** — verifier reward 기반 fine-tuning의 reward 가중 단계

**기대 효과** — matched single-point ES에서 정규화 미적용 대비 더 높은 training reward를 일관되게 달성(RQ3 Takeaway 1)

### 모델 스케일 기반 population size 자동 축소 규칙 도입

논문 Table 6은 Qwen2.5-0.5B는 N=32, 1.5B/3B는 N=16만 해도 N=64 대비 0.01 이내 보상을 얻음을 보인다. 적용 지점은 ES fine-tuning job의 population size 설정 단계이며, 4배의 forward pass 절감으로 wall-clock을 단축한다. "larger models contain more effective structures"(Section 5.1) 가설을 실전 운영 규칙으로 구체화한다.

**적용 지점** — ES 기반 fine-tuning job의 population size 설정

**기대 효과** — 1.5B+ 모델에서 N=64 → N=16으로 4배 forward pass 절감, reward 손실 0.01 이내(Table 6 update 300)

### 큰 magnitude 업데이트 subset만 모니터링하는 품질 게이트

논문 Section 4.2는 ES의 성능 기여가 7~22%의 큰 magnitude 업데이트에 집중됨을 보인다(0<(0,τ] 범위 s_τ=77.6~93.0%). 적용 지점은 학습 루프의 매 N step checkpoint 평가 단계로, top-K magnitude 파라미터의 위치(LayerNorm, attention projection)와 누적량을 별도 로깅한다. catastrophic forgetting 조기 감지와 ES/GRPO 진단 자동화의 기준으로 사용한다.

**적용 지점** — fine-tuning 체크포인트 평가 파이프라인의 drift 진단 단계

**기대 효과** — target-task Pass@1이 sparsity 92.47~98.11%까지도 base model 이상을 유지(Table 4, Figure 4) — 작은 업데이트는 모니터링 비용만 늘리고 정보가 적음

### 메모리 제약 환경용 1-point ES 추론 fine-tuner 공개

논문 Appendix E는 regenerated rollout이 필요한 추론 과제에서는 2-point ES의 paired subtraction이 분산 감소 이점을 잃음을 보인다(Table 13, GSM8K κ_pair=1.9870). 즉 추론 fine-tuning에서는 1-point가 2-point 대비 우위다. 적용 지점은 memory-efficient fine-tuning 옵션 선택 단계이며, ES를 GRPO의 대안(메모리 효율)뿐 아니라 동등한 대안(검증된 Pass@K 보존)으로 포지셔닝한다.

**적용 지점** — memory-constrained 환경의 LLM fine-tuning 도구 선택 단계

**기대 효과** — 1-point ES는 GRPO 대비 backprop state 미저장으로 activation memory 절감, GSM8K에서 2-point 대비 보상/성능 우위(RQ3 Takeaway 3)

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 (파일럿, 2~4주) | ES 기본 파이프라인 재현 및 baseline 비교 | Qwen2.5-1.5B-Instruct + GSM8K 1 epoch로 1-point ES(z-score 정규화, N=32) vs GRPO 학습을 동일 연산 예산으로 수행, Pass@1/16/32과 entropy trajectory 측정 | GRPO의 entropy collapse와 Pass@32 baseline 미달 여부를 자체 환경에서 확인, ES 도입 정당성 확보 |
| Phase 2 (스케일 검증, 1~2개월) | 모델 크기·population size·순차 조합 최적화 | 1.5B/3B/7B 모델에서 N∈{8,16,32,64} sweep, ES→GRPO 및 GRPO→ES 순차 조합으로 Pareto 전선 확장, held-out 태스크(MBPP, CSQA 등) 보존율 검증 | GPU당 처리 가능한 perturbation 수 도출, 메모리·시간 제약 하 최적 구성 확정 |
| Phase 3 (운영 배포, 2~3개월) | 프로덕션 추론 서비스에 ES 후속 학습 통합 | 검증된 하이퍼파라미터 세트를 학습 파이프라인에 자동화, 평가 세트에 Pass@K 모니터링 추가, catastrophic forgetting 조기 경보용 held-out 체크포인트 평가 체계 구축 | 단발 정확도와 재시도 성공률 모두 개선된 모델 버전 출시, 사용자당 과제 완수율 상승 |

---

원문 PDF: `2026-08-31-understanding-evolution-strategies-for-llm-reasoning-broader-reasoning-c.pdf`
