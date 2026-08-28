---
title: "AI 칩이 학습할 때 옆 칸 기억장치를 건드리지 않도록 만든 새로운 메모리 소자"
date: 2026-08-29T07:40:01+09:00
draft: false
description: "이 논문은 아날로그 ReRAM 크로스바 어레이의 완전 병렬 가중치 업데이트 시 발생하는 cross-point 소자 간섭(update disturbance) 문제를 해결하기 위해, 사전 형성된 나노 필라멘트가 열-전기 에너지를 국소화하는 메커니즘에 기반한 CMOS 호환 CMO/HfOx ReRAM 소자를 350 nm 실리콘 기술로 개발했다."
cover:
  image: "/images/update-disturbance-resilient-analog-reram-crossbar-arrays-for-in-memor/_page_2_Figure_2.jpeg"
  alt: "아날로그 AI 가속기의 전체 구조와 완전 병렬 가중치 업데이트 메커니즘, 그리고 소자 비-선형성의 역할"
  caption: "논문 원문 발췌"
tags: ["Neuromorphic Hardware / In-Memory Computing", "논문 분석", "논문 리뷰", "ReRAM", "Crossbar", "Update disturbance"]
categories: ["논문분석"]
---


AI 칩이 학습할 때 옆 칸 기억장치를 건드리지 않도록 만든 새로운 메모리 소자

**무엇이 문제였나** — 스마트폰이나 IoT 기기 안에서 AI를 직접 학습하려면, 수많은 메모리 칸의 값을 한꺼번에 고쳐야 한다
**어떻게 풀었나** — 이때 한 칸을 고치면 옆칸까지 살짝 흔들리는 '교차섭동' 때문에 정확도가 떨어지곤 했다
**그래서 뭐가 좋아졌나** — 연구팀은 도전성 필라멘트로 열과 전기 에너지를 한 점에 모아, 큰 전압에만 반응하는 메모리를 만들어 이 문제를 해결했다

> 마치 수많은 수도꼭지가 달린 배수판에서, 한 꼭지를 틀어도 다른 꼭지가 물을 흘리지 않는 장치와 같다. 가벼운 돌림(절반 전압)에는 완전히 막혀 있고, 제대로 틀었을 때(전체 전압)만 물이 나와서 옆 칸이 새지 않는다.

## 논문 정보

Wooseok Choi, Tommaso Stecconi, Donato Francesco Falcone, Matteo Galetta et al. · IBM Research Europe-Zurich, Switzerland; Instituto de Microelectrónica de Sevilla (IMSE-CNM), CSIC and Univ. de Sevilla, Spain · arXiv preprint (cs.ET) · 2026

## 왜 중요한가

지금 AI 학습에는 엄청난 전력과 비용이 든다. 이 소자 칩이 상용화되면, 폰이나 IoT 기기 안에서도 AI를 직접 학습시킬 수 있어 데이터센터 왕복이 줄어들고 전력·비용이 크게 낮아진다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 비-선형성 계수 k | **< 0.005(σ ≈ 0.025)** | 100k disturbance 펄스 후 평균; 기존 문헌(0.03~0.13) 대비 1~2단계 낮음 |
| MNIST 시험 정확도 | **89.08%** | k=0.005 SGD, 10k 훈련/시험 이미지; k=0 이상적(90.6%) 대비 1.52%p 차이 |
| Tiki-Taka 통합 MNIST 정확도 | **95.2%** | TT v4 + σd-to-d=0.18 노이즈 포함, FP baseline에 근접 |
| 아날로그 스위칭 속도 | **60ns** | 단일 소자 60 ns 펄스로 set/reset 동작 검증; 어레이 실험은 2.5 µs 펄스 사용 |

## 어떻게 동작하나

이 연구는 아날로그 ReRAM 크로스바에서 가중치를 병렬로 업데이트할 때 발생하는 update disturbance 문제를 사전 형성된 나노 스케일 도전성 필라멘트(CF)의 열-전기 에너지 국소화 현상으로 해결한다. CMOS 호환 350 nm BEOL 공정으로 TiN/CMO/HfOx/TiN 구조의 1T1R 셀을 제작하고, 평균 2.8 V 포밍 후 +1.4 V/-1.9 V, 2.5 µs 펄스(단일 소자에서는 60 ns +1.6 V/-2.3 V)로 아날로그 스위칭을 구현했다. COMSOL 다물리 시뮬레이션으로 ~11 nm 반지름 CF가 전계와 Joule 열을 CMO 박막의 반구형 활성 영역에 집중시켜 Arrhenius 이온 이동률이 입력 전압 진폭에 대해 강한 비-선형성을 갖게 됨을 보였다. 평균 Nstate≈27과 >10^8 사이클의 내구성을 확보한 5×5 와이어 본딩 어레이에서 Gmin·Gmax 양 경계 모두 100k 비-동시 펄스 인가 후에도 k<0.005를 유지하고, stochastic half-Vs 펄스 트레인을 이용한 교란 없는 병렬 가중치 매핑을 시연했다. 마지막으로 soft-bounds 모델을 기반으로 한 하드웨어-인지 시뮬레이터로 MNIST 학습을 수행해 89.08%(Tiki-Taka 통합 시 95.2%) 정확도를 달성, 완전 인-메모리 학습 가속기 적용 가능성을 입증했다.

![아날로그 AI 가속기의 전체 구조와 완전 병렬 가중치 업데이트 메커니즘, 그리고 소자 비-선형성의 역할](/images/update-disturbance-resilient-analog-reram-crossbar-arrays-for-in-memor/_page_2_Figure_2.jpeg)
*아날로그 AI 가속기의 전체 구조와 완전 병렬 가중치 업데이트 메커니즘, 그리고 소자 비-선형성의 역할*

half-Vs 펄스의 비-동시 노이즈가 동시 펄스보다 압도적으로 많은 환경에서, 강한 비-선형성이 없으면 가중치가 표류함

핵심 수식:

```
P(\mathbf{x}) = \begin{pmatrix} p(x_1) \\ p(x_2) \\ p(x_3) \end{pmatrix}, \quad P(\mathbf{d}) = \begin{pmatrix} p(d_1) \\ p(d_2) \\ p(d_3) \end{pmatrix}, \quad P(\mathbf{x})P(\mathbf{d})^T = \begin{pmatrix} p(x_1)p(d_1) & p(x_1)p(d_2) & p(x_1)p(d_3) \\ p(x_2)p(d_1) & p(x_2)p(d_2) & p(x_2)p(d_3) \\ p(x_3)p(d_1) & p(x_3)p(d_2) & p(x_3)p(d_3) \end{pmatrix} \quad (1)

k = \frac{\Delta g(0.5V_s)}{\Delta g(V_s)} \quad (2)

w_{ij} \leftarrow w_{ij} + \eta x_i d_j \quad (3)

N_{\text{update}_{ij}} = \sum_{n=1}^{BL} P_i^n \wedge P_j^n \quad (4)

\begin{aligned}\Delta w^+ &= \alpha^+ \left( \frac{\check{w}_{\max} - w}{\check{w}_{\max}} + \sigma_{c\text{-to-}c}\xi \right) \\ \Delta w^- &= -\alpha^- \left( \frac{\check{w}_{\min} - w}{\check{w}_{\min}} + \sigma_{c\text{-to-}c}\xi \right)\end{aligned}\t
```

Eq.(1): P(x)P(d)^T ∝ xd^T는 확률 인코딩된 외적 가중치 갱신 행렬. Eq.(2): k = Δg(0.5V_s)/Δg(V_s). 0에 가까울수록 이상적이며 본 소자는 평균 <0.005(σ≈0.025). Eq.(3): w_ij는 i행-j열 시냅스 가중치, η는 학습률, x_i·d_j는 순전파 활성화와 역전파 오차. Eq.(4): BL은 확률 비트스트림 길이, P_i^n∧P_j^n은 n번째 비트에서의 동시 펄스(AND)로, N_update_ij는 원하는 가중치 변화 ηx_i d_j에 비례. Eq.(5)~(7): soft-bounds 모델; α^±은 업데이트 기울기, w_max/min은 경계값, σ_c-to-c는 사이클 간 변동, σ_k^±은 비-동시 half-V_s 펄스로 인한 왜곡으로 k와 lookup table로 연결.

## 한계와 주의할 점

- 5×5 어레이(25 셀)에서만 실험적 매핑 시연, 대규모 어레이(수천~수만 셀)로 확장 시 IR drop·배선 기생저항·누설 영향 미검증
- 350 nm CMOS 기술로 제작되어 28 nm/14 nm 등 첨단 노드 대비 집적도·속도 불리. 상용 가속기 적용을 위한 미세화 이전 필수
- MNIST(10 클래스)만 검증. CIFAR-10·ImageNet 등 복잡 데이터셋에서 학습 정확도와 수렴 안정성 미평가
- kup과 kdn의 비대칭성이 0.01을 넘으면 정확도가 급격히 저하(Fig 6e)되어, 공정 산포에 의한 비대칭 보정 회로·펄스 설계가 필요
- BL(비트스트림 길이)를 동적으로 10→1로 줄이는 휴리스틱에 의존. BL이 길수록 disturbance 누적 가능성이 커지나 최적점은 데이터셋·네트워크 구조에 의존
- 1M non-coincident 펄스의 극한 조건에서 Gmax 상태에서 Joule heating 누적에 의한 G drift가 관측됨(Fig 5c). 100k까지는 안정적이나, 장기 신뢰성 추가 검증 필요
- k 비대칭성(kup≠kdn) → 한쪽 방향으로 가중치가 일방향 표류해 학습 발산 또는 정확도 급락 (Fig 6e)
- 고전도(Gmax) 상태에서 1M 비-동시 펄스 인가 시 Joule heating 누적에 의한 G drift 발생 (Fig 5c)
- 디바이스 간 σd-to-d 변동성(0.18)으로 경계 상태 분포가 퍼지면 학습 정확도 분산 확대 가능 (Fig 6f)
- cycle-to-cycle 메타안정적 산소 이온 이동에 의해 단일 펄스 응답이 k=0.05까지 변동 (Fig 5d)

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### k<0.01 품질 게이트를 아날로그 메모리 검증 라인에 삽입

본 논문의 Fig 6e에서 k>0.01일 때 정확도가 급락한다는 사실을 역이용한다. 1T1R 셀 검증 단계에 half-Vs 펄스 자동 인가 + Δg 측정 모듈을 추가해, 평균 k<0.01·kup≈kdn인 셀만 합격 처리한다. k가 비대칭이거나 분산이 큰 셀은 보상 회로(논문 4장 baseline offset)와 페어링하거나 폐기한다. 이는 기존 단순 on/off 판정만 하던 메모리 테스트를 '학습 가능성' 기준으로 확장한 품질 게이트다.

**적용 지점** — 아날로그 메모리 소자/어레이 검증 단계

**기대 효과** — 학습 정확도 분산 σd-to-d=0.18 환경에서도 Tiki-Taka 적용 시 95.2% 정확도를 안정적으로 재현 (Fig 6f 기반)

### k-결합 soft-bounds 시뮬레이터를 표준 학습 정확도 예측 도구로 채택

논문 Eq. (5)~(7)의 soft-bounds 모델은 σk 파라미터로 비-동시 펄스 교란을 명시적으로 반영한다. 이를 인-메모리 컴퓨팅 칩 설계 시뮬레이터의 표준 모듈로 채택하면, (1) 제작 전 k sweep으로 학습 정확도 컨투어(Fig 6e)를 그릴 수 있고, (2) 비트스트림 길이·baseline 오프셋·하이퍼파라미터를 한 시뮬레이션 안에서 공동 최적화할 수 있다. 기존 cross-sim·NeuroSim 대비 disturbance 항이 명시적이라는 점에서 차별화된다.

**적용 지점** — 인-메모리 컴퓨팅 학습 정확도 사전 시뮬레이션

**기대 효과** — k=0.005 환경에서 SGD 89.08%, Tiki-Taka 95.2% 정확도를 시뮬레이션으로 사전 예측·검증 (Fig 6c, 6f 기반)

### 비대칭 k 보상을 위한 row/column baseline 전압 오프셋 펄스 설계

논문 Discussion 4장의 비대칭 k 보상 원리를 펄스 발생기 회로에 구체화한다. 통상 row와 column에 동일한 baseline을 걸어 비-선택 셀의 전위차가 0이 되지만, kup≠kdn 소자에서는 row와 column baseline을 비대칭으로 설정해 한쪽 half-pulse 진폭을 줄이고 반대편 baseline 차로 보상한다. 동시에 BL을 짧게 가져가 비-동시 펄스 빈도를 줄이고, 학습 데이터셋 크기를 교란 누적 한도 이내로 최적화한다. Fig 6e의 kup/kdn 비대칭 영역에서 정확도 손실을 상당 폭 완화할 잠재력이 있다.

**적용 지점** — 병렬 업데이트용 펄스 발생기

**기대 효과** — 비대칭 k 환경에서 정확도 손실 완화(논문 Fig 6e kup≠kdn 영역 분석 기반), 추가 검증을 통해 정확도 회복 가능

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 소자/어레이 품질 관리 체계 확립 | 각 1T1R 셀의 k·Nstate·σd-to-d 자동 측정 파이프라인 구축, k<0.01 품질 게이트 통과 소자 풀 식별, 28 nm CMOS 이전을 위한 소자 다운-스케일링(70 nm SiO2 결과 기반) 검증 | 인-메모리 학습 가능 소자 선별 기준 정립, 출하 수율 확보 기반 마련 |
| Phase 2 | 알고리즘-하드웨어 공동 검증 | IBM AIHwKit과 연동해 CIFAR-10·ImageNet 등 복잡 데이터셋 학습 정확도 측정, Tiki-Taka v4 외 분산 학습·TT 확장 버전 통합 검증, 비대칭 k 보상을 위한 baseline 전압 오프셋 펄스 발생기 구현 | 90% 이상 학습 정확도를 다양한 NN 구조에서 재현, 알고리즘·펄스 설계 공동 최적화 |
| Phase 3 | 첨단 노드 파일럿 및 상용 학습 가속기 양산 | 28 nm/14 nm 첨단 노드 BEOL 통합 검증, 다중 어레이 적층을 위한 크로스바 인터커넥트 설계, 실제 엣지 디바이스·데이터센터 가속기 카드 파일럿 도입 | 고집적 인-메모리 학습 가속기 상용화 기반 마련 |

---

원문 PDF: `2026-08-29-update-disturbance-resilient-analog-reram-crossbar-arrays-for-in-memory.pdf`
