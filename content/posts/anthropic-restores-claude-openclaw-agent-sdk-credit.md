---
title: "Anthropic, Claude 구독에서 OpenClaw 등 서드파티 에이전트 다시 허용 — 단, Agent SDK Credit이라는 catch"
date: 2026-05-14T12:05:00+09:00
draft: false
description: "Anthropic이 4월 초에 차단했던 OpenClaw·서드파티 에이전트의 Claude 구독 사용을 다시 허용했습니다. 단 일반 구독 풀이 아니라 'Agent SDK Credit'이라는 별도 풀에서 차감되고, rollover 없이 매월 소멸합니다. compute arbitrage 시대의 종결을 정확히 정리합니다."
author: "TechLLM"
tags: ["Anthropic", "Claude", "OpenClaw", "Agent SDK", "AI 정책", "Claude 구독", "프로그래매틱 AI", "AI 인프라"]
categories: ["AI·정책", "기술 분석"]
image: "/images/anthropic-claude-agent-sdk-credit-cover.png"
---

지난 4월 4일, Anthropic은 OpenClaw나 Conductor 같은 서드파티 에이전트가 Claude 구독으로 동작하는 것을 금지했습니다. 이유는 단순했습니다 — 한 달 $20 구독으로 수백 달러어치 토큰을 쓰는 사용자가 너무 많아 GPU 인프라가 못 버텼다는 것입니다. 그리고 약 한 달 만에 정책이 뒤집혔습니다. 단, 그냥 "다시 허용"이 아니라 새 카테고리 **Agent SDK Credit**을 통한 절충안입니다.

## 핵심 요약

- Anthropic이 OpenClaw·T3 Code·Conductor·Zed·Jean 같은 서드파티 에이전트 사용을 Claude 구독에서 다시 허용했습니다 (2026-05-13 @ClaudeDevs 발표).
- 다만 일반 구독 풀이 아니라 별도 **Agent SDK Credit**에서 차감됩니다. Pro $20 / Max 5x $100 / Max 20x $200 / Team·Enterprise는 좌석당 $100~$200.
- 이 크레딧은 **rollover 안 됨, 매월 소멸**. 다 쓰면 일반 구독 한도로 옮겨갈 수 없고 별도 사용 크레딧을 구매해야 합니다.
- Interactive(브라우저 채팅·Claude Code interactive)는 기존 구독 풀 그대로, **Programmatic**(`claude -p`, GitHub Action, OpenClaw 등 서드파티)만 새 풀에서 차감.
- 커뮤니티 반응은 부정적입니다 — "사용량 25배 감소를 free credits로 위장했다", "GPU 상황 나쁘다는 신호" 같은 평가가 X에서 확산.

## 무엇이 바뀌었나

4월 초 정책의 핵심은 "Claude 구독으로 서드파티 에이전트를 돌리는 것 금지"였습니다. 우회로는 두 가지였습니다 — API 키로 토큰 단위 종량 결제, 또는 구독 위에 추가 사용 크레딧 구매. 어느 쪽이든 "월 $20 정액으로 수백 달러 워크플로를 돌리던" 흐름은 끊겼습니다.

이번 변경은 그 흐름을 일부 복원합니다. Pro/Max/Team/Enterprise 모든 유료 구독자는 기존 구독비 그대로 두면서 **Agent SDK Credit이라는 추가 풀**을 받습니다. 이 풀로는 OpenClaw, Conductor 같은 서드파티 에이전트를 인증해 돌릴 수 있고, 결제는 API 요율로 차감됩니다.

Anthropic 측 Lydia Hallie의 X 포스트가 가장 간결한 요약이었습니다.

> "분명히 하자면, 추가 비용 없습니다. 같은 구독, 같은 월 가격."

그러나 모든 변경이 그렇듯 진짜 이야기는 디테일에 있습니다. 핵심 catch는 **rollover 안 됨**과 **별도 풀**이라는 두 줄입니다.

## Anthropic이 처음에 OpenClaw를 막았던 이유

복원의 의미를 이해하려면 4월 4일 차단의 기술적 배경을 봐야 합니다.

Anthropic의 자사 도구(Claude Code, Claude Cowork)는 **prompt cache hit rate**를 극대화하도록 설계되어 있습니다. 같은 컨텍스트를 여러 번 재사용해 비용을 줄이는 캐시 기법입니다. 정액 구독이 가능한 이유가 이 캐시에 있었습니다.

문제는 OpenClaw 같은 서드파티 도구가 이 캐시 흐름에 잘 맞지 않는다는 점이었습니다. Discord나 Telegram 같은 외부 채널 위에서 동작하면 캐시 키가 매번 달라지거나 무효화되기 쉽습니다. Head of Claude Code 보리스 체르니의 표현은 직설적이었습니다.

> "서드파티 서비스를 sustainably 하기 정말 어려웠다 — 그들은 우리가 정액 구독을 제공할 수 있게 해 주는 캐싱 메커니즘을 우회한다."

이 비효율은 GPU 공급량을 빠르게 갉아먹었습니다. Anthropic이 Colossus 1 데이터센터(300MW, 220,000+ GPU 액세스)까지 확장했지만, 에이전트형 워크플로 수요가 지속 가능한 공급을 추월했다는 게 회사의 설명입니다.

새 Agent SDK Credit 시스템은 이 병목을 정확히 사용자 비용으로 옮깁니다. 비효율적인 에이전트가 토큰을 빠르게 태우면, 그것은 Anthropic의 정액 구독 가치를 초과하는 게 아니라 **사용자의 $20~$200 크레딧을 빠르게 소진**시키는 형태가 됩니다.

## Agent SDK Credit — 플랜별 금액과 동작 방식

| 플랜 | 월 Agent SDK Credit | 용도 예시 |
|---|---|---|
| Pro | $20 | 개별 스크립트, 가벼운 SDK 사용 |
| Max 5x | $100 | 중간 규모 에이전트 자동화 |
| Max 20x | $200 | 전문가 개발 환경 |
| Team (Premium) | $100 / 좌석 | 협업 팀 자동화 |
| Enterprise (Premium) | $200 / 좌석 | 좌석 기반 대규모 엔터프라이즈 |

이 크레딧은 **추가 비용 없이** 기존 구독에 얹어 주는 것이지만, 핵심 제약이 둘 있습니다.

- **Non-rollover**: 매월 안 쓴 크레딧은 만료됩니다. "use it or lose it" 구조.
- **별도 풀**: 다 쓰면 일반 구독 한도로 넘어가지 못합니다. 추가 사용 크레딧을 구매해야 합니다.

요율은 Anthropic Developer Platform(API) 기준 — 토큰 백만당 가격이 그대로 적용됩니다. 즉 같은 작업이라도 캐시 활용을 잘하는 도구일수록 이 풀이 오래 갑니다.

## Interactive vs Programmatic — 왜 둘이 분리됐나

새 시스템의 또 다른 핵심은 사용 모드를 두 가지로 나눈 점입니다.

- **Interactive**: 브라우저에서 Claude와 채팅하거나, 터미널에서 Claude Code를 대화형으로 쓰는 경우. 기존의 큰 구독 풀에서 차감.
- **Programmatic**: `claude -p` 비대화형 명령, GitHub Action, OpenClaw 같은 서드파티 에이전트 연결. 새 Agent SDK Credit 풀에서 차감.

이 분리는 단순한 빌링 분리 이상의 의미를 가집니다. 사람이 직접 키보드 위에 손을 올려둔 사용은 자연히 caching이 잘 되고 컨텍스트도 작은 편입니다. 반면 에이전트는 긴 plan을 굴리고, 자동 retry로 같은 호출을 반복하며, 컨텍스트를 끊임없이 갱신합니다. 이 두 패턴의 GPU 비용 구조가 다르다는 사실을 가격에 직접 반영한 셈입니다.

전략적으로는 **compute arbitrage의 종결**입니다. 2026년 초만 해도 $20 Pro 구독을 OpenClaw에 연결해 수백 달러어치 API 가치를 끌어내는 흐름이 있었습니다. 이번 변경으로 그 차익 거래는 사실상 불가능해집니다. 구독 가치는 그대로 두되, programmatic 사용은 API와 동일한 종량제 위에 얹힙니다.

## 커뮤니티 반응 — "win처럼 포장한 사용량 25배 감소"

Anthropic 임원진은 이번 변경을 "단순화"로 표현했지만, 개발자 커뮤니티는 **구독 가치의 큰 하향 조정**으로 받아들였습니다.

- **Theo Browne (T3.gg, @theo)**: "Claude 구독을 T3 Code, Conductor, Zed, Jean 같은 외부 도구와 같이 쓰던 분이라면 사용량이 25배 감소할 겁니다. 이걸 'free credits'로 위장하지 마세요."
- **Kun Chen (전 Meta·Microsoft·Atlassian L8)**: "공식. Anthropic이 Claude 구독의 모든 프로그래매틱 사용을 끊었다." 그는 "Anthropic의 유일한 우위였던 코딩 성능을 GPT 5.5가 이미 뒤집었다"는 주장도 덧붙였습니다.
- **Ben Hylak (Raindrop.ai CTO)**: "이건 정말 어리석은 결정이거나, Anthropic의 GPU 상황이 얼마나 나쁜지 보여 주는 신호다. $20 API 크레딧이 몇 턴이나 갈 수 있을지 다들 한번 계산해 보시라."
- **EverNever (inkstone.uk)**: "잠깐 — 내가 돈 내는 구독을 활용할 수 있는 방법을 더 뺐으면서, 그걸 승리처럼 포장한다고?"

공통 정서는 명확합니다. Anthropic 입장에서 "기존 차단에 비하면 개선"이지만, 사용자 입장에서는 "차단 전 흐름의 일부 복원"에 그쳤다는 인식. 이 간극이 이번 발표 톤과 커뮤니티 반응 사이의 큰 차이를 만들고 있습니다.

## 실무자가 볼 핵심 포인트

- **OpenClaw·서드파티 에이전트 운영자에게는 차단보다 분명한 개선이다.** 4월 전면 금지보다 한 단계 풀린 셈. 단 비용 모델을 정액(구독)에서 종량(크레딧·API)으로 다시 짜야 한다.
- **캐싱 최적화 가치가 다시 커진다.** Agent SDK Credit은 API 요율이라 prompt cache hit rate가 곧 비용 차이로 직결된다. 자체 에이전트 하네스 운영자라면 캐시 친화적 컨텍스트 구조(고정 prefix·재사용 가능한 시스템 프롬프트)에 더 신경 쓸 가치가 있다.
- **6월 15일이 분기점.** 모든 Claude 구독자에 새 모델이 적용되는 마감일. 그 전에 비용 시나리오를 모델링해 두는 게 안전.
- **'Pro 구독으로 무한 에이전트'는 끝났다.** Pro $20 크레딧으로는 본격 자동화는 부족하다. Max 5x($100)나 그 이상으로 올리거나 API 키 직접 결제로 전환하는 판단이 필요하다.
- **GPU 인프라 신호로 읽을 가치도 있다.** Colossus 1까지 확장한 회사가 사용량 통제를 강화한다는 사실 자체가 산업 전반의 GPU 공급 상황을 보여 준다. 자체 추론 인프라를 검토 중인 조직이라면 이번 신호를 무시하기 어렵다.
- **경쟁 구도 변화 관찰.** 일부 헤비 개발자가 OpenAI나 다른 공급자로 옮길 가능성이 있다. 모델 락인 비용이 낮은 시점에 멀티 프로바이더 추론 라우터(예: OpenRouter, Together) 위에 워크플로를 얹는 전략이 유효해진다.

*원문: [Anthropic reinstates OpenClaw and third-party agent usage on Claude subscriptions — with a catch — VentureBeat](https://venturebeat.com/technology/anthropic-reinstates-openclaw-and-third-party-agent-usage-on-claude-subscriptions-with-a-catch)*
