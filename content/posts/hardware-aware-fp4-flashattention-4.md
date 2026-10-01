---
title: "AI가 문장이나 이미지를 처리할 때 자주 쓰는 어텐션 계산을 4비트 숫자로 더 빠르게 돌리려는 연구다."
date: 2026-10-02T07:33:17+09:00
draft: false
description: "Blackwell의 4비트 텐서 코어가 빨라져도 어텐션의 softmax 변환과 P 구성 단계가 병목이 되는 문제를, 점수를 MXFP4 확률 코드로 직접 매핑하는 Direct-P로 줄인 연구다. 비인과 forward는 GB200에서 BF16 대비 최대 2.13배 빠르고, B300에서는 D128/H64/S9472에서 3159 TFLOP/s에 도달한다. 학습 쪽에서는 forward에서 저장한 양자화 Q/K와 LSE를 backward가 재사용해 단일 GB200의 8.03B 모델 업데이트를 최대 1.14배 빠르게 한다."
tags: ["GPU Kernel Optimization / Efficient Attention", "논문 분석", "논문 리뷰", "FP4", "FlashAttention", "softmax"]
categories: ["논문분석"]
---


AI가 문장이나 이미지를 처리할 때 자주 쓰는 어텐션 계산을 4비트 숫자로 더 빠르게 돌리려는 연구다.

**무엇이 문제였나** — 문제: GPU는 4비트 곱셈을 아주 빨리 할 수 있지만, 어텐션 중간에서 확률값을 만드는 단계가 발목을 잡았다.
**어떻게 풀었나** — 해결: 확률을 정밀하게 만든 뒤 줄이는 대신, 처음부터 GPU가 바로 쓸 수 있는 4비트 코드에 점수를 넣는다.
**그래서 뭐가 좋아졌나** — 결과: 좋은 조건에서는 어텐션 forward가 BF16보다 최대 2.13배 빨랐고, 8B급 모델의 한 번 학습 업데이트도 최대 1.14배 빨라졌다.

> 긴 줄을 정리할 때 모든 사람의 정확한 키를 재고 다시 순서를 매기는 대신, 처음부터 몇 개의 키 구간표에 바로 넣는 방식과 비슷하다. 아주 정밀하지는 않지만, 정해진 구간만 필요하다면 훨씬 빠르게 처리할 수 있다. 단, 값이 너무 극단적인 경우에는 별도 안전장치가 필요하다.

## 논문 정보

Robert Hu · Graphcore Research · arXiv Technical Report (2609.04105) · 2026

## 왜 중요한가

대형 AI 모델은 어텐션 계산을 매우 많이 반복한다. 이 부분이 빨라지면 같은 GPU로 더 많은 요청을 처리하거나 학습 시간을 줄일 수 있다. 이 논문은 4비트 연산이 단순한 행렬곱뿐 아니라 어텐션 중간 확률 계산까지 실제 병목을 줄일 수 있음을 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Forward peak speedup vs BF16 | **2.13×** | Direct-P noncausal forward on favorable GB200 Blackwell shapes |
| Peak TFLOP/s on B300 | **3159TFLOP/s** | D128/H64/S9472 wave-aligned B300 row |
| 8B end-to-end update speedup | **1.14×** | Single-GPU 8.03B Llama-3.1-style update, abstract result |
| Fast mean cosine vs BF16 | **0.943789cosine** | Fast NV/MX forward mean cosine; HAO NV/FP8 mean cosine is 0.9899 |

## 어떻게 동작하나

이 연구는 NVIDIA Blackwell GPU에서 어텐션 내부의 Q, K, P, V 네 operand를 낮은 정밀도로 만들 때 실제 속도와 정확도가 어떻게 바뀌는지 측정한다. Forward 실험에서는 HAO AI Lab의 두-query FA4 스케줄과 TMEM 소유권 구조를 유지하고, ready FP32 score fragment를 PV가 소비할 수 있는 MXFP4 확률 operand로 바꾸는 구간만 Direct-P로 교체한다. Direct-P는 정규화된 score를 E2M1 코드로 직접 매핑하고, PV가 실제로 소비하는 rounded code와 block scale로 denominator를 누적한다. 극단 logit이 있는 Wan 레이어에는 sampled QK guard와 underflow-safe denominator 순서를 적용한다. Training 실험에서는 forward가 저장한 NVFP4 Q/K payload, block/global scale, LSE를 backward로 넘겨 확률을 재구성하고, gradient matrix product에는 FP8 계열 operand를 사용한다. 단일 GPU와 projection-inclusive attention, complete 8B update를 분리해 측정하며, 분산 학습에서는 MXFP4 P/V가 발산해 FP8 P/V를 채택한다.

핵심 수식:

```
\tilde{p}_{ij}=\delta_B q_{ij}=\alpha_B q_{ij}/6,\quad x_{ij}=(z_{ij}-m_i)\log_2 e-e_B+\log_2 6,\quad q_{ij}=Q_{E2M1}(2^{x_{ij}})
```

z_ij는 Q_iK_j^T/√d로 만든 raw score, m_i는 row reference, e_B는 MXFP4 E8M0 scale byte u_B에서 얻은 exponent, α_B=2^{e_B}, δ_B=α_B/6이다. 실제 fast 구현은 정확한 2^x 계산만 쓰기보다 affine classifier max(0, Ax+B)와 packed conversion을 주로 쓰고, 일부 위치에서는 native EX2를 선택한다.

## 한계와 주의할 점

- Fast 경로의 operator mean cosine은 0.943789로 HAO NV/FP8의 0.9899보다 낮다. 속도를 얻는 대신 operator-level error를 크게 받아들이는 설계다.
- Wan2.1-14B에서는 20-step final latent가 fast 0.8496 / 0.5337까지 drift한다. HAO NV/NV의 0.9036 / 0.4435보다 장기 누적 오차가 크다.
- 분산 학습에서 테스트한 모든 MXFP4 P/V training trajectory가 발산해, 훈련 기본 경로는 FP8 P/V로 돌아간다.
- 극단 logit이 있는 Wan late layer에는 sampled guard가 필요하며, guarded layer는 개별적으로 21-23% 느리다.
- BF16 checkpoint를 drop-in으로 바꾸는 결과는 Attn-QAT의 trained quality를 재현하지 못하며, QAT checkpoint나 training recipe가 별도로 필요하다.
- MXFP4 P/V 분산 학습 궤적 divergence: 테스트한 모든 MXFP4 P/V trajectory가 발산했다.
- 극단 logit layer의 subnormal flush: E8M0 code 1에서 (α'_B/6)c_B 순서로 계산하면 valid block이 zero로 사라질 수 있다.
- Layer-wise affine calibration 부호 반전: BF16 teacher trajectory에서 고른 보정이 composed all-FP4 trajectory에서는 held-out prompt에서 반대로 작동했다.
- Long-horizon diffusion drift: Wan2.1-14B fast는 1-step 0.9938 cosine에서 20-step 0.8496 cosine으로 누적 오차가 커졌다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 점수를 4비트 코드 빈에 직접 매핑하는 Direct-P 일반화

Direct-P는 x=(z-m)log2e-eB+log2 6로 score를 scale 좌표로 옮긴 뒤 E2M1 code를 정한다. fast 정책은 A=1.50, B=1.20 같은 affine classifier를 쓰고, Wan 평가에서는 A=1.60, B=0.95를 선택한다. 이 관점은 exp 계산의 실수 정밀도를 높이는 것보다 최종 code agreement가 더 중요한 저정밀 softmax 경로에 적용할 수 있다.

**적용 지점** — 양자화 softmax, attention probability construction, sampling 분포 근사

**기대 효과** — GB200 favorable forward shape에서 BF16 대비 최대 2.13배 throughput

### 저장된 양자화 페이로드로 backward 확률 재구성

Causal training path는 forward의 NVFP4 Q/K payload, block scale, global factor, row LSE를 저장하고 backward에서 QKT와 P를 재구성한다. isolated backward reconstruction core는 BF16 0.501 ms 대비 0.356 ms로 1.405배 빠르지만, E5M2 dO/statistics publisher까지 포함하면 0.508 ms로 이득이 사라진다. 그래서 논문은 isolated kernel, projection-inclusive attention, full update를 분리해 보고한다.

**적용 지점** — QAT forward/backward 인터페이스, saved-tensor 기반 gradient computation

**기대 효과** — Projection-inclusive attention forward+backward 1.245배, single-GPU 8.03B update 최대 1.14배

### fast/accurate 두 운영점으로 속도-정확도 조절

논문은 fast와 accurate 정책을 분리한다. fast는 GB200 D128에서 all-affine, 기본 anchor 없음, 12 K/V stages로 최소 latency를 노린다. accurate는 13 K/V stages, 32 fixed rows anchor, 약 25% native EX2, correction WG denominator로 더 높은 fidelity를 노린다. 평균 cosine은 fast 0.943789, accurate 0.951669이고, 평균 relative-L2는 각각 0.336602와 0.327225다.

**적용 지점** — 추론 latency budget 기반 attention policy selection, 생성 모델 self-attention, ViT/BERT batch inference

**기대 효과** — ViT S4096에서 fast 1.783배·accurate 1.490배, Wan2.1-14B에서 fast 2.09배·accurate 1.75배

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 정밀도와 속도 경계 정의 | NVFP4 Q/K + MXFP4 P/V fast와 accurate 정책을 attention 라이브러리 옵션으로 추가한다. 분산 학습에서는 원문 결과에 맞춰 FP8 P/V를 기본값으로 둔다. | 비인과 forward에서 favorable GB200 shape 기준 최대 2.13배 speedup을 기대할 수 있다. |
| Phase 2 | 워크로드별 guard와 정책 선택 | 극단 logit layer를 감지해 sampled QK guard를 적용하고, Wan 계열처럼 누적 drift가 큰 workload에는 accurate 또는 FP8 P/V fallback을 둔다. | guarded layer의 21-23% 개별 slowdown을 전체 layer 비중으로 제한하면서 finite 실행을 유지한다. |
| Phase 3 | 학습 파이프라인 통합 | forward의 NVFP4 Q/K payload, block/global scale, LSE를 backward에 전달하는 인터페이스를 표준화하고, E5M2 dO publisher와 FP8 gradient operand 경로를 함께 관리한다. | Projection-inclusive attention forward+backward 1.245배, complete 8.03B single-GPU update 최대 1.14배 가속을 목표로 한다. |

---

원문 PDF: `2026-09-04-hardware-aware-fp4-flashattention-4.pdf`
