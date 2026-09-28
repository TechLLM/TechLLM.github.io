---
title: "반도체 소자 안의 3차원 계산 격자를 그대로 읽는 신경망을 만들어, 오래 걸리는 정밀 시뮬레이션을 훨씬 빠른 예측으로 대신하게 한 연구다."
date: 2026-09-29T07:34:34+09:00
draft: false
description: "TCAD 시뮬레이션을 사면체 메쉬 위에서 직접 동작하는 물리정보 GAT 대리 모델로 대체해 3D GaN FinFET 설계 공간 탐색 비용을 크게 줄이는 방법을 제안한다. 모델은 전위 ψ와 전자·정공 준페르미 레벨 Φn, Φp를 노드별로 예측하고, 데이터 손실에 유한체적 전류 연속 잔차를 결합한다. 5개 GATv2 모델의 딥 앙상블이 노드별 불확실성을 만들고, 능동학습 루프가 큰 후보 풀 중 가장 유익한 설계만 Sentaurus 풀 시뮬레이션으로 넘긴다."
tags: ["Semiconductor TCAD / Physics-Informed ML", "논문 분석", "논문 리뷰", "TCAD", "FinFET", "Drift-Diffusion"]
categories: ["논문분석"]
---


반도체 소자 안의 3차원 계산 격자를 그대로 읽는 신경망을 만들어, 오래 걸리는 정밀 시뮬레이션을 훨씬 빠른 예측으로 대신하게 한 연구다.

**무엇이 문제였나** — 정밀 반도체 시뮬레이션은 한 설계안을 계산하는 데 몇 분에서 몇 시간이 걸려, 많은 후보를 비교하기 어렵다.
**어떻게 풀었나** — 이 연구는 소자 내부의 3차원 점과 연결을 그래프로 보고, 각 지점의 전기 상태를 신경망이 예측하게 했다.
**그래서 뭐가 좋아졌나** — 모델이 자신 없는 후보만 골라 실제 시뮬레이터에 다시 보내므로, 수천~1만 개 규모 후보를 훨씬 현실적인 비용으로 걸러낼 수 있다.

> 많은 여행 경로를 모두 현장 답사하지 않고, 지도 앱이 먼저 빠르게 후보를 추린 뒤 애매한 구간만 더 자세히 확인하는 것과 비슷하다. 여기서 메쉬는 지도, 신경망은 빠른 경로 추정기, 실제 TCAD는 비용이 큰 정밀 확인 단계다.

## 논문 정보

Leonid Popryho, Ayoub Sadeghi, Inna Partin-Vaisband · University of Illinois Chicago · ICCAD '26 · 2026

## 왜 중요한가

새 반도체 구조는 성능이 좋아도 설계 후보를 충분히 시험할 수 없으면 제품으로 이어지기 어렵다. 이 연구는 모든 후보를 비싼 정밀 시뮬레이션으로 끝까지 계산하는 대신, 대부분은 빠른 신경망으로 평가하고 중요한 후보만 정밀 계산하는 흐름을 제시한다. 3D 전력 소자, 차세대 트랜지스터, TCAD 라이선스가 제한된 설계 환경에서 특히 의미가 있다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Per-field RMSE (학습 범위 Nfins≤5) | **0.16–1.3V** | Sentaurus 대비 세 드리프트-디퓨전 장(ψ, Φn, Φp)의 노드별 RMSE 범위 |
| 추론 속도 향상 vs Sentaurus | **1.6×10^4 – 4.1×10^4×** | 동일 메쉬에서 Sentaurus Device 풀 솔버 대비 PI-GNN 단일 forward pass |
| 추론 시간/메쉬 (RTX 4090, Nfins 2~38) | **65 – 1700ms** | 캐시된 메쉬에서 그래프 구성과 한 앙상블 멤버 추론을 포함한 단일 디자인 처리 시간 |
| Vth 절대 오차 (held-out 1~8 fins) | **0.14–0.29V** | PI-GNN의 문턱전압 절대 오차 범위. 데이터-only ablation은 valid Vth를 산출하지 못함 |

## 어떻게 동작하나

입력은 Sentaurus SDE가 만든 사면체 메쉬를 그래프로 변환한 것이다. 각 노드는 좌표, 5개 재료 one-hot, 도핑, Al 조성, 소스·드레인·게이트 접촉 플래그, 바이어스, 유전율, volume tag를 포함한 17차원 특징을 갖고, 각 엣지는 거리, 3차원 변위, cross-material indicator를 포함한 5차원 특징을 갖는다. GATv2 기반 모델은 8층, hidden 128, 4-head, 약 1,111,683개 파라미터로 구성되며, 노드마다 ψ, Φn, Φp를 예측한다. 손실은 접촉 노드를 제외한 z-score 데이터 MSE와 유한체적 전류 연속 잔차 L_cont를 결합하고, λ_phys를 epoch 20 이후 150 epoch 동안 0.1까지 ramp-up한다. 학습 데이터는 200개 Sentaurus Device run에서 얻은 1,786개 bias snapshot이며, 147개 bootstrap 설계와 53개 acquisition-selected 설계로 구성된다. 후보 풀 단계에서는 full SDevice solve 대신 SDE mesh generation만 수행해 9개 bias snapshot 그래프를 만들고, 5개 독립 GAT 앙상블의 노드별 분산을 interior node 평균 및 snapshot max로 요약한 U(x)를 UCB-style acquisition score에 넣어 상위 후보만 full TCAD로 보낸다.

핵심 수식:

```
L(θ) = w_data · L_data(θ) + λ_phys(t) · w_cont · L_cont(θ)
L_cont = (1/|V_int|) Σ_v [ log(1 + (∇·J̃_n)²_v) + log(1 + (∇·J̃_p)²_v) ]
λ_phys(t) = 0 (t<t_start),  λ_max·(t−t_start)/t_ramp (t_start≤t<t_start+t_ramp),  λ_max otherwise
```

L_data는 source, drain, gate 접촉 노드를 제외한 interior node에서 계산하는 per-field z-score MSE다. w_data=1, w_cont=0.1이며, L_cont는 예측된 ψ, Φn, Φp로부터 Boltzmann carrier density와 edge flux를 재구성한 뒤 bidirectional edge scatter-add로 계산한 유한체적 전류 연속 잔차다. log(1+x²) robust penalty를 쓰고 접촉 노드는 전류가 들어오고 나가는 경계이므로 마스킹한다. λ_phys는 t_start=20, t_ramp=150 epochs, λ_max=0.1로 ramp-up된다.

## 한계와 주의할 점

- 능동학습은 선택된 설계의 SDevice 풀 솔버 자체를 빠르게 만들지는 않는다. 장점은 full solve를 호출할 후보 수를 줄이는 데 있으며, 선택된 후보는 여전히 20–60분 또는 더 긴 Sentaurus 계산을 거친다.
- 노드 feature의 5-재료 one-hot이 GaN/AlGaN/HfO2/TiN/Au 스택에 종속되어 있어, 다른 소자 패밀리로 확장하려면 원문이 제안한 learned material embedding 같은 일반화가 필요하다.
- 물리 손실은 Sentaurus의 Scharfetter-Gummel box scheme을 재구현한 것이 아니라 edge length, unit face area, edge-averaged Boltzmann density, constant mobility, no generation-recombination을 쓰는 soft regularizer다.
- 검증은 주로 Nfins 1~40 크기 외삽에 집중되어 있으며, 완전히 다른 게이트 스택, 재료 조합, 바이어스 sweep에서의 일반화는 future work로 남아 있다.
- 단일 워크스테이션(2×RTX 4090, 124GB RAM) 기준으로 평가되어, 더 큰 메쉬에서는 GPU 메모리와 dynamic batching 한도가 실제 병목이 될 수 있다.
- 학습 범위 밖 fin count나 희소한 설계 영역에서는 field RMSE가 커질 수 있다. 원문에서도 PI-GNN field RMSE는 Nfins=38에서 학습 범위 대비 약 2–12× 증가한다.
- 물리 손실이 soft regularizer이므로 생성-재결합, 정확한 face area, full Scharfetter-Gummel discretization이 중요한 조건에서는 잔차가 실제 solver 오차를 충분히 대변하지 못할 수 있다.
- L_cont가 접촉 노드를 마스킹하므로 접촉 경계 근처의 전류 흐름 오차는 내부 영역보다 약하게 제어될 수 있다.
- AL-selected 53개 설계 중 64%가 Nfins≥3에 집중되었다. 이는 모델이 불확실한 크기 영역을 잘 찾았다는 증거이지만, stratum별 예산 제어가 없으면 특정 fin count에 데이터가 쏠릴 수 있다.
- Vth는 GaN channel mask의 평균 전자 농도가 10^16 cm^-3을 넘는 지점을 5개 gate-sweep snapshot에서 선형 보간해 얻으므로, 예측 field가 비보존적이거나 transfer characteristic이 불안정하면 산출 자체가 실패할 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 노드별 앙상블 불확실성으로 풀 솔버 호출을 점수 기반으로 제한하는 능동학습 루프

본 논문은 GATv2 5-모델 앙상블의 노드별 분산을 interior node 평균과 max-over-snapshots로 요약한 U(x)로 후보를 점수화한다. mesh-only 후보는 SDE로 만들고, UCB-style score s(x)=α[z(Id,max)+z(Vth)]+βz(U)와 δ-diversity filter를 거쳐 선택된 후보만 full SDevice solve로 보낸다. 본문 Sec. 3.4 및 Algorithm 1 참조.

**적용 지점** — 고비용 시뮬레이터/풀 솔버 호출 단계

**기대 효과** — 학습 데이터 200개 중 147개는 bootstrap, 53개는 acquisition-selected 설계다. AL-selected 설계의 64%가 Nfins≥3에 집중되어, 불확실성이 큰 크기 영역을 우선 보강했다.

### 물리-정보 손실을 데이터 손실에 점진 가중치로 결합해 외삽 성능 안정화

손실 L = w_data·L_data + λ_phys(t)·w_cont·L_cont에서 λ_phys는 epoch 20 이후 150 epoch 동안 0.1까지 증가한다. 먼저 데이터 fitting으로 합리적인 field를 만든 뒤, 전류 연속 잔차를 regularizer처럼 적용하는 구조다. 본문 Sec. 3.3 참조.

**적용 지점** — 물리/도메인 제약을 손실에 직접 주입해야 하는 학습 파이프라인

**기대 효과** — data-only ablation은 Nfins=6에서 Id,max 오차 53%, Nfins=8 단일 디자인에서 약 300%까지 커졌고 valid Vth를 산출하지 못했다. PI-GNN은 같은 조건에서 Id,max 오차가 각각 38%, 4%였고 Vth 오차는 0.14–0.29 V 범위였다.

### 저비용 mesh-only 후보 풀과 고비용 full solve의 비대칭 활용

후보 풀에서는 SDE mesh generation만 수행하고 target field는 비워 둔 그래프를 만든다. GAT 앙상블은 이 그래프만으로 field와 uncertainty를 예측하므로, full SDevice solve는 acquisition-selected 후보에 집중된다. 본문 Sec. 3.4와 Fig. 4 참조.

**적용 지점** — 전처리 또는 mesh generation은 비교적 싸고, 본 solver가 매우 비싼 파이프라인

**기대 효과** — Sentaurus Device wall time은 Nfins=2에서 약 19분, Nfins=38에서 7.5시간 이상인 반면, PI-GNN 단일 forward pass는 65 ms에서 1.7 s로 증가한다. 원문은 약 1.6×10^4–4.1×10^4배 속도 향상을 보고한다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 대상 설계 문제 1개에 PI-GNN + 능동학습 적용 | (1) 기존 Sentaurus 풀 솔버 결과로 bootstrap 데이터 구성. (2) GATv2 5-모델 앙상블 학습. (3) sde-only 후보 풀에서 acquisition score 기반으로 상위 후보만 full SDevice solve에 송신. | full solver 호출 횟수를 줄이면서 Pareto 후보 탐색을 더 넓게 수행. |
| Phase 2 | 학습 범위 밖 크기와 바이어스 조건 검증 | (1) Nfins 또는 process corner를 별도 테스트셋으로 두고 RMSE와 device metric error 측정. (2) data-only ablation과 비교해 physics loss의 외삽 안정화 효과 확인. (3) GPU 메모리 한도 내 최대 메쉬 크기와 throughput 측정. | 모델을 어디까지 믿을 수 있는지 fin count와 설계 영역별로 정의. |
| Phase 3 | 다른 소자 패밀리·재료로 전이 가능한 일반화 | (1) 5-재료 one-hot을 learned material embedding으로 교체. (2) generation-recombination, face-area, 더 정교한 flux discretization을 손실에 포함하는지 검토. (3) 예측 field와 uncertainty를 gradient-based inverse design 루프와 연결. | GaN FinFET을 넘어 다른 트랜지스터 및 TCAD 문제에 적용할 수 있는 기반 확보. |

---

원문 PDF: `2026-09-04-mesh-native-physics-informed-graph-surrogates-for-tcad-in-the-loop-desig.pdf`
