---
title: "큰 모델의 일부만 작은 추가로 바꾸는 LoRA의 크기(랭크)를 정할 때, 실제 작업에서 모델이 ‘어느 단어를 얼마나 볼지’를 얼마나 잘 따라갈 수 있는지 계산하는 이론이다."
date: 2026-11-09T07:35:16+09:00
draft: false
description: "이 논문은 다운스트림 작업의 입력 분포에서 이미 얻어진 목표 attention을 LoRA가 각 랭크에서 얼마나 정확히 재현할 수 있는지 이론적 상·하한으로 분석한다. 원래 가중치의 특이값만 보는 대신, 실제 작업의 query와 key가 활성화하는 업데이트 방향을 이용해 attention KL의 rank–error 곡선을 구한다. 결과는 attention 확률 분포의 오차에 관한 이론이며, head 출력이나 최종 작업 성능을 보장하지 않는다."
tags: ["Transformer Attention / Parameter-Efficient Fine-Tuning", "논문 분석", "논문 리뷰", "LoRA", "랭크", "attention"]
categories: ["논문분석"]
---


큰 모델의 일부만 작은 추가로 바꾸는 LoRA의 크기(랭크)를 정할 때, 실제 작업에서 모델이 ‘어느 단어를 얼마나 볼지’를 얼마나 잘 따라갈 수 있는지 계산하는 이론이다.

**무엇이 문제였나** — LoRA의 랭크가 낮으면 추가 장치가 담을 수 있는 변화 방향이 적어 목표와 다른 주의 분포가 될 수 있습니다.
**어떻게 풀었나** — 논문은 실제 작업 입력에서 자주 쓰이는 변화 방향에 가중치를 주어, 각 랭크의 오차 상한과 하한을 계산합니다.
**그래서 뭐가 좋아졌나** — 결과는 attention 확률 분포의 차이까지를 다루며, 최종 답변이 같은지나 작업 점수가 좋아지는지는 보장하지 않습니다.

> 시험에 거의 나오지 않는 참고서 내용까지 모두 외우는 대신, 실제 문제에서 반복해서 쓰이는 개념부터 남기는 것과 비슷합니다. 다만 이 논문은 어떤 개념을 남길지 계산하는 방법만 제시하며, 그 방법만으로 최종 시험 점수까지 보장하지는 않습니다.

## 논문 정보

Gerard Conangla Planes · Aily Labs · arXiv preprint (arXiv:2608.26052v1 [cs.LG]) · 2026

## 왜 중요한가

작업에서 사용되지 않는 방향까지 저장하면 LoRA를 불필요하게 크게 만들 수 있습니다. 이 분석은 실제로 영향을 주는 정보에 근거해 필요한 랭크를 줄이는 판단을 돕지만, 가정이 성립하지 않으면 보장으로 사용할 수 없습니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 정리된 rank–KL 경계 | **a/[2e²(1+Λ√κ_h)]·ψ(√T_r) ≤ E_r** | 목표 attention이 dense query update Δ*로 정확히 실현되고 최소 목표확률, 독립성, 기하·모멘트 조건이 성립할 때, 다운스트림 가중 잔여 에너지 T_r로 최적 기대 attention KL을 제한한다. |
| softmax 오차 상한 | **KL(p*‖softmax(z*+d)) ≤ min{‖d‖** | 중심화한 후보–목표 점수 차이에 대한 무조건적 점별 상한이다. 작은 오차에서는 이차적으로, 큰 오차에서는 선형적으로 증가한다. |
| Walsh 예제의 유한 점수 랭크 | **krank** | 구성된 query-only Walsh-attention 계열에서 유한한 목표 logits를 정확히 실현하는 모든 업데이트의 랭크는 k이다. |
| Walsh 예제의 포화 attention 폐포 랭크 | **k − ⌊k/3⌋rank** | 같은 isolated-triple 계열에서 극한 attention을 임의의 정확도로 재현할 수 있는 정확한 relative softmax closure rank이다. |

## 어떻게 동작하나

저자는 고정된 사전학습 attention head, 목표 attention 함수, 다운스트림 입력 분포를 고정하고 랭크 r 이하 query LoRA 후보가 달성하는 최소 기대 attention KL을 E_r로 정의한다. 먼저 공통 점수 이동을 제거한 점수 차이 d에 대해 Theorem 3.1의 ψ(t)=min{t²,t}와 ψ_up(t)=min{t²/4,√2t} 비교를 제시한다. 목표가 dense query update Δ*로 정확히 실현되고 최소 목표확률, query–key 독립성, 기하 및 네 번째 모멘트 조건이 성립하면 Theorem 4.1은 가중 잔여 특이값 에너지 T_r에 대한 양쪽 경계를 얻는다. 독립성이 성립하지 않을 때는 Theorem 4.3의 직접 비교 상수와 후보군 모멘트 조건을 이용한다. 확률 바닥값이 약하면 점수 범위가 제한된 후보군에 대한 target-Fisher 양쪽 경계와, 높은 확률 질량을 가진 토큰 집합에 대한 비제한 하한을 각각 사용할 수 있다. Theorem 6.1은 isolated-triple Walsh 계열에서 유한 logits의 정확한 랭크와 softmax closure rank를 분리하며, 별도의 선형 토큰 구성은 포화 시 더 낮은 랭크 경로를 달성함을 보인다. 이후 fused multi-head LoRA에서는 head별 KL 합과 공유 랭크의 효과를, joint query/key LoRA에서는 effective score rank와 별도 Q/K 인수분해 갭 ρ를 분석한다. Section 9는 목표 클래스 확인, 완전한 입력 단위 보정 데이터 수집, 적용할 경로 선택, 가중 특이값 꼬리 계산, 상수 민감도 점검, 허용 오차와 비교하는 절차를 제시한다.

핵심 수식:

```
\psi(t)=\min\{t^2,t\},\quad \psi_{\mathrm{up}}(t)=\min\{t^2/4,\sqrt{2}\,t\}
\frac{a}{2e^2(1+\Lambda\sqrt{\kappa_h})}\,\psi(\sqrt{T_r})\le E_r\le\psi_{\mathrm{up}}(\sqrt{T_r}),\quad T_r=\sum_{j>r}\sigma_j\!\left(G^{1/2}\Delta^{*}\Sigma^{1/2}\right)^2
r_{\mathrm{suff}}(\epsilon)=\min\{r:\psi_{\mathrm{up}}(\sqrt{T_r})\le\epsilon\},\quad \psi(\sqrt{T_r})\le\frac{2e^2(1+\Lambda\sqrt{\kappa_h})}{a}\,\epsilon\text{ (error}\le\epsilon\text{를 달성하는 rank의 필요조건)}
```

E_r는 랭크 r 이하 후보 전체에서 얻는 최소 기대 target-to-candidate attention KL이다. T_r는 G=β²E[K(u)ᵀΠ_n(u)K(u)], Σ=E[h(u)h(u)ᵀ]로 정의한 다운스트림 가중 좌표에서 D*=G^{1/2}Δ*Σ^{1/2}의 r번째 이후 특이값 제곱합이다. a는 거의 확실하게 성립하는 목표 attention의 최소 확률이고, Λ는 key Gram의 기하 상한, κ_h는 query activation의 네 번째-두 번째 모멘트 상수이다. 위 양쪽 경계는 목표가 query-only Δ*로 정확히 실현되고 query–key 독립성과 해당 조건들이 성립할 때만 적용된다. 하한은 모든 rank-r 후보에 적용되고, 상한 쪽에는 가중 좌표의 truncated SVD로 만든 후보가 대응한다. 이 공식은 population 수준의 조건부 보장이며 유한 보정 표본의 인증서나 신뢰구간을 만들지는 않는다.

## 한계와 주의할 점

- 주요 spectral 경계는 목표 attention이 지정된 query-only 또는 joint query/key 업데이트로 정확히 실현된다는 가정에 의존한다. 일반적인 전체 모델 fine-tuning은 key, value, 앞선 layer와 입력 activation도 바꾸므로 추가적인 irreducible approximation error가 생길 수 있다.
- 확률 바닥값 a가 작으면 전역 하한 상수가 급격히 약해진다. Theorem 4.1에서 a=10⁻², Λ=5, κ_h=3을 넣은 상·하한 비율은 약 2.0×10⁴까지 벌어질 수 있다.
- target-Fisher 하한은 점수 차이가 지정된 범위 안에 있는 제한된 후보군에만 적용되므로 비제한 최적값 E_r의 하한으로 옮길 수 없다. high-mass 결과도 전체 KL의 상한을 제공하지 않는다.
- 정리는 population 수준의 결과이다. 보정 표본에서 추정한 G, Σ와 T_r는 진단값이며, 확률 바닥값·기하·모멘트 상수에 대한 유한표본 신뢰구간이나 보정 곡선의 인증을 제공하지 않는다.
- 결과는 최적 후보의 표현력을 설명하지만 SGD나 다른 학습 알고리즘이 그 후보나 상한을 달성하는 학습 해를 찾는다는 보장은 아니다.
- attention KL이 head 출력이나 최종 task loss로 이어지는 오차 전파를 제한하려면 value/output projection, residual, feed-forward 및 후속 layer에 대한 추가 가정이 필요하다.
- 긴 입력에서 attention이 일부 토큰에 sharply peaked하면 목표 확률 바닥값 a가 매우 작아져 전역 하한이 실용적으로 거의 아무것도 배제하지 못할 수 있다.
- 목표가 query-only 또는 명시된 joint Q/K 클래스 밖에 있으면 spectral 공식은 그目標를 그대로 근사하지 못하며 별도의 irreducible error가 남는다.
- query와 key가 같은 입력에서 계산되므로 독립성 가정이 성립하지 않을 수 있다. 의존성 허용 정리를 사용하려면 실제 후보군 전체에서 비교 상수와 모멘트 조건을 확인해야 한다.
- calibration 입력과 실제 배포 입력의 분포가 다르면 추정한 query–key 가중 특이값 꼬리와 rank–error 곡선이 실제 사용 조건을 반영하지 못할 수 있다.
- joint Q/K 업데이트에서 최적 effective score update가 주어진 두 인수의 랭크 제약으로 구현되지 않으면 factorization gap ρ가 커져 상한이 느슨해질 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### Calibration 입력으로 LoRA rank–KL 곡선 산출기 구현

LoRA 압축 파이프라인의 rank 선택 단계에 논문의 query-only 절차를 붙인다. 완전한 calibration 입력에서 query activation h(u), centered key Gram G(u), 목표 업데이트 Δ*와 목표 attention을 모으고, D*=G^{1/2}Δ*Σ^{1/2}의 특이값 꼬리 T_r를 계산한다. 정리 4.1의 전제 조건이 확인된 경우에만 하한을 표시하고, 확률 바닥값과 모멘트 상수는 가정값 민감도와 함께 제공한다. 경계가 허용하는 rank, 하한이 배제하는 rank, 결정되지 않는 rank를 구분한다.

**적용 지점** — LoRA 압축 파이프라인의 rank 선택 단계

**기대 효과** — 논문은 rank별 상·하한을 계산하는 절차를 제시하지만 실제 모델에서 얻은 압축률, latency 또는 task 성능 향상 수치는 보고하지 않는다.

### Fused multi-head LoRA에 공유 rank 예산 진단 추가

multi-head LoRA 구성 도구에서 head별 rank 설정을 검토하는 지점에 fused 분석을 추가한다. head별 key Gram을 block-diagonal 형태로 묶고 공통 query activation covariance로 가중한 stacked update의 spectral tail을 계산한다. 여러 head에 동시에 기여하는 방향이 있으면 독립 adapter 가정과 다른 공유 예산 효과를 드러낸다. 합산 KL 경계의 √H 의존성과 정리 가정도 결과에 함께 표시한다.

**적용 지점** — Transformer attention의 fused multi-head LoRA rank 할당

**기대 효과** — 정리의 합산 KL 상한은 min{T_r^MH/4, √(2H·T_r^MH)}이다. 실제 토큰 수나 latency 감소 수치는 논문에서 측정하지 않았다.

### Q/K 업데이트에서 effective rank와 factorization gap 분리

query/key 동시 업데이트를 압축하는 단계에서 rank 합 s=r_Q+r_K로 얻은 spectral tail만 단독 기준으로 쓰지 않는다. 목표 effective update의 가중 저랭크 근사 후보가 주어진 개별 Q/K rank 예산으로 실현되는지 점검하고 불일치분을 ρ로 추적한다. ρ가 크면 이론 상한이 느슨해질 수 있으므로 해당 후보를 확정 rank로 취급하지 않는다. RoPE 사용 시 상대 위치별 결합 때문에 단일 행렬 특수화가 적용되는지 별도로 확인한다.

**적용 지점** — joint query/key LoRA의 factorization 및 rank 검증 단계

**기대 효과** — 논문은 상한을 ψ_up(√(T_s^eff+ρ))로 제시하며 ρ=0이 되는 조건도 설명한다. ρ 계산은 일반적으로 비볼록 문제이고 논문은 실용적 알고리즘이나 보편적 상한을 제공하지 않는다.

### 포화 attention에 맞춘 rank 해석 단계 추가

큰 score margin으로 attention이 거의 one-hot에 가까워진 head에서는 업데이트 rank를 원시 logits의 rank만으로 판단하지 않는다. 논문의 isolated-triple 구성에서는 k와 k−⌊k/3⌋의 분리가 증명되며, 별도 선형 토큰 구성은 k−max{⌊k/3⌋,3⌊k/7⌋}의 달성 경로를 보인다. 실제 모델에서는 포화 정도와 margin을 별도 측정한 뒤, 어떤 rank 판정이 유한 logits인지 함수 자체인지 명시한다.

**적용 지점** — 포화된 attention을 사용하는 LoRA 압축 및 rank 해석

**기대 효과** — 포화가 rank 요구량을 줄일 수 있음을 엄밀하게 보이지만, 실제 language-model head에서 closure rank를 계산하는 일반적인 절차나 실측 이득은 제시하지 않는다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 분석 대상 목표와 적용 가능한 정리의 조건 확인 | 고정 pretrained head, 목표 adapter와 다운스트림 입력을 준비한다. 목표가 query-only 또는 명시된 joint Q/K 클래스에서 정확히 실현되는지 확인하고, 독립성·확률 바닥값·기하 및 모멘트 조건의 근거를 정리한다. | 이론적 rank–error 경계를 적용할 수 있는 head와 조건의 범위를 명확히 하며, 적용 불가능한 목표를 구분한다. |
| Phase 2 | 작업 가중 rank–error 곡선 추정 | 완전한 입력 단위로 h(u), centered key Gram G(u), Δ*와 목표 attention을 수집한다. G와 Σ를 추정하고 D*=G^{1/2}Δ*Σ^{1/2}의 rank별 잔여 에너지 T_r 및 후보별 상·하한을 계산한다. 작은 확률 바닥값에는 target-Fisher 또는 high-mass 경로를 조건에 맞춰 검토한다. | 원시 업데이트 특이값과 실제 작업에서 활성화되는 방향을 구분하고, 조건부로 가능한 rank와 미결정 구간을 제시한다. |
| Phase 3 | 실제 압축 후보의 오차와 적용 범위 점검 | 가중 truncated SVD로 후보 rank를 만들고 별도 held-out 입력에서 target-to-candidate attention KL을 측정해 예측 곡선과 비교한다. 최종 task 지표와 layer 출력 영향도는 별도로 측정하고, Q/K factorization gap이나 RoPE 구조를 기록한다. | 이론적 표현력 분석과 실제 학습·배포 성능 사이의 차이를 확인하고, 정리가 지지하는 범위 안에서 rank를 선택한다. |

---

원문 PDF: `2026-08-28-how-much-rank-does-lora-need-rank-error-bounds-for-transformer-attention.pdf`
