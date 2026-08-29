---
title: "수학 문제 풀이를 가르칠 때, 큰 모델 혼자 백지에서 풀지 말고 다른 가족의 작은 모델이 좀 풀어놓은 데서 이어서 풀게 하면 더 다양한 풀이법을 익힌다."
date: 2026-08-30T07:38:46+09:00
draft: false
description: "RLVR(검증 가능한 보상 기반 강화학습) 후훈련 단계에서 발생하는 정책 엔트로피 붕괴와 추론 다양성 감소 문제를 해결하기 위해, 더 작고 약한 모델이 생성한 부분 추론 경로를 prefix로 사용하는 prefix-completion RLVR 프레임워크를 제안한다. 타겟 모델이 약한 모델의 prefix를 이어서 풀도록 훈련하면 자기 확신이 강한 경로에서 벗어나 새로운 추론 경로를 탐색하게 되며, 수학 추론 6개 벤치마크 평균에서 Qwen2.5-7B는 pass@128이 vanilla GRPO 67.76%에서 70.71%로…"
cover:
  image: "/images/boosting-llm-exploration-via-weak-model-guidance-in-rlvr/_page_4_Diagram_0.jpeg"
  alt: "Prefix-completion RLVR 프레임워크 전체 개요"
  caption: "논문 원문 발췌"
tags: ["Large Language Model / Reinforcement Learning", "논문 분석", "논문 리뷰", "RLVR", "GRPO", "정책 엔트로피"]
categories: ["논문분석"]
---


수학 문제 풀이를 가르칠 때, 큰 모델 혼자 백지에서 풀지 말고 다른 가족의 작은 모델이 좀 풀어놓은 데서 이어서 풀게 하면 더 다양한 풀이법을 익힌다.

**무엇이 문제였나** — 큰 AI가 같은 유형의 수학 문제만 반복해 풀면 한 가지 풀이 방식에 고착되어 새로운 문제를 잘 못 푼다.
**어떻게 풀었나** — 다른 계열의 작은 AI가 일부 풀어놓은 추론을 시작점으로 주고, 큰 AI가 나머지를 이어서 풀도록 훈련한다.
**그래서 뭐가 좋아졌나** — 큰 AI가 다양한 풀이법을 탐색하게 되어, 여러 번 시도하면 더 많은 문제를 맞출 수 있게 된다.

> 학생이 혼자 백지에서 시작하면 한 가지 방법만 떠올리지만, 다른 학생이 일부 풀어놓은 것을 보고 이어서 풀면 더 다양한 해결책을 떠올릴 수 있다. 어설픈 풀이도 오히려 새로운 시각을 자극하는 계기가 된다.

## 논문 정보

Xingyu Shen, Huishuai Zhang, Peng Li, Yinchun Wang, Dongyan Zhao et al. · Peking University (Wangxuan Institute of Computer Technology), National Engineering Research Center of New Electronic Publishing Technologies · Preprint (arXiv) · 2025

## 왜 중요한가

AI가 수학이나 코딩 문제를 풀 때 한 가지 방식만 고집하면 새로운 유형의 문제를 못 푸는 약점이 있다. 다양한 풀이법을 가르치는 것이 더 똑똑하고 안정적인 AI를 만드는 핵심이며, 이 연구는 그 다양성을 데이터 수준에서 가볍게 살리는 새로운 방법을 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Qwen2.5-7B pass@1 | **39.01%** | Gemma-2-2B prefix vs vanilla GRPO 38.29% (6벤치 평균) |
| Qwen2.5-7B pass@128 | **70.71%** | Gemma-2-2B prefix vs vanilla GRPO 67.76% (6벤치 평균) |
| Qwen2.5-7B + LLaMA-3.2-1B prefix pass@128 | **69.06%** | LLaMA-3.2-1B prefix vs vanilla GRPO 67.76% (6벤치 평균) |
| Qwen2.5-Math-7B pass@1 | **40.11%** | Gemma-2-2B prefix vs vanilla GRPO 40.08% (6벤치 평균) |

## 어떻게 동작하나

RLVR로 추론을 가르칠 때 모델의 정책 엔트로피가 빠르게 떨어지면서 한 가지 풀이 방식에 고착되는 문제를 다룬다. 저자들은 타겟 모델과 다른 계열의 1B~2B급 작은 모델(LLaMA-3.2-1B, Gemma-2-2B 등)이 만든 풀이를 '원본'으로 사용하고, 그 풀이를 엔트로피가 급격히 떨어지기 직전까지 잘라 prefix로 만든다. 타겟 모델은 이 prefix를 이어서 풀도록 학습되며, 전체 학습 데이터의 80%는 원래 질문만, 20%는 prefix가 붙은 형태로 섞어 평가 시점(질문만 받는 상황)과 일치시킨다. 이 데이터 수준 교란만으로 KL 페널티, 복잡한 보상 설계, 추가 SFT 없이 추론 다양성을 회복할 수 있다.

![Prefix-completion RLVR 프레임워크 전체 개요](/images/boosting-llm-exploration-via-weak-model-guidance-in-rlvr/_page_4_Diagram_0.jpeg)
*Prefix-completion RLVR 프레임워크 전체 개요*

작은 모델이 만든 풀이를 엔트로피 기반으로 자른 뒤, 그 prefix 위에서 타겟 모델이 나머지를 이어 풀도록 GRPO를 수행하는 두 갈래 흐름을 보여준다.

핵심 수식:

```
\theta^* = \operatorname{argmax}_{\theta} \mathbb{E}_{q \sim \mathcal{D}} \left[ (1-p)\,\mathbb{E}_{r \sim \pi_{\theta}(\cdot|q)} R(q, r) \;+\; p\,\mathbb{E}_{r_{\text{suf}} \sim \pi_{\theta}(\cdot|q, \tilde{r})} R(q, \tilde{r} \circ r_{\text{suf}}) \right]
L^* = \operatorname{argmax}_{L} \left[ \bar{H}_{\theta_0}(\tilde{s}_L) - \bar{H}_{\theta_0}(\tilde{s}_{L+1}) \right]
```

상단은 혼합 학습 목적함수: (1-p) 확률로 원래 질문만으로, p 확률로 약한 모델의 prefix r̃를 이어 풀도록 한다(p=0.2). 하단은 prefix 절단 지점 결정식: 인접 두 reasoning step의 평균 엔트로피 차이가 최대가 되는 L* 지점에서 자르며, 이 지점 직후에 타겟 모델의 불확실성이 급격히 줄어드는 구간이 시작하므로 그 직전까지의 prefix만 보존한다.

## 실험 결과

![Step-level 엔트로피 동역학 (Qwen2.5-7B, GRPO 전/후)](/images/boosting-llm-exploration-via-weak-model-guidance-in-rlvr/_page_3_Figure_8.jpeg)
*Step-level 엔트로피 동역학 (Qwen2.5-7B, GRPO 전/후)*

약한 모델 prefix에 조건부일 때 타겟 모델은 초반 추론 step에서 더 높은 엔트로피를 보이며, GRPO 후에도 cross-model prefix가 더 넓은 탐색 신호를 제공함을 시사한다.

![Prefix 주입 확률 p에 따른 학습 동역학 (4-panel)](/images/boosting-llm-exploration-via-weak-model-guidance-in-rlvr/_page_6_Figure_2.jpeg)
*Prefix 주입 확률 p에 따른 학습 동역학 (4-panel)*

p가 높을수록 초기 엔트로피가 더 유지되어 보상 sparsity 문제가 완화되지만, 동시에 평균 보상이 낮아지는 trade-off가 존재한다.

![Prefix 품질 분포 (4-class 분류, 모델별)](/images/boosting-llm-exploration-via-weak-model-guidance-in-rlvr/_page_7_Figure_0.jpeg)
*Prefix 품질 분포 (4-class 분류, 모델별)*

작은 모델 prefix는 대부분 'no guidance' 또는 'misleading'임에도 cross-family prefix는 pass@k를 올리며, perturbation 자체가 효용의 핵심임을 보여준다.

## 한계와 주의할 점

- 하이퍼파라미터 p에 민감: p=0.2가 최적이지만 p=0.5부터 pass@128 개선이 사라지고, p=1.0에서는 pass@1까지 하락한다(논문 Table 2).
- 수학 추론 도메인에서만 검증: 논리, 코드, 일반 상식 추론 등 다른 도메인에서의 효과는 확인되지 않았다(Limitations 섹션).
- prefix 품질이 대부분 낮음: 6.2절의 4-class 분석에서 small model prefix의 다수가 'no guidance' 또는 'misleading'으로 분류되어 보조 모델 선택이 까다롭다.
- 동일 계열 prefix는 효과 없음: Qwen2.5-1.5B·Qwen2.5-7B prefix는 vanilla GRPO 대비 개선이 없어, 결국 cross-family 약한 모델이 필수다(논문 Table 2).
- prefix 생성에 별도 추론 비용 발생: 학습 시작 전에 base model로 엔트로피 기반 절단 지점을 한 번만 계산하지만, prefix 자체는 작은 모델로 매번 생성해야 한다.
- 약한 모델이 타겟과 너무 가까우면(같은 계열·비슷한 크기) 분포 교란이 부족해 pass@k 개선이 사라진다(논문 Table 2, Qwen2.5-1.5B/Qwen2.5-7B prefix).
- p=0.5 이상으로 prefix 비율을 높이면 학습·평가 컨텍스트 불일치가 발생해 pass@1·pass@128 모두 하락한다(논문 Table 2, p=1.0).
- prefix가 너무 길면 모델이 중간 추론을 건너뛰고 답만 출력해 정책 학습이 제대로 되지 않는다(섹션 4.2, 너무 긴 prefix 경고).
- 약한 모델 prefix가 misleading한 경우, 모델이 잘못된 중간 단계를 답습해 오답으로 수렴할 수 있다(섹션 6.1·6.2).

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 약한 모델 prefix perturbation을 RAG 재순위 단계로 이식

RAG 파이프라인에서 top-k 청크가 결정되면, 이를 다른 계열·더 작은 모델(LLaMA-3.2-1B, Gemma-2-2B 등)로 재요약·재구성한 단락을 원본 청크 앞에 prefix로 붙여 메인 모델에 입력한다. 본 논문의 prefix-completion RLVR이 훈련 단계에서 '자기 확신 경로에서 벗어나기' 위해 다른 모델의 흔적을 넣은 것과 같은 메커니즘이다. 추론 단계에서도 같은 효과를 내려면 prefix 생성 모델이 메인 모델과 다른 계열이어야 하고, prefix 길이는 메인 모델의 첫 추론 step 직전까지 조절한다(섹션 3의 엔트로피 분석 참조).

**적용 지점** — RAG 파이프라인의 재순위 단계 입력 구성

**기대 효과** — pass@k(k≥8) 최대 +2.95%p (논문 Table 1, Qwen2.5-7B에서 vanilla GRPO 67.76% → 제안 70.71%)

### 엔트로피 기반 절단 규칙을 외부 컨텍스트 주입 시점 결정으로 일반화

본 논문의 식 (5)는 L* = argmax_L [H̄_θ0(s̃_L) - H̄_θ0(s̃_{L+1})]로, 인접 step의 엔트로피 차이가 최대가 되는 지점에서 prefix를 자른다. 이 아이디어는 외부 context를 모델에 주입할 때 '모델이 가장 확신이 강한 곳 직전'에 배치하는 일반 원칙으로 쓸 수 있다. 검색 결과·도구 출력·에이전트 메모리 등 임의 외부 context를 토큰 길이를 늘리지 않으면서도 perturbation 효과를 극대화할 수 있다. 논문 4.2절의 entropy-based truncation이 핵심 출처다.

**적용 지점** — 외부 컨텍스트 주입 위치 결정 (검색 결과·도구 출력·에이전트 메모리)

**기대 효과** — 랜덤 step 절단 대비 pass@128 +0.52%p (논문 Table 2, 70.19% → 70.71%)

### 자기 개선 루프에 약한 대안 prefix 주입으로 local optimum 탈출

에이전트가 자기 답을 반복 다듬는 self-refine 루프에서는 같은 답안으로 수렴하기 쉽다. 본 논문 6.1·6.2절이 보여주듯, '낮은 품질이지만 분포가 다른' 외부 prefix가 오히려 새로운 추론 경로를 자극한다. 이를 일반화하면 refinement k번째 iteration에서 직전 답안을 다른 계열의 작은 모델로 다시 풀게 한 prefix를 컨텍스트 앞에 붙여 메인 모델이 '이전 답에서 출발하지만 다른 방식으로 풀어보기'를 시도하게 한다. cross-family perturbation이 핵심 메커니즘이며, 섹션 6.2의 prefix quality 분석은 '대부분 misleading이어도 효과 있음'을 뒷받침한다.

**적용 지점** — 자기 개선·리뷰 루프의 입력 컨텍스트

**기대 효과** — 수학 추론에서 pass@128 최대 +2.95%p, 정성적으로는 local optimum 탈출에 유의미 (논문 Table 1)

### 혼합 학습 비율 20/80을 평가-훈련 일관성 보장 패턴으로 일반화

본 논문 4.3절은 prefix-completion 비율을 p=0.2로 고정하고, p=1.0(100% prefix)에서는 pass@1까지 하락한다고 보고한다(논문 Table 2: p=1.0에서 pass@1=38.56, pass@128=68.54). 이는 '학습 시점과 평가 시점의 컨텍스트 구조가 다르면 안 된다'는 일반 원칙을 보여준다. 추론 에이전트 훈련·도구 사용 학습·RAG 적응형 fine-tuning에서 동일하게, 전체 학습 데이터의 10~20%만 보조 입력을 포함한 분포로 두면 평가 시점 도움 없이도 동작하는 강건함이 유지된다.

**적용 지점** — 에이전트·RAG·도구 사용 모델의 훈련 데이터 구성 비율

**기대 효과** — p=1.0 대비 p=0.2에서 pass@1 +0.45%p, pass@128 +2.17%p (논문 Table 2)

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 약한 모델 prefix의 효과를 내부에서 검증 | Qwen2.5-7B + GRPO 베이스라인 위에 Gemma-2-2B prefix를 p=0.2로 주입하는 미니 실험을 단일 GPU 노드에서 실행. MATH 500과 AIME 2024의 pass@1·pass@64·pass@128을 비교하고 엔트로피 거동을 측정한다. | 적용 가능성과 엔트로피 메커니즘 확인, 약 2주 소요 |
| Phase 2 | 다른 추론 도메인으로 확장 + 하이퍼파라미터 그리드 | 논리 추론·코드 생성 벤치마크에서 prefix 생성 모델 계열과 주입 비율 p∈{0.1,0.2,0.3}을 그리드 서치. 절단 지점을 step-level 외 token-level 옵션과 비교. | 도메인 일반화 가능성 확인, 핵심 하이퍼파라미터 가이드라인 확보 |
| Phase 3 | 프로덕션 통합 및 자동화 | 약한 모델 prefix 생성을 배치 잡으로 자동화하고, 4-class prefix 품질 평가를 온라인 모니터링에 통합. KL 페널티·entropy regularization과 결합하는 변형 실험 수행. | 사람 개입 없이 추론 다양성을 유지하는 지속 가능한 훈련 파이프라인 |

---

원문 PDF: `2026-08-30-boosting-llm-exploration-via-weak-model-guidance-in-rlvr.pdf`
