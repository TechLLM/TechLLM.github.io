---
title: "Agent Engineering: AI 에이전트를 정의하는 6가지 축"
date: 2026-05-01T12:15:00+09:00
draft: false
description: "Latent.Space의 Agent Engineering 글을 바탕으로, AI 에이전트를 구성하는 도구 사용, 목표 인코딩, 제어 흐름, 계획, 메모리, 위임 권한의 6가지 요소를 정리한다."
cover:
  image: "/images/latent-space-agent-engineering-impact.jpg"
  alt: "Agent Engineering IMPACT framework slide"
  caption: "Source: Latent.Space"
tags:
  - AgentEngineering
  - AIAgent
  - LLM
  - Planning
  - Memory
  - ToolUse
categories:
  - AI Agent
  - 기술 인사이트

---

출처: Latent.Space  
문서유형: 번역·해설  
#AgentEngineering #AIAgent #LLM #ToolUse #Memory

## 핵심 요약

Latent.Space의 「Agent Engineering」은 “에이전트가 무엇인가”라는 오래된 논쟁을 꽤 실용적인 방식으로 정리합니다. 핵심은 하나의 정의를 강요하는 것이 아니라, 사람들이 실제로 에이전트라고 부르는 시스템에 어떤 요소가 반복해서 등장하는지 보는 것입니다.

글은 이를 **IMPACT**라는 6가지 축으로 묶습니다. 도구를 쓰는 LLM, 목표와 평가 기준, LLM이 결정하는 제어 흐름, 다단계 계획, 장기 메모리, 그리고 위임된 권한입니다.

![Agent Engineering IMPACT framework](/images/latent-space-agent-engineering-impact.jpg)

## 에이전트 정의가 어려운 이유

AI 업계에서 “agent”라는 말은 자주 쓰이지만, 모두가 같은 뜻으로 쓰지는 않습니다. 어떤 사람은 도구를 쓰는 LLM만으로도 에이전트라고 부르고, 어떤 사람은 메모리와 계획, 자율 실행 권한까지 있어야 에이전트라고 봅니다.

OpenAI의 Agents SDK 정의는 모델, 지시문, 도구, 런타임을 강조합니다. 반면 Lilian Weng의 정의는 LLM, 메모리, 계획, 도구 사용을 강조합니다. 둘 다 맞지만, 빠지는 부분이 다릅니다.

![AI agent definitions comparison](/images/latent-space-agent-engineering-definitions.png)

그래서 이 글은 “정답 정의”보다 “현장에서 공통으로 등장하는 구성 요소”에 집중합니다.

## IMPACT: 에이전트 엔지니어링의 6요소

첫 번째는 **LLM with Tools**입니다. RAG, 검색, 브라우저, 샌드박스, 캔버스처럼 모델이 외부 세계와 연결되는 도구는 거의 모든 에이전트 정의의 공통분모입니다.

두 번째는 **Encoded Intent**입니다. 에이전트는 단순 응답기가 아니라 목표를 추구해야 합니다. 이 목표는 instruction, goal, eval, environment 같은 형태로 시스템 안에 인코딩됩니다.

세 번째는 **LLM-driven Control Flow**입니다. 정해진 workflow와 agent의 차이는 LLM이 어느 정도 실행 흐름을 결정하느냐에서 갈립니다. 모델이 다음 행동을 고를수록 더 agentic해집니다.

네 번째는 **Multi-step Planning**입니다. Deep Research, Devin, Manus 같은 시스템이 보여주듯, 실제 업무형 에이전트에는 수정 가능한 계획과 여러 단계의 실행 흐름이 필요합니다.

다섯 번째는 **Long-running Memory**입니다. 장기 작업을 수행하려면 과거 결정, 사용자 맥락, reusable workflow, skill library 같은 기억 구조가 필요합니다.

여섯 번째는 **Delegated Authority**입니다. 에이전트는 누군가를 대신해 행동합니다. 따라서 신뢰, 승인, 권한 범위, 검증 방식이 빠지면 “자율성”은 금방 불편한 확인 버튼 모음이 됩니다.

## 왜 지금 Agent Engineering인가

글은 에이전트 붐이 단순한 유행이 아니라 몇 가지 흐름이 겹친 결과라고 봅니다. reasoning model의 발전, structured output의 안정화, tool use benchmark 개선, MCP 같은 도구 연결 표준, 추론 비용 하락, 다중 모델 생태계가 동시에 움직이고 있습니다.

![ChatGPT growth and reasoning agent work](/images/latent-space-agent-engineering-growth.jpg)

또 하나의 중요한 관점은 “agent horizon”입니다. 모델이 안정적으로 수행할 수 있는 작업 시간이 점점 길어지고 있다는 주장입니다. 신뢰 가능한 작업 시간이 늘어날수록, 에이전트가 맡을 수 있는 업무 범위도 넓어집니다.

![Agent horizon benchmark](/images/latent-space-agent-engineering-horizon.jpg)

## 실무자가 볼 포인트

이 글의 좋은 점은 에이전트를 마케팅 단어가 아니라 엔지니어링 대상으로 본다는 데 있습니다. 에이전트를 만들 때 “도구를 붙였는가”만 볼 것이 아니라, 목표가 명확한지, 흐름을 누가 결정하는지, 계획이 수정 가능한지, 기억이 오래 유지되는지, 어떤 권한까지 위임할 수 있는지를 함께 봐야 합니다.

특히 기업 환경에서는 마지막 요소인 위임 권한이 중요합니다. 에이전트가 매번 확인만 요구하면 자동화 가치가 떨어지고, 반대로 아무 제약 없이 실행하면 위험합니다. 결국 좋은 에이전트는 자율성과 통제 사이의 경계를 설계한 시스템입니다.

Agent Engineering은 “프롬프트를 잘 쓰는 법”보다 더 넓은 문제입니다. 모델, 도구, 메모리, 계획, 평가, 권한을 하나의 제품 구조로 엮는 일입니다. 그래서 앞으로 에이전트 개발자는 프롬프트 작성자라기보다, 작은 소프트웨어 조직을 설계하는 아키텍트에 가까워질 가능성이 큽니다.

원문 : <a href="https://www.latent.space/p/agent">Agent Engineering</a>
