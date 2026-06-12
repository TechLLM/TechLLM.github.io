---
title: "Perplexity Deep Research, Computer 위에 올라타다 — 20+ 모델 라우팅으로 리포트·덱·대시보드까지"
date: 2026-06-12T21:32:00+09:00
draft: false
description: "Perplexity가 Deep Research를 Computer 멀티모델 오케스트레이션에 통합했습니다. 20개 이상의 프런티어 모델 사이에서 서브태스크를 잘게 쪼개 라우팅하고, BrowseComp 정확도가 40.7%에서 83.8%로 두 배 가까이 뛰었습니다. 리포트·덱·대시보드를 인용까지 붙여서 한 번에 뽑아주는 구조입니다."
cover:
  image: "/images/perplexity-deep-research-computer-multi-model/perplexity-deep-research-computer-multi-model-cover.png"
  alt: "Perplexity Deep Research가 Computer 멀티모델 오케스트레이션 위에서 20개 이상의 프런티어 모델로 서브태스크를 라우팅하는 모습"
  caption: ""
tags: ["Perplexity", "Deep Research", "Perplexity Computer", "Multi-Model Routing", "BrowseComp", "Agentic Search", "Opus 4.6", "Agent API"]
categories: ["LLM-info"]
---

## 개요

Perplexity가 6월 11일에 큰 그림을 바꿨습니다. 2월 말에 공개한 멀티모델 오케스트레이션 시스템 **Computer** 위에 **Deep Research**를 통째로 올린 겁니다. 예전 Deep Research가 단일 흐름으로 검색하고 정리해 주는 도구였다면, 이번 버전은 질문을 잘게 쪼개서 **20개가 넘는 프런티어 모델**에 서로 다른 일을 시키는 구조입니다. 결과물도 그냥 글 한 편이 아니라 **리포트·브리프·덱·대시보드·라이브 스프레드시트**까지 인용을 박아서 한 번에 나옵니다.

성과 수치도 셉니다. 가장 까다로운 에이전트 브라우징 벤치마크인 **BrowseComp에서 40.7% → 83.8%**로 두 배가 넘게 올랐습니다. 사람이 검색창 여기저기 들쑤시고 다녀야 답이 나오는 종류의 문제에서 점프가 크다는 뜻입니다.

## 핵심 요약

- **무엇이 바뀌었나**: Deep Research가 별도 기능이 아니라, Computer라는 멀티모델 오케스트레이션 위에서 도는 한 가지 모드가 됐습니다.
- **모델 구성**: 핵심 추론은 **Opus 4.6**, 깊은 리서치 서브태스크는 **Gemini** 같은 전용 모델로 라우팅합니다. 총 **20+ 프런티어 모델**이 일을 나눠 갖습니다.
- **검색 방식**: "Search as Code". 질문마다 검색 실행 코드를 LLM이 직접 짜고, 그 코드가 **수천 단계의 검색·필터·중복 제거·재랭킹**을 병렬로 돌립니다.
- **출력 포맷**: 리포트, 브리프, 덱, 대시보드, 라이브 스프레드시트. 전부 **인라인 인용** 포함.
- **벤치마크**: Humanity's Last Exam **36.4% → 50.5%**, BrowseComp **40.7% → 83.8%**, DeepSearchQA **81.9% → 85.0%**.
- **접근**: 소비자는 **Perplexity Max** 구독, 개발자는 **Agent API**의 `deep-research` 프리셋(`POST /v1/agent`)으로 종량제.
- **데이터 소스**: PitchBook, CB Insights 같은 프리미엄 데이터셋 연동(법률 데이터는 프리뷰).

## 본문

### Search as Code — 왜 이 구조가 빠르고 정확한가

Perplexity가 이번에 강조한 키워드가 **Search as Code**입니다. 말 그대로 "검색을 코드로 짠다"는 뜻입니다. 사용자가 "올해 AI 칩 제조사 4곳 현금흐름과 마진을 비교해줘" 같은 질문을 던지면, 시스템이 먼저 **이 질문을 풀기 위한 검색 실행 코드를 즉석에서 작성**합니다. 그 코드는 Perplexity의 **Agentic Search SDK**가 제공하는 기본 블록 — 검색, 필터링, 중복 제거, 재랭킹 — 을 조립한 형태입니다.

그다음이 핵심입니다. 그 코드가 **수천 단계의 검색을 병렬**로 돌립니다. 단순히 "키워드 한 번 던지고 페이지 몇 개 받아오기"가 아닙니다. 질문에 맞춰 검색 경로 자체가 매번 다르게 짜이고, 거기서 나온 자료를 다시 LLM이 평가하고 추리는 순환을 빠르게 반복합니다. 결국 사람이 "검색 → 읽기 → 비교 → 추가 검색"을 머리로 돌리던 루프를, **코드가 대신 수천 번 돌려주는** 셈입니다.

### 멀티모델 라우팅 — 일은 잘하는 모델한테

Computer의 진짜 무기는 **모델 라우팅**입니다. 한 모델이 다 처리하지 않습니다. 작업 종류에 따라 다른 모델을 부릅니다.

- **법률 비교**: 법률 추론에 특화된 모델
- **숫자/표 다루기**: 스프레드시트와 데이터 처리에 강한 모델
- **최종 글쓰기**: 글쓰기에 강한 모델
- **깊은 리서치**: Gemini 계열 서브에이전트
- **전체 추론 엔진**: Opus 4.6

기준은 단순합니다. **잘하는 모델이 잘하는 일을 한다.** 이전에는 한 모델이 모든 단계를 책임지면서 가격과 속도가 같이 묶였다면, 이제는 단계별로 최적 모델을 골라 쓸 수 있게 된 겁니다. 비용은 종량제로 흘러갑니다.

### 벤치마크에서 진짜 의미 있는 숫자는 BrowseComp

발표된 벤치마크 셋은 세 개입니다.

| 벤치마크 | 출처 | 이전 Deep Research | Computer 버전 |
|---|---|---|---|
| Humanity's Last Exam | Center for AI Safety & Scale AI | 36.4% | **50.5%** |
| BrowseComp | OpenAI | 40.7% | **83.8%** |
| DeepSearchQA | Google DeepMind | 81.9% | **85.0%** |

DeepSearchQA는 이미 80%대였던 만큼 상승 폭이 크지 않고, Humanity's Last Exam은 약 14%p 올랐습니다. 진짜 눈에 띄는 건 **BrowseComp의 43.1%p 점프**입니다. BrowseComp는 답이 한 페이지에 떨어져 있지 않고, 여러 페이지를 거치며 단서를 모아야 하는 문제를 다룹니다. "사람이 직접 브라우징했을 때만 풀리던 종류의 문제"에서 두 배 가까이 오른 건 의미가 다릅니다.

다만 형님이 신뢰도를 따질 때 짚어 둘 게 있습니다. **이 숫자들은 모두 Perplexity가 자체 측정한 1자 벤치마크**입니다. 독립 기관 검증은 아직 없습니다.

### 어디에 어떻게 쓰나 — 네 가지 시나리오

Perplexity가 직접 든 사용 예시는 거칠지만 명확합니다.

- **금융**: 여러 해 치 현금흐름과 마진 비교 분석
- **법무**: 국가별 데이터 프라이버시 규제 비교 지도
- **헬스케어**: 임상시험 근거 자료 합성
- **테크**: 모델 벤치마크를 추론력·비용·컨텍스트 길이 기준으로 비교

공통점은 **출처가 흩어져 있고, 비교 축이 여러 개라서 한 번 만든 표가 곧장 보고서가 되는 종류의 일**이라는 점입니다. 라이브 스프레드시트와 대시보드 출력이 받쳐 주니까, "검색 → 표 → 슬라이드"로 가는 시간이 크게 줄어듭니다.

### 개발자가 붙이는 법 — Agent API의 `deep-research` 프리셋

개발자 입장에서는 진입점이 단순해졌습니다.

```python
from perplexity import Perplexity

client = Perplexity()
response = client.responses.create(
    preset="deep-research",
    input="Compare cash flow and profit margins of major AI chip makers."
)
```

엔드포인트는 `POST https://api.perplexity.ai/v1/agent`이고, 과금은 종량제입니다. 한 줄짜리 프리셋 호출로 위에 적은 멀티모델 라우팅 전체가 돌아갑니다. 내부 파일도 같이 읽을 수 있어서, 사내 문서와 웹 자료를 한 번에 묶어 인용을 박은 결과물을 만들 수 있습니다.

### 강점과 한계, 솔직하게

강점은 분명합니다.

- 질문당 **수천 단계의 병렬 검색**
- 에이전트 브라우징(BrowseComp) 기준 **두 배 가까운 정확도 향상**
- 내부 파일 + 라이브 웹을 한 번에, 인용 포함
- 결과물을 글로만 받지 않고 **덱·대시보드·스프레드시트로 받을 수 있는** 포맷 유연성

반대로 짚을 부분도 있습니다.

- 벤치마크가 **1자 측정**이라 독립 검증이 필요합니다.
- **Perplexity Max 구독자 전용**으로 무료 티어가 없습니다.
- 프리미엄 데이터 소스 커버리지가 분야마다 다릅니다(법률은 아직 프리뷰).
- 인용을 잘 박아도 **결과물은 사람이 검토**해야 합니다. 자동 보고서를 그대로 결재 라인에 올릴 수준은 아닙니다.

![BrowseComp 벤치마크 등에서의 Deep Research(Computer) 향상치를 보여주는 그래픽](/images/perplexity-deep-research-computer-multi-model/source-fig1.png)

## 실무자가 볼 핵심 포인트

- **리서치 워크플로**: "검색 → 표 정리 → 슬라이드" 루프가 잦은 직군이라면, 시간 절감 폭이 가장 큽니다. 금융·법무·전략 쪽에서 먼저 효과를 볼 가능성이 높습니다.
- **벤치마크 해석**: BrowseComp 점프(40.7% → 83.8%)가 가장 의미 있는 신호입니다. 단순 QA가 아니라 **다중 페이지 브라우징**을 잡았다는 뜻이라, 자동화 가능 영역이 한 단계 넓어졌습니다.
- **모델 선택 책임 이동**: 사용자가 모델을 고르지 않아도, Computer가 단계별로 라우팅합니다. 단점은 어떤 단계에서 어떤 모델이 도는지가 항상 투명하지는 않다는 점입니다.
- **개발 통합**: `deep-research` 프리셋 한 줄로 내부 문서 + 웹을 묶을 수 있어서, 사내 RAG에 외부 리서치를 얹는 패턴을 빠르게 시제품화할 수 있습니다.
- **검토 워크플로 필수**: 인용이 잘 박혀 있어도 결과물은 검수 대상입니다. 자동 발행이 아니라 **자동 초안 + 사람 검토** 흐름을 전제로 설계해야 합니다.
- **비용 모델**: Max 구독 또는 종량제 API. 자주 쓸수록 비용 변동이 크니, 운영 단계에서는 **호출당 평균 비용**을 미리 측정해 두는 게 안전합니다.

## 원문 출처

- MarkTechPost, "Perplexity Moves Deep Research Into Computer, Routing Research Subtasks Across 20+ Frontier Models For Reports, Decks, And Dashboards" (2026-06-11) — <https://www.marktechpost.com/2026/06/11/perplexity-moves-deep-research-into-computer-routing-research-subtasks-across-20-frontier-models-for-reports-decks-and-dashboards/>
