---
title: "AI 에이전트가 잠시 툴을 쓰러 가도, 다음에 다시 쓸 대화 기록을 더 잘 남겨두는 메모리 관리 장치를 제안한 연구."
date: 2026-10-07T07:32:31+09:00
draft: false
description: "LLM 에이전트 루프는 툴 대기 동안 세션 KV 캐시를 유지해야 하므로, 기존의 recency·timeout 정책은 살아 있는 대기를 cold로 잘못 취급한다. UNISON은 메모리 계층 옆에 배치된 이벤트 기반 근메모리 스케줄러로, SPEAR(eviction)와 TIDE(tier placement)가 단일 랭킹 상태를 공유하며 gap EMA와 turn-indexed hazard로 다음 참조 거리를 근사한다."
tags: ["Computer Architecture / LLM Inference", "논문 분석", "논문 리뷰", "KV cache", "session", "SRAM / HBM"]
categories: ["논문분석"]
---


AI 에이전트가 잠시 툴을 쓰러 가도, 다음에 다시 쓸 대화 기록을 더 잘 남겨두는 메모리 관리 장치를 제안한 연구.

**무엇이 문제였나** — 문제: 에이전트는 툴 결과를 기다리다가 같은 작업으로 돌아오는데, 기존 캐시 정책은 그 기다림을 '오래 안 쓴 데이터'로 보고 버리기 쉽다.
**어떻게 풀었나** — 해결: 각 작업이 보통 얼마나 있다가 돌아오는지와 지금 몇 번째 단계인지 보고, 버릴 작업과 빠른 메모리에 둘 작업을 같은 점수로 고른다.
**그래서 뭐가 좋아졌나** — 결과: 6개 실제 에이전트 트레이스에서 적중률은 0.3~23.1%p 높아지고, 평균 메모리 접근 시간은 22~51% 줄었으며, 긴 작업에서는 첫 토큰 지연도 58~89% 줄었다.

> 공용 사물함을 관리하는 담당자에 비유할 수 있다. 누가 곧 돌아와 물건을 다시 찾을지, 누가 거의 일을 끝냈는지를 보고 가장 가까운 사물함과 먼 창고를 배정한다. UNISON은 AI 에이전트의 대화 기록에 대해 이 판단을 매우 빠르게 하는 담당자다.

## 논문 정보

Fan He, Yan Li, Xiaoyang Zeng · Fudan University, State Key Laboratory of Integrated Chips and Systems · arXiv preprint (arXiv:2609.09643v1) · 2026

## 왜 중요한가

에이전트 서비스에서는 모델 계산만 빠르게 하는 것만으로 부족하다. 여러 작업이 툴을 기다리며 같은 메모리 풀을 공유하므로, 다음에 곧 돌아올 작업의 기록을 어디에 둘지가 응답 시간을 크게 바꾼다. 이 논문은 그 결정을 소프트웨어 추측이 아니라 메모리 가까이의 작은 하드웨어가 정확한 이벤트를 보고 처리하게 만든다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Hit rate gain (per-trace range) | **+0.3 to +23.1pp** | 6개 트레이스 모두에서 LRU 대비 |
| AMAT reduction (per-trace range) | **-22 to -51%** | 6개 트레이스 모두에서 LRU 대비 |
| TTFT reduction (long-horizon traces) | **-58 to -89%** | extra prefill이 critical path인 긴 horizon 트레이스 |
| Bélády ratio (BR) | **0.93** | Bélády oracle 대비 online 정책의 hit rate 비율 |

## 어떻게 동작하나

에이전트 루프는 툴 호출마다 cs,k−1 → as,k 사이의 예약된 복귀 간격인 gap gs,k를 만들고, KV prefix는 턴이 진행될수록 커져 두 계층 풀을 채운다. UNISON은 gap EMA ĝs와 turn-indexed survival σ(t)=max(ε,1−h(min(t,50)))를 한 점수 score(s)=ĝs/σ(t)+(1−σ(t))P로 합성해 누구를 내보낼지(SPEAR) 정하고, 같은 점수의 반대 순위로 누구를 SRAM에 둘지(TIDE) 정한다. TIDE는 gap 시간 ∆을 DMA 예산 budget=∆·BW로 바꿔 빈 시간 동안 저비용 마이그레이션을 수행하고, 둘은 단일 session register file과 event FIFO로 묶여 cycle 단위 갱신을 보장한다. 마지막으로 28nm CMOS로 합성 가능한 5단 파이프라인으로 구현하고, 64 세션 설계점에서 (bh, bg, bs, τ, PZ)=(12, 32, 64, 10³, 5×10⁸) 포맷이 Kendall τ > 0.998 랭킹 충실도를 낸다.

핵심 수식:

```
score(s) = Smax, if s completed
score(s) = ĝ_s / σ(t) + (1 − σ(t)) · P, otherwise
ĝ_s ← (3·g_{s,k} + 7·ĝ_s) / 10
σ(t) = max(ε, 1 − h(min(t, 50))), ε = 0.01
budget = ∆ · BW
```

ĝ_s: 세션 s의 gap 지수이동평균, σ(t): turn t에서의 local survival mass, P: 완료에 가까운 세션의 eviction 우선순위를 높이는 programmable penalty, Smax: 완료 세션에 부여하는 최대 eviction 점수, ∆: 관측된 idle window, BW: 논리 DMA 대역폭, budget: gap 동안 옮길 수 있는 토큰 예산.

## 한계와 주의할 점

- 오프라인 oracle에는 7% 격차(BR=0.93)가 남아, 인과 신호만으로는 닫을 수 없는 손실이 존재한다.
- 툴 gap이 decode 윈도우보다 짧아지면 vLLM 같은 블록 캐시 timestamp로는 신호가 뒤집혀 HR이 6.6pp 떨어지며, cycle 단위 event 인터페이스 없이는 일반화가 어렵다.
- Hazard LUT가 작은 트레이스(예: GAIA/Gemma4 128 세션)에서는 노이즈가 커서 advantage를 가릴 수 있다.
- 추가 prefill이 GPU 큐를 saturate하는 SWE/Qwen3·SWE/Devstral 같은 GPU-bound regime에서는 hit rate 이득이 TTFT로 환산되지 않는다.
- 듀얼 IP로 분리하고 동기화 주기를 늘리면 HR 5.4pp 감소, AMAT 부호 비일관 등 documented failure mode가 재발한다.
- 단주기 툴 대기: gap < decode latency일 때 software timestamp가 idle 시작을 못 잡아 ranking이 뒤집힘
- 소규모 트레이스: hazard 표 분산이 커서 SPEAR 이득이 가려짐
- GPU-bound 부하: prefill이 큐 지배이므로 hit 이득이 first-token latency에 전파되지 않음
- 동기화 지연 듀얼 엔진: gap/요청 인터리빙이 빽빽할 때 stale register로 victim/placement 결정이 어긋남

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### SPEAR 점수로 멀티세션 RAG 컨텍스트 eviction 재설계

장기 기억을 들고 있는 RAG 에이전트라면, 각 retrieval 세션의 마지막 사용 이후 경과 시간을 보는 LRU는 '툴 응답을 기다리는 동안 다음 turn을 위해 다시 쓸 컨텍스트'도 cold로 잘라낸다. UNISON의 SPEAR 점수 score(s)=ĝs/σ(t)+(1−σ(t))P를 retrieval session 단위로 적용해, gap이 길고 자주 반복되는 세션은 살리고, σ(t) 즉 turn hazard가 낮은 곧 끝날 세션은 먼저 비운다. 이 점수를 retrieval 결과 재순위 단계 직전에 끼워 넣어 같은 ranking으로 검색 후보를 다시 정렬하고, eviction을 그 ranking의 arg max로 결정한다. 논문에서 6개 트레이스 모두에서 LRU 대비 hit rate이 0.3~23.1pp, AMAT이 22~51% 개선된 결과를 RAG 캐시에 옮겨 검증할 수 있다.

**적용 지점** — 에이전트 다중 RAG 세션 eviction 및 검색 재순위 단계

**기대 효과** — LRU 대비 hit rate +0.3~23.1pp, AMAT -22~51% (논문 6-trace 결과 인용)

### TIDE 스타일 idle-window tier migration을 일반 세션 스토어로 이식

장기 기억과 tool call이 섞인 에이전트라면, 툴 응답이 늦게 올수록 next-turn prefill이 커진다. UNISON의 TIDE 예산 budget=∆·BW를 일반화해, 현재 gap 추정치 ∆와 fast/slow 저장소 간 전송 대역폭 BW를 곱해 이번 idle 동안 옮길 수 있는 토큰 또는 객체 budget을 산정한다. 같은 SPEAR ranking의 arg min/arg max로 promote/demote 후보를 뽑고, dual-engine 동기화 없이 단일 ranking state에서 결정한다. retrieval 인덱스 업데이트, 임베딩 캐시, vector store hot shard rebalance 등 fast/slow 분리가 있는 저장 계층에 적용할 수 있다. 논문은 N=64에서 평균 scan latency 2.00µs로 TIDE 결정이 툴 대기보다 충분히 빠름을 보였다.

**적용 지점** — 에이전트 컨텍스트의 fast/slow 저장소 promote/demote 단계

**기대 효과** — idle 동안 migration 완료로 next-turn latency 절감, TIDE-with-LRU 단독은 prefetch accuracy 1.1%에 그치므로 SPEAR와 결합 필요

### 사이드밴드 event bus로 툴 gap onset/closure를 cycle 단위로 계측

에이전트 하네스라면, 툴 호출이 시작되는 순간과 끝나는 순간을 OS 타이머나 cache timestamp 대신 전용 사이드밴드 버스로 찍는다. UNISON의 event FIFO와 동일하게 cycle 단위로 stamped event를 흘려보내면, 단주기 툴 대기에서도 gap 신호가 뒤집히지 않는다. vLLM 실험에서 tool gap이 decode latency보다 짧아지면 software timestamp가 신호를 invert하여 HR -6.6pp로 무너진 케이스가 있었다. 결정 latency는 worst case 3.14µs이고 GAIA median tool gap 3.7~7.2s 대비 충분한 headroom이 있어 에이전트 runtime을 흔들지 않는다.

**적용 지점** — 에이전트 툴 호출/응답 이벤트 계측과 ranking 스케줄러 입력 인터페이스

**기대 효과** — 짧은 툴 대기에서 신호 역전 회피, vLLM cache-bound 케이스 TTFT -35%, p99 e2e -72% (논문 Tab. V 인용)

### Eviction과 placement가 공유하는 단일 ranking state로 통합

에이전트 하네스나 retrieval 서빙 파이프라인에서 eviction과 prefetch/migration을 별도 컴포넌트로 두고 주기적으로 sync하는 패턴은 흔하지만, agent workload처럼 request와 gap이 빽빽하게 인터리빙되면 stale view 때문에 victim이 어긋난다. UNISON의 단일 register file Ru에 SPEAR 점수를 매 이벤트마다 갱신하고, eviction은 arg max, migration은 arg min/arg max로 같은 ranking에서 즉시 읽도록 한다. 논문 Tab. I은 dual IP + 8-request sync에서 HR -5.4pp, AMAT 부호 비일관 등 failure mode를 측정했다. 같은 ranking을 공유하는 컴포넌트로 묶으면 이 손실을 피할 수 있다.

**적용 지점** — eviction + tier-placement 이중 엔진의 단일 ranking 통합

**기대 효과** — dual IP + 8-request sync 대비 HR 손실 최대 5.4pp 제거 (논문 Tab. I 인용)

### Turn-indexed hazard로 '곧 끝날 세션' 우선 eviction

장기 기억을 다루는 에이전트라면, 어떤 세션이 평균적으로 turn t에서 완료되는지 d(t)/n(t) 비율로 hazard h(t)를 누적하고, σ(t)=max(ε,1−h(min(t,50)))를 룩업한다. 그 세션의 score에 (1−σ(t))·P 항을 더해 '곧 끝날 세션'이 먼저 evict되도록 한다. 논문은 SWE/Qwen3에서 5-fold cross-validation을 수행해 held-out LUT와 all-session LUT의 차이가 최대 0.85pp, 평균 0.17pp임을 보였고, online으로도 관측 세션이 쌓이면 offline 수준에 도달함을 보였다. 따라서 종료 확률을 미리 알 수 없는 도메인이라도 운영 중 누적 데이터로 비슷한 신호를 만들 수 있다.

**적용 지점** — 세션 종료 예측 기반 eviction 우선순위 산정

**기대 효과** — SWE/Qwen3 5-fold CV에서 hazard LUT held-out vs all-session ∆ max 0.85pp, online 관측 후 A(n)=1 수렴

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 소프트웨어 단계에서 SPEAR 점수만 도입하여 eviction 결정 교체 | 기존 prefix cache(예: vLLM prefix cache, radix tree)의 LRU victim 선택을 score(s)=ĝs/σ(t)+(1−σ(t))P로 대체. gap EMA와 turn-indexed hazard를 request/gap 이벤트에서 채우고, 통합된 단일 ranking을 eviction 전용으로 사용. 논문 vLLM 검증처럼 cache-bound 조건에서 TTFT -35%, p99 e2e -72% 수준의 즉시 이득을 노린다. | 소프트웨어 패치만으로 cache-bound 운영 환경의 응답 지연 단축, 무하드웨어 변경 |
| Phase 2 | TIDE의 idle-window migration을 같은 ranking으로 결합 | 동일 score 함수를 재사용해 SRAM↔HBM swap 후보를 선정. 툴 호출 응답을 기다리는 동안 ∆·BW 토큰 budget을 산정하고, dual-IP 대신 단일 ranking state로 eviction과 migration을 묶어 동기화 지연으로 인한 5.4pp HR 손실을 회피. 두 메커니즘을 event log 단일 FIFO에서 업데이트한다. | HR gain을 0.3~23.1pp 전체 구간으로 끌어올리고 두 계층 풀 활용도 극대화 |
| Phase 3 | 근메모리 전용 컨트롤러 IP 통합 | 64 세션, 5단 파이프라인 SPEAR+TIDE 코어를 28nm CMOS 0.169mm² / 13.6mW / 150MHz로 합성. APB+CSR+Event FIFO 인터페이스로 메모리 컨트롤러 옆에 배치, 사이드밴드 이벤트 버스로 gap onset/closure를 cycle 단위로 수신. floating-point 참조에 대해 Kendall τ > 0.998 충실도 검증. | 소프트웨어가 놓치기 쉬운 짧은 툴 대기를 cycle 단위로 관찰해 failure mode를 줄이고, KV 계층이 커지는 추론 가속기에서 작은 제어기 비용으로 큰 메모리 효율을 얻음 |

---

원문 PDF: `2026-09-10-unison-a-co-designed-near-memory-scheduler-of-session-kv-residency-for-l.pdf`
