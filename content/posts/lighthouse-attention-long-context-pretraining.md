---
title: "아주 긴 글로 AI를 학습할 때 모든 단어를 서로 비교하지 않고, 여러 크기의 묶음에서 중요한 부분만 골라 빠르게 학습한 뒤 마지막에 일반 방식으로 잠깐 다시 학습시키는 방법이다."
date: 2026-08-08T18:29:30+09:00
draft: false
description: "Lighthouse Attention is a training-only hierarchical attention method for long-context pretraining. It symmetrically pools queries, keys, and values into a multi-resolution pyramid, selects important pyramid entries with a non-differentiable top-K step, gathers them into a dense sub-sequence, and…"
cover:
  image: "/images/lighthouse-attention-long-context-pretraining/_page_2_Diagram_0.jpeg"
  alt: "Lighthouse Attention의 forward trunk, selector branch, gradient path를 보여주는 구조도"
  caption: "논문 원문 발췌"
tags: ["Large Language Model", "논문 분석", "논문 리뷰", "Scaled Dot-Product Attention", "Causal mask", "FlashAttention"]
categories: ["논문분석"]
---


아주 긴 글로 AI를 학습할 때 모든 단어를 서로 비교하지 않고, 여러 크기의 묶음에서 중요한 부분만 골라 빠르게 학습한 뒤 마지막에 일반 방식으로 잠깐 다시 학습시키는 방법이다.

**무엇이 문제였나** — 긴 글을 학습하려면 보통 모든 단어 쌍을 비교해야 해서 글 길이가 늘수록 계산량과 메모리가 크게 늘어난다.
**어떻게 풀었나** — Lighthouse Attention은 단어들을 여러 단계로 묶어 요약하고, 점수가 높은 묶음만 골라 작은 입력으로 일반 어텐션을 실행한 뒤 결과를 원래 위치로 되돌린다.
**그래서 뭐가 좋아졌나** — 실험에서는 같은 약 503억 토큰 학습 예산에서 일반 방식의 최종 손실 0.7237보다 낮은 0.6980-0.7102를 얻었고, 전체 학습 시간은 1.40-1.69배 빨라졌다.

> 1000페이지 책을 매번 한 줄씩 전부 대조하지 않고, 먼저 장과 절 단위 요약을 훑어 중요한 부분을 골라 읽은 뒤, 마지막에는 전체 읽기 방식으로 다시 적응시키는 것에 가깝다.

## 논문 정보

Bowen Peng, Subho Ghosh, Jeffrey Quesnelle et al. · Nous Research · arXiv preprint (Nous Research) · 2025

## 왜 중요한가

10만 토큰이 넘는 문서, 코드, 대화를 다루는 모델은 학습 비용이 매우 크다. 이 논문은 학습 중에는 더 싼 근사 어텐션을 쓰고, 마지막에 일반 어텐션으로 복구하면 같은 토큰 예산에서 더 빠르고 손실도 낮을 수 있음을 보였다. 다만 이 방법 자체는 학습용이며, 실제 서빙 가능한 일반 어텐션 모델을 얻으려면 논문처럼 dense-SDPA 재개 단계가 필요하다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 최종 학습 손실 (10k+6k 레시피) | **0.6980** | 동일 50.3B 토큰 dense SDPA 기준선 0.7237 대비 낮은 손실 |
| 엔드-투-엔드 wall-clock 속도 향상 | **1.40-1.69×** | 16k step / 50.3B 토큰 / 8×B200 기준, 22.5-27.0h vs dense SDPA 37.9h |
| Forward-pass 속도 (512K 컨텍스트) | **21×** | 단일 B200, L=3, p=4, sparsity ≈ 1:64 설정에서 cuDNN SDPA 대비 |
| 학습 처리량 (Lighthouse stage-1 최고) | **126.0k tok/s/GPU** | Norm scorer, L=3, p=4, k=1536 설정; dense SDPA 기준선은 45.6k |

## 어떻게 동작하나

Lighthouse Attention은 긴 시퀀스 사전학습에서 SDPA의 O(N²) 병목을 줄이기 위해 어텐션 커널 바깥에 선택·압축·복원 단계를 둔다. 각 레이어의 Q, K, V를 p배 평균풀링으로 L단계 피라미드로 만들고, 원문 기본 설계에서는 파라미터 없는 ℓ² 노름 기반 점수와 max-pooling으로 후보를 채점한다. 이후 fused chunked-bitonic top-K가 선택한 피라미드 엔트리를 causality가 유지되는 연속 부분 시퀀스로 gather하고, 그 위에 stock SDPA/FlashAttention을 그대로 실행한 뒤 scatter-back으로 전체 N개 위치에 결과를 되돌린다. top-K 인덱스는 미분하지 않으며 STE, Gumbel softmax, 보조 손실을 쓰지 않는다. 그래디언트는 scatter, FlashAttention, gather, pyramid pool을 거쳐 WQ, WK, WV로만 흐른다. 실험에서는 norm scorer 외에 dilated softmax scorer도 비교했고, 손실은 대체로 0.01 안팎 차이였으며 norm scorer가 더 저렴했다. 마지막 dense-SDPA resumption은 학습 중 근사 어텐션을 썼던 모델이 일반 full-attention 모델로 회복되는지를 검증하는 핵심 단계다.

![Lighthouse Attention의 forward trunk, selector branch, gradient path를 보여주는 구조도](/images/lighthouse-attention-long-context-pretraining/_page_2_Diagram_0.jpeg)
*Lighthouse Attention의 forward trunk, selector branch, gradient path를 보여주는 구조도*

선택기는 pooled summary에서 ℓ² norm 기반 점수를 계산해 top-K 인덱스를 만들지만, 그 가지는 미분되지 않는다. 실제 그래디언트는 scatter-back, FlashAttention, gather, pyramid pool을 지나 Q/K/V projection으로 돌아간다.

핵심 수식:

```
S = \frac{N}{p^{L-1}} + (L-1)pk, \quad L = \log_p(N/k) \Rightarrow S = pkL = \Theta\left(pk\log_p(N/k)\right), \quad T_{\text{layer}} = \Theta(Nd) + \Theta(N\log k) + \Theta(k^2\log^2 N\,d)
```

S: FlashAttention이 보는 gathered sub-sequence 길이 / N: 전체 시퀀스 길이 / p: 풀링 배율 / L: 피라미드 단계 수 / k: top-K 예산 / d: head dimension. 원문 Eq. 8과 Appendix B에 따르면 coarsest level은 N/p^{L-1}개를 전부 유지하고, 나머지 L-1개 level은 각각 최대 pk개를 더한다. L=log_p(N/k)로 잡으면 N/p^{L-1}=pk가 되어 S=pkL이다. 부분 시퀀스 어텐션 비용은 Θ(S²d)=Θ(k²log²N d)이고, scoring/scatter 등 선형 단계와 top-K 선택 Θ(N log k)를 합치면 bounded k에서는 전체 per-layer compute가 N에 대해 선형으로 지배된다.

## 한계와 주의할 점

- 대칭 Q/K/V 풀링은 모든 쿼리가 한 번에 존재하는 학습 forward에 맞춘 설계다. 자기회귀 디코딩에서는 한 번에 새 쿼리가 하나씩 생기므로 Lighthouse forward 자체를 그대로 서빙에 쓰기 어렵고, 논문도 dense-SDPA resumption 뒤 dense inference로 평가한다.
- 내부 어텐션은 gathered sub-sequence S에 대해 Θ(S²d)로 실행된다. bounded k에서는 전체 비용이 선형 단계에 의해 지배되지만, k가 N과 함께 커져야 하는 환경에서는 이 이점이 줄어들 수 있다.
- chunked-bitonic top-K는 정확한 global top-K가 아니라 chunk별 후보를 남기는 stratified selection이다. 원문 Appendix D.2도 높은 점수가 한 청크에 몰리면 낮은 점수 후보가 다른 청크에서 들어올 수 있음을 인정한다.
- dense-SDPA 재개 직후 loss spike가 1.12-1.57까지 나타나고 약 1-1.5k step 뒤 안정화된다. 더 큰 모델이나 더 긴 컨텍스트에서 spike 지속 시간과 안정성이 같은지는 아직 제한적으로만 확인됐다.
- 실험 모델은 530M 규모이고, 레이어 {0,1,28,29}는 dense SDPA로 유지하며 나머지 26개 레이어에 Lighthouse를 적용한다. 이 레이어 정책이 다른 아키텍처에서도 그대로 최적인지는 추가 검증이 필요하다.
- 하이퍼파라미터 미스튜닝: k, p, L 조합이 부적절하면 S가 커져 가속이 줄거나, 반대로 너무 작은 선택 예산 때문에 정보 손실이 커질 수 있다.
- 복구 step 부족: dense-SDPA 재개가 충분하지 않으면 loss spike 이후 안정화되기 전에 학습이 끝날 수 있다. 원문에서는 4k-6k resume이 모두 dense baseline보다 낮은 최종 손실을 보였지만, 긴 resume tail일수록 손실이 낮았다.
- 중요 토큰 클러스터링: 점수 상위 토큰이 특정 구간에 몰리는 입력에서는 stratified top-K가 strict global top-K와 다른 선택을 하므로 일부 고점수 항목이 빠질 수 있다.
- retrieval 중심 과제에서 norm scorer와 작은 k가 불리할 수 있다. Appendix F의 simplified NIAH에서는 k=1536 norm 평균 retrieval이 0.65로 dense baseline 0.72보다 낮았다.
- 초기/말단 레이어 dense 유지 휴리스틱이 다른 모델, 데이터, 길이 설정에 일반화되는지는 아직 실험적으로 열려 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 장문서 RAG 리랭커에 대칭 Q/K/V 피라미드 풀링 적용

Lighthouse의 핵심은 선택을 attention kernel 밖에 두고, 선택된 항목을 연속 dense sub-sequence로 만들어 stock attention을 실행하는 것이다. 장문서 cross-encoder에서도 문서 전체를 매번 dense attention으로 처리하는 대신, Q/K/V를 피라미드로 요약하고 top-K 구간만 모아 attention을 수행하는 연구를 할 수 있다. 다만 논문은 LLM pretraining만 평가했으므로 RAG 품질 개선은 별도 실험이 필요하다.

**적용 지점** — 장문서 cross-encoder 리랭킹 단계

**기대 효과** — 원문 수식상 attention 입력 길이를 N에서 S로 줄일 수 있어 계산량 감소가 기대된다. 실제 리랭킹 품질은 별도 검증이 필요하다.

### ℓ²-노름 기반 0-파라미터 후보 프리필터

논문의 projection-norm scorer는 추가 학습 파라미터 없이 Q/K projection의 ℓ² norm과 max-pooling을 사용한다. Appendix E.1에서 norm scorer는 dilated scorer와 손실이 약 0.01 이내였고, L=3, p=4 조건에서 B200-hours가 179.6-180.9로 dilated의 197.2-199.7보다 낮았다. 이 아이디어는 후보를 줄이는 빠른 1차 필터로 실험할 수 있다.

**적용 지점** — 리트리벌 후보 재정렬 전 1차 필터

**기대 효과** — 논문 내부 기준 약 9% B200-hour 절감이 관찰됐다. 다른 파이프라인에서는 후보 감소율과 품질 회귀를 따로 측정해야 한다.

### 다양성 보존형 chunked-bitonic top-K 회수

Appendix D.2에 따르면 chunked-bitonic top-K는 이론적 global top-K와 같은 index set을 만들지 않는다. 대신 청크별 후보가 남아 특정 span으로 selection이 붕괴되는 것을 줄일 수 있다. 장기 메모리나 RAG 회수에서 최근 구간 또는 특정 구간으로 후보가 몰리는 문제가 있다면, 이 stratified selection을 다양성 보존 장치로 실험할 수 있다.

**적용 지점** — 장기 메모리 회수, 에피소드 선별, RAG passage 선택

**기대 효과** — 정량 효과는 논문 범위 밖이다. 다만 Figure 4와 Appendix F는 k와 scorer 선택이 retrieval 평균 0.65-0.76 범위의 큰 차이를 만들 수 있음을 보여준다.

### 근사 학습 후 dense 복구 레시피 일반화

이 논문의 중요한 실증은 Lighthouse로 대부분 학습한 뒤 dense-SDPA로 이어 학습하면 dense-from-scratch baseline을 같은 token budget에서 match 또는 beat할 수 있다는 점이다. 이 패턴은 sparse attention뿐 아니라 quantization, pruning, routing 같은 학습 중 근사에도 적용 후보가 된다. 단, 원문에서 확인된 것은 Lighthouse Attention과 dense-SDPA resume 조합이다.

**적용 지점** — 학습 시 근사 기법을 쓰는 pretraining 또는 continued pretraining 파이프라인

**기대 효과** — 원문 recoverability 실험에서는 12k+4k, 11k+5k, 10k+6k 모두 dense baseline 0.7237보다 낮은 0.7102, 0.7001, 0.6980을 달성했다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 소규모(≤1B)·단일 노드에서 레시피 검증 | 530M-1B 모델과 98K-256K 컨텍스트에서 Lighthouse stage 후 dense-SDPA resume을 재현한다. p ∈ {2,4}, L ∈ {3,4}, k ∈ {1536,2048,4096}, scorer ∈ {norm,dilated}를 비교하고, dense baseline 대비 final loss, throughput, NIAH retrieval을 함께 본다. | 도입 전 가장 중요한 질문인 '우리 모델에서도 dense baseline보다 빠르고 손실이 낮은가'를 작은 규모에서 확인한다. |
| Phase 2 | 프로덕션 스케일과 context parallelism 통합 | 8-32 GPU 이상의 CP 환경에서 pooling, scoring, top-K가 shard-local로 충분한지 검증하고, gathered dense sub-sequence가 ring attention과 문제없이 결합되는지 측정한다. per-layer dense 정책과 k scheduling을 실험한다. | 논문이 보고한 CP 확장성 주장을 실제 학습 인프라와 모델 크기에서 검증하고, 7B+ 규모에서도 wall-clock 절감이 유지되는지 확인한다. |
| Phase 3 | 서빙 가능한 sparse target 또는 dense resume 최적화 | dense-SDPA resume 비율을 줄이는 스케줄을 탐색하거나, 논문 future work처럼 DSA, NSA, HISA, MoBA 같은 asymmetric sparse target으로 resume하는 방법을 실험한다. retrieval 과제에서는 k와 scorer를 loss-only 기준이 아니라 NIAH/다운스트림 지표로 고른다. | 학습 가속에 머무르지 않고, 긴 문맥 서빙 비용까지 낮출 수 있는지 검증한다. |

---

원문 PDF: `2026-05-07-lighthouse-attention-long-context-pretraining.pdf`
