---
title: "여러 AI 에이전트가 같은 메모리를 나눠 쓸 때, 곧 다시 돌아올 작업은 빠른 메모리에 남기고 한동안 안 쓸 작업은 밀어내는 작은 전용 스케줄러다."
date: 2026-09-14T02:01:24+09:00
draft: false
description: "LLM 에이전트가 도구 호출 사이에도 점점 커지는 KV 캐시를 유지하며 여러 세션이 SRAM/HBM 풀을 공유하는 상황에서, 기존 LRU/TTL/ETA 정책이 도구 대기 중인 살아 있는 세션을 cold로 오인해 evict하는 문제를 다룬다. UNISON은 메모리 계층 옆에 놓이는 이벤트 기반 near-memory 스케줄러로, SPEAR(갭 EMA + 턴별 hazard 기반 evictor)와 TIDE(idle 구간을 DMA 예산으로 쓰는 tier 배치기)가 하나의 라이브 랭킹을 공유한다."
tags: ["Computer Architecture / LLM Inference", "논문 분석", "논문 리뷰", "KV 캐시", "에이전트 루프", "evict"]
categories: ["논문분석"]
---


여러 AI 에이전트가 같은 메모리를 나눠 쓸 때, 곧 다시 돌아올 작업은 빠른 메모리에 남기고 한동안 안 쓸 작업은 밀어내는 작은 전용 스케줄러다.

**무엇이 문제였나** — AI 에이전트는 검색이나 코드 실행 같은 도구를 기다리는 동안에도 이전 대화 내용을 빠르게 다시 쓰기 위한 메모리를 붙잡고 있다.
**어떻게 풀었나** — 기존 방식은 오래 안 쓴 순서로 치우기 때문에, 잠깐 도구를 기다리는 작업까지 버려서 다시 계산하는 비용이 생긴다.
**그래서 뭐가 좋아졌나** — UNISON은 각 작업이 보통 얼마나 쉬었다가 돌아오는지와 지금 몇 번째 단계인지 보고 점수를 매겨, 누구를 남길지와 어디에 둘지를 동시에 정한다.

> 도서관에서 여러 사람이 책을 읽다가 잠깐 자리를 비운 상황과 비슷하다. 단순한 LRU는 가장 오래 자리를 비운 사람의 책부터 치우지만, UNISON은 이 사람이 보통 금방 돌아오는지, 책을 거의 다 읽었는지 같은 단서를 보고 책을 빠른 서가에 둘지, 보관대로 옮길지, 아예 치울지 결정한다.

## 논문 정보

Fan He, Yan Li, Xiaoyang Zeng · State Key Laboratory of Integrated Chips and Systems, Fudan University · arXiv preprint (arXiv:2609.09643) · 2026

## 왜 중요한가

에이전트형 AI가 길고 복잡한 일을 맡을수록 GPU 주변 메모리는 쉽게 부족해진다. 한 번 버린 KV 캐시를 다시 채우면 첫 응답이 늦어지므로, 이 논문은 메모리 옆의 작은 하드웨어가 캐시 보존과 위치 배치를 빠르게 결정해 응답 지연을 줄이는 방법을 제시한다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Hit rate gain over LRU | **0.3–23.1pp** | 6개 트레이스에서 UNISON이 LRU 대비 올린 캐시 적중률 폭 |
| AMAT reduction | **22–51%** | 6개 트레이스에서 평균 메모리 접근시간이 줄어든 폭. Table II 기준 전체 AMAT/LRU geomean은 0.65, 0.78, 0.55, 0.49, 0.72, 0.52다. |
| TTFT reduction (long-horizon) | **58–89%** | extra prefill이 critical path에 놓이는 장기 트레이스에서 보고된 첫 토큰 지연 감소 폭. 별도 vLLM 검증의 cache-bound 사례는 mean TTFT −35%, p99 e2e −72%다. |
| Bélády ratio (BR) | **0.93** | 미래를 아는 offline oracle 대비 UNISON의 hit rate 비율. 1.00이 oracle 기준이다. |

## 어떻게 동작하나

UNISON은 LLM 에이전트 세션의 KV 캐시가 도구 대기 중에도 메모리에 머무는 사실에 주목한다. 세션 s의 도착 간격 g_{s,k}=a_{s,k}-c_{s,k-1}를 EMA 계수 α=3/10으로 평활화해 평균 도구 대기 길이를 추정하고, 턴 t별 완료 hazard h(t)=d(t)/n(t)에서 σ(t)=max(ε, 1−h(min(t,50)))를 조회한다. SPEAR는 score(s)=g_s/σ(t)+(1−σ(t))P로 모든 resident 세션을 정렬하며, 완료된 세션은 Smax를 받아 즉시 높은 evict 우선순위를 갖는다. TIDE는 gap_start에서 관측 또는 추정된 idle 길이 Δ를 DMA 예산 B=Δ·B_DMA로 바꾸고, 낮은 score의 HBM 세션을 SRAM으로 승격하고 높은 score의 SRAM 세션을 HBM으로 강등한다. 두 결정은 같은 session register file과 같은 ranking을 읽으며, 28nm CMOS에서 N=64 세션 기준 0.169 mm² / 13.6 mW / 150 MHz로 구현된다.

핵심 수식:

```
score(s) = Smax if completed, otherwise g_s / σ(t) + (1 − σ(t)) · P;   h(t)=d(t)/n(t);   σ(t)=max(ε, 1−h(min(t,50)));   B_mig = Δ · B_DMA
```

g_s는 세션의 평활화된 도구 대기 길이, h(t)는 t번째 턴에서 완료되는 세션 비율, σ(t)는 누적 생존확률이 아니라 논문 식 (6)의 hazard local complement, P는 완료에 가까운 세션의 eviction 우선순위를 높이는 programmable penalty, B_DMA는 논리 DMA 대역폭이다. score가 높을수록 evict 또는 느린 티어 강등 우선순위가 높고, score가 낮을수록 빠른 티어 승격 대상이다.

## 한계와 주의할 점

- 소프트웨어 timestamp만으로 SPEAR를 구현하면, 도구 대기가 decode window보다 짧은 경우 gap 신호가 뒤집혀 hit rate가 떨어질 수 있다(Section V-G: GAIA/Devstral tight schedule에서 −6.6pp).
- GPU가 prefill로 이미 포화 상태라면(SWE/Qwen3 등), 캐시 적중을 올려도 queuing 지연이 지배해 TTFT 개선이 작거나 사라진다.
- hazard LUT가 안정화되려면 충분한 세션 수가 필요하다. GAIA/Gemma4처럼 128세션 규모의 작은 코퍼스에서는 분산이 커져 SPEAR advantage가 묻힐 수 있다.
- 평가 코퍼스는 SWE-bench와 GAIA 기반 단일 에이전트 replay이며, 실제 동시 다중 에이전트 워크플로의 상호작용은 직접 측정하지 않는다.
- 하드웨어 이벤트 FIFO와 unified register file에 의존하는 설계라, 기존 추론 스택에 소프트웨어 패치만 얹으면 full SPEAR+TIDE 효과를 얻기 어렵다.
- Gap inversion: 도구 대기가 decode window보다 짧으면 소프트웨어 block-cache timestamp가 실제 gap 시작을 거칠게 잡아 score가 잘못 정렬될 수 있다.
- GPU-bound saturation: 캐시 적중이 늘어도 queuing이 지배하는 구간에서는 TTFT가 개선되지 않는다.
- Noisy hazard LUT: 세션 수가 적을 때 hazard 분포가 들쭉날쭉해 evictor가 baseline과 비슷해질 수 있다.
- Stale dual-IP views: eviction과 tiering을 독립 IP로 나누고 동기화를 늦추면, interleaved 에이전트 부하에서 hit rate가 최대 5.4pp 떨어지고 AMAT 변화 방향도 일관되지 않다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### RAG 재순위에 gap-EMA 점수를 더하는 메모리 회수기

장기 기억을 쓰는 에이전트의 RAG 검색 파이프라인에서, LRU/LFU로 문서 청크를 캐시에서 밀어내는 단계를 SPEAR식 점수로 바꾼다. 사용자 또는 작업 세션별 쿼리 간격 EMA를 g_s로, 누적 턴 수 기반 완료 가능성을 σ(t)로 근사해, 짧게 쉬고 곧 돌아오는 세션의 청크는 보존하고 길게 쉬거나 완료에 가까운 세션의 청크부터 회수한다. 적용 지점은 retrieval 이후 re-ranker 직전 캐시 evict 결정 모듈이다.

**적용 지점** — RAG 문서 캐시 evict 단계 / 에이전트 세션 단위 메모리 회수

**기대 효과** — 논문에서 UNISON 전체 정책은 LRU 대비 hit rate 0.3–23.1pp, AMAT 22–51% 개선을 보였다. RAG에는 같은 방향의 세션 단위 캐시 효율 개선을 기대할 수 있으나, 논문이 직접 RAG 문서 캐시를 평가하지는 않았다.

### 툴 idle 구간을 데이터 마이그레이션 예산으로 쓰는 티어링기

장기 기억을 두 단계(예: GPU HBM과 CPU RAM, 또는 로컬 SSD)에 보관하는 에이전트라면, TIDE의 B_mig=Δ·B_DMA 공식을 적용할 수 있다. 도구 요청 직후 예상 대기 시간 Δ를 두 티어 간 대역폭으로 곱해 옮길 수 있는 토큰 또는 청크 예산으로 쓰고, score가 낮은 느린 티어 resident를 빠른 티어로 승격하며 score가 높은 빠른 티어 resident를 느린 티어로 강등한다. 적용 지점은 tool-call outbound 이벤트 직후의 background migration dispatcher다.

**적용 지점** — 에이전트 메모리 계층 간 자동 마이그레이션 / GPU↔CPU KV 이동

**기대 효과** — 논문 Fig. 5는 SPEAR와 TIDE가 대체재가 아니라 보완재임을 보이며, TIDE with LRU는 prefetch accuracy가 낮고 UNISON 결합에서 hit rate·AMAT·prefill reduction이 함께 개선된다.

### 에이전트 종료 가능성을 작업 완료 검문에 사용

장기 작업을 끝까지 완주해야 하는 에이전트라면 SPEAR의 hazard h(t)=d(t)/n(t)를 종료 검문 신호로 사용할 수 있다. 특정 턴에서 완료 hazard가 높아지는 구간에 self-check 또는 answer summarization 루틴을 호출해, 캐시가 밀려나기 전에 중간 결과를 정리한다. 다만 논문에서 hazard는 캐시 랭킹 신호로만 검증됐으므로, 작업 종료 정책에는 별도 안전장치와 평가가 필요하다.

**적용 지점** — 에이전트 자기검증·작업 종료 결정 단계 / long-horizon 작업 완주 보장

**기대 효과** — 논문 Fig. 6은 hazard 제거가 hit rate와 AMAT를 악화시켜 hazard가 유효한 완료 진행 신호임을 보인다. 직접적인 작업 성공률 개선은 논문에서 측정하지 않았다.

### 공유 자원 풀을 위한 unified ranking 스케줄러 일반화

다중 에이전트가 도구 핸들, API rate-limit 슬롯, DB connection 같은 공유 자원을 두고 경쟁하는 시스템이라면, UNISON의 제어평면 원칙을 일반화할 수 있다. 각 자원에 gap-like interval과 완료 가능성 기반 점수를 매기고, 낮은 점수는 빠른/우선 자원에, 높은 점수는 회수 또는 느린 자원에 배치한다. 독립 모듈로 나누고 주기적으로 sync하는 구조는 상태가 stale해질 수 있으므로 allocation과 reclamation이 같은 ranking을 읽도록 설계한다.

**적용 지점** — 에이전트 하네스의 자원 스케줄러 / 다중 결정이 한 상태를 공유해야 하는 컨트롤 플레인

**기대 효과** — 논문 Table I에서 dual-IP 구조는 sync granularity에 따라 hit-rate drop이 최대 5.4pp까지 발생하고 AMAT 변화 부호도 일관되지 않았다. unified register file은 이 failure mode를 피한다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | SPEAR 랭킹을 기존 추론 스택(vLLM prefix cache)에 소프트웨어 패치로 이식 | 런타임에서 관측 가능한 gap/turn 메타데이터만으로 점수를 계산하는 모듈을 vLLM v1 prefix cache에 통합하고, 트레이스 리플레이로 hit rate/TTFT를 측정 | cache-bound 워크로드에서는 논문 vLLM 검증처럼 mean TTFT 35%·p99 e2e 72% 개선 가능성을 확인할 수 있다. |
| Phase 2 | TIDE 배치기까지 포함한 near-memory 스케줄러 IP를 FPGA에서 검증 | Zynq-7020 등 FPGA에 64세션 용량의 결정 파이프라인을 합성하고, 실제 에이전트 트레이스를 event FIFO로 주입해 latency·충실도를 측정한다. hazard LUT는 완료 세션 누적으로 online 갱신한다. | gap_start 이벤트에서 DMA descriptor가 나오는 하드웨어 결정 지연이 마이크로초 단위에 머무는지 확인하고, ASIC 진입 전 RTL 검증을 마친다. |
| Phase 3 | 추론 SoC에 통합 가능한 28nm CMOS IP로 마무리 | Design Compiler로 150 MHz timing closure, APB·CSR·event FIFO 인터페이스 확정, 메모리 계층 옆 sideband event bus 연결을 설계하고 GAIA·SWE 워크로드 end-to-end 측정을 수행한다. | 논문이 보고한 hit rate 0.3–23.1pp 상승, AMAT 22–51% 절감, 장기 트레이스 TTFT 58–89% 절감을 실제 통합 환경에서 재현하는 것이 목표다. |

---

원문 PDF: `2026-09-10-unison-a-co-designed-near-memory-scheduler-of-session-kv-residency-for-l.pdf`
