---
title: "메모리 셀 하나에 작은 수도꼭지와 큰 수도꼭지를 함께 달아, 조심스럽게 쓸 때와 확실히 지울 때를 따로 맡긴 칩 설계다."
date: 2026-09-21T07:33:37+09:00
draft: false
description: "OTTER는 28 nm CMOS 위에 TaOx VCM RRAM을 집적한 6×6 mm² 연구용 칩으로, 한 RRAM 셀에 고구동(HD, W/L=10)·저구동(LD, W/L=2) 트랜지스터를 병렬로 붙인 2T1R 구조를 검증한다. SET은 LD로 세밀하게 제어하고 RESET은 HD로 수행해 LD-HD 구성에서 SET WL 1.8/2.2/2.4 V 조건 모두 on/off 비 5 이상을 유지했다."
tags: ["Emerging Memory / Compute-in-Memory / Neuromorphic Hardware", "논문 분석", "논문 리뷰", "2T1R", "RRAM", "SET / RESET"]
categories: ["논문분석"]
---


메모리 셀 하나에 작은 수도꼭지와 큰 수도꼭지를 함께 달아, 조심스럽게 쓸 때와 확실히 지울 때를 따로 맡긴 칩 설계다.

**무엇이 문제였나** — RRAM은 값을 쓸 때는 전류를 조금씩 조절해야 하고, 값을 지울 때는 충분히 큰 힘이 필요하다.
**어떻게 풀었나** — 이 논문은 한 셀에 트랜지스터 두 개를 붙여 작은 쪽은 쓰기, 큰 쪽은 지우기에 쓰면 두 요구를 함께 만족할 수 있음을 보였다.
**그래서 뭐가 좋아졌나** — 그 결과 여러 단계의 저항값을 더 촘촘히 만들고, 메모리 안에서 곱하고 더하는 AI 계산도 더 정확하게 수행했다.

> 얇은 펜으로 글씨를 쓰고 큰 지우개로 지우는 것과 비슷하다. 한 도구로 둘 다 하려면 어중간하지만, 쓰기용 도구와 지우기용 도구를 나누면 더 정확하고 안정적이다.

## 논문 정보

Yang Chen, Daniele Storelli, Xinyi Zhao, Ankit Bende et al. · Forschungszentrum Jülich (PGI-7, PGI-4, PGI-14) · RWTH Aachen University · IOP Publishing Journal preprint (arXiv:2609.08898) · 2026

## 왜 중요한가

AI 계산에서는 데이터를 메모리에서 계산기로 계속 옮기는 일이 큰 비용이다. OTTER는 메모리 안에서 바로 계산하려는 칩이고, 그 핵심 부품인 RRAM을 더 안정적으로 쓰고 지우는 방법을 제시한다. 그래서 신경망 가속기나 빠른 검색용 메모리 같은 차세대 하드웨어를 크게 만들 때 필요한 설계 기준을 제공한다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| program-verify 목표 레벨 수 | **6단계** | 30, 40, 50, 60, 70, 80 µA 목표 read-current 레벨에서 LD SET이 HD SET보다 인접 레벨 중첩을 줄임 (Fig. 11) |
| MAC RMSE (LD-LD, 최우수 구성) | **2.27µA** | 15×15 CIM1 의사-크로스바, 5,000회 MAC 연산의 선형 피팅 오차 (Table 3, Fig. 14) |
| aCAM 동적 범위 (top-connected) | **1.240V** | 회로 시뮬레이션에서 top-connected RRAM comparator의 obtainable dynamic range. bottom-connected는 0.965 V (Fig. 13) |
| aCAM 전원 전압 민감도 (top-connected) | **2.2%** | VDD,nom=0.60 V에서 ±10% 변동 시 VDL,bound 평균 정규화 오차. bottom-connected는 13.9% (Fig. 13) |

## 어떻게 동작하나

TSMC 28 nm CMOS BEOL 위에 200 nm × 200 nm Pt/7 nm TaOx/13 nm Ta/Pt RRAM을 약 30단계, 300 °C 이하 공정으로 집적해 6×6 mm² OTTER 칩을 제작했다. 단일 2T1R 셀은 HD NMOS(W/L=10)와 LD NMOS(W/L=2)를 병렬로 두고 각 WL을 독립 구동한다. DC sweep에서는 HD-HD, LD-LD, LD-HD 세 구성을 100사이클 비교했고, LD-HD는 LD로 SET을 수행하면서 HD로 RESET해 모든 SET WL 조건에서 on/off 비 5 이상을 유지했다. 펄스 프로그래밍은 IGVVA 방식으로 HD SET(1.1~1.8 V, 25 mV 간격, 29 pulses)과 LD SET(1.7~3.3 V, 25 mV 간격, 65 pulses)을 비교했으며, 30~80 µA의 6개 target read-current level을 program-verify 방식으로 평가했다. JART VCM Rth compact model과 PDK transistor model을 사용해 RESET transistor W/L, VSL,max={2.0, 2.5, 3.3} V, programmed LRS 사이의 설계 가이드라인을 도출했다. 칩에는 8×8 aCAM 두 배열(CAM1 top-connected, CAM2 bottom-connected), NOR/NAND match-line, 여러 aCAM cell variant, 15×15 CIM1 pseudo-crossbar와 CIM2 conventional array가 포함되며, MAC은 CIM1에서 FPGA 기반으로 실측했다.

핵심 수식:

```
R_{th,eff}=\frac{\beta}{\alpha+\gamma N_{disc}^{2}} \quad;\quad \frac{dN_{disc}}{dt}=-\frac{I_{ion}}{z_{VO}eAl_{disc}} \quad;\quad T=(V_{disc}+V_{plug}+V_{Schottky})IR_{th,eff}+T_0 \quad;\quad g_m=\frac{I^{(n+1)}_{cc,SET}-I^{(n)}_{cc,SET}}{\Delta V^{SET}_{WL}} \quad;\quad MAC=\sum_{i=1}^{N}w_ix_i
```

Rth,eff는 disc 영역 산소 공공 농도 Ndisc에 의존하는 유효 열저항이며 α, β, γ는 polarity-dependent fitting coefficient다. Ndisc 변화율은 ionic current Iion, vacancy charge zVO, elementary charge e, filament 단면적 A=πRfil², disc length ldisc로 정해진다. 온도 T는 disc·plug·Schottky 전압강하와 전류 I에 의한 Joule heating 및 ambient temperature T0로 계산된다. gm은 25 mV WL 증가당 SET compliance current 변화량이고, MAC은 binary weight와 input의 dot product다.

## 한계와 주의할 점

- OTTER는 단일 연구용 다이와 15×15 CIM1 array 중심의 시연이므로, 수백~수천 행 규모에서의 배선 RC, sneak path, IR drop, 셀 간 변동성 누적은 별도 검증이 필요하다.
- aCAM의 1.240 V 동적 범위와 2.2% 전원 민감도는 회로 시뮬레이션 결과이며, 논문은 실험 칩 측정이 진행 중이라고 명시한다.
- LD 트랜지스터의 낮은 drive current 때문에 CIM MAC 실험의 LRS target은 양쪽 트랜지스터가 안정적으로 만들 수 있는 3 kΩ로 제한되었다.
- 2T1R 구조는 1T1R보다 트랜지스터와 WL 경로가 늘어나므로 셀 면적, 라우팅, 고밀도 어레이 집적도에서 불리할 수 있다.
- RESET transistor sizing 시뮬레이션의 절대 수치는 저자들도 주의해서 해석해야 한다고 밝히며, RESET 중 transistor IDS-VDS trajectory의 직접 실험 검증은 향후 과제다.
- LD-LD 구성에서 SET WL=2.2 V(Icc≈175 µA)일 때 약 50% 사이클이 HRS로 복귀하지 못하고, SET WL=2.4 V(Icc≈200 µA)에서는 대부분 RESET 실패가 발생한다.
- 깊은 LRS 상태에서는 VSL,max를 높여도 RESET transistor가 saturation/pinch-off 쪽으로 이동해 추가 전압의 이득이 제한된다.
- HD SET program-verify에서는 30, 40, 50 µA 낮은 target level에서 이웃 분포가 겹쳐 판독 모호성이 생기지만, LD SET에서는 인접 레벨 사이 measurable overlap이 없었다.
- Bottom-connected aCAM은 readout과 RESET 방향에서 body effect 영향을 받아 top-connected보다 dynamic range가 0.965 V로 작고 supply-induced error가 13.9%로 크다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 멀티레벨 메모리 셀의 coarse-fine 2-path 프로그래밍 전략

OTTER에서 LD SET은 1.7~3.3 V 범위의 65개 pulse step으로 촘촘한 read-current 상태를 만들고, gm이 약 200 µA/V 수준으로 비교적 일정하다. HD SET은 1.1~1.8 V 범위의 29개 pulse step이며 gm이 더 크고 Icc가 커질수록 증가해 overshoot와 target level overlap이 늘어난다. 이를 이용하면 목표 저항까지 멀리 떨어진 구간은 HD 경로로 빠르게 접근하고, 목표 근처에서는 LD 경로로 바꾸어 fine tune하는 coarse-fine strategy를 구성할 수 있다. 논문도 Section 6.3에서 이 상보성을 combined coarse-fine programming strategy로 제안한다.

**적용 지점** — 멀티레벨 RRAM weight programming 및 program-verify 알고리즘

**기대 효과** — LD SET은 30~80 µA의 6개 target level에서 HD SET보다 좁은 분포와 낮은 CV를 보이고, 인접 target level의 measurable overlap을 제거했다.

### 메모리 안 analog 검색의 supply-robust comparator orientation

OTTER의 aCAM 회로 시뮬레이션에서 top-connected 구성은 bottom-connected 대비 dynamic range가 1.240 V vs 0.965 V로 크고, VDD ±10% 변동에 따른 normalized error가 2.2% vs 13.9%로 작았다. 이는 aCAM comparator에서 RRAM electrode orientation과 access transistor body effect가 decision boundary 안정성을 크게 바꾼다는 뜻이다. 실측은 진행 중이므로 확정적인 제품 성능은 아니지만, analog search 회로 설계 단계에서 orientation을 supply tolerance와 함께 선택해야 한다는 지침을 준다.

**적용 지점** — in-memory aCAM, similarity search, analog comparator topology

**기대 효과** — 시뮬레이션 기준 dynamic range 1.240 V, VDD ±10% 변동 시 normalized error 2.2%로 bottom-connected 13.9% 대비 약 6배 낮음

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 단일 셀 및 소형 어레이 검증 | OTTER 칩에서 DC sweep, IGVVA pulse programming, 100-cycle switching statistics, 15×15 CIM1 MAC 실측, aCAM circuit simulation 수행 | 2T1R의 SET/RESET 역할 분리 효과, JART VCM Rth model calibration, RESET W/L sizing guideline, LD 기반 MAC 정확도 확인 |
| Phase 2 | aCAM 실측 및 어레이 확장 | CAM1/CAM2 top-/bottom-connected orientation, NOR/NAND ML, 6T2M/10T2M/개선형 cell variant를 실제 칩에서 측정하고 15×15보다 큰 array로 확장 | 시뮬레이션 기반 aCAM margin이 실리콘에서 유지되는지 확인하고, supply variation·body effect·programming trade-off를 정량화 |
| Phase 3 | 시스템 통합 및 응용 데모 | FPGA/소프트웨어 제어, calibration, coarse-fine programming algorithm, ADC/readout 보정, 실제 neural-network/search workload mapping 구현 | energy-per-MAC, latency, accuracy, retention/endurance까지 포함한 시스템 레벨 벤치마크 확보 |

---

원문 PDF: `2026-09-10-otter-two-transistor-one-rram-architecture-for-reliable-in-memory-comput.pdf`
