---
title: "메모리 셀 하나에 정밀하게 쓰는 길과 확실히 지우는 길을 따로 넣어, 메모리 안에서 계산을 더 안정적으로 하게 만든 28나노미터 칩 연구"
date: 2026-09-16T07:34:21+09:00
draft: false
description: "OTTER는 28nm CMOS 위에 TaOx 기반 RRAM을 적층한 6mm × 6mm 연구 칩으로, 한 셀이 두 트랜지스터(LD·HD)와 한 RRAM 소자로 구성된 2T1R 구조를 채택했다. LD 트랜지스터는 미세한 SET 전류 제어를, HD 트랜지스터는 안정적인 RESET을 담당해, 단일 트랜지스터에서 충돌하던 정밀 프로그래밍과 견고한 소거 요구를 분리했다."
tags: ["Neuromorphic Hardware / In-Memory Computing", "논문 분석", "논문 리뷰", "RRAM", "VCM", "2T1R"]
categories: ["논문분석"]
---


메모리 셀 하나에 정밀하게 쓰는 길과 확실히 지우는 길을 따로 넣어, 메모리 안에서 계산을 더 안정적으로 하게 만든 28나노미터 칩 연구

**무엇이 문제였나** — 기존 방식은 작은 셀 안의 한 제어 장치가 쓰기와 지우기를 모두 맡아야 해서, 섬세한 조절과 강한 지우기가 서로 충돌했다.
**어떻게 풀었나** — 이 연구는 한 셀에 작은 제어 장치와 큰 제어 장치를 함께 넣고, 작은 쪽은 정밀한 쓰기, 큰 쪽은 안정적인 지우기에 쓰도록 나눴다.
**그래서 뭐가 좋아졌나** — 그 결과 더 촘촘한 저장 단계를 만들고, 작은 15×15 배열에서 메모리 안 곱셈-더하기 계산이 거의 직선적으로 동작함을 보였다.

> 얇은 펜과 큰 지우개를 한 칸에 같이 넣어둔 것과 비슷하다. 얇은 펜은 글씨를 조금씩 정확히 쓰는 데 좋고, 큰 지우개는 한 번에 깨끗하게 지우는 데 좋다. OTTER의 2T1R 셀은 이 두 역할을 서로 다른 트랜지스터에 맡긴 구조다.

## 논문 정보

Yang Chen, Daniele Storelli, Xinyi Zhao, Ankit Bende et al. · Forschungszentrum Jülich & RWTH Aachen University · IOP Publishing Journal (preprint, arXiv:2609.08898) · 2026

## 왜 중요한가

인공지능 계산은 데이터를 메모리에서 계산 장치로 계속 옮기는 데 많은 시간과 에너지를 쓴다. RRAM 같은 메모리가 값을 저장하면서 동시에 계산까지 하면 이 낭비를 줄일 수 있다. 다만 그러려면 메모리 셀이 여러 단계의 값을 안정적으로 저장하고 다시 지울 수 있어야 하는데, 이 논문은 그 문제를 셀 구조 차원에서 풀려는 시도다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 펄스 프로그래밍 단계 수 | **65 (LD) / 29 (HD)단계** | IGVVA에서 LD SET은 약 10~85 µA read current 범위에 65개 단계, HD SET은 같은 범위에 29개 단계를 형성 |
| MAC RMSE — LD-LD 구성 | **2.27µA** | 15×15 CIM1 array의 5,000회 MAC 측정에서 네 구성 중 최저 RMSE (HD-HD: 7.37 µA) |
| MAC R² — LD-LD 구성 | **0.9996** | 5,000회 MAC 연산의 선형성 지표 (HD-HD: 0.9982) |
| aCAM 공급 전압 normalized error | **2.2 (top) / 13.9 (bottom)%** | VDD nominal 0.60 V에서 ±10% 공급 전압 변화 시 top-connected와 bottom-connected 구성의 시뮬레이션 오차 |

## 어떻게 동작하나

OTTER는 TSMC 28nm CMOS 위에 BEOL 호환 공정으로 200 nm × 200 nm Pt/7 nm TaOx/13 nm Ta/Pt RRAM을 적층한 6mm × 6mm 연구 칩이다. 2T1R 셀은 HD(W/L=10)와 LD(W/L=2) I/O 트랜지스터를 병렬로 두고 하나의 RRAM 소자와 직렬 연결한다. 단일 셀에서는 HD-HD, LD-LD, LD-HD 세 SET/RESET 조합을 100회 DC triangular sweep으로 비교했고, pulse programming에서는 HD 또는 LD로 SET하고 HD로 RESET하는 IGVVA 프로토콜을 적용했다. JART VCM Rth compact model에 state-dependent effective thermal resistance를 넣어 측정된 SET/RESET 거동과 저항 분포를 재현하고, RESET transistor W/L과 LRS 저항의 설계 지침을 시뮬레이션했다. aCAM은 top-connected와 bottom-connected RRAM comparator를 회로 시뮬레이션으로 비교했으며, CIM은 15×15 CIM1 pseudo-crossbar에서 HD-HD, HD-LD, LD-HD, LD-LD 네 SET/MAC read 조합의 MAC 정확도(MAE, RMSE, R², slope)를 칩에서 측정했다.

핵심 수식:

```
R_{th,eff} = \frac{\beta}{\alpha + \gamma \cdot N_{disc}^{2}}
```

α, β, γ는 SET/RESET 극성에 따라 달라지는 fitting 계수이고, N_disc는 disc 영역의 산소 공공 농도다. SET 중 N_disc가 증가하면 R_th,eff가 감소해 thermal runaway를 완화하고 안정적인 다중 레벨 프로그래밍을 돕는다. RESET 중에는 반대 경향으로 R_th,eff가 증가해 점진적인 전류 감소를 설명한다.

## 한계와 주의할 점

- 15×15 어레이 규모의 검증이므로 실제 제품급 대형 어레이에서의 IR drop, sneak current, 주변 회로 보정은 추가 검증이 필요하다.
- aCAM 결과는 회로 시뮬레이션 기반이며, 논문은 실험적 칩 측정이 진행 중이라고 명시한다.
- 2T1R는 셀당 트랜지스터가 하나 더 필요하므로 1T1R 대비 면적·배선 오버헤드가 생길 수 있다.
- TSMC 28nm + TaOx VCM 조합에서의 결과이므로 HfOx, TiOx 등 다른 RRAM 재료와 공정으로의 일반화는 별도 검증이 필요하다.
- 논문은 장기 endurance·retention 실험을 핵심 결과로 제시하지 않으므로 양산 신뢰성 판단에는 추가 데이터가 필요하다.
- LD-LD 구성은 SET WL=2.2 V에서 약 50% 사이클이 HRS로 돌아가지 못하고, 2.4 V에서는 대부분 RESET에 실패한다.
- bottom-connected aCAM은 VDD ±10% 변동에서 normalized error 13.9%로 top-connected의 2.2%보다 공급 전압 변화에 더 민감하다.
- HD SET 프로토콜은 30, 40, 50 µA target level에서 인접 분포가 겹쳐 readout ambiguity가 생길 수 있다.
- 깊은 LRS 상태에서는 RESET transistor의 saturation/pinch-off 및 body effect 때문에 추가 RESET 전압이 RRAM에 충분히 전달되지 않을 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 기억 회수에 점진적-검증 루프 도입

RAG 재순위 단계에서 먼저 많은 후보를 빠르게 추린 뒤, 작은 폭의 가중치 조정과 검증을 반복해 최종 후보를 고르는 coarse-to-fine 루프를 구성한다. 논문에서는 LD SET이 65개 pulse step을 통해 더 작은 current increment를 만들고, 30~80 µA 여섯 target level에서 HD SET보다 분포 겹침을 줄였다. 이 패턴은 한 번에 크게 이동해 목표를 지나치는 문제를 줄이는 설계 원리로 해석할 수 있다.

**적용 지점** — RAG 재순위 단계, 후보 압축 파이프라인

**기대 효과** — 인접 후보 또는 상태 사이의 겹침 감소 — 논문에서는 LD SET이 HD SET 대비 target level 분포의 overshoot와 overlap을 줄임

### 정밀/견고 이중 경로 회수 구조

장기 기억 인덱스에서 빠른 후보 수집 경로와 정밀 재정렬 경로를 분리한다. 이는 논문의 2T1R 구조가 SET 정밀도와 RESET 견고성을 하나의 트랜지스터에 동시에 맡기지 않고 LD와 HD에 나눈 것과 같은 설계 패턴이다. MAC 실험에서는 SET과 readout 모두 LD를 쓴 LD-LD 구성이 HD-HD 대비 RMSE 7.37 µA에서 2.27 µA로 낮아졌고 R²도 0.9982에서 0.9996으로 높아졌다.

**적용 지점** — 에이전트 장기기억 인덱스, RAG 검색-재순위 결합 단계

**기대 효과** — 단일 경로 대비 정밀 단계의 오차 감소 가능성 — 하드웨어 실험에서는 LD-LD MAC이 HD-HD보다 RMSE 기준 약 3.2배 낮음

### 사용 환경에 따른 aCAM 연결 방향 선택 패턴

매칭/검색 시스템에서 비교 경로의 연결 방향을 설계 옵션으로 둔다. 논문 시뮬레이션에서는 top-connected 구성이 1.240 V dynamic range와 ±10% 공급 변동에 2.2% normalized error를 보였고, bottom-connected 구성은 0.965 V dynamic range와 13.9% error를 보였다. 다만 논문은 programmability trade-off와 실험적 칩 측정이 아직 진행 중이라고 하므로, 실제 적용에서는 read 안정성과 프로그래밍 선형성을 함께 검증해야 한다.

**적용 지점** — 임베딩 매칭/유사도 검색 경로, ADC 대체 aCAM 블록

**기대 효과** — top-connected 선택 시 ±10% 공급 변동에 대해 bottom-connected보다 낮은 normalized error (13.9% → 2.2%)

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 단일 셀과 소규모 어레이에서 2T1R 개념 검증 | DC sweep, IGVVA pulse programming, JART VCM Rth model calibration, 15×15 crossbar MAC 측정 | LD transistor의 fine SET과 HD transistor의 robust RESET 역할 분담을 실험과 시뮬레이션으로 확인하고 RESET transistor sizing guideline을 도출 |
| Phase 2 | aCAM과 CIM 회로 수준 검증 강화 | 진행 중인 aCAM 칩 측정 완료, top/bottom-connected comparator의 프로그래밍·read margin 비교, MAC readout gain calibration 검토 | 시뮬레이션에서 보인 top-connected aCAM의 공급 전압 내성과 LD-LD MAC의 낮은 RMSE가 실제 시스템 조건에서도 유지되는지 확인 |
| Phase 3 | 대형 어레이와 장기 신뢰성 평가 | 더 큰 어레이에서 IR drop과 sneak current 영향 분석, endurance·retention 장기 시험, coarse-fine programming 전략 평가 | RRAM-CMOS 기반 뉴로모픽 및 인메모리 컴퓨팅 시스템으로 확장할 때 필요한 신뢰성·보정 조건을 정립 |

---

원문 PDF: `2026-09-10-otter-two-transistor-one-rram-architecture-for-reliable-in-memory-comput.pdf`
