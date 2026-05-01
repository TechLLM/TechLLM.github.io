---
title: "TradingAgents: 금융 트레이딩을 멀티 에이전트로 나누면 무엇이 달라질까"
date: 2026-05-01T12:30:00+09:00
draft: false
description: "TauricResearch의 TradingAgents 저장소를 바탕으로, LLM 기반 멀티 에이전트 금융 트레이딩 프레임워크의 구조와 실무적 의미를 정리한다."
cover:
  image: "/images/tradingagents-cover.png"
  alt: "TradingAgents GitHub repository cover image"
  caption: "Source: TauricResearch/TradingAgents"
tags:
  - TradingAgents
  - AIAgent
  - MultiAgent
  - FinanceAI
  - LangGraph
  - LLM
categories:
  - AI Agent
  - 기술 인사이트
---

출처: TauricResearch / GitHub  
문서유형: 오픈소스 분석  
#TradingAgents #MultiAgent #FinanceAI #LangGraph

## 핵심 요약

TradingAgents는 금융 트레이딩 의사결정을 하나의 LLM에게 통째로 맡기지 않고, 실제 투자회사처럼 여러 역할의 에이전트로 나눠 처리하는 오픈소스 프레임워크입니다. GitHub 기준 5만 개가 넘는 star를 받은 프로젝트로, LLM 기반 금융 에이전트 구조를 살펴보기에 좋은 사례입니다.

중요한 점은 “AI가 종목을 맞힌다”가 아닙니다. 이 프로젝트는 투자 조언 도구라기보다, 복잡한 의사결정을 **전문 역할·토론·리스크 검토·최종 승인** 흐름으로 분해한 멀티 에이전트 아키텍처 예제에 가깝습니다.

![TradingAgents cover](/images/tradingagents-cover.png)

## 실제 트레이딩 조직을 에이전트로 모사한다

TradingAgents의 구조는 꽤 직관적입니다. 먼저 분석가 팀이 시장을 여러 관점에서 봅니다. Fundamentals Analyst는 재무와 기업 지표를 보고, Sentiment Analyst는 소셜·대중 정서를 분석합니다. News Analyst는 뉴스와 거시 이벤트를 살피고, Technical Analyst는 MACD나 RSI 같은 기술 지표를 해석합니다.

![TradingAgents framework schema](/images/tradingagents-schema.png)

이후 bullish researcher와 bearish researcher가 서로 다른 관점에서 분석 결과를 검토합니다. 단순히 “좋다/나쁘다”를 출력하는 것이 아니라, 찬성과 반대 논리를 구조적으로 부딪히게 만드는 방식입니다.

## Trader, Risk Manager, Portfolio Manager의 분리

TradingAgents에서 흥미로운 부분은 분석 이후의 흐름입니다. Trader Agent는 분석가와 연구자들의 보고서를 바탕으로 거래 판단을 구성합니다. 하지만 여기서 바로 실행하지 않습니다.

Risk Management 팀이 변동성, 유동성, 포트폴리오 위험을 다시 평가하고, 최종적으로 Portfolio Manager가 거래 제안을 승인하거나 거절합니다.

![TradingAgents analyst team](/images/tradingagents-analyst.png)

이 구조는 AI 에이전트 설계에서 중요한 교훈을 줍니다. 의사결정 시스템에서는 “생각하는 에이전트”와 “검토하는 에이전트”, “최종 승인하는 에이전트”를 분리해야 합니다. 특히 금융처럼 실패 비용이 큰 영역에서는 더 그렇습니다.

## v0.2.4에서 강화된 운영 기능

최근 v0.2.4 릴리스에서는 structured-output agents, LangGraph checkpoint resume, persistent decision log, DeepSeek·Qwen·GLM·Azure provider 지원, Docker, Windows UTF-8 수정 등이 추가되었습니다.

특히 decision log와 checkpoint resume은 실험용 에이전트를 운영형 시스템에 가깝게 만드는 기능입니다. 완료된 판단을 기록하고 다음 실행에서 같은 ticker의 과거 결정을 반영하며, 중간에 끊긴 LangGraph 실행을 마지막 성공 지점부터 이어갈 수 있습니다.

![TradingAgents risk management](/images/tradingagents-risk.png)

## 실무자가 볼 포인트

TradingAgents를 볼 때 가장 조심해야 할 점은 이것을 실제 투자 수익 도구로 과신하지 않는 것입니다. README에서도 연구 목적이며 투자 조언이 아니라고 명확히 밝힙니다. LLM, 온도 설정, 기간, 데이터 품질, 비결정성에 따라 결과는 크게 달라질 수 있습니다.

대신 아키텍처 관점에서는 배울 점이 많습니다. 복잡한 문제를 역할별 에이전트로 나누고, 서로 다른 관점을 토론시키고, 리스크 평가와 최종 승인 단계를 분리하는 구조는 금융뿐 아니라 법무, 보안, 리서치, 운영 자동화에도 그대로 응용할 수 있습니다.

좋은 멀티 에이전트 시스템은 에이전트를 많이 붙인다고 만들어지지 않습니다. 각 에이전트가 맡을 역할, 서로 넘길 산출물, 반대 의견을 다루는 방식, 최종 결정 권한이 명확해야 합니다. TradingAgents는 그 설계 감각을 보여주는 좋은 참고 사례입니다.

원문 : <a href="https://github.com/TauricResearch/TradingAgents">TauricResearch/TradingAgents</a>
