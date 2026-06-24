---
title: "LangChain Fleet가 범용 채팅과 전문 에이전트를 둘 다 두는 이유"
date: 2026-06-24T14:20:00+09:00
draft: false
description: "한 번 쓰고 끝나는 일과 매주 돌아오는 일은 다른 도구가 필요하다. LangChain Fleet이 General Purpose Chat과 Specialized Agents를 분리한 이유, 그리고 두 모드를 어떻게 갈아 쓰는지 정리."
tags: ["LangChain", "Fleet", "AI에이전트", "에이전트설계", "LangSmith"]
cover:
  image: /images/langchain-fleet-general-chat-specialized-agents/langchain-fleet-general-chat-specialized-agents-cover.png
  alt: "일회성 채팅과 반복 업무용 전문 에이전트의 분리"
---

## 개요

에이전트에게 일을 시키다 보면 두 가지 패턴이 보입니다. 하나는 즉흥적인 부탁이고, 다른 하나는 매주 같은 방식으로 돌아오는 반복 업무입니다. LangChain의 Brace Sproul이 2026년 6월 16일 공개한 글에서 정확히 이 분리를 다룹니다. Fleet에는 General Purpose Chat과 Specialized Agents가 따로 있는데, 같은 채팅창에 둘을 욱여넣지 않는 데에는 이유가 있습니다.

![Fleet의 두 가지 에이전트 모드](/images/langchain-fleet-general-chat-specialized-agents/fleet-agent-types.png)

## 핵심 요약

- 에이전트 업무는 일회성(ad hoc)과 반복(recurring) 두 갈래로 나뉩니다.
- 둘 다 채팅 한 스레드로 처리하면 매번 프롬프트와 컨텍스트를 다시 만들어야 합니다.
- Fleet은 General Purpose Chat으로 일회성을, Specialized Agents로 반복 업무를 처리합니다.
- Specialized Agents는 지시문, 도구, 모델, 서브에이전트, 트리거, 메모리를 고정해 둡니다.
- 가장 큰 차이는 메모리 — 스레드 단위 컨텍스트와 작업 단위 영속 메모리.

## 채팅 한 스레드로 다 처리하면 왜 깨지는가

대부분의 AI 제품은 모든 요청을 일회성 채팅처럼 다룹니다. 짧은 질문에는 충분합니다. 그런데 같은 일이 매주 반복되면 얘기가 달라집니다. 프롬프트를 매번 다시 짜고, 컨텍스트를 다시 모으고, 채팅 스레드 하나를 운영 프로세스처럼 굴리게 됩니다. 결국 그 일이 어떻게 돌아가는지 아는 사람이 한 명만 남는 상황이 옵니다.

Fleet이 두 모드를 분리한 이유는 이겁니다. 일의 모양에 도구를 맞추자는 것이죠.

## General Purpose Chat — 준비 없이 던질 수 있는 일

휴가 일주일 다녀와서 Slack 스레드, GitHub PR, Linear 티켓, 캘린더 초대를 한꺼번에 따라잡아야 한다고 해봅시다. 도구 여러 개를 넘나들어야 하고, 판단도 필요하고, 결과물은 긴 요약이거나 다음 액션 목록일 겁니다. 그런데 이 작업 자체는 다음 주에 똑같이 다시 하지 않습니다.

이런 일이 General Purpose Chat의 영역입니다. 어떤 도구를 쓸지, 어떤 프롬프트를 줄지 미리 정하지 않고 그냥 부탁하면 됩니다. 워크스페이스 통합을 그대로 쓰고, 파일 시스템으로 컨텍스트를 관리하고, 코드·파일·데이터 분석처럼 실제 환경이 필요할 때는 가상 컴퓨터를 붙입니다. 스레드가 끝나면 그 일도 끝납니다.

![General Purpose Chat의 흐름 — 일회성 요청, 도구 자동 선택, 스레드 종료](/images/langchain-fleet-general-chat-specialized-agents/general-purpose-chat-flow.png)

## Specialized Agents — 반복 업무에 거처를 마련해 주는 것

반복되는 일은 더 단단한 셋업이 필요합니다. 매주 월요일에 돌아오는 플래닝 업데이트, 인박스 정리, 고객 리서치 브리프, 백로그 점검 같은 작업이죠. 이런 일을 매번 다른 사람이 기대치를 다시 설명해야 한다면 운영이 사람에 묶입니다.

플래닝 에이전트라면 매주 월요일에 Linear를 훑어 무엇이 출시됐는지 정리하고, 막힌 작업을 표시하고, 팀이 쓰는 양식으로 초안을 만들어 둡니다. 인박스 에이전트라면 새 메일을 분류하고 초안을 잡고 고객 이슈는 에스컬레이션하면서, 어떤 메일은 형님이 직접 처리하고 싶어 하는지 기억합니다.

Specialized Agents는 다음을 직접 정의합니다.

- **지시문(Instructions)** — 역할, 판단 기준, 출력 포맷, 에스컬레이션 규칙, 경계.
- **도구(Tools)** — 그 업무에 필요한 도구만 골라 붙입니다. 잡다한 권한을 주지 않습니다.
- **모델(Models)** — 메인 에이전트와 서브에이전트마다 모델을 따로 고를 수 있습니다. 슈퍼바이저는 계획·리뷰용 강한 모델을 쓰고, 좁은 서브태스크는 가벼운 모델로 처리하는 식입니다.
- **서브에이전트(Subagents)** — 자기만의 지시문·도구·모델을 가진 전문가를 호출 가능한 형태로 둡니다. 컨텍스트가 무거운 작업을 서브로 떼어내면 메인 에이전트의 컨텍스트가 오염되지 않습니다.
- **스킬(Skills)** — 회사 전체가 공유하는 워크스페이스 스킬과 그 에이전트 전용 비공개 스킬을 같이 씁니다. 반복 업무에 재사용 가능한 지식 베이스를 붙이는 셈입니다.
- **트리거와 스케줄(Triggers & Schedules)** — Slack, Gmail, Outlook, Teams 같은 도구의 이벤트나 정해진 시간에 자동 실행됩니다. Gmail 트리거는 새 메일마다 실행하고, 스케줄은 매일 아침이나 매주로 돌립니다.
- **Computer Access** — 진짜 환경이 필요할 때 컴퓨터를 붙입니다. General Purpose Chat에서는 스레드별로 활성화하지만, Specialized Agent에서는 에이전트 환경의 일부로 두고 스레드 간 컨텍스트 유지가 필요하면 단일 Computer를 공유하도록 설정할 수 있습니다.

![Specialized Agent의 흐름 — 트리거, 도구, 서브에이전트, 메모리가 한 셋업에 묶인다](/images/langchain-fleet-general-chat-specialized-agents/specialized-agent-flow.png)

## 가장 큰 차이는 메모리

General Purpose Chat의 컨텍스트는 스레드 단위입니다. 스레드 안에서 일어난 일을 기억하고, 스레드가 끝나면 그 일도 함께 끝납니다.

Specialized Agents의 메모리는 업무 단위로 살아 있습니다. 사실을 기억하고, 시간이 지나면 갱신하고, 다음 실행에서 다시 설명해 줄 필요가 없습니다.

Linear 티켓을 관리하고 GitHub PRs를 지켜보는 PM 에이전트를 예로 들어 봅시다. 시간이 지나면 이 에이전트는 한 엔지니어가 백엔드 이슈를 선호한다는 것, 다른 엔지니어는 티켓을 잘게 쪼개길 원한다는 것, 형님이 릴리스 차단 버그는 즉시 에스컬레이션을 원한다는 사실을 학습합니다. 이런 사실이 매주 월요일에 누군가 다시 쓰는 프롬프트에 들어 있을 일이 아닙니다. 에이전트의 작업 메모리가 되어야 할 정보입니다.

이 지점이 Specialized Agent를 "저장된 채팅"과 다르게 만듭니다. 지시문은 안정적으로 고정되어 있지만, 메모리는 일의 변화에 따라 진화합니다.

## 언제 어떤 모드를 쓸까

판단 기준은 일의 난이도가 아니라 모양입니다. 일회성 작업도 복잡할 수 있고, 반복 작업도 단순할 수 있습니다. 핵심은 "이 작업이 재사용 가능한 패턴인가"입니다.

| 구분 | General Purpose Chat | Specialized Agent |
|---|---|---|
| 적합한 일 | 일회성, 탐색적, ad hoc | 반복·스케줄·이벤트 기반 |
| 셋업 | 없음, 요청부터 시작 | 지시문·도구·스킬·모델·트리거 구성 (AI가 도와주거나 직접 구성) |
| 도구 | 워크스페이스 통합 전체 | 그 업무용 도구로 한정 |
| 서브에이전트 | 범용 서브에이전트 | 자체 모델·도구·프롬프트를 가진 커스텀 서브에이전트 |
| 스킬 | 워크스페이스 스킬 | 워크스페이스 스킬 + 비공개 에이전트 스킬 |
| 메모리 | 스레드 단위 컨텍스트 | 업무 단위 영속 메모리 + 스레드 컨텍스트 |
| Computer Access | 스레드별 활성화 | 에이전트 환경에 포함, 스레드별/에이전트별 선택 |

요약하면 — 일이 넓거나 임시적이면 General Purpose Chat, 반복적으로 위임하고 싶은 책임이 되면 Specialized Agent입니다.

## 실무자가 볼 핵심 포인트

이 분리는 단순한 UI 결정이 아닙니다. 팀이 에이전트를 도입할 때 자주 빠지는 함정 — "모든 걸 한 채팅창에 욱여넣다가 사람만 남는 시나리오" — 를 막는 구조적 장치입니다.

**시작은 가볍게, 굳어지면 위임하라.** General Purpose Chat에서 캐치업·리서치·요약·CSV 분석·답장 초안 같은 일을 던지다가, 같은 패턴이 자꾸 돌아오면 Fleet이 그걸 Specialized Agent로 굳혀 줍니다. 지시문·도구·스킬·트리거·서브에이전트·메모리가 한 번에 셋업됩니다. 그 시점부터 "그 일을 어떻게 시키는지 아는 사람"에 의존하지 않게 됩니다.

**메모리 설계가 곧 에이전트 설계다.** 매번 다시 알려줘야 하는 정보가 늘어나면 그 일은 Specialized Agent로 옮길 신호입니다. 반대로 한 번 쓰고 잊어도 되는 정보까지 영속 메모리에 쌓으면 에이전트가 무거워집니다. 메모리 스코프는 일의 수명과 맞춰야 합니다.

**서브에이전트로 컨텍스트를 나눠라.** 메인 에이전트의 컨텍스트가 오염되면 판단이 흐려집니다. 컨텍스트가 무거운 작업은 자기 메모리·모델·도구를 가진 서브에이전트로 떼어내는 것이 LangChain이 권장하는 패턴입니다.

도입을 검토 중이라면 [Fleet 무료 체험](https://smith.langchain.com/agents?skipOnboarding=true)에서 직접 두 모드를 비교해 볼 수 있고, [LangSmith Fleet 문서](https://docs.langchain.com/langsmith/fleet)에서 기술적인 세부 사항을 확인할 수 있습니다.

## 원문 출처

[원문 보기](https://www.langchain.com/blog/why-fleet-has-both-general-purpose-chat-and-specialized-agents) — Brace Sproul, LangChain Blog (2026-06-16)
