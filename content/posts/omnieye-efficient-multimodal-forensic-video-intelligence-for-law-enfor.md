---
title: "경찰 바디캠 영상을 30초씩 나눠 미리 요약하고, 나중에 질문을 받으면 중요한 장면을 다시 확인한 뒤 근거가 있는 답만 보여주는 도구다."
date: 2026-09-11T08:17:18+09:00
draft: false
description: "OmniEye는 경찰 바디캠(BWC) 영상을 기관 내부 장비에서 분석하기 위한 멀티모달 영상 인텔리전스 시스템이다. 30초 윈도우(5초 오버랩)마다 영상 30프레임과 16kHz 모노 오디오를 Gemma 4 12B 기반 모델이 함께 인식하고, 결과를 단일 SQLite workspace에 저장해 FTS5+BM25와 구조화 필터로 검색한다. 질의 응답 에이전트는 후보 윈도우를 검색한 뒤, 인용 직전에 현재 턴에서 해당 원본 픽셀과 오디오를 다시 인식한 윈도우만 인용할 수 있다."
tags: ["Multimodal Video Intelligence / Forensic AI", "논문 분석", "논문 리뷰", "멀티모달 파운데이션 모델", "4-bit NF4 QAT", "Speculative decoding"]
categories: ["논문분석"]
---


경찰 바디캠 영상을 30초씩 나눠 미리 요약하고, 나중에 질문을 받으면 중요한 장면을 다시 확인한 뒤 근거가 있는 답만 보여주는 도구다.

**무엇이 문제였나** — 경찰 바디캠 영상은 매년 수만 건씩 쌓이지만, 실제로 감독·교육·공개 요청에 필요한 순간은 일부라서 사람이 전부 보기 어렵다.
**어떻게 풀었나** — 영상을 30초 단위로 자르고 화면과 소리를 함께 분석해 요약, 대화 내용, 중요도, 위험 신호를 저장한다. 질문이 들어오면 검색된 장면을 AI가 다시 본 뒤에만 그 장면을 인용한다.
**그래서 뭐가 좋아졌나** — 평가 샘플에서 중요한 장면은 무작위보다 훨씬 빨리 찾을 수 있었다. 또 각 분석 결과와 사람이 고친 기록은 해시 체인에 묶여 나중에 바뀌면 어디가 바뀌었는지 드러난다.

> 수천 권의 기록 영상을 먼저 30초짜리 쪽지로 나누어 제목과 색인을 붙여 두고, 질문이 들어오면 관련 쪽지를 찾은 뒤 실제 장면을 다시 확인해 답하는 사서에 가깝다. 기록마다 봉인이 있어 누가 언제 무엇을 고쳤는지도 추적된다.

## 논문 정보

Mamadou K. Keita, Angela Srbinovska, Anita Srbinovska, Nishka Desai et al. · Rochester Institute of Technology; Rochester Police Department; University at Albany School of Criminal Justice; New York State Youth Justice Institute · AAAI 2027 · 2026

## 왜 중요한가

경찰 영상은 개인정보와 증거 보존 의무 때문에 클라우드 서비스로 보내기 어렵다. OmniEye는 한 대의 16GB GPU부터 기관 내부 클러스터까지 로컬 환경에서 돌아가도록 설계되어, 민감한 영상을 밖으로 내보내지 않고도 검색, 검토, 교육, 공개 기록 대응을 할 수 있게 한다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 고우선순위 P@25 향상 | **3.3배** | anomaly_score 상위 25개에서 high-priority(A) 정밀도 0.60, base rate 0.180 대비 |
| 무손실 temporal decoding 처리속도 | **1.48배** | 이전 윈도우 출력을 draft reference로 쓰는 temporal speculative decoding의 측정 window speedup |
| GPU 메모리 풋프린트 | **6–8GB** | 12B 멀티모달 모델을 4-bit NF4 및 double quantization으로 적재할 때의 대략적 footprint |
| 주석자 간 binary κ | **0.171** | 두 명 인간 주석자 사이의 binary Cohen's κ; OmniEye는 Annotator A와 κ=0.290으로 B보다 더 일치 |

## 어떻게 동작하나

OmniEye는 BWC 녹화를 w=30초, o=5초 오버랩, stride 25초 윈도우로 나누고, 각 윈도우에서 1fps로 30프레임을 샘플링하며 16kHz 모노 오디오를 추출한다. 하나의 멀티모달 모델(Gemma 4 12B)이 프레임과 오디오를 한 번에 받아 strict JSON으로 시각 설명, 오디오 설명, cross_modal 신호, speaker-tagged transcript, 3-way category와 score vector, tags, audio_events, evidence_flags, structured booleans, anomaly_score를 출력한다. 결과는 단일 SQLite workspace에 window row로 커밋되고, description, audio_description, cross_modal, transcript는 FTS5+Porter로 색인되어 Okapi BM25 검색에 쓰인다. category, evidence flags, audio events, boolean detections, officer, environment, anomaly threshold, time range 같은 구조화 필터도 같은 SQL에서 결합된다. 정책 문서는 문단 단위로 chunking되어 같은 검색 공간에 들어간다. 질의 응답 단계에서는 agent가 후보 윈도우를 검색하고, 인용하려는 윈도우를 현재 turn에서 다시 원본 픽셀과 오디오로 re-perceive한 경우에만 citation으로 허용한다. grounding verifier는 what/where/when/how 규칙으로 초안 답변을 다시 대조해 증거가 받치는 주장만 남긴다. 엔진은 16GB GPU용 4-bit NF4/double quantization과 QAT INT4 checkpoint, higher-precision embedder/head, per-GPU data-parallel replica, previous-window output을 이용한 lossless temporal speculative decoding, GPU OOM과 host-memory pressure에 반응하는 AIMD batch controller를 사용한다. 각 window는 per-video SHA-256 chain에 묶이고, correction·agent action·answer 같은 mutating action은 attributed global audit log에 append된다. 비디오별로는 10개 윈도우 단위 segment narrative와 전체 video overview도 만든다.

핵심 수식:

```
h_i = SHA256( canon( f, i, o_i, t_i, h_{i-1} ) )
S = (alpha_bar + 1) / (1 + c)
y'_t = strip( y_t, cites(y_t) \ R_t )
```

h_i는 윈도우 i의 해시이며, source file hash f, window index i, raw model output o_i, ingest timestamp t_i, previous hash h_{i-1}를 key-sorted canonical JSON으로 직렬화해 SHA256한 값이다. 첫 윈도우는 고정 genesis value h_{-1}=g를 쓴다. S는 temporal speculative decoding에서 verification forward 한 번당 평균 alpha_bar개의 drafted token이 받아들여질 때의 이상적 speedup이며, c는 drafting과 verification의 상대 오버헤드다. y'_t는 초안 y_t에서 현재 턴에 re-perceived된 윈도우 집합 R_t에 속하지 않는 citation marker와 그 citation이 받치던 unsupported claim을 제거한 filtered answer다.

## 한계와 주의할 점

- 주석자가 2명뿐이라 κ=0.171이라는 패턴은 사실이지만, 더 큰 주석자 풀에서 같은 구조가 유지될지는 알 수 없다.
- Must absolutely watch 평가는 annotated sample의 15개 윈도우에 크게 의존하므로, 범주별 균등 할당과 population rate 재가중이 더 날카로운 추정을 줄 수 있다.
- 클라우드 API나 더 큰 모델과 직접 비교하지 못했다. 개인정보, chain-of-custody, 허용 모델, compute 제약 때문이다.
- Cohen's κ는 주석자 threshold 차이와 클래스 불균형의 영향을 크게 받으므로 correctness보다는 특정 주석자와의 closeness로 해석해야 한다.
- category 단독 필터는 안전하지 않다. Boring을 건너뛰면 Annotator A 기준 worth-reviewing 278개 중 147개와 high_priority_review 90개 중 42개를 놓친다.
- 해시 체인과 감사 로그는 모델 출력과 수정 이력의 변조 탐지를 보장하지만, 카메라가 기록한 원본 영상 자체의 세계적 진실성을 증명하는 것은 아니다.
- obstructed camera, off-target view, severe low light에서는 인간 주석자도 unable_to_assess를 사용했지만, 모델의 3-way category에는 이와 직접 대응하는 label이 없다.
- 두 주석자는 worth-reviewing window 수가 278개와 59개로 4.7배 차이였다. 같은 ordering을 공유하더라도 threshold가 달라 라벨이 크게 갈릴 수 있다.
- 각 replica stream의 첫 윈도우는 이전 출력 reference가 없어 temporal speculative decoding 이득을 얻지 못한다.
- 4-bit inference에서 window batch 2는 1.03배에 그쳐 batching 이득이 거의 없고, 이 경우 multi-GPU throughput은 data-parallel replica에 의존한다.
- 64GB cgroup host-memory cap에서는 naive 1,000-video run이 몇십 개 영상 뒤 kill될 수 있었다. 논문은 memory-pool 반환, page-cache drop, fragmentation bound, cgroup-aware AIMD backoff로 이를 완화한다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### RAG 답변에 재추론 강제 회로(Citation Grounding Filter) 추가

장기 기억이나 문서 검색을 쓰는 에이전트에서 답변 직전 '이번 턴에서 모델이 다시 본 청크 집합 R_t'를 추적하고, y'_t = strip(y_t, cites(y_t) \ R_t)로 R_t 밖 citation marker와 그 marker가 받치던 unsupported claim을 제거한다. OmniEye Section 2.5의 구조를 일반 RAG citation 검증에 옮긴 것이다.

**적용 지점** — 장기 기억 회수 단계의 인용 후처리

**기대 효과** — 환각 인용을 구조적으로 줄인다. OmniEye의 8-question supervisory review form 테스트에서는 16개 답변 모두 window-level citation과 timestamp를 가졌다.

### 에이전트 액션 비거부 감사 로그(Actor-Chained Audit Log)

도구 호출, re-perception, 답변, citation 같은 지정 액션마다 content hash c_j와 previous log hash를 묶어 l_j = SHA256(c_j || l_{j-1})를 append-only log에 추가한다. actor identity, action content, session order가 함께 묶이므로 나중에 '그 답을 안 했다', '다른 내용을 냈다', '다른 순서였다'는 주장을 검증으로 다룰 수 있다.

**적용 지점** — 에이전트 액션 감사 로그(도구 호출·답변·수정)

**기대 효과** — 감사·법적 사용 시 변조 탐지, attribution, sequence-localized verification을 제공한다.

### 연속 청크 간 무손실 투기적 디코딩(Lossless Temporal Speculative Decoding)

연속 window에서 직전 출력 y^(i-1)의 마지막 n=2 토큰 match를 찾아 최대 K_s=12개 token을 draft하고, 모델의 greedy prediction과 일치하는 prefix만 채택한다. 매번 검증을 통과한 토큰만 쓰므로 output은 greedy decoding과 byte-identical이다.

**적용 지점** — 연속 컨텍스트 윈도우 처리 파이프라인(스트리밍 문서·센서 로그 등)

**기대 효과** — 논문 측정 기준 약 1.48배 window speedup, 추가 draft model·weights·memory 불필요.

### What/Where/When/How 그라운딩 검증기(Grounding Verifier)

답변 초안 y_t를 R_t의 window record와 '볼 수 있거나 들린 것만 주장하고 나머지는 not_determinable로 둔다'는 규칙에 비추어 다시 읽게 한다. 증거가 받치는 claim만 남기고 나머지는 삭제하는 최종 품질 게이트로 쓸 수 있다.

**적용 지점** — 에이전트 답변 단계의 최종 품질 게이트

**기대 효과** — 근거 없는 주장과 overclaim을 줄이고, citation이 실제 evidence record와 맞도록 한다.

### 도메인 이벤트용 3-단계 검색-확인 디텍터 카탈로그

firearm-drawn, gunshot, taser, use-of-force 같은 detector마다 structured prefilter, lexical aliases, preferred modality, focused prompt를 둔다. find-event는 structured flag, synonym text, top-anomaly fallback으로 후보를 만들고, 각 후보를 re-perception해 yes/no/unsure를 받은 뒤 confirmed window만 report 또는 citation에 쓴다.

**적용 지점** — 도메인 이벤트 검색 단계(질의-응답 에이전트의 find-event 호출)

**기대 효과** — 예시 firearm query에서 9개 후보 중 상위 6개를 재인식해 4 yes, 1 no, 1 unsure를 얻고 최종 4-citation answer만 사용자에게 제공한다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Stage 1 | 부서 인프라에서 archive processing | Rochester Police Department 인프라에서 archived recordings를 처리하고 reviewers가 output을 annotate한다. 7개 zero-duration file처럼 문제 파일은 log-and-skip하며 incremental commit과 recovery registry로 중단 후 재개한다. | 일상 운영 전 단계에서 실제 부서 데이터에 대한 searchable workspace와 baseline distribution을 확보한다. |
| Stage 2 | 핵심 직원 교육과 training gap 식별 | TUI/CLI, clickable citation, metrics dashboard, annotation/review screen을 활용해 staff가 anomaly ranking, critical windows, safety summaries, policy checks를 검토하도록 훈련한다. | 검토자가 먼저 볼 장면을 좁히고 교육·전술 분석에 필요한 사례를 빠르게 모을 수 있다. |
| Stage 3 | 기존 분석 workflow 통합 | incident timeline, redaction worksheet, reproducible debrief reports, audit verification, evidence packet export를 기존 분석 절차에 연결한다. | 감독, 공개 기록, 내부 보고 업무에서 window-level citation과 tamper-evident provenance를 일관되게 쓸 수 있다. |

---

원문 PDF: `2026-09-10-omnieye-efficient-multimodal-forensic-video-intelligence-for-law-enforce.pdf`
