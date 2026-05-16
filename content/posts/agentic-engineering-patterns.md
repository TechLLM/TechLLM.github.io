---
title: "Agentic Engineering Patterns: AI 에이전트 시대의 소프트웨어 개발 패턴"
date: 2026-05-05
draft: false
tags: ["AI", "Agentic Engineering", "Software Development", "Claude Code", "TDD"]
categories: ["AI Insights"]
cover:
  image: "images/agentic-engineering-patterns-cover.jpg"
  alt: "Agentic Engineering Patterns - 4-panel comic showing AI-assisted development workflow"
description: "Simon Willison이 정리한 AI 코딩 에이전트 시대의 개발 패턴. Vibe Coding과 Agentic Engineering의 차이, 그리고 새로운 개발 디시플린에서의 핵심 패턴들을 소개합니다."
---

## AI가 코드를 써주는 시대, 우리는 어떻게 개발해야 할까?

Simon Willison이 최근 시작한 **Agentic Engineering Patterns** 프로젝트가 흥미롭습니다. 그는 AI 코딩 에이전트(Claude Code, OpenAI Codex 같은 도구들)를 활용해 소프트웨어를 만드는 새로운 디시플린을 **Agentic Engineering**이라고 정의했는데요, 이게 단순히 "AI한테 시켜서 코드 짜는 것"과는 결이 다릅니다.

## Agentic Engineering vs Vibe Coding

Simon은 두 개념을 명확히 구분합니다.

**Vibe Coding**은 원래 정의대로, 코드 자체에는 전혀 주의를 기울이지 않는 방식입니다. 보통 비개발자들이 LLM을 써서 코드를 만들 때 연관되는 스타일이죠.

반면 **Agentic Engineering**은 전문 소프트웨어 엔지니어가 코딩 에이전트를 사용해 자신의 전문성을 증폭시키고, 업무를 가속화하는 방식을 말합니다. 이건 "AI 대신 시키기"가 아니라, "AI와 협업해서 더 큰 결과 내기"에 가깝습니다.

## 왜 지금 이 패턴들이 필요할까?

코딩 에이전트의 결정적 특징은 **코드를 생성할 뿐만 아니라 실행까지 할 수 있다**는 점입니다. 즉, 인간의 턴바이턴 가이드 없이도 스스로 테스트하고 반복할 수 있죠.

이게 기존 개발 방식과는 완전히 다른 패러다임을 요구합니다. Simon은 이미 345개가 넘는 ai-assisted-programming 관련 포스트를 썼지만, 이제는 "이걸로 어떻게 좋은 결과를 얻지?"라는 질문에 한 번에 답할 수 있는 구조화된 패턴을 정리하려는 겁니다.

## 첫 두 가지 패턴

Simon이 공개한 첫 번째 챕터 두 개가 꽤 인상적입니다.

### 1. Writing code is cheap now (이제 코드 쓰기는 싸다)

가장 근본적인 도전입니다. 초기 작동 코드를 뽑아내는 비용이 거의 0에 수렴했어요. 그럼 우리의 직관은 어떻게 바뀌어야 할까요?

- 개인적으로나 팀 차원에서, "코드를 짜는 데 드는 노력"이 더 이상 병목이 아닙니다.
- 대신 **무엇을 만들지 결정하는 것**, **올바른 질문을 던지는 것**이 진짜 가치가 됩니다.
- "빨리 짜고 버리기"가 가능해지면서, 프로토타이핑과 검증의 속도가 압도적으로 빨라집니다.

### 2. Red/green TDD (테스트 주도 개발의 새로운 쓰임)

이건 정말 실무적인 인사이트입니다. 테스트를 먼저 작성하고(RED), 최소한의 코드로 테스트를 통과시키고(GREEN), 리팩토링하는 이 클래식한 TDD 방식이 **에이전트한테도 효과적**이라는 거죠.

- 에이전트에게 "이걸 구현해줘"라고만 하면, 종종 불필요하게 복잡한 코드를 내놓습니다.
- 하지만 "이 테스트를 통과하는 코드를 짜줘"라고 하면, 훨씬 간결하고 신뢰할 수 있는 결과가 나옵니다.
- 테스트가 명확한 가이드라인이 되어주니까요.

## Simon의 원칙: AI 글쓰기는 내 이름으로 안 해

Simon은 개인적인 정책으로 **자신의 이름으로는 AI가 생성한 글을 발행하지 않는다**고 못 박았습니다. 이 프로젝트도 마찬가지입니다.

- 교정, 예제 코드 보완, 기타 사이드 태스크에는 LLM을 쓰겠지만
- 실제 읽는 글은 **자신의 말**로 쓰겠다는 거죠.

이게 왜 중요하냐면, AI가 쓴 글은 정보는 줄 수 있어도 **경험과 맥락**은 주지 못하기 때문입니다. Agentic Engineering Patterns는 Simon의 실무 경험이 녹아있는 프로젝트니까요.

## "가이드"라는 새로운 형식

이 프로젝트는 책은 아니지만 책처럼 생겼습니다. Simon은 **Guide**라는 새로운 콘텐츠 형식을 도입했어요.

- 가이드는 여러 챕터로 구성
- 각 챕터는 블로그 포스트처럼 보이지만 날짜가 덜 강조됨
- 시간이 지나도 업데이트될 수 있는 "상록수(evergreen) 콘텐츠" 형태

이건 블로그에서 상록수 콘텐츠를 발행하려는 그의 오랜 고믨의 결과물입니다.

## 실무 개발자가 가져갈 점

1. **AI 에이전트는 도구지, 대체재가 아이다**: 전문성을 증폭시키는 용도로 써야 합니다.
2. **테스트가 더 중요해졌다**: 에이전트에게 명확한 가이드를 주는 방법입니다.
3. **의사결정 능력이 핵심이다**: 코드를 짜는 건 싸졌으니, "뭘 짤지" 고민하는 시간이 진짜 일이 됩니다.
4. **패턴을 익혀라**: 이런 새로운 디시플린에는 정해진 답이 없으니, 선구자들의 패턴을 배우는 게 지름길입니다.

Simon은 주 1-2개 챕터씩 꾸준히 추가할 계획이라고 합니다. 1994년의 "Design Patterns"가 객체지향 프로그래밍에 표준을 제시했듯, 2026년의 Agentic Engineering Patterns는 AI 에이전트 시대의 개발 표준을 제시할지도 모르겠네요.

---

**원문:** [Agentic Engineering Patterns - Simon Willison](https://simonw.substack.com/p/agentic-engineering-patterns)

**관련 태그:** #AI #AgenticEngineering #ClaudeCode #SoftwareDevelopment #TDD