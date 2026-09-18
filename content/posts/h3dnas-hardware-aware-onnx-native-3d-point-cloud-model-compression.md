---
title: "이미 만들어진 ONNX 모델 파일만 가지고 3D 인식 모델을 더 작고 빠르게 줄여 주는 방법이다."
date: 2026-09-19T07:33:00+09:00
draft: false
description: "H3DNAS는 원본 PyTorch 코드나 모델 클래스 없이 ONNX 계산 그래프만으로 3D 점구름 모델을 압축하는 하드웨어 인지형 NAS 프레임워크다. Channel Dependency Graph(CDG)는 Conv/Gemm 노드의 채널 의존성을 4개 연산자 클래스와 5개 제약 규칙으로 분석해 자유 파라미터 분율 ρf를 O(|V|+|E|)에 계산한다."
tags: ["Model Compression / Neural Architecture Search", "논문 분석", "논문 리뷰", "ONNX", "NAS", "채널 가지치기"]
categories: ["논문분석"]
---


이미 만들어진 ONNX 모델 파일만 가지고 3D 인식 모델을 더 작고 빠르게 줄여 주는 방법이다.

**무엇이 문제였나** — 보통 모델을 줄이려면 원래 학습 코드와 모델 설계 파일이 필요하지만, H3DNAS는 ONNX 파일만으로 시작한다.
**어떻게 풀었나** — 먼저 어떤 부분을 줄여도 안전한지 그래프 구조를 보고 찾고, 그다음 여러 후보 중 정확도와 속도의 균형이 좋은 모델을 고른다.
**그래서 뭐가 좋아졌나** — PointNet 같은 3D 점구름 모델에서는 파라미터를 크게 줄여도 정확도는 거의 유지했고, CPU 추론 속도는 최대 1.99배 빨라졌다.

> 완성된 기계의 설계도를 보고 어떤 부품은 줄여도 되고 어떤 부품은 건드리면 안 되는지 표시한 뒤, 안전한 부품만 작게 바꾸는 방식에 가깝다. GhostConv는 비싼 부품 하나를 더 싼 두 단계 부품으로 바꿔 비슷한 역할을 하게 만드는 추가 선택지다.

## 논문 정보

Anchit Mulye, Rhythm Baghel, Sujay Kumar Ingle, Hardik Jain · Indian Institute of Technology Jodhpur · arXiv (cs.LG) · 2026

## 왜 중요한가

자율주행, 로봇, AR 기기처럼 작은 장치에서 3D 데이터를 처리하려면 모델이 작고 빨라야 한다. 하지만 실제 배포 현장에서는 원본 코드 없이 ONNX 파일만 받는 경우가 많다. H3DNAS는 이런 상황에서도 모델을 줄일 수 있고, 시작 전에 ‘이 구조는 채널을 잘라서 얼마나 줄일 수 있는지’를 대략 판단하게 해 준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| PointNet 파라미터 감소율 | **65.5%** | ModelNet40, Table 4의 H3DNAS 결과 |
| PointNet 추론 속도 향상 | **1.99×** | ORT CPU P50, 11.98ms → 6.02ms |
| PointNet++ SSG 파라미터 감소율 | **43.2%** | ModelNet40, Table 4의 H3DNAS 결과 |
| PointMLP 파라미터 감소율 | **49.1%** | ModelNet40, Table 4의 H3DNAS 결과 |

## 어떻게 동작하나

H3DNAS는 ONNX ModelProto를 직접 입력으로 삼아 shape inference, FLOP/파라미터 계산, 그래프 변형, 후보 평가를 수행한다. CDG 분석은 ONNX 연산자를 Channel-Generating(CG), Channel-Transparent(CT), Channel-Constraining(CC), Channel-Terminating(CX)으로 분류하고 R1~R5 제약 규칙으로 자유롭게 가지치기 가능한 Conv/Gemm 노드를 찾는다. 이렇게 얻은 ρf는 기본 그래프 G에서 채널 가지치기가 줄일 수 있는 자유 파라미터 비율을 나타내며 O(|V|+|E|)에 계산된다. Stage 1은 width multiplier와 prune ratio 후보를 만들고 L1 중요도 기반 채널 선택, downstream Cin 전파, BatchNorm 정렬을 적용한다. N=32개 랜덤 입력에서 베이스 logits와 후보 logits의 코사인 유사도인 output fidelity로 후보를 사전 선별하며, 기본 K=15개만 라벨이 있는 ORT 평가로 넘긴다. Stage 2는 Pareto 후보의 eligible free Conv(groups=1, Cout≥16)에 GhostConv 구조 변이를 적용하고, Stage 1/2 후보를 정확도와 FLOPs 기준 Pareto frontier로 합친다. HardwareConstraints는 파라미터, FLOPs, 모델 크기, latency 하드 제약을 검색 루프 안에서 적용한다. 미세조정은 onnx2torch로 ONNX에서 직접 재구성한 trainable model을 사용하므로 원래 모델 소스코드나 클래스 정의가 필요 없다.

핵심 수식:

```
\rho_f(G)\;=\;\frac{\sum_{n\in F}\,|\Theta_n|}{\sum_{n\in V_{conv}}\,|\Theta_n|}
```

G는 고정 폭의 기본 ONNX 그래프, F는 CDG에서 단일 컴포넌트로 남는 자유 Conv/Gemm 노드 집합, V_conv는 모든 Conv/Gemm 노드, |Θ_n|은 기본 채널 폭에서 노드 n의 파라미터 수다. ρf(G)는 가중치 값이 아니라 op type과 연결 구조로 결정되는 위상 불변량이며, 기본 그래프 G에서의 채널 가지치기 상한으로 해석된다. width scaling으로 G′가 되거나 downstream Cin 절감이 함께 계산되면 ρf(G)를 넘는 감소처럼 보일 수 있으므로 별도 해석이 필요하다.

## 한계와 주의할 점

- 대표 latency는 ORT CPU P50 기준이다. 보충 Table 14의 TensorRT FP16 GPU speedup은 PointNet 1.06×, PointNet++ SSG 1.03×, PointMLP 1.45×로 CPU speedup보다 작다.
- 본문은 CDG를 compression ceiling으로 설명하지만 보충 자료는 downstream Cin 절감 때문에 실현 감소가 ρf를 넘을 수 있다고 보완한다. 따라서 ρf는 기본 그래프의 채널 가지치기 가능성을 알려주는 안전 불변량으로 읽어야 한다.
- Level 2 구조 변이의 일반화는 제한적이다. 논문 Discussion은 depthwise decomposition 같은 구조 변이는 재초기화가 필요해 향후 과제로 남긴다고 설명한다.
- onnx2torch fine-tuning은 세 주요 모델에서는 성공했지만, 지원하지 않는 연산자나 PTv3 같은 특수 export 패턴에서는 수동 등록 또는 개입이 필요할 수 있다.
- attention 기반 PCT/PTv3는 QKV head split과 MatMul 제약 때문에 채널 단위 가지치기 효과가 작다. 논문은 head pruning이나 quantization이 더 자연스러운 방향이라고 설명한다.
- PointMLP는 residual Add 제약이 많아 Stage 2 GhostConv가 오히려 나쁘다. Table 7에서 Stage 1은 93.11%, 1.24×이고 Stage 2는 92.83%, 1.20×다.
- PointNet++ SSG는 Stage 2의 이득이 거의 없다. Table 7에서 Stage 1은 33.8% 감소와 2.67×, Stage 2는 34.1% 감소와 2.64×다.
- MobileNetV2처럼 depthwise convolution이 많은 구조는 R3 제약 때문에 자유 노드가 매우 적다. 보충 자료는 53개 Conv/Gemm 중 2개만 자유 노드라고 보고한다.
- PTv3는 Reshape Constant에 채널 차원이 박혀 있어 채널 수를 바꾸면 ORT shape mismatch가 발생할 수 있으며, 논문은 PTv3 compression을 deferred로 둔다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 지식 그래프 노드의 구조 역할 4분류로 ‘잠긴 노드’ 사전 식별

장기 기억 그래프에서 각 노드를 새로운 정보를 생성하는 노드, 그대로 전달하는 노드, 다른 노드와 강하게 묶인 노드, 차원이나 의미를 끝내는 노드로 나눈다. H3DNAS의 R1~R5처럼 ‘상수 shape에 박혀 있음’, ‘다른 분기와 Add로 결합됨’, ‘출력 의미가 고정됨’ 같은 패턴을 잠금 규칙으로 둔다. 자유 노드만 병합하거나 압축하고, 묶인 노드는 함께 보존한다. 적용 지점은 장기 기억 그래프 압축 파이프라인과 검색 색인 갱신 직전의 안전 판정 모듈이다.

**적용 지점** — 장기 기억 그래프의 노드 병합·압축 사전 판정 단계

**기대 효과** — H3DNAS가 29개 ONNX Model Zoo 모델에서 ORT-valid 그래프를 방출한 것처럼, 구조를 먼저 판정하면 잘못된 그래프 변형을 줄일 수 있다.

### 출력 충실도(Output Fidelity) 제로샷 사전선별을 후보 평가 게이트로

H3DNAS Stage 1은 N=32개 랜덤 입력에서 base logits와 pruned logits의 코사인 유사도를 계산하고, 기본 K=15개 후보만 라벨 평가로 넘긴다. LLM 시스템에서도 여러 계획이나 답안 후보를 만든 뒤 기준 답안 또는 이전 검증 결과와의 임베딩 유사도로 1차 정렬할 수 있다. 사람 평가나 외부 도구 검증처럼 비싼 절차는 상위 후보에만 적용한다.

**적용 지점** — 후보 생성 직후 정밀 평가 직전의 1차 필터 단계

**기대 효과** — 논문 설정에서는 output fidelity가 전체 후보를 top-15로 줄여 라벨 평가 비용을 낮추는 역할을 한다.

### 위상 안전 불변량으로 실행 가능성 천장을 사전 산출

H3DNAS의 ρf는 ONNX 그래프의 op type과 연결 구조만으로 계산된다. 같은 아이디어를 워크플로우 자동화에 적용하면, 의존 그래프를 분석해 자유롭게 줄일 수 있는 단계와 반드시 유지해야 하는 단계를 나눌 수 있다. 예를 들어 문서 처리 파이프라인에서 요약, 분류, 승인, 보관 단계 중 어떤 단계가 강하게 결합되어 있는지 먼저 파악하면 무리한 최적화 시도를 피할 수 있다.

**적용 지점** — 워크플로우 자동 계획 직전의 feasibility 산출 모듈

**기대 효과** — PCT, PTv3처럼 ρf가 낮은 모델에서 채널 가지치기 대신 head pruning이나 quantization을 고려하도록 유도하는 것과 같은 사전 방향 전환 효과를 기대할 수 있다.

### 두 단계 위계 최적화 — 저비용 광역 탐색 → 고비용 정밀 변이

H3DNAS는 Stage 1에서 width와 prune ratio 조합을 탐색하고 output fidelity로 후보를 줄인 뒤, Stage 2에서 Pareto 후보에만 GhostConv 변이를 적용한다. 이 구조를 문서 작성이나 계획 생성에 옮기면, 먼저 여러 초안을 빠르게 만들고 자동 점수로 추린 다음, 상위 후보에만 자기 검토나 외부 도구 재호출을 적용할 수 있다. 다만 PointMLP에서 Stage 2가 해로웠던 것처럼, 구조적 제약이 많은 작업에는 2단계를 끄는 조건도 함께 필요하다.

**적용 지점** — 초안 생성 후 정밀 수정·재작성 직전의 변이 후보 생성 단계

**기대 효과** — PointNet ablation에서 같은 32.3% parameter reduction 조건으로 Stage 2는 Stage 1의 1.46×보다 높은 1.80× speedup을 보였지만 정확도는 90.07%에서 89.99%로 낮아졌다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | ONNX 입력 기반 압축 파이프라인 제품화 | ONNX 입력, CDG 분석, Stage 1 pruning, HardwareConstraints 필터링, ORT 검증을 CLI/SDK로 묶는다. 기본 프리셋은 Jetson Orin Nano 8GB처럼 파라미터, FLOPs, 모델 크기, latency 예산을 함께 가진 장치로 둔다. | 원본 학습 코드가 없는 모델도 배포 예산을 만족하는 후보로 줄일 수 있다. |
| Phase 2 | 미세조정과 디바이스 프로파일링 자동화 | onnx2torch 재구성 가능 여부를 후보 생성 전에 검사하고, Adam 및 cosine annealing fine-tuning 루프를 자동화한다. ORT CPU뿐 아니라 TensorRT/ORT-CUDA 측정 경로를 함께 제공한다. | CPU 측정과 실제 GPU 배포 성능 사이의 차이를 줄이고, 압축 후 검증 과정을 더 신뢰할 수 있게 만든다. |
| Phase 3 | attention 모델과 양자화 확장 | PCT/PTv3처럼 채널 단위로 잠긴 구조에는 head pruning, Constant shape 업데이트, post-training quantization을 결합한다. 2D CNN에서 검증한 CDG 분석도 일반 모델 경량화로 확장한다. | 채널 가지치기가 잘 듣지 않는 모델군까지 H3DNAS의 사전 feasibility 판단과 우회 전략을 적용할 수 있다. |

---

원문 PDF: `2026-09-03-h3dnas-hardware-aware-onnx-native-3d-point-cloud-model-compression.pdf`
