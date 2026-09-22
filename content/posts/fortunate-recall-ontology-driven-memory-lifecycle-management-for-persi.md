---
title: "사용자의 정보를 11가지 종류로 나누고, 각 종류마다 다르게 적용되는 '잊는 규칙'을 만들어 챗봇이 옛 정보나 바뀐 정보를 답하지 않게 하는 시스템이다."
date: 2026-09-23T07:35:01+09:00
draft: false
description: "Fortunate Recall은 LLM 메모리 시스템이 모든 개인 사실을 균일하게 취급해 발생하는 일관성 붕괴 문제를, 11개 행동 카테고리별 결정론적 수명주기 정책으로 해결한다. LifecycleBench에서 76.9% pass rate를 기록하며 Mem0 대비 confabulation을 절반 이하(전체 쿼리 13.0% vs 32.2%)로 줄이고, BEAM 외부 벤치마크에서도 46.8%로 Mem0 32.9%를 13.9pp 앞질렀다."
tags: ["Large Language Model / Agent Memory", "논문 분석", "논문 리뷰", "행동 온톨로지", "슬롯 키 교체", "사건 시각 유효성"]
categories: ["논문분석"]
---


사용자의 정보를 11가지 종류로 나누고, 각 종류마다 다르게 적용되는 '잊는 규칙'을 만들어 챗봇이 옛 정보나 바뀐 정보를 답하지 않게 하는 시스템이다.

**무엇이 문제였나** — 챗봇이 사용자의 모든 정보를 똑같이 다루면서 옛날 취향이나 끝난 약속을 계속 기억하고 답해, 대화가 길어질수록 어긋났어요.
**어떻게 풀었나** — 각 정보를 11가지 행동 카테고리(신상, 관계, 취향, 약속, 취미 등)로 분류하고, 카테고리마다 다르게 망각·교체·만료 규칙을 명확한 수식으로 자동 적용했어요.
**그래서 뭐가 좋아졌나** — 거짓 정보를 만들어내는 비율이 절반으로 줄었고(전체 쿼리 기준 13.0% vs Mem0 32.2%), 맞는 답변 비율은 31.2%로 12.6%p 늘었어요.

> 비서에게 '직장 정보는 자주 바뀌니까 새 소식으로 자동 갱신해줘, 생일은 절대 안 바뀌니까 그대로 둬줘, 다음 주 화요일 병원 약속은 그날까지만 기억하고 지나면 잊어줘'라고 미리 지시한 것과 같아요. 모든 정보를 똑같이 다루는 게 아니라, 정보의 성격에 따라 다르게 기억하고 잊는 거죠.

## 논문 정보

Ansuman Mullick, Eray Tüzün · Bilkent University · arXiv preprint (under review) · 2026

## 왜 중요한가

사용자가 '피자 좋아해요'라고 했다가 나중에 '초밥이 좋아요'라고 바꾸면, 챗봇은 더 이상 피자를 계속 추천하면 안 됩니다. 그런데 대부분의 메모리 시스템은 옛 정보를 그대로 가지고 있어, 시간이 지날수록 사용자에게 맞지 않는 말을 하게 됩니다. 이 논문은 이 '기억의 청소'를 자동화하는 방법을 보여줍니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| LifecycleBench Pass Rate | **76.9%** | Mem0 61% 대비 +15.9pp (95% CI [73.3, 80.6]) |
| E2E Correct Rate | **31.2%** | Mem0 18.6% 대비 +12.6pp (516 LifecycleBench 전체 쿼리 기준) |
| Confabulation (all 516 queries) | **13.0%** | Mem0 32.2% 대비 -19.2pp (어블레이션 p<0.001 유의미) |
| BEAM Transfer (외부 검증) | **46.8%** | Mem0 32.9% 대비 +13.9pp, 280문항 중 131 정답 |

## 어떻게 동작하나

Fortunate Recall은 LLM 메모리 시스템의 모든 사실이 동일하게 취급되는 문제를 정면으로 다룹니다. 각 추출된 사실을 11개 행동 카테고리(Identity, Relational, Preferences, Obligations 등)로 분류하고, 카테고리마다 다른 결정론적 수명주기 정책(감쇠율, supersession, 사건시각 유효성, 카테고리 인식 라우팅)을 적용합니다. LLM은 ingestion 시 분류·추출과 retrieval 시 후보 distillation 한 번에만 사용되며, lifecycle 정책 자체는 47마이크로초 안에 끝나는 순수 수식입니다. 516문항의 LifecycleBench에서 76.9% pass rate, 500문항의 LongMemEval-S에서 75.2% pass@10을 기록하고, BEAM 외부 벤치마크에서 46.8% 정답률로 32.9% Mem0을 앞질렀습니다. 핵심 발견은 generic metadata(슬롯 키, lifecycle state, event-time anchor)가 정확도 이점을 가져가고, behavioral ontology는 카테고리별 parameter화를 가능케 해 confabulation을 절반으로 줄인다는 분리입니다.

핵심 수식:

```
ℓ(e, q, t) = β·σ(e, q) + log ρ(c_e|q) − λ_{c_e}·Δt_e + log V_{c_e}(t, h_e) + log Ω(e) + log M_q(ξ_e)
```

β·σ(e,q) 의미적 유사도 / ρ(c_e|q) 쿼리-카테고리 사전 / -λ_{c_e}·Δt_e 카테고리 감쇠 / V_{c_e}(t,h_e) 사건시각 유효성 커널 / Ω(e) 슬롯 키 대체 인자 / M_q(ξ_e) lifecycle state 마스크

## 한계와 주의할 점

- 절대 수치는 LLM judge에 의존해 judge-relative이다. 100-verdict stratified human slice가 계획만 되고 미실행 상태로, 사람 검증 부재가 명시적인 한계다.
- LifecycleBench의 attack vector가 Mem0·Graphiti의 실패 모드에서 도출되어 benchmark-method co-design 위험이 존재. BEAM 외부 검증은 bound만 잡고 fully eliminate하지는 못한다.
- 경쟁 시스템은 shipped default로 동작하고 FR은 정교하게 튜닝된 stack으로, 비교 공정성 한계가 있다(untyped-arm ablation으로 내부 분해는 했지만 maximally tuned competitor는 부재).
- 두 substrate(Graphiti, flat bank)와 한 agent loop에서만 테스트되어 multi-framework·concurrent writer 환경에서 동작은 미측정이다.
- FR-Bank는 57.9% 쿼리만 답변하며 correctness-abstention trade-off가 존재. 추가 abstention은 오답에서 비롯되지만 '반드시 답해야 하는' 배포 환경에는 그대로 적용하기 어렵다.
- AV7 선택적 망각: FR-Bank의 5% 검색 통과율은 철회된 사실을 노출하지 않았다는 의도된 결과이나, retraction detector가 40개 중 19개만 탐지하고 단 2개만 메타데이터 레벨에서 깨끗하게 차단(suppress)하여 정보 추출 재현율(extraction recall)이 한계점으로 작용한다.
- Long-term regime(Δt > 2000hr)에서 activation이 3.3×10⁻¹⁰까지 underflow하며, score가 의미유사도로 collapse해 결정성이 사라진다.
- Slot key over-matching 시 over-broad slot key가 ingest-time supersession을 over-fire해 BEAM knowledge update 12건 중 10건(10/12 사례)에서 현재 값을 deactivate한다.
- Soft supersession이 high-commitment generator(Kimi K2.5 AV9)에서는 두 후보 모두 유지해 abstention 대신 commitment를 만들어낸다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 장기 기억 시스템에 카테고리별 감쇠율과 슬롯 키 교체 도입

장기 기억을 가진 에이전트의 ingestion 단계에서 LLM이 각 사실을 11개 카테고리 중 하나로 분류하고 slot key, lifecycle state, event-time anchor를 부착하도록 한다. retrieval 단계에서는 논문의 Model 1과 Equation 2의 결정론적 log-score로 후보를 재정렬한다. 이 적용이 '기억의 청소'를 자동화하는 핵심 메커니즘이다.

**적용 지점** — 장기 기억 에이전트의 retrieval 재정렬 단계

**기대 효과** — confabulation 45.1% → 22.4% (answered), 32.2% → 13.0% (all queries), correct rate 18.6% → 31.2%

### RAG 파이프라인에 카테고리 인식 라우팅을 추가해 어휘 격차 해소

RAG 파이프라인의 retrieval 후보 생성 단계에서, 쿼리를 행동 카테고리로 분류하고 해당 카테고리의 모든 후보를 강제 검색(top-20)한다. 일반 의미 검색과 BM25 후보와 merge한 뒤 단일 distillation call로 top-20을 선정한다. 이 레이어는 기존 vector store 위에 얇은 wrapper로 얹을 수 있으며, 논문의 category-aware routing과 category-forced retrieval을 그대로 옮긴다.

**적용 지점** — RAG 파이프라인의 retrieval 후보 생성 단계

**기대 효과** — routing만으로 +6pp pass rate (Table 3 ablation), scale-emergent 효과

### 이중 시간 메타데이터로 다가오는 일정의 anticipatory activation 구현

장기 기억 시스템의 Obligations/Logistics 카테고리에서 creation time 외에 event-time anchor(ℎ)를 별도로 저장한다. retrieval 시 거리 기반 validity kernel Vc(t,h)로 activation을 재계산해 deadline이 가까워질수록 점수가 증가하고, 지나면 즉시 expired 상태로 전환된다. paper의 Vc 항을 분리된 시간 차원으로 구현하는 변경이며, 4-state lifecycle state machine의 expired 전이를 event-time 기반으로 자동 발생시킨다.

**적용 지점** — 일정·약속·마감일 저장 단계 및 retrieval 단계

**기대 효과** — AV2 expired logistics +20pp over Mem0 (FR-Bank 88% vs Mem0 65%)

### 명시적 4-state lifecycle mask로 철회·만료 사실 노출을 차단해 환각을 억제

장기 기억 시스템의 메타데이터 단계에서 각 사실에 lifecycle state를 명시적으로 부여하고, retrieval 시 Mq(ξ) 호환 마스크를 적용해 current-state 쿼리에서는 retracted·expired를 차단하며, change-aware 쿼리에서는 superseded만 노출한다. paper의 Mq(ξ) 항과 4-state machine을 그대로 옮긴다. 기존에 단일 deletion으로 처리하던 철회 요청을 'retained but masked'로 모델링하는 것이 핵심이며, 이를 통해 Mem0의 UPDATE로는 구현 불가한 (0,1) relevance pattern을 구현한다.

**적용 지점** — 장기 기억의 메타데이터 단계 및 retrieval gating

**기대 효과** — AV7 end-to-end correct 37.5% (FR-Bank) vs 2.5% (Mem0·Memory-R1), downstream 환각 90% 이상 발생 방지

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | Ingestion 단계에 행동 카테고리 분류 + slot key 추출 + lifecycle state 결정 통합 | LLM extractor에 11개 카테고리 분류, (subject, attribute) slot key, event-time anchor, 4-state lifecycle(active/superseded/expired/retracted) 추출을 추가한다. 3-judge classifier agreement audit(목표 κ ≥ 0.7)로 분류기 품질을 모니터링한다. | generic metadata 토대 구축. 논문 결과에 따르면 generic metadata만으로도 +12pp pass rate가 generic lifecycle stack에서 나온다. |
| Phase 2 | 결정론적 lifecycle 수식 레이어 구현 (Eq. 2 기반) | 카테고리별 감쇠율 λc, supersession factor Ω(e), event-time validity kernel Vc(t,h), query-conditioned mask Mq(ξ)를 closed-form log-score로 통합한다. bi-temporal 메타데이터(transit time + event time)를 분리 저장하고, slot key over-matching을 방지하는 negative-constraint 룰을 둔다. | LifecycleBench +12pp over uniform baseline, AV2 expired logistics +20pp, AV4 multi-version +22pp. 47μs median latency 추가. |
| Phase 3 | 카테고리 인식 retrieval routing + 평가 안정화 | category-aware routing과 category-forced retrieval로 추상 쿼리-구체 사실 어휘 격차를 해소한다. hybrid BM25+semantic+category 후보를 merge하고 단일 distillation call로 top-20을 선정한다. 두 judge 패널(Fleiss κ=0.834 기준)로 judge noise를 5% 이내에서 안정화한다. | routing만으로 +6pp pass rate, contradiction resolution +10~13 of 70. AV6 retrieval pass vs E2E correct decoupling을 막아 retrieval-metric paradox를 회피. |

---

원문 PDF: `2026-09-10-fortunate-recall-ontology-driven-memory-lifecycle-management-for-persist.pdf`
