---
title: "아주 얕은 양자 회로로도, 멀리 떨어진 두 큐비트의 결과를 하나의 동전 던지기로 연결하면 더 깊은 회로에서나 가능한 상관관계를 만들 수 있다는 것을 증명한 논문"
date: 2026-08-07T07:41:39+09:00
draft: false
description: "본 논문은 얕은 국소 양자회로에 하나의 공유 고전 난수 비트를 사용하는 Pauli 문자열을 중간층에 삽입하면, 같은 깊이의 순수 유니터리 Born 모델로는 표현할 수 없는 분포를 만들 수 있음을 증명한다. 1D 최근접 이웃 구조에서 이 분포를 순수 유니터리로 재현하려면 Ω(N) 깊이가 필요하며, MBQC(측정기반 양자계산)에서는 측정 결과의 피드포워드 제어만으로 이 공유 난수를 자연스럽게 구현할 수 있다."
cover:
  image: "/images/representational-separation-between-unitary-and-channel-quantum-genera/_page_4_Diagram_2.jpeg"
  alt: "공유 난수 비트 s가 제어하는 Pauli-Z 문자열이 중간 층에 삽입되는 shallow channel 학습 모델"
  caption: "논문 원문 발췌"
tags: ["Quantum Machine Learning", "논문 분석", "논문 리뷰", "Born machine", "Pauli string", "MBQC"]
categories: ["논문분석"]
---


아주 얕은 양자 회로로도, 멀리 떨어진 두 큐비트의 결과를 하나의 동전 던지기로 연결하면 더 깊은 회로에서나 가능한 상관관계를 만들 수 있다는 것을 증명한 논문

**무엇이 문제였나** — 짧고 얕은 양자 회로는 가까운 이웃끼리만 연결되어 멀리 떨어진 출력 사이 상관관계를 만들 수 없다.
**어떻게 풀었나** — 회로 중간에 하나의 공유된 무작위 비트로 멀리 떨어진 두 곳의 Pauli 연산을 동시에 적용하는 채널 모델을 도입했다.
**그래서 뭐가 좋아졌나** — 양자 깊이나 장거리 게이트를 추가하지 않고도 shallow 회로가 만들 수 있는 분포의 가족이 엄격하게 더 넓어졌다.

> 마치 두 명의 먼 지역 예술가가 같은 라디오 방송을 듣고 동시에 손을 들거나 내리는 것과 같다. 둘 사이에 전화선이 필요 없고, 방송 신호 하나만 있으면 두 동작이 같이 일어난다.

## 논문 정보

Arunava Majumder, Marius Krumm, Hendrik Poulsen Nautrup, Hans J. Briegel · University of Innsbruck, Department of Theoretical Physics, Austria · arXiv preprint · 2026

## 왜 중요한가

하드웨어 연결성이 제한된 근미래 양자 컴퓨터에서 깊이를 늘리는 대신 값싼 고전 난수 하나로 표현력을 키울 수 있음을 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 필요 회로 깊이 (1D 최악) | **Ω(N)** | 거리 Θ(N)인 두 qubit의 상관을 순수 유니터리로 재현하려면 선형 깊이 필요 |
| TV 분리 하한 (보편 상한 δ*_max) | **1/6 ≈ 0.1667TV distance** | p=1/2, |ΔaΔb|=4일 때 δ* = (1/24)|ΔaΔb| 의 보편 상한. 채널 출력 Q*와 모든 shallow unitary 출력 사이의 TV 거리 하한 |
| 수치 실험 모델 규모 | **N=6, D=2** | Fig. 5의 학습 비교에 사용된 qubit 수와 회로 깊이 |
| 학습 샘플 수 | **6000samples** | MMD 손실 추정에 사용된 표본 수 |

## 어떻게 동작하나

양자 생성 모델은 Born 규칙에 따라 비트열을 샘플링한다. 제한된 연결성을 가진 얕은 유니터리 회로는 backward light cone이 분리되어 먼 지점 사이 상관관계를 만들 수 없다. 저자들은 회로 중간층에 하나의 고전 난수 비트로 제어되는 Pauli 문자열 P_M^s를 삽입한 채널 모델을 정의했다. 이 비트는 떨어진 두 지점의 국소 Pauli 연산을 동시에 켜거나 끄므로, 깊이를 늘리지 않고도 출력 분포에 비국소적 상관을 심는다. 채널 평균 시 두 지점 Z-covariance는 p*(1-p*)(m_a(1)-m_a(0))(m_b(1)-m_b(0))이 되며, 같은 분리를 만드는 순수 유니터리 분포가 없음이 Theorem 15에서 보인다. 1D 최근접 이웃 회로에서 이 분포를 순수 유니터리로 재현하려면 깊이 Ω(N)이 필요하다는 것이 핵심 정리다.

![공유 난수 비트 s가 제어하는 Pauli-Z 문자열이 중간 층에 삽입되는 shallow channel 학습 모델](/images/representational-separation-between-unitary-and-channel-quantum-genera/_page_4_Diagram_2.jpeg)
*공유 난수 비트 s가 제어하는 Pauli-Z 문자열이 중간 층에 삽입되는 shallow channel 학습 모델*

단일 Bernoulli 비트가 멀리 떨어진 qubit들의 Z 연산을 동시에 켜거나 꺼서 shallow depth에서 장거리 상관을 만든다.

핵심 수식:

```
U^{(s)}(\boldsymbol{\theta}) = U_D(\boldsymbol{\theta}_D) \cdots U_{l+1}(\boldsymbol{\theta}_{l+1}) P_{\mathcal{M}}^s U_l(\boldsymbol{\theta}_l) \cdots U_1(\boldsymbol{\theta}_1)
\mathcal{E}_{\boldsymbol{\theta},p}(\rho_{\mathrm{in}}) = \sum_{s\in\{0,1\}} p^s(1-p)^{1-s} U^{(s)}(\boldsymbol{\theta}) \rho_{\mathrm{in}} U^{(s)}(\boldsymbol{\theta})^\dagger
\mathrm{Cov}_{\mathcal{E}^*}(\hat{Z}_a,\hat{Z}_b) = p^*(1-p^*)(m_a(1)-m_a(0))(m_b(1)-m_b(0))
```

첫째 줄(Eq. 9): 공유 비트 s=0/1에 따라 Pauli 문자열 P_M^s가 중간층에 삽입되는 branch unitary. 둘째 줄(Eq. 11): branch들을 확률 p로 평균낸 채널. 셋째 줄(Eq. B16): 채널 출력의 두 지점 Z-covariance. unitary는 shallow depth(D < dist(a,b)/4)에서 backward light cone이 분리되어 Cov=0이 되므로 이 값이 0이 아니면 표현력 분리가 생긴다.

## 실험 결과

![얕은 회로 vs 깊은 회로 vs 공유 난수 삽입의 장거리 상관 생성 개념도](/images/representational-separation-between-unitary-and-channel-quantum-genera/_page_2_Diagram_20.jpeg)
*얕은 회로 vs 깊은 회로 vs 공유 난수 삽입의 장거리 상관 생성 개념도*

shallow circuit에서 light cone이 겹치지 않으면 covariance가 0이지만, 공유 난수 Pauli 문자열이 같은 상관을 만든다.

![QCBM 학습 절차: 목표 분포와 모델 분포의 표본으로 MMD 손실을 계산하고 parameter-shift로 최적화](/images/representational-separation-between-unitary-and-channel-quantum-genera/_page_3_Diagram_2.jpeg)
*QCBM 학습 절차: 목표 분포와 모델 분포의 표본으로 MMD 손실을 계산하고 parameter-shift로 최적화*

학습 루프는 unitary와 channel 모델에 공통으로 적용된다.

![MBQC에서 독립/공유 byproduct를 만들기 위한 측정 결과 보정/반보정 방식과 등가 회로](/images/representational-separation-between-unitary-and-channel-quantum-genera/_page_6_Diagram_2.jpeg)
*MBQC에서 독립/공유 byproduct를 만들기 위한 측정 결과 보정/반보정 방식과 등가 회로*

측정 결과를 보정할지 반보정할지를 같은 비트로 묶으면 독립 난수로는 불가능한 공유 상관이 생긴다.

![Unitary 모델과 correlated channel 모델의 20회 독립 초기화 최소 MMD 손실 분포](/images/representational-separation-between-unitary-and-channel-quantum-genera/_page_11_Figure_2.jpeg)
*Unitary 모델과 correlated channel 모델의 20회 독립 초기화 최소 MMD 손실 분포*

correlated channel이 unitary보다 낮은 MMD 손실을 보이고 초기화에 대한 변동도 작다.

## 한계와 주의할 점

- 분리 정리는 quantum model class 간의 표현력 분리이지 classical computation 대비 계산 우위를 보이는 것은 아니다.
- 분리가 성립하려면 p∈(0,1)이고 Δa, Δb가 모두 0이 아니어야 하므로 모든 파라미터 선택에서 성립하지 않는다.
- 수치 실험은 N=6, D=2의 작은 규모와 branch-peaked mixture라는 제한된 목표 분포만 다룬다.
- 고연결 하드웨어나 native long-range gate가 있는 구조에서는 그래프 거리가 짧아져 분리 효과가 약해진다.
- MBQC 구현은 클러스터 상태 준비와 관련된 자원·오류 부담을 추가로 요구하며, 이 비용은 분리 정리에 포함되지 않는다.
- p=0 또는 p=1이 되면 채널이 결정적 유니터리 branch로 붕괴하여 분리가 사라진다.
- Pauli 문자열이 입력 상태에 대해 자명하게 작용하거나, 비-Clifford 회전의 각도 부호를 바꾸지 못하면 출력 분포가 변하지 않는다.
- 공유되지 않은 독립 random Pauli 연산을 쓰면 Cov(Z_a,Z_b)=0이 되어, naive한 확률 도입만으로는 상관을 만들 수 없다.
- 목표 분포의 두 지점 간 상관이 본질적으로 없으면 채널 모델의 이점이 실제 손실에서 드러나지 않을 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 공유 난수 Pauli 회전을 기존 Pauli 회전 각도 부호 반전으로 흡수하는 회로 컴파일러 최적화

이 논문의 Section II C 4에서 유도한 endpoint 보정 후에도 중간 비-Clifford 회전의 각도 부호 반전이 남는다는 성질을 이용한다. 파라미터화된 Pauli 회전을 지원하는 하드웨어에서, stochastic Pauli 문자열 삽입을 선택된 qubit들의 R_x 각도에 대한 공유 sign flip으로 컴파일한다. 회로 중간층에는 아무 게이트도 추가하지 않으므로 shallow depth가 유지된다. 이 최적화는 양자 회로 컴파일러의 게이트 스케줄러에 구현할 수 있다.

**적용 지점** — 양자 회로 컴파일러의 게이트 스케줄링/파라미터 변환 단계

**기대 효과** — 추가 양자 게이트 깊이 없이 unitary 대비 필요 깊이 Ω(N)을 고정 shallow depth로 대체한다.

### MBQC 피드포워드에서 보정/반보정을 같은 비트로 묶는 공유 난수 생성기

이 논문의 Eq. (44)-(49)에서 단일 Bernoulli 변수 s가 boundary qubits의 byproduct를 함께 켜고 끄는 구성을 그대로 시스템화한다. 기존 MBQC 컨트롤러는 항상 byproduct를 보정하지만, trainable 확률 p로 보정/반보정을 선택하고 support M의 qubits에 동일한 s를 적용하도록 확장한다. 이러면 추가 양자 게이트나 ancilla 없이 채널 모델이 된다. 광자 클러스터 상태 기반 양자 컴퓨팅 SDK의 피드포워드 레이어에 구현할 수 있다.

**적용 지점** — MBQC 컨트롤러의 측정 결과 피드포워드 규칙

**기대 효과** — 유효 byproduct 확률을 [0,1] 전 구간에서 조절하면서, 독립 난수로는 불가능한 Cov(Z_a,Z_b)≠0을 만든다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 이론적 분리 재현 및 시뮬레이터 검증 | 1D 최근접 이웃 구조에서 N=6~12, D=2 수준의 회로를 구현하고, 단일 공유 Pauli-Z 문자열을 중간층에 삽입한 뒤 MMD 손실과 parameter-shift 기울기로 학습한다. unitary 모델과의 TV 거리 및 손실 분포를 비교한다. | Theorem 15의 δ*와 unitary depth Ω(N) 경향을 실측으로 확인한다. |
| Phase 2 | 실제 bounded-degree 하드웨어로 이식 | 2D 격자/중성원자 배열에서 interaction graph distance를 기준으로 Pauli 문자열의 support와 삽입 슬롯을 자동 탐색한다. p 초기화 범위와 정규화를 추가하고, dynamic circuit 대비 샘플 비용과 오류 영향을 비교한다. | 하드웨어 연결성 제약 아래 공유 난수 채널 모델의 실질적 이점을 확인한다. |
| Phase 3 | MBQC 및 클라우드 양자 서비스에 통합 | MBQC 컨트롤러에 byproduct 보정/반보정 로직을 추가하고, 공유 byproduct 문자열 라이브러리를 구축한다. 이를 API화하여 shallow-depth 양자 생성 모델을 외부 개발자가 호출할 수 있게 한다. | 추가 양자 깊이 없이 장거리 상관을 가진 생성 모델을 산업 현장에 제공한다. |

---

원문 PDF: `2026-08-07-representational-separation-between-unitary-and-channel-quantum-generati.pdf`
