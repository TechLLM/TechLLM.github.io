---
title: "Google I/O 2026: 에이전트 Gemini 시대의 시작"
description: "Sundar Pichai가 Google I/O 2026 기조연설에서 발표한 핵심 내용 — 월 3.2경 토큰 처리, Gemini 3.5 Flash, Gemini Omni, TPU 8세대, Ask YouTube, Docs Live까지 총정리."
date: 2026-05-20T08:11:00+09:00
draft: false
tags: ["GoogleIO2026", "Gemini", "AI에이전트", "Google", "LLM"]
cover:
  image: /images/google-io-2026-agentic-gemini-era-cover.png
  alt: "Google I/O 2026 에이전트 Gemini 시대"
---

## 개요

2026년 5월 19일, Google I/O 2026에서 Sundar Pichai CEO가 기조연설을 통해 "에이전트 Gemini 시대"의 본격 개막을 선언했다. 단순한 챗봇의 시대를 넘어, AI가 Search·YouTube·Docs·Maps 등 Google의 모든 제품에 에이전트로 내재화되는 전환점이다.

## 핵심 요약

- **토큰 처리량**: 월 3.2경(quadrillion) — 전년 대비 7배 성장
- **신모델**: Gemini 3.5 Flash, Gemini Omni Flash 오늘 출시
- **신기능**: Ask YouTube, Docs Live(음성 문서 작성), Ask Maps
- **인프라**: Capex $31B(2022) → $180~190B(2026), TPU 8세대 공개
- **SynthID**: OpenAI·Kakao·Eleven Labs 채택으로 AI 콘텐츠 워터마킹 표준화

---

## 숫자로 보는 AI 모멘텀

Pichai가 가장 먼저 꺼낸 지표는 토큰이었다. 2024년 월 9.7조였던 처리량이 2025년 I/O에서 480조로 뛰더니, 2026년 3.2**경**에 달했다. 1년 새 7배 성장이다.

제품 규모도 뚜렷하다:
- 월간 활성 사용자 **10억 이상** 제품: 13개 (그중 5개는 30억+)
- AI Overviews: **25억** MAU
- AI Mode(검색): 출시 1년 만에 **10억** MAU 돌파
- Gemini 앱: **4억 → 9억** MAU (1년, 2배 이상 성장), 일일 요청 7배 증가
- Nano Banana 이미지 생성 모델로 생성된 이미지: **500억 장** 이상

개발자·기업 지표도 인상적이다. 매월 Google 모델로 앱을 만드는 개발자가 **850만 명**, 모델 API는 분당 **190억 토큰**을 처리 중이고, 지난 12개월간 1조 토큰 이상 처리한 Google Cloud 고객이 **375개사** 이상이다.

---

## 제품에 녹아드는 대화형 AI

### Ask YouTube
YouTube의 방대한 영상 라이브러리에서 원하는 정보를 찾는 방식이 완전히 바뀐다. Ask YouTube는 질문에 맞는 영상을 보여주되, **바로 관련 장면으로 점프**한다. 미국에서 올여름 본격 출시 예정.

### Docs Live
"정확한 프롬프트를 타이핑하지 않아도 된다." 머릿속 생각을 그냥 말하면 Gemini가 문서를 완성해준다. 올여름 유료 구독자 대상 출시, 이후 Gmail·Keep에도 음성 기능 추가 예정.

### Ask Maps
10년 만에 가장 큰 Maps 업그레이드. 복잡하고 긴 질문도 자연어로 받아 처리한다.

---

## 인프라: Capex 6배, TPU 8세대

구글의 연간 Capex는 2022년 $310억에서 2026년 **$1,800~1,900억**으로 약 6배 뛰었다. 이 투자의 핵심은 자체 실리콘이다.

**TPU 8세대**는 처음으로 학습·추론을 분리한 이중 칩 구조를 채택했다:

| 칩 | 용도 | 특징 |
|---|---|---|
| TPU 8t | 대규모 사전학습 | 이전 세대 대비 연산력 3배, 전 세계 100만+ TPU 분산 학습 |
| TPU 8i | 추론 | 속도 대폭 개선, 에너지 효율 2배 향상(성능/와트 기준) |

JAX + Pathways 조합으로 학습이 단일 데이터센터 한계를 넘어 멀티 사이트로 분산된다. 대규모 모델 학습 기간이 **수개월 → 수주**로 단축된다는 의미다.

---

## 새 모델: Gemini 3.5 Flash & Gemini Omni

### Gemini 3.5 Flash
Gemini 3 시리즈 첫 번째 업그레이드. 3.1 Pro 대비 거의 모든 벤치마크에서 앞선다. 에이전트 코딩과 장기 과제(long-horizon task)에 특히 집중 개선됐다.

### Gemini Omni
"텍스트 예측을 넘어 현실 시뮬레이션으로." 어떤 입력에서도 어떤 출력 형태든 생성할 수 있는 새 모델 계열이다. 현재는 비디오 출력부터 시작하며, 향후 이미지·텍스트로 확장 예정. 첫 모델인 **Gemini Omni Flash**는 오늘부터 Gemini 앱, Google Flow, YouTube Shorts에서 사용 가능하다.

---

## SynthID: AI 콘텐츠 투명성 표준으로

딥페이크 탐지율이 약 25%에 불과한 현실에서 Google이 3년 전 출시한 SynthID(눈에 보이지 않는 AI 워터마크)가 업계 표준으로 자리잡고 있다. 현재까지 **1,000억 장** 이상의 이미지·영상, **6만 년** 분량의 오디오에 워터마킹이 완료됐다.

이번 I/O에서 **OpenAI, Kakao, Eleven Labs**가 SynthID 채택을 발표했다. Search·Chrome에도 Content Credentials 검증이 추가된다.

---

## 실무자가 볼 핵심 포인트

- **Gemini 3.5 Flash 즉시 사용 가능**: 3.1 Pro를 대체할 성능, Flash 가격으로
- **Gemini Omni Flash**: 영상 생성이 가능한 통합 멀티모달 모델, API 출시 임박
- **인프라 6배 투자**: Google의 AI 확장은 속도보다 지속성에 베팅하는 신호
- **SynthID 확산**: AI 생성 콘텐츠 식별이 사실상 업계 표준 워크플로가 될 가능성
- **에이전트 전환**: Search, YouTube, Docs, Maps 전체가 에이전트 인터페이스로 재설계되는 중

---

원문 : <a href="https://blog.google/innovation-and-ai/sundar-pichai-io-2026/">I/O 2026: Welcome to the agentic Gemini era — Google The Keyword</a>
