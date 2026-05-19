---
title: "GPT-Realtime-2, 이제 목소리로 GPT-5급 추론을 한다"
date: 2026-05-07T22:00:00+09:00
draft: false
description: "OpenAI가 실시간 음성 API에 GPT-5급 추론 모델 GPT-Realtime-2, 70개 언어 동시통역 모델, 스트리밍 전사 모델 세 가지를 동시 공개했다."
cover:
  image: "/images/openai-realtime-voice-cover.jpg"
  alt: "GPT-Realtime-2 voice intelligence models"
  caption: "Generated illustration"
tags:
  - OpenAI
  - 음성AI
  - GPT-Realtime-2
  - 실시간번역
  - Whisper
  - API
  - LLM
  - 음성인터페이스
  - AI 트렌드 & 산업
  - LLM & 모델
categories: ["AI-LLM"]
summary: "GPT-Realtime-2(GPT-5급 추론), GPT-Realtime-Translate(70개 언어 동시통역), GPT-Realtime-Whisper(스트리밍 전사). 2026년 5월 7일 OpenAI가 실시간 음성 API에 세 가지 신모델을 출시했다. 음성 인터페이스가 단순 응답을 넘어 실제 업무를 처리하는 에이전트 수준으로 올라간다."
---

## 핵심 요약

2026년 5월 7일, OpenAI가 실시간 음성 API에 세 가지 신모델을 공개했다.

| 모델 | 핵심 기능 |
|------|-----------|
| **GPT-Realtime-2** | GPT-5급 추론 탑재, 128K 컨텍스트, 조절 가능한 추론 강도 |
| **GPT-Realtime-Translate** | 70개 언어 → 13개 언어 실시간 동시통역 |
| **GPT-Realtime-Whisper** | 말하는 동안 실시간 스트리밍 전사 |

세 모델의 공통 목표는 하나다. 음성 인터페이스가 단순한 질의응답을 벗어나 실제 업무를 수행하는 수준으로 올라가는 것.

---

## GPT-Realtime-2: 목소리로 하는 GPT-5급 추론

### 기존 모델과의 차이

GPT-Realtime-1.5까지는 빠른 응답속도에 초점이 맞춰져 있었다. GPT-Realtime-2는 여기에 **추론 능력**을 더했다. 복잡한 요청도 대화를 이어가면서 처리할 수 있다.

주요 신기능은 다음과 같다:

- **Preambles(선행 발화)**: "잠깐 확인해볼게요"처럼 처리 중임을 알리는 짧은 문구를 자동으로 삽입해, 침묵 없이 자연스러운 대화 흐름을 유지
- **병렬 도구 호출 + 투명성**: 여러 도구를 동시에 실행하면서 "캘린더 확인 중입니다", "지금 검색하고 있어요" 같은 상태 발화로 사용자에게 진행 상황 안내
- **강화된 복구 동작**: 처리 실패 시 침묵이나 오류 대신 "지금 당장은 어렵네요" 같은 자연스러운 대처
- **컨텍스트 128K 확장**: 기존 32K에서 128K로 확장, 장시간·복잡한 에이전트 세션 지원
- **도메인 어휘 강화**: 의료, 법률, 기술 용어와 고유명사 처리 정확도 향상
- **톤 제어**: 문제 해결 시 차분하게, 사용자가 불편할 때 공감적으로, 성공 확인 시 활기차게 — 상황에 따른 어조 자동 조절
- **추론 강도 선택**: `minimal / low / medium / high / xhigh` 5단계. 기본값은 `low`(저지연). 복잡한 요청에는 `high` 이상을 선택

### 벤치마크

| 지표 | 향상 폭 |
|------|---------|
| Big Bench Audio (high) | GPT-Realtime-1.5 대비 **+15.2%** |
| Audio MultiChallenge (xhigh) | GPT-Realtime-1.5 대비 **+13.8%** |
| Zillow 가장 어려운 내부 벤치마크 | 콜 성공률 **69% → 95%** (+26 포인트) |

Zillow는 GPT-Realtime-2를 적용해 "복잡한 음성 인터랙션에서 지능과 도구 호출 신뢰도가 눈에 띄게 올랐다"고 평가했다. 특히 부동산 서비스에서 민감한 공정주택법(Fair Housing) 준수율도 함께 향상됐다고 밝혔다.

---

## GPT-Realtime-Translate: 실시간 동시통역

70개 이상 입력 언어를 13개 출력 언어로 실시간 번역한다. 각자 자신이 편한 언어로 말하고 상대방 언어로 즉시 듣는 구조다.

실제 활용 패턴:

- **글로벌 고객 지원**: 고객이 자신의 언어로 말하면 상담원 언어로 번역(Deutsche Telekom 테스트 중)
- **온라인 강의 및 이벤트**: 별도 더빙 없이 글로벌 청중에게 실시간 제공(Vimeo 시연)
- **다언어 음성 에이전트**: 한 에이전트가 여러 언어 사용자를 동시 지원

BolnaAI(인도)는 힌디어, 타밀어, 텔루구어 평가에서 **타 모델 대비 단어 오류율(WER) 12.5% 감소**를 확인했다고 밝혔다. 지역 방언과 도메인 특화 언어 처리가 강점이다.

---

## GPT-Realtime-Whisper: 스트리밍 전사

말하는 도중 실시간으로 텍스트를 생성하는 저지연 전사 모델이다.

활용 시나리오:

- 회의, 강의, 방송 중 자막 즉시 표시
- 대화가 진행되는 동안 메모·요약 실시간 생성
- 고객 지원, 의료, 영업, 채용 등 고빈도 음성 업무의 후속 처리 자동화

---

## 음성 AI 3가지 패턴

OpenAI는 이번 출시와 함께 개발자들이 구축하는 음성 AI 패턴을 세 가지로 정리했다.

**1. Voice-to-Action** — 사용자가 말로 요청하면 시스템이 추론하고 도구를 쓰고 작업을 완료한다.
- 예: "BuyAbility 범위 내에서 조용한 거리 주택을 찾고 토요일 투어 예약해줘" (Zillow)

**2. Systems-to-Voice** — 시스템이 상황을 분석해 사용자에게 음성으로 능동적으로 알려준다.
- 예: "연결 항공편은 탈 수 있어요. 최단 경로 안내드릴게요" (여행 앱)

**3. Voice-to-Voice** — AI가 언어 간 실시간 통역으로 대화를 이어준다.
- 예: 독일어 사용자와 한국어 사용자가 각자 모국어로 대화 (Deutsche Telekom)

---

## 가격

| 모델 | 단가 |
|------|------|
| GPT-Realtime-2 입력 | $32 / 1M 오디오 토큰 (캐시 적중 시 $0.40) |
| GPT-Realtime-2 출력 | $64 / 1M 오디오 토큰 |
| GPT-Realtime-Translate | $0.034 / 분 |
| GPT-Realtime-Whisper | $0.017 / 분 |

---

## 개발자가 가져갈 점

- **추론 강도(reasoning effort) 파라미터**가 생겼다. 단순 응답엔 `low`, 복잡한 에이전트 작업엔 `high/xhigh`를 선택해 지연-품질 트레이드오프를 직접 제어할 수 있다.
- **Preambles + 병렬 도구 호출**이 결합되면 사용자가 느끼는 체감 지연이 크게 줄어든다. 실제 처리 시간보다 응답이 "빠른 것처럼 느껴지는" UX 설계가 가능하다.
- 컨텍스트가 32K → 128K로 늘어나면서 **멀티턴 에이전트 세션**을 음성으로 구현하는 데 실질적 한계가 낮아졌다.
- 번역과 전사를 API에서 별도 모델로 분리한 만큼, **파이프라인 비용 최적화**가 가능해졌다. 전사만 필요하면 Whisper, 번역만 필요하면 Translate를 사용하면 된다.

---

**원문**: [Advancing voice intelligence with new models in the API](https://openai.com/index/advancing-voice-intelligence-with-new-models-in-the-api/) — OpenAI (2026-05-07)
