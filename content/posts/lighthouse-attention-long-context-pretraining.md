---
title: "학습 중에만 어텐션을 압축했다가 마지막에 원래 방식으로 돌려놓으면, 긴 문맥을 훨씬 빠르고 저렴하게 학습하면서도 정상적인 모델을 얻는다."
date: 2026-08-08T19:08:12+09:00
draft: false
description: "Lighthouse Attention은 Q/K/V를 대칭적으로 다중 해상도 피라미드로 풀링한 뒤, 상위 K개 엔트리만 골라 표준 FlashAttention에 통과시키는 학습 전용 희소 어텐션이다. selection이 어텐션 커널 밖에 있어 forward/backward가 dense 트랜스포머와 동일하며, 마지막에 짧은 dense-SDPA resume만 거치면 from-scratch dense baseline과 동등 이상의 loss를 1.4~1.7× 더 빠른 wall-clock에 달성한다."
tags: ["머신러닝 / 트랜스포머 아키텍처 (Long-context Pretraining)", "논문 분석", "논문 리뷰", "SDPA", "FlashAttention", "Pyramid Pool"]
categories: ["논문분석"]
---


학습 중에만 어텐션을 압축했다가 마지막에 원래 방식으로 돌려놓으면, 긴 문맥을 훨씬 빠르고 저렴하게 학습하면서도 정상적인 모델을 얻는다.

**무엇이 문제였나** — 긴 문맥(10만~100만 토큰) 학습은 어텐션의 제곱 비용 때문에 GPU 시간과 메모리가 폭발한다.
**어떻게 풀었나** — 질문·키·값을 같이 여러 해상도로 압축하고 중요한 것만 골라 표준 어텐션을 돌린 뒤, 마지막에 잠깐 원래 어텐션으로 마무리한다.
**그래서 뭐가 좋아졌나** — 동일 토큰 예산에서 dense baseline보다 loss가 더 낮거나 같으면서 1.4~1.7× wall-clock을 절약하고, 512K에서는 21× 빨라진다.

> 수백 페이지 문서를 읽고 요약할 때 처음부터 끝까지 정독하는 대신, 목차-챕터-단락으로 먼저 훑어 중요한 부분에만 집중해 읽듯, 모델이 여러 해상도로 문맥을 압축하고 중요 구간만 표준 방식으로 처리한다. 마지막에는 전체를 다시 한 번 정독하듯 원래 어텐션으로 마무리해, 빠르게 읽은 습관이 정독 능력을 해치지 않게 한다.

## 논문 정보

Bowen Peng, Subho Ghosh, Jeffrey Quesnelle (공동 제1저자 Peng·Ghosh) · Nous Research · arXiv preprint (arXiv:2605.06554), 2026 — 학회 미게재 · 2026

## 왜 중요한가

최근 LLM의 컨텍스트가 128K, 1M을 넘나들며 학습 비용이 가장 큰 병목이 되었는데, 이 방법은 추론 모델의 구조를 바꾸지 않고 학습 비용만 크게 줄여준다. 즉 기존 서빙 스택, KV 캐시, 커널을 그대로 쓰면서 사전학습 단계에서만 효율을 얻는다는 점이 실용성의 핵심이다. 다만 검증 규모가 작고 추론 가속이 아닌 학습 가속에 국한되어, 산업 적용은 추가 스케일업 검증이 선행되어야 한다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 최종 training loss | **0.6980nats** | 10k+6k 레시피(dilated, k=6144)의 16k 스텝 최종 loss. dense-from-scratch 0.7237 대비 0.026 개선. |
| End-to-end wall-clock speedup | **1.69배** | 동일 16k 스텝/50.3B 토큰 기준 dense SDPA(37.9h) 대비 최대 단축비. 범위는 1.40~1.69×. |
| 512K forward latency speedup | **21배** | 단일 B200, 단일 레이어, sparsity 1:64 기준 dense cuDNN SDPA 대비 forward 속도. fwd+bwd는 17.3×. |
| Stage-1 처리량 | **126k tok/s/GPU** | projection-norm scorer, L=3/p=4/k=1536의 stage-1 처리량 최댓값. dense SDPA는 ~46k. |

## 어떻게 동작하나

Lighthouse Attention은 어텐션 커널 자체를 건드리지 않고 그 주위를 감싸는 네 단계 파이프라인으로 동작한다. (1) Pyramid Pool: Q, K, V를 동일한 인자 p로 L단계 평균 풀링해 일관된 (Q,K,V) 트리플을 만든다. 대칭 풀링은 기존 NSA/HISA/InfLLM-V2가 K,V만 압축하던 것과 달리, 풀링된 query와 key가 같은 표현 공간을 공유하게 한다. (2) Score & Top-K: 모수 없는 ℓ2 norm 기반 점수로 각 엔트리를 평가하고, chunked-bitonic 커널로 상위 K개를 고른다. 이 단계는 미분 불가능해 직진 추정기(straight-through) 없이 인덱스엔 기울기가 흐르지 않는다. (3) Dense sub-sequence attention: 선택된 엔트리를 인과적 순서로 정렬해 길이 S의 연속 부분열로 만들고, 표준 FlashAttention을 그대로 호출한다. (4) Scatter-back: 각 출력을 shift된 범위 R(ℓ,i)로 되돌려 인과성을 보존한다. 핵심은 selection이 커널 밖에 있어 forward/backward가 dense 트랜스포머와 동일하다는 점이며, 학습 종료 직후 짧은 dense-SDPA resume으로 순정 dense 가중치를 회복한다.

핵심 수식:

```
S = \frac{N}{p^{L-1}} + (L-1) p k, \quad L=\log_p(N/k) \Rightarrow S = \Theta(k\log_p N), \quad T_{layer}=\Theta(T\cdot d)\ \text{(bounded k)}
```

N은 시퀀스 길이, p는 풀링 인자, L은 피라미드 단 수, k는 선택 예산. 첫 항은 최상위 단(전체 보존), 둘째 항은 나머지 L-1단의 기여. L=log_p(N/k)로 잡으면 S가 Θ(k log N)으로 억제되어 어텐션 비용 Θ(S²d)이 N에 대해 polylog가 된다. 결과적으로 k가 고정일 때 총 레이어 연산은 시퀀스 길이 T에 대해 선형 Θ(T·d)가 되어 linear attention/SSM과 같은 점근 등급을 가진다.

## 한계와 주의할 점

- 평가 규모가 530M 단일 모델에 불과하다. 7B~100B급, 수조 토큰 규모로의 확장성은 검증되지 않았고, 회복 효과가 스케일에 따라 유지될지 미지수다.
- 주 성과 지표가 C4 training loss이며 표준 downstream 벤치마크(MMLU, RULER 등)가 부재하다. NIAH도 단일 숫자 passkey 변형만 써 실제 장문 검색 난이도를 반영하기 어렵다.
- 총 예산 50.3B 토큰/16k 스텝은 실제 대규모 pretraining 대비 매우 작아, 희소 학습의 정칙화 효과(k가 작을수록 loss가 낮아지는 비직관적 결과)가 대규모에서도 유지될지 열린 문제다.
- symmetric Q 풀링은 autoregressive decoding과 근본적으로 양립하지 않아, 모든 평가가 dense-SDPA resume 이후에만 수행된다. resume tail이 짧거나 데이터 분포가 다르면 회복 불량 시나리오가 탐구되지 않았다.
- chunked-bitonic top-K는 엄밀한 global top-K가 아니라 stratified top-K로, 모든 구간이 일정 수식 기여하도록 의도되었으나 선택 편향이 성능에 미치는 영향이 정량화되지 않았다.
- 모든 실험이 단일 NVIDIA BGX 8×B200 노드에 의존한다. 다른 하드웨어(H100/A100, AMD MI 시리즈)에서의 커널 효율과 FlashAttention 상속 주장은 검증되지 않았다.
- 추론 시 dense-SDPA resume 없이 그대로 사용하면 symmetric 풀링이 AR 디코딩 단일-query 가정을 위반해 품질이 붕괴한다. 본문도 이를 명시적 한계로 인정한다.
- k가 N과 함께 스케일해야 하는 영역(초장문+높은 recall 필요 태스크)이 미특성화되어, Θ(k² log² N) 항이 선형 비용을 잠식할 수 있다.
- projection-norm scorer는 retrieval을 손상시킨다. k=1536 norm의 NIAH는 0.65로 baseline 0.72 대비 0.07 하락해, retrieval-민감 태스크에서 기본값 선택이 위험하다.
- resume 시점에서 loss가 1.12~1.57로 일시 스파이크하므로, resume 길이 예산이 부족하면 미회복 상태로 학습이 종료될 위험이 있다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 스케일 및 downstream 검증 | 7B~30B급 모델로 1조 토큰 이상 pretraining; MMLU/RULER/LongBench 표준 벤치; H100·A100·MI300X 이기종 커널 검증; k-N 스케일 곡선 측정 | 소규모 530M에서의 정칙화 효과와 회복성이 실제 스케일에서 유지되는지 확인해 산업 신뢰 확보 |
| Phase 2 | 네이티브 서빙 체크포인트 도출 | dense-SDPA resume 대신 DSA/NSA/HISA/MoBA 같은 비대칭 sparse target으로 resume해 서빙 가능한 sparse 가중치 생성; continuous batching·speculative decoding·KV-cache 관리 통합 | 학습 효율을 추론까지 연장해 end-to-end 비용 절감 및 serving 플랫폼 통합 가치 창출 |
| Phase 3 | 적응형·멀티모달 확장 | per-layer/per-head adaptive k 도입; 비전·오디오·비디오 피라미드 적용; 학습 스케줄 자동 탐지(resume 시점·비율) 자동화 | 고정 k의 한계 극복, 멀티모달 long-context 학습 비용 절감, 운영자 개입 최소화로 프로덕션 적용성 강화 |

---

원문 PDF: `2026-05-07-lighthouse-attention-long-context-pretraining.pdf`
