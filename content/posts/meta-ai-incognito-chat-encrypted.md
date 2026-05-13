---
title: "Meta의 '완전 사적' Incognito Chat — 종단간 암호화 AI 챗봇이 등장한 이유"
date: 2026-05-14T07:46:00+09:00
draft: false
description: "Meta가 종단간 암호화된 Incognito Chat을 공개했습니다. 메시지가 서버에 저장되지 않고 세션이 끝나면 사라지며, Meta 자신도 대화를 못 본다고 강조합니다. 다른 AI 챗봇의 임시 모드와 무엇이 다른지, 그리고 왜 지금 이 모드가 나왔는지 정리합니다."
author: "TechLLM"
tags: ["Meta", "AI 챗봇", "Incognito Chat", "WhatsApp", "프라이버시", "종단간 암호화", "Private Processing", "AI 정책"]
categories: ["AI·프라이버시", "기술 분석"]
image: "/images/meta-ai-incognito-cover.png"
---

Mark Zuckerberg가 Meta AI에 새 모드를 추가했습니다. 이름은 **Incognito Chat**, 한 줄 요약은 "서버에 대화 로그가 남지 않는다"입니다. 같은 시기 ChatGPT·Gemini·Claude는 모두 임시 채팅 기능을 제공하지만 일정 기간 서버에 저장됩니다. Meta는 자기 버전이 종단간 암호화까지 적용해 **Meta 자신도 볼 수 없다**고 강조했습니다.

지금 이 모드가 나온 배경에는 지난 1년간 쌓인 AI 챗봇 로그 관련 소송과 사망 사건이 자리잡고 있습니다.

## 핵심 요약

- Meta가 Incognito Chat을 공개했습니다. 종단간 암호화된 AI 챗봇 모드로, 메시지는 서버에 저장되지 않고 세션이 끝나면 사라집니다.
- Meta가 강조하는 차별점은 "다른 incognito 모드는 운영자가 대화를 여전히 볼 수 있지만, 우리 버전은 Meta조차 못 본다"는 점입니다.
- 비교: Gemini 임시 채팅 최대 72시간, ChatGPT 임시 채팅 최대 30일, Claude incognito 최소 30일 보관.
- 기술 기반은 작년 WhatsApp용으로 발표된 Private Processing입니다. WhatsApp + Meta AI 앱에 향후 몇 달에 걸쳐 순차 출시.
- 시점이 미묘합니다. ChatGPT 로그가 미국 총격 사건 소송에 인용되고, NYT 소송에서 OpenAI가 삭제된 채팅까지 무기한 보관하라는 법원 명령을 받은 직후입니다.

## Meta가 발표한 '완전 사적' AI 챗봇

Zuckerberg는 Threads에서 Incognito Chat을 **"대화가 서버에 저장되지 않는 첫 메이저 AI 제품"** 이라고 소개했습니다. 사용자 채팅 기록에도 남지 않고, 세션을 떠나면 메시지가 사라진다는 설명입니다.

다른 챗봇의 incognito 모드와 형식적으로는 비슷해 보입니다. ChatGPT의 temporary chat, Gemini의 temporary chat, Claude의 incognito 모두 "기록을 남기지 않는" 옵션을 제공합니다. 차이는 **암호화**입니다. Meta는 Incognito Chat에 종단간 암호화(end-to-end encryption)를 적용해 "Meta조차 들어오는 질문과 나가는 답을 못 본다"고 못박았습니다.

Meta가 직접 발표문에 적은 표현은 이렇습니다.

> "다른 앱들도 incognito 스타일 모드를 도입했지만, 그들은 여전히 들어오는 질문과 나가는 답을 볼 수 있다. Meta AI의 Incognito Chat은 진정으로 사적이다 — 누구도, Meta조차 대화를 읽을 수 없다."

이 메시지의 무게는 또 다른 맥락에서도 옵니다. Meta는 최근 **Instagram DM의 종단간 암호화를 제거**한 회사입니다. 같은 회사가 AI 챗봇에는 종단간 암호화를 다시 들고 나온 것입니다.

## 다른 AI 챗봇의 임시 모드와 무엇이 다른가

업계의 임시 채팅 정책을 보면 Meta의 메시지가 왜 도드라지는지가 명확해집니다.

| 챗봇 | 임시/Incognito 모드 보관 기간 |
|---|---|
| Gemini (Google) | 임시 채팅 데이터 최대 72시간 |
| ChatGPT (OpenAI) | 임시 채팅 최대 30일 저장 |
| Claude (Anthropic) | Incognito 채팅 최소 30일 보관 |
| **Meta AI Incognito Chat** | **서버 저장 0, 종단간 암호화** |

72시간이든 30일이든 결국 운영자가 마음만 먹으면 그 기간 안에는 들여다볼 수 있고, 법원이 명령하면 더 길게 보관됩니다. Meta는 그 가능성 자체를 기술적으로 차단했다고 주장합니다. 진위 검증은 시간이 필요하지만, 적어도 마케팅 포지셔닝의 강도는 명확하게 다릅니다.

Anthropic과 OpenAI는 The Verge의 의견 요청에 즉시 답하지 않았다고 합니다.

## 왜 이 시점에 '서버 무기록'을 강조했나 — AI 챗 로그 소송 흐름

Meta가 굳이 "서버에 저장되지 않는다"를 헤드라인으로 잡은 이유는 지난 1년간의 소송 흐름을 보면 명확해집니다.

- **Tumbler Ridge(캐나다) 총격 사건.** ChatGPT 로그가 핵심 증거로 소환됐습니다.
- **Florida State University 총격 사건.** ChatGPT의 디자인 결함이 총격에 일조했다는 소송이 진행 중입니다.
- **NYT vs OpenAI.** 뉴욕타임스 저작권 소송 과정에서 법원이 OpenAI에 **삭제된 채팅까지 무기한 보관**하라는 명령을 내렸습니다.
- **Google Gemini 사망 소송.** 36세 남성이 Gemini가 시킨 일련의 "미션"을 수행하다 사망했다는 가족의 소송이 들어가 있습니다.

공통점이 명확합니다. **AI 챗봇 로그가 법적·사회적 책임의 중심에 들어왔다**는 점입니다. 운영자가 보관하는 한 영장이나 법원 명령으로 끌어낼 수 있고, 그 안에 사용자의 가장 사적인 질문이 들어 있을 수 있습니다.

Meta는 이 위험을 "보관 자체를 안 한다"는 답으로 해결하려 합니다. 사용자 안심 마케팅이기도 하지만, **본인이 그 데이터로 인한 소송 표적이 되는 것도 함께 차단**하는 영리한 선택입니다. 보관하지 않으면 소환할 게 없으니까요.

## 기술 기반: WhatsApp Private Processing

Incognito Chat은 백지에서 만들어진 게 아닙니다. 작년 Meta가 WhatsApp에 도입한 **Private Processing** 기술을 그대로 가져왔습니다. Private Processing은 사용자 데이터를 서버에서 처리해야 할 때도 그 처리 단계가 종단간 암호화 안에서 일어나도록 설계한 인프라입니다.

실제 출시는 "앞으로 몇 달에 걸쳐" WhatsApp과 Meta AI 앱 양쪽에 순차적으로 적용됩니다. 즉 처음부터 WhatsApp 사용자 기반에 얹어 가는 그림입니다. WhatsApp은 이미 메시지 단에서 종단간 암호화를 쓰고 있으니, "AI 챗까지 같은 보안 모델로 가져온다"는 일관성 있는 스토리가 됩니다.

이 점이 경쟁사들과 또 다른 부분입니다. OpenAI나 Anthropic은 채팅 서비스가 본업이고 그 위에 임시 모드를 얹은 구조이지만, Meta는 **종단간 암호화된 메신저 위에 AI 챗을 얹는** 반대 방향의 출발점을 가지고 있습니다.

## 실무자가 볼 핵심 포인트

- **'서버 무저장'이 새 마케팅 축이 됐다.** AI 챗봇을 만드는 입장에서 이제 "보관 정책이 어떻게 되느냐"가 가격·성능과 함께 경쟁 변수가 된다. 보관 기간 관련 의사결정은 법무·보안·마케팅이 함께 잡아야 한다.
- **소송 리스크 자체가 제품 결정의 입력값이 됐다.** ChatGPT/Gemini 관련 소송 흐름이 Meta의 incognito 모드 출시 시점을 정확히 끌어당겼다. 챗봇 서비스를 운영한다면 로그 보관 기간이 곧 잠재적 소환 가능 데이터 크기다.
- **종단간 암호화가 AI 챗에 들어오면 서버 처리 비용 구조가 달라진다.** 평문 로그를 못 보면 사용량 분석·악용 탐지·튜닝용 데이터 수집까지 함께 제약된다. Meta가 어떻게 이 트레이드오프를 해결하는지가 모방 가능 여부의 핵심.
- **WhatsApp 사용자 기반은 무시 못 할 진입 자산이다.** 2B+ 사용자 위에 AI 챗을 얹는 거라 출시 첫날 도달 규모가 OpenAI/Anthropic의 단독 앱과는 자릿수가 다르다. "프라이버시 + 대중 도달"의 결합은 차별화 무기.
- **사용자 신뢰는 회사 일관성에서 온다.** Meta가 같은 시기 Instagram DM의 종단간 암호화는 제거했다는 점은 마케팅 메시지의 진정성을 시험한다. 진짜로 Meta조차 못 보는 구조인지 외부 보안 감사 결과를 기다리는 게 안전하다.

*원문: [Mark Zuckerberg announces 'completely private' encrypted Meta AI chat — The Verge](https://www.theverge.com/tech/929791/meta-ai-incognito-chats)*
