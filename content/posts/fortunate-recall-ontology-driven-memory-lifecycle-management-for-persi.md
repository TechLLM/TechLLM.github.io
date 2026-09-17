---
title: "AI가 사람에 대해 기억한 내용을 종류별로 다르게 보관하고 지우게 만드는 방법이다."
date: 2026-09-18T07:32:21+09:00
draft: false
description: "Fortunate Recall은 LLM 메모리 시스템이 모든 개인 사실을 균일하게 취급해 outdated 정보가 retrieval을 오염시키는 문제를, 10+1 행동 온톨로지와 결정론적 수명주기 정책 계층으로 해결한다. FR-Bank는 LifecycleBench에서 76.9%, LongMemEval-S에서 75.2%, BEAM의 4개 binary-scorable lifecycle-relevant ability에서 46.8%(Mem0 32.9%)를 기록했다."
tags: ["Large Language Model / Agent Memory", "논문 분석", "논문 리뷰", "Lifecycle management", "Behavioral ontology", "Supersession"]
categories: ["논문분석"]
---


AI가 사람에 대해 기억한 내용을 종류별로 다르게 보관하고 지우게 만드는 방법이다.

**무엇이 문제였나** — 기존 AI 메모리는 오래된 취향, 끝난 일정, 아직 중요한 신상 정보를 비슷하게 다뤄서 헷갈릴 수 있다.
**어떻게 풀었나** — 이 논문은 기억을 신원, 관계, 건강, 취향, 약속, 일정 같은 10+1가지 종류로 나누고, 종류마다 보관 기간과 교체 규칙을 다르게 둔다.
**그래서 뭐가 좋아졌나** — 그 결과 새로 만든 시험인 LifecycleBench에서 76.9%를 기록했고, 잘못된 옛 정보를 바탕으로 답하는 비율도 Mem0보다 크게 줄였다.

> 책상 위 메모를 정리하는 것과 비슷하다. 주민등록증 같은 정보는 오래 보관하고, 좋아하는 음식은 새 취향이 생기면 바꾸고, 어제 회의 일정은 회의가 끝나면 치운다. 이 논문은 AI 기억에도 이런 정리 규칙을 붙인다.

## 논문 정보

Ansuman Mullick, Eray Tüzün · Bilkent University · Under review (arXiv preprint) · 2026

## 왜 중요한가

AI 비서가 사람과 오래 대화할수록 예전 정보를 현재 정보처럼 말하는 문제가 생긴다. 이 방법은 기억마다 라벨과 유효기간을 붙여, 지금도 맞는 정보와 더 이상 맞지 않는 정보를 구분하게 한다. 오래 쓰는 개인 비서, 고객 지원 챗봇, 건강 관리 도우미처럼 사용자 정보를 계속 다루는 시스템에 중요하다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| LifecycleBench Pass Rate | **76.9%** | FR-Bank vs MemoryOS 70.5% / Memory-R1 66.9% / Mem0(default) 61% |
| LongMemEval-S Pass@10 | **75.2%** | full 500-question LongMemEval-S, Wu et al. (ICLR 2025) judge protocol |
| All-Queries Confabulation | **13.0%** | FR-Bank vs Mem0(default) 32.2% over all 516 LifecycleBench queries |
| BEAM Correct | **46.8%** | FR-full 131/280 vs Mem0 92/280 (32.9%) on four binary-scorable abilities |

## 어떻게 동작하나

Fortunate Recall은 추출된 각 사실에 behavioral category c, slot key κ, lifecycle state ξ, event-time anchor h, ingest time t, confidence v 같은 메타데이터를 붙인다. Ingestion에서는 gpt-4.1-mini 한 번으로 추출과 분류를 수행하고, retrieval에서는 cosine top-60, BM25 top-20, category-forced top-20 후보를 병합한 뒤 작은 모델 호출로 top-20을 고른다. 이후 deterministic lifecycle layer가 category-conditioned decay, slot-key supersession, event-time validity, lifecycle-state mask, category-aware routing을 Eq. (2)의 log-score로 적용한다. 이 계층은 k=20에서 median 47μs, empirically O(k)로 동작한다. 이론적으로는 metadata basis (c, κ, ξ, h)의 sufficiency, minimality, individual necessity를 보이고, category-specific parameterization 없이는 calibration feasible region을 만족하기 어렵다는 점을 Theorem 4로 설명한다.

핵심 수식:

```
ℓ(e, q, t) = β·σ(e, q) + log ρ(c_e|q) − λ_{c_e}·Δt_e + log V_{c_e}(t, h_e) + log Ω(e) + log M_q(ξ_e)
```

βσ는 semantic similarity, ρ(c_e|q)는 query-category prior, −λ_{c_e}Δt_e는 category survival S_c(d)=exp(−λ_c d)의 로그값, V는 event-time validity kernel, Ω는 같은 slot key의 later edge들이 만드는 supersession survival factor, M_q는 query-conditioned lifecycle-state compatibility mask이며 log 0 = −∞로 둔다.

## 한계와 주의할 점

- 휴먼 검증 부재: 모든 verdict는 LLM judge 기반이며, six-model cross-family panel과 pinned judge의 일치도는 κ=0.715로 보고되어 절대 수치는 judge-relative하다.
- 벤치마크-방법 공동 설계 위험: LifecycleBench attack vector가 baseline 실패 모드에서 정의되었고, BEAM transfer로 완화했지만 완전히 제거되지는 않는다.
- 경쟁 시스템 공정성 한계: 경쟁 시스템은 shipped default로 실행되었고 maximally tuned competitor는 만들지 않았다.
- 멀티 프레임워크/멀티 에이전트 미검증: 두 substrate와 하나의 agent loop에서만 검증되어 concurrent writer 환경은 미측정이다.
- 정확도-회피 trade-off: FR-Bank는 42.1% abstain rate를 보이며, 반드시 답해야 하는 배포 환경에서는 이득이 줄어들 수 있다.
- 고확약 생성기에서 soft supersession 실패: Kimi K2.5 AV9에서 두 후보 값이 함께 남을 때 abstention 대신 commitment가 발생할 수 있다.
- Slot key의 over-broad matching: BEAM knowledge update에서 lifecycle-off가 더 높게 나온 discordant case 중 다수가 ingest-time supersession이 current value를 비활성화한 데서 왔다.
- Retraction extraction recall 부족: 40개 scripted retraction 중 detector는 19개에만 반응했고 metadata level에서 clean suppression은 2개뿐이었다.
- Classifier 경계 사례: classifier audit은 κ=+0.67이며 disagreement는 정책이 비슷한 category pair에 집중된다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### RAG retrieval 결과에 slot-key supersession 필터 추가

Hybrid semantic search 결과가 들어온 직후 후보 memory의 normalized slot key를 비교한다. 같은 slot 안에 더 최근의 high-confidence contradictory edge가 있으면 old edge의 Ω(e)를 낮추거나 current-state query에서 제외한다. 이 아이디어는 §3.3의 slot-key supersession과 Eq. (2)의 log Ω(e)에 해당하며, LifecycleBench AV1과 AV4의 큰 개선이 이 기능의 중요성을 뒷받침한다.

**적용 지점** — RAG 재순위 단계

**기대 효과** — superseded preference와 multi-version fact에서 stale retrieval 감소

### 이벤트 시점 기반 anticipation/expiry를 retrieval 점수에 결합

일정, 마감, 비행편 같은 기억에는 event-time anchor h를 저장하고, retrieval score에 V_c(t,h)를 추가한다. 다가오는 event는 더 중요해지고, 지난 event는 current-state query에서 낮아지거나 제외된다. 원문은 AV2에서 FR-Bank 88% vs Mem0 65%를 보고하며, Theorem 3′는 event-time-invariant system의 구조적 한계를 설명한다.

**적용 지점** — 시간 민감 사실의 retrieval ranking

**기대 효과** — 만료된 일정과 다가오는 의무를 더 잘 구분

### Lifecycle state mask로 철회된 기억을 current-state query에서 제외

단순 삭제는 나중에 사용자가 무엇을 취소했는지 물을 때 답할 수 없고, 단순 보존은 현재 상태 질문에서 틀린 답을 만든다. ξ를 active, superseded, expired, retracted로 두고 M_q(ξ)를 query intent별로 다르게 적용하면 두 요구를 동시에 만족할 수 있다. 원문은 AV7에서 FR-Bank의 E2E correct 37.5%가 가장 높았다고 보고하지만, metadata-level retraction suppression recall은 아직 약하다고도 밝힌다.

**적용 지점** — 철회와 취소가 있는 장기 기억 처리

**기대 효과** — 철회된 계획에 대한 confabulation 감소와 이력 질의 보존

### 행동 온톨로지로 retrieval 라우팅: category-forced 후보 풀

추상적인 질문과 구체적인 저장 문장 사이에는 vocabulary gap이 생길 수 있다. query category classifier가 질문을 예컨대 Preferences나 Obligations로 분류하면, 해당 category의 edge를 top-20 후보 풀에 포함시켜 semantic search만으로 놓치는 정보를 보완한다. §6.2의 FR-Graphiti ablation에서 routing 제거 시 73%에서 67%로 하락해 +6pp 기여가 보고된다.

**적용 지점** — RAG candidate generation 단계

**기대 효과** — category-level 질문의 recall 개선

### 47μs deterministic lifecycle layer를 retrieval middleware로 삽입

후보 edge에 c, κ, ξ, h 메타데이터가 있으면 Eq. (2)의 ℓ(e,q,t)를 계산해 rerank 직전에 적용할 수 있다. 논문은 k=20, single-threaded Python 3.13, AMD Zen 3에서 median 47μs overhead와 O(k) scaling을 보고한다. 이 방식은 기존 retrieval stack을 크게 바꾸지 않고 stale context를 줄이는 middleware로 도입하기 좋다.

**적용 지점** — retrieval 후처리 / rerank 단계

**기대 효과** — 낮은 latency overhead로 lifecycle-aware reranking 추가

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 단일 도메인 파일럿 | 가장 가치가 분명한 Preferences와 Obligations부터 slot-key supersession, lifecycle-state mask, event-time validity를 부분 도입한다. 기존 RAG retrieval 위에 deterministic lifecycle layer를 얹고 stale context와 abstention을 함께 측정한다. | 운영 데이터에서 오래된 정보가 답변에 섞이는 비율이 줄어드는지 확인하고, retrieval 정확도와 회피율의 균형을 점검한다. |
| Phase 2 | 온톨로지 확장 + category-aware routing | Identity, Relational, Health, Logistical Context를 추가하고 실제 데이터로 fact-level classifier를 검증한다. query classification으로 category-forced 후보 풀을 만들고 semantic 후보와 병합한다. supersede/retract 신호에는 사용자 확인 UI를 붙인다. | LifecycleBench에서 관찰된 routing과 behavioral decay의 이득이 실제 서비스 로그에서도 재현되는지 확인한다. |
| Phase 3 | 전체 스택 배포 + 지속적 calibration | FR-Bank식 lifecycle metadata를 production memory store에 통합하고, retrieval 단계의 deterministic score를 SLO 안에서 운영한다. 분기마다 stratified human-labeled slice를 만들어 judge drift와 category calibration을 점검한다. | 장기 메모리의 최신성, 설명 가능성, 회피-정답 균형을 지속적으로 관리하는 운영 체계를 만든다. |

---

원문 PDF: `2026-09-10-fortunate-recall-ontology-driven-memory-lifecycle-management-for-persist.pdf`
