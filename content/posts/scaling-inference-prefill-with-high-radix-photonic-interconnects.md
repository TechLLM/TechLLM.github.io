---
title: "아주 긴 질문을 AI가 빨리 읽게 하려면, GPU끼리 데이터를 주고받는 길을 전기선보다 훨씬 넓은 빛의 길로 바꾸는 것이 효과적임을 보인 논문이다."
date: 2026-10-11T07:35:21+09:00
draft: false
description: "이 논문은 MoE 기반 LLM 추론의 prefill 단계에서 전기식 scale-up 연결이 통신 병목과 rack 경계를 만들며 TTFT를 제한한다는 문제를 정량화한다. XLA/MLIR 기반 비용 모델로 3D-integrated photonic interconnect를 시뮬레이션한 결과, 통신 지배 구간에서 prefill latency가 2.1–3.2×, communication-limited 구성에서 2.8–5.8× 개선되고, 1152-GPU scale-up pod가 1M-token context 처리에 핵심임을 보인다."
tags: ["AI Infrastructure / Photonic Interconnects", "논문 분석", "논문 리뷰", "Prefill", "TTFT", "Scale-up pod"]
categories: ["논문분석"]
---


아주 긴 질문을 AI가 빨리 읽게 하려면, GPU끼리 데이터를 주고받는 길을 전기선보다 훨씬 넓은 빛의 길로 바꾸는 것이 효과적임을 보인 논문이다.

**무엇이 문제였나** — AI가 긴 문서를 한꺼번에 읽을 때 GPU들이 서로 많은 데이터를 주고받아야 해서 느려진다.
**어떻게 풀었나** — 이 논문은 GPU 사이 연결을 광통신 기반의 더 넓고 멀리 가는 연결로 바꾸면 어떤 일이 생기는지 시뮬레이션했다.
**그래서 뭐가 좋아졌나** — 특히 긴 문맥과 많은 GPU를 쓰는 경우 첫 답변까지 걸리는 시간이 크게 줄어들 수 있음을 보였다.

> 여러 사람이 큰 책 한 권을 나눠 읽고 요약한다고 생각하면 된다. 각자가 읽은 내용을 계속 주고받아야 하는데, 좁은 복도 하나로만 오가면 사람이 많아질수록 막힌다. 광연결은 그 복도를 넓고 긴 고속도로로 바꾸는 것에 가깝다.

## 논문 정보

Arulselvan Madhavan, Peter Carson, Taylor Groves, Thomas Graham · Lightmatter · 33rd IEEE Symposium on High-Performance Interconnects (HotI 2026) · 2026

## 왜 중요한가

긴 보고서, 코드 저장소, 대화 기록을 AI에게 한 번에 넣는 서비스가 늘고 있다. 이때 AI 모델 자체만 빠르게 만들어도 GPU들이 서로 데이터를 나누는 길이 막히면 답이 늦게 나온다. 이 논문은 그 병목이 어디서 생기고 어떤 하드웨어 변화가 실제로 도움이 되는지 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Short-context latency gain | **2.1–3.2×** | 1K–8K token 고배치 prefill 구간에서 optical interconnect가 electrical baseline 대비 보인 개선 범위 |
| Communication-limited gain | **2.8–5.8×** | 통신 병목이 지배적인 구성에서 baseline 대비 prefill latency 개선 범위 |
| Optical scale-up pod | **1152GPUs** | 논문이 128K–1M token prefill을 위해 모델링한 최대 optical scale-up pod 크기 |
| p99 TTFT reduction | **12–20%** | B300 FP4 disaggregated serving DES에서 optical scale-up 적용 시 p99 TTFT 감소 범위 |

## 어떻게 동작하나

논문은 production-grade MoE 모델의 prefill을 MLIR로 표현하고, XLA compiler fork로 compute cost와 communication collective cost를 추출한다. 모델은 Mini, R1, Next 세 규모로 구성되며 각각 21B, 42B, 201B active parameters를 가진다. 하드웨어는 B200, B300, Rubin, R4 전기식 baseline과, 동일 compute/HBM 조건에서 scale-up bandwidth를 4×로 높이고 최대 1152 GPU pod를 허용하는 optical counterpart를 비교한다. 실험은 device sweep과 batch sweep으로 나뉘며, 1K, 8K, 128K, 1M token context에서 overlapped prefill latency ratio를 계산한다. 핵심 가설은 더 빠른 GPU와 긴 context가 collective communication을 critical path로 밀어내므로, bandwidth와 radix를 동시에 늘리는 optical scale-up이 TTFT를 줄인다는 것이다.

핵심 수식:

```
Speedup = L_electrical / L_optical
L_prefill = overlap(T_compute, T_communication)
B_optical = 4 \times B_electrical, \quad N_{pod,optical}=1152
```

L은 overlapped prefill latency, T_compute는 연산 시간, T_communication은 collective 통신 시간, B는 per-GPU scale-up bandwidth, N_pod는 high-bandwidth scale-up pod의 GPU 수를 뜻한다.

## 한계와 주의할 점

- 결과는 배포된 photonic hardware 실측이 아니라 XLA 기반 analytical cost model과 projected optical layer에 의존한다.
- Optical case는 이상적인 4× scale-up bandwidth를 가정하며 추가 link latency, thermal limit, signal-integrity effect를 모델링하지 않는다.
- TCO, 배치 비용, 유지보수 난이도, 광소자 수율 같은 실제 데이터센터 도입 비용은 분석 범위 밖이다.
- 논문은 prefill-centric이므로 decode capacity가 부족한 serving system에서는 end-to-end latency 개선이 TTFT 개선만큼 나타나지 않는다.
- R4는 speculative roadmap-class 구성으로, 해당 수치는 확정 제품 성능이 아니라 projection으로 읽어야 한다.
- Decode worker가 포화되면 optical prefill이 완료 요청을 더 빨리 밀어 넣어 TPOT가 77–110% 증가할 수 있다.
- Compute-bound cell에서는 optical interconnect가 병목을 건드리지 못해 speedup이 1.01–1.10× 수준에 머문다.
- 전기식 baseline이 native scale-up pod 안에 머무는 작은 device count에서는 optical radix의 장점이 제한된다.
- 긴 context에서 KV cache 배치와 prefill-to-decode 전달을 함께 설계하지 않으면 TTFT 개선이 최종 사용자 latency로 전환되지 않을 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### Prefill worker와 decode worker를 분리 계측하는 SLO 게이트

Disaggregated LLM serving system에서는 request scheduler 앞단에 TTFT, prefill queue wait, decode queue wait, TPOT를 분리 기록하는 gate를 둔다. 논문의 DES 결과처럼 optical prefill이 빨라지면 decode batch가 커져 TPOT가 증가할 수 있으므로, prefill 증설 결정은 decode utilization cap과 함께 승인해야 한다. 구현상으로는 batch admission controller가 prefill worker 가동률뿐 아니라 decode worker의 memory-bound saturation을 동시에 확인하게 바꾼다.

**적용 지점** — disaggregated LLM serving scheduler

**기대 효과** — 논문 DES에서 p99 TTFT는 12–20% 감소했지만 p99 TPOT는 77–110% 증가했으므로, 두 지표를 함께 제어해 end-to-end latency 상쇄를 줄일 수 있다.

### 128K 이상 요청을 optical scale-up prefill pod로 라우팅

RAG나 agentic workflow에서 입력 token 수가 128K를 넘는 요청은 일반 prefill pool이 아니라 high-bandwidth scale-up pod로 라우팅한다. 논문은 128K batch 64에서 72 GPU는 compute가 56.1초, communication이 20.3초지만 288 GPU 전기식 baseline은 compute가 14.3초로 줄고 communication이 35.5초로 증가한다고 보인다. 따라서 router는 context length와 예상 device footprint를 기준으로, scale-out boundary를 넘는 요청을 optical pod에 배정하도록 바꾼다.

**적용 지점** — LLM inference request router

**기대 효과** — B300 FP4 R1 128K device sweep에서 optical configuration은 2.93× 개선을 보였다.

### 고배치 오프라인 prefill 작업을 통신 민감 작업으로 분류

오프라인 문서 임베딩 전처리, prompt-cache warming, 대량 long prompt evaluation처럼 batch가 큰 작업은 GPU compute만 보는 큐가 아니라 activation collective traffic을 예측하는 큐로 보낸다. 논문은 8K token, batch 2048, 72 devices에서 electrical communication이 40.6초이고 compute가 16.8초라고 보고한다. 같은 지점에서 optical communication은 10.2초로 줄며 compute는 그대로이므로, batch planner가 통신량이 큰 작업을 optical-connected pool에 우선 배치하게 만들 수 있다.

**적용 지점** — offline prefill batch scheduler

**기대 효과** — 8K-token, batch-2048 B300 FP4 예시에서 communication component가 40.6초에서 10.2초로 감소했다.

### Mesh 선택기에 통신 축 우선 규칙을 넣는 compiler cost pass

Compiler-level partitioner가 Tensor, Expert, Sequence parallelism 후보 mesh를 평가할 때 단순 device 균등 분할이 아니라 all-to-all, all-gather, reduce-scatter가 몰리는 y axis 비용을 크게 반영하게 한다. 논문 Appendix B는 DeepSeek-R1 288 devices에서 2×144×1 mesh를 선호하며, y axis가 expert routing과 attention head partitioning에 가장 bandwidth-intensive하다고 설명한다. 따라서 distributed inference compiler의 mesh search objective에 interconnect topology와 axis별 collective cost를 직접 넣어 prefill latency를 낮춘다.

**적용 지점** — distributed inference compiler mesh search

**기대 효과** — 논문은 수백 개 후보 shape 중 overlapped prefill latency가 최소인 mesh를 선택했으며, 288 devices에서 2×144×1 구성이 사용됐다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | Prefill 병목 진단 | 서비스 trace에서 context length, batch size, TTFT, collective communication 비중, decode queue 상태를 분리 측정한다. | Optical scale-up이 효과를 낼 communication-limited 구간과 효과가 작은 compute-bound 구간을 구분한다. |
| Phase 2 | Prefill pod 실험 | 128K 이상 context와 고배치 prefill worker를 대상으로 4× bandwidth 가정의 시뮬레이션 또는 소규모 optical prototype을 검증한다. | TTFT 개선 가능성과 rack boundary 회피 효과를 서비스별 workload에서 확인한다. |
| Phase 3 | Prefill-decode 공동 설계 | Prefill worker 수, decode worker 수, KV transfer 경로, batch cap을 함께 조정하고 p99 TTFT, TPOT, end-to-end latency를 통합 최적화한다. | Prefill에서 확보한 headroom이 decode 포화로 사라지지 않도록 전체 serving capacity를 맞춘다. |

---

원문 PDF: `2026-09-03-scaling-inference-prefill-with-high-radix-photonic-interconnects.pdf`
