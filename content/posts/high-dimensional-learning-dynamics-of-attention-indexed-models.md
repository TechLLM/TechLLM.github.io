---
title: "어텐션 행렬을 어떻게 쪼개 표현하느냐에 따라 거대한 모델이 빈 상태에서 정보를 학습해 빠져나오는 속도와 경로가 완전히 달라진다는 것을 수학적으로 증명한 이론 논문이다."
date: 2026-09-06T08:09:14+09:00
draft: false
description: "본 논문은 어텐션 행렬의 랭크가 임베딩 차원에 비례해 커지는 extensive-rank 체제에서 attention-indexed 모델의 고차원 학습 동역학을 분석한다. 핵심 발견은 population loss는 유한 차원의 order parameter(μ, Ω, Ψ)로 기술되지만, online SGD는 무한 차원의 matrix moment 계층을 생성한다는 점이다."
tags: ["Deep Learning Theory / Foundation Models", "논문 분석", "논문 리뷰", "Attention-indexed model", "Extensive-rank", "Order parameter"]
categories: ["논문분석"]
---


어텐션 행렬을 어떻게 쪼개 표현하느냐에 따라 거대한 모델이 빈 상태에서 정보를 학습해 빠져나오는 속도와 경로가 완전히 달라진다는 것을 수학적으로 증명한 이론 논문이다.

**무엇이 문제였나** — 어텐션은 모든 최신 거대 모델의 핵심 부품인데, 학습 과정이 수학적으로 어떻게 돌아가는지 거의 알려진 바가 없었다
**어떻게 풀었나** — 모델의 차원을 무한대로 키우는 극한에서 어텐션-인덱스 모델이라는 틀을 세우고, 어텐션 행렬을 직접 쓰는 경우·대칭 형태로 묶는 경우·두 행렬의 곱으로 푸는 경우 세 가지를 비교했다
**그래서 뭐가 좋아졌나** — 어떤 어텐션 구조가 언제, 왜 정보를 학습하기 시작하는지 정확히 알 수 있게 되었고, 무한 차원 동역학을 유한 차원으로 근사하는 방법도 함께 얻었다

> 이 논문의 핵심 아이디어는 마치 두 개의 다른 지도(한 장은 흑백 대칭으로만 그려진 지도, 한 장은 컬러 비대칭 지도)를 들고 같은 미로를 찾는 것과 같다. 똑같이 똑똑한 사람이라도 어떤 지도냐에 따라 미로에서 빨리 나갈 수도, 영원히 헤맬 수도 있다. 어텐션의 표현 방식, 즉 어떤 '지도'를 들고 학습하느냐가 신경망의 학습 운명을 결정한다는 것이 이 논문의 주장이다.

## 논문 정보

Yizhou Xu, Margarita Sagitova, Lenka Zdeborová, Florent Krzakala · EPFL (Information, Learning and Physics Laboratory & Statistical Physics of Computation Laboratory) · arXiv preprint (arXiv:2609.03858v1, cs.LG) · 2026

## 왜 중요한가

이 분석은 단순한 이론이 아니라 실제 트랜스포머를 어떻게 설계하고 어떤 초기화로 시작하며 어떤 학습률 규칙을 쓸지에 대한 단서를 준다. 특히 tied 구조가 대칭을 깨는 메커니즘은 왜 어떤 트랜스포머는 빠르게 학습하고 다른 모델은 한참 멈춰 있는지를 이해하는 열쇠가 된다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 약한 회복 샘플 복잡도 (tied) | **Θ(d²log d)samples** | tied 어텐션(S=WW⊤)이 uninformative 초기화에서 teacher overlap을 만들기까지 필요한 샘플 수 (Corollary 3, 최대 학습률 스케일 α_d=Θ(1/(d log d))에서) |
| Population loss 차원 | **Finite (μ, Ω, Ψ)** | 고차원 극한에서 population loss를 완전히 결정하는 order parameter의 집합 (Theorem 1) |
| SGD 동역학 차원 | **Infinite hierarchy** | Tied/untied 어텐션의 online SGD가 생성하는 matrix moment 계층의 본질적 차원 (Theorem 2·3) |
| 유한 절단 근사 오차 | **지수 감쇠 (C²*/s₀)^(M+1)** | M차 절단 ODE의 무한 차원 동역학 근사 오차 상한. Figure 1(d=400, softmax, MSE)에서 M을 키울수록 경험적 궤적과 일치함을 확인 |

## 어떻게 동작하나

이 논문은 attention-indexed 모델이라는 일반 틀을 도입한다. 입력 토큰들 사이의 2차 형식 x_i⊤ S_k x_j / √d 의 모음으로 손실을 표현하며, multi-layer multi-head 어텐션(어텐션-only 트랜스포머 전체)도 이 틀로 표현 가능하다(부록 B에 자기회귀 시퀀스 모델, 다중 위치 회귀, 다단계 추론, 광범위-랭크 행렬 디노이징 등 추가 예시). 핵심 가정은 어텐션 행렬의 랭크가 차원 d와 함께 커지는 extensive-rank 체제(||S||_op/||S||_F → 0)이다. 이 가정 하에서 Theorem 1이 2차 형식들의 결합 분포가 다변량 가우시안으로 수렴함을 보여, population loss는 μ, Ω, Ψ라는 유한한 trace 통계량만으로 결정됨을 증명한다(Corollary 1은 최적화 수준에서의 유한 차원 정리를 준다). 그러나 학습 동역학은 다르다. Tied S=WW⊤나 untied S=UV⊤로 분해하면 moment들이 서로 의존하는 무한 계층을 형성하며, 부록 D.3의 정확히 풀리는 예시에서 유한 차원 ODE로는 모든 궤적을 재현할 수 없음이 확인된다. Theorem 2는 이 무한 계층의 결정론적 ODE 극한을 도출하고, Corollary 2는 M차 절단으로 근사할 때 오차가 M에 대해 지수적으로 작아짐을 보인다. Theorem 3은 untied 분해에서 mean이 빠른 시간 척도(t=nα_d), matrix moment가 느린 시간 척도(τ=nα_d/d)로 움직이는 fast-slow 구조를 밝힌다. 마지막으로 Corollary 3, 4는 각 분해에서 weak recovery가 일어나는 조건과 Θ(d²log d) 샘플 복잡도(및 그 실패 조건)를 증명한다.

핵심 수식:

```
\mathrm{Cov}(G_{ijk}, G_{i'j'k'}) = C_{ii'}C_{jj'}\,\Omega_{ijk,i'j'k'} + C_{ij'}C_{ji'}\,\Psi_{ijk,i'j'k'}
```

G_ijk는 2차 형식의 고차원 극한 가우시안 변수(평균은 C_ij μ_ijk). Ω는 Tr(SS'ᵀ)/d 극한(전치를 포함하는 2차 trace, Eq.4에서 C_ii'C_jj' 항과 결합), Ψ는 Tr(SS')/d 극한(전치 없는 2차 trace, C_ij'C_ji' 항과 결합)이다. Population loss는 이 유한 통계량만으로 결정된다(Theorem 1).

## 한계와 주의할 점

- Gaussian 입력 데이터 가정을 전제로 한다. 자연어·이미지 등 실제 데이터의 heavy-tailed 특성은 본 분석의 적용 범위를 제한한다.
- 본 결과는 attention-only 트랜스포머에 한정된다. 실제 트랜스포머의 FFN, residual scaling, layer norm 등은 본 틀에 포함되지 않아 일반화 트랜스포머에 그대로 적용하기 어렵다. 저자들도 일반 딥 트랜스포머의 Q·K·V 전체 동역학은 유도하지 않았다고 명시한다.
- Online SGD(샘플당 1스텝)만 분석한다. 배치 SGD, empirical risk minimization, 경사 흐름 등 실전 최적화 절차에서 생기는 추가 상관 구조는 본 결과로 설명되지 않으며, 결론에서 future work로 명시된다.
- Θ(d²log d) weak recovery는 정보 노출 시점만 다룬다. 그 이후의 strong recovery 속도(PL 조건 하 부록 D.5·F.4에서만 다룸), 일반화 오차, 그리고 활성화 함수의 information exponent가 지배하는 더 긴 시간 스케일의 거동은 본 논문에서 미해결로 남는다(Figure 3도 정량 복잡도는 future work로 언급).
- Theorem 2는 4회, Theorem 3는 6회까지의 매끄러움과 균일 spectral bound, weight decay(Assumption 2.4·4.5) 등 강한 정규성 가정을 요구한다. 특히 weight decay는 균일 시간 오차를 위한 것으로, 수치 실험에서는 없어도 궤적이 유계로 남는다고 저자들이 언급한다.
- Direct S 최적화: 고차 활성화(h2, h3) 하에서 uninformative manifold이 invariant하게 남아 학습이 정지함 (Figure 2 우측, 부록 E).
- Untied 어텐션: 자유 상태 집합 Mfree 위에서 cross-gradient [∇q^(r) Φ(m*(q),q)]₁₂=0이 유지되면 d²log d 샘플 척도에서 weak recovery가 일어나지 않음 (Corollary 4 (ii)). 다만 fast phase가 student-side 평균을 이동시켜 E[σ'(Z₁)]≠0로 만들면 회복이 가능함 (Eq.48–49).
- Tied 어텐션: cross-gradient [∇Φ(q̄(0))]₁₂=0이면 비대칭을 만들 수 없어 symmetry-breaking 메커니즘이 작동하지 않음 (Corollary 3, condition (19)).
- Weight decay(γ>γ*) 부재 시 Corollary 2의 균일 시간 오차 상한이 깨지고 절단 오차 상수가 시간 수평 T에 의존하게 됨(발산은 아님). Untied 경우 Assumption 4.4의 균형 조건(|t̄A_k(0)-t̄B_k(0)|≥c_bal) 위반 시 slow 흐름의 분모 t̄A_k+t̄B_k 제어가 실패할 수 있음.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 저차 모멘트 절단으로 attention 블록 학습을 예측하는 시뮬레이터

본 논문의 Theorem 2와 Corollary 2는 M차 절단 ODE가 무한 차원 moment 계층을 M에 대해 지수적으로 작아지는 오차로 근사함을 보인다. Figure 1에서 d=400, softmax 활성화, MSE 손실 설정으로 M을 키울수록 결정론적 이론과 online SGD 궤적이 일치함이 확인되었다. 이 결과를 활용해, transformer의 attention 블록 한 개를 떼어내 저차(예: M=3~4) moment만 추적하면서 잠재적 학습 궤적을 미리 예측하는 경량 시뮬레이터를 만들 수 있다. 적용 지점은 트랜스포머의 단일 attention 블록(키·쿼리 결합 행렬 S를 tied S=WW⊤ 또는 untied S=UV⊤로 분해한 형태)이고, 입력은 가우시안 합성 데이터로 시작해 실제 입력에 대해 점진 보정한다. 이 시뮬레이터는 GPU 없이도 수만 step의 학습 궤적을 빠르게 탐색할 수 있어 optimizer·학습률·초기화 비교 탐색 비용을 크게 줄인다.

**적용 지점** — attention 블록 단위 학습 동역학 시뮬레이션 및 optimizer 탐색 단계

**기대 효과** — Corollary 2가 명시한 M에 대한 지수적 오차 감쇠 덕분에, M=3~4 정도만 써도 무한 차원 궤적에 근사 가능하다 (수치 정확도는 truncation 차수 M으로 직접 제어 가능, Figure 1의 정성적 확인과 일치)

### Untied 어텐션의 fast-slow 학습률 스케줄

Theorem 3에 따르면 untied S=UV⊤의 online SGD는 mean 변수 m이 빠른 시간 척도 t=nα_d로, matrix moment가 느린 시간 척도 τ=nα_d/d로 움직이는 두 시계 영역을 가진다. 이는 학습 초기 빠른 시간 동안 mean을 사전 조정하고, 이후 천천히 covariance를 학습하는 자연스러운 분리를 의미한다. 이를 학습률 스케줄로 옮기면, 초기에 α_d를 크게(빠른 사전 조건화 구간) 가져갔다가 mean이 critical manifold m⋆(q)에 안착한 후 α_d를 1/d 스케일로 줄이는(timescale-aware) 규칙을 적용할 수 있다. 적용 지점은 untied 어텐션을 쓰는 트랜스포머 블록의 optimizer 래퍼 단계이며, weakly-supervised 작업에서 student mean 사전 조정이 중요한 경우 효과가 크다.

**적용 지점** — untied attention을 쓰는 트랜스포머의 optimizer 학습률 스케줄 단계

**기대 효과** — Fast phase에서 student-side 대칭을 깨는 데 필요한 시간을 단축하고, Corollary 4(i) 조건(Q₂g*₁₂≠0) 충족 시 Θ(d²log d) 스케일 회복이 시작되도록 한다

### Tied 어텐션의 자동 대칭 깨짐을 활용한 사전학습 초기화 설계

Corollary 3은 tied S=WW⊤가 dp̄₁₂/dt|₀ = -2[∇Φ(q̄(0))]₁₂t̄₁(0)p̄₂₂ 항을 통해 uninformative manifold을 자동으로 벗어남을 보인다. 이 메커니즘을 더 강하게 활용하려면, 초기화에서 (a) t̄₁(0)=Tr(W₁W₁⊤)/d를 충분히 큰 양수로 두고, (b) cross-gradient [∇Φ(q̄(0))]₁₂≠0인 위치에 두는 초기화 스킴을 설계한다. 논문의 Hermite 전개(Eq.23)는 활성화의 기울기가 0이 아닐 때 조건 (19)가 자동으로 만족됨을 보여준다. 이 통찰은 단순한 가우시안 초기화 대신, trace 통계량을 명시적으로 제어하는 '대칭 깨짐 친화' 초기화 전략으로 일반화될 수 있다. 적용 지점은 foundation model의 첫 self-attention 블록(특히 pre-training 초기 teacher signal이 약한 단계)이다.

**적용 지점** — foundation model의 첫 self-attention 블록 사전학습 초기화 단계

**기대 효과** — Tied 분해 선택 시 Θ(d²log d) 스케일의 weak recovery 시점을 앞당길 수 있다 (Corollary 3의 sample complexity bound는 초기화 스케일 t̄₁(0)와 cross-gradient에 의존)

### Information exponent 기반 어텐션 활성화·분해 조합 선택기

Figure 3(d=800, MSE)와 결론에서 저자들은 untied 어텐션의 weak recovery sample complexity가 활성화 함수의 information exponent에 의존함을 관찰하고, 정량 분석을 future work로 남긴다. Figure 2에서도 direct S는 고차 활성화(h2, h3)에서 uninformative 상태에 갇히는 반면 tied 흐름은 탈출한다. 실용적으로는 작업별로 (i) 선형에 가까운 활성화에서는 모든 분해가 빠르게 회복하지만, (ii) 고차 활성화에서는 tied 분해가 직접 S 대비 압도적으로 빠르고, untied는 fast phase의 mean 사전 조정 여부에 따라 갈린다는 정성적 규칙이 이미 도출 가능하다. 이를 트랜스포머의 head별 분해(어떤 head는 tied, 어떤 head는 untied) 또는 attention 활성화와 결합해 작업별 최적 구성을 추천하는 의사결정 모듈로 만들 수 있다. 적용 지점은 새 모델 아키텍처를 설계하는 단계의 구조 탐색 단계다.

**적용 지점** — 새 transformer 아키텍처 설계 시 head별 분해 방식과 활성화 함수 조합을 선택하는 단계

**기대 효과** — Figure 2·3의 정성적 결과(고차 활성화에서 직접 S는 학습 정지, tied는 회복, untied는 지연)에 기반해, 잘못된 분해-활성화 조합을 사전에 회피한다 (정량 수치는 본 논문에서 future work로 남아 향후 보완 필요)

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 저차 모멘트 추정 파이프라인 구축 및 검증 | Transformer의 1개 attention 블록에 대해 학습 중 trace 통계량(μ, Ω, Ψ)과 2~3차 moment을 주기적으로 추정하는 프로브를 구현한다. 작은 모델(≤10M 파라미터)에서 본 논문의 Theorem 1이 예측하는 가우시안 근사를 실험으로 확인한다. | 이론이 예측하는 population loss가 실제 트랜스포머에서도 잘 맞는지를 검증하고, 후속 단계의 진단 시스템 신뢰도를 확보한다. |
| Phase 2 | 어텐션 구조 비교 실험 및 약한 회복 감지 | 동일한 데이터·옵티마이저 하에서 tied/untied/direct S 어텐션을 비교하는 작은 스케일 실험을 돌려, 본 논문이 예측한 Θ(d²log d) 스케일의 weak recovery 패턴이 실제 학습에서도 나타나는지 확인한다. Figure 2(d=400)·3(d=800)와 동일한 정성적 결과를 재현한다. | 구조 선택 가이드라인의 실효성을 검증하고, 작업별 최적 어텐션 분해를 결정한다. |
| Phase 3 | 프로덕션 학습 파이프라인 통합 | 검증된 저차 모멘트 추정기를 실제 foundation model 학습 로그 분석에 붙이고, tied/untied 선택 가이드를 표준 아키텍처 카탈로그에 반영한다. 정보가 약한 단계(early training)에서의 옵티마이저·학습률 자동 결정에 본 논문의 timescale 분리 통찰을 활용한다. | 거대 모델 학습의 안정성과 수렴 속도를 개선하고, 학습 실패 사례의 조기 진단이 가능해진다. |

---

원문 PDF: `2026-09-05-high-dimensional-learning-dynamics-of-attention-indexed-models.pdf`
