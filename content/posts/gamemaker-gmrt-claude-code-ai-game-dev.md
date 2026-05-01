---
title: "GameMaker 2026, Claude Code와 GMRT로 게임 개발 워크플로우를 바꾸다"
date: 2026-05-01T19:20:00+09:00
draft: false
description: "GameMaker가 새 런타임 GMRT와 GM-CLI, Claude Code 통합을 공개했다. 2D 게임 엔진이 IDE 중심 도구에서 CLI·AI 보조·자동화 가능한 개발 플랫폼으로 이동하는 흐름을 짚어본다."
cover:
  image: "/images/gamemaker-gmrt-claude-code-cover.svg"
  alt: "GameMaker GMRT, GM-CLI, Claude Code가 연결된 게임 개발 워크플로우 일러스트"
  caption: "GameMaker 2026 update: GMRT, GM-CLI, Claude Code"
tags:
  - GameMaker
  - ClaudeCode
  - Anthropic
  - GMRT
  - GameDev
  - AICoding
  - LLM
categories:
  - AI Coding
  - Game Dev
---

출처: Outlook Respawn / Opera Newsroom  
문서유형: 뉴스 해설  
#GameMaker #ClaudeCode #GMRT #AICoding #GameDev

## 핵심 요약

GameMaker가 2026년 봄 업데이트에서 **GMRT(GameMaker Runtime)**와 **GM-CLI**, 그리고 **Anthropic Claude Code 통합**을 공개했습니다. 겉으로는 “게임 엔진에 AI가 붙었다”는 뉴스처럼 보이지만, 실제 의미는 조금 더 큽니다.

GameMaker는 오랫동안 2D 게임을 빠르게 만드는 친근한 엔진으로 인식됐습니다. 그런데 이번 업데이트는 그 방향을 **IDE 중심의 쉬운 제작 도구**에서 **CLI, Git, 자동화, AI 보조가 가능한 개발 플랫폼**으로 넓히는 신호에 가깝습니다.

![GameMaker GMRT Claude Code](/images/gamemaker-gmrt-claude-code-cover.svg)

## Claude Code는 어디에 들어가나

이번 통합의 핵심은 Claude Code가 GameMaker의 새 명령줄 도구인 **GM-CLI** 안에서 동작한다는 점입니다. 개발자는 터미널에서 자연어로 프로젝트 구조를 묻고, 버그를 추적하고, 빌드 설정을 다룰 수 있습니다.

예전에는 메뉴를 찾아가거나 IDE 안에서 직접 설정해야 했던 작업을 이제는 “이 빌드 설정 왜 깨졌는지 봐줘”, “이 프로젝트 구조 설명해줘”처럼 요청할 수 있는 셈입니다. 흔히 말하는 vibe coding을 게임 개발 쪽 워크플로우에 끌어오는 움직임입니다.

![GM-CLI Claude Code Flow](/images/gamemaker-gmrt-claude-code-flow.svg)

## GMRT가 더 중요한 이유

다만 이 소식의 중심은 AI만이 아닙니다. **GMRT**는 GameMaker가 더 큰 팀과 복잡한 프로젝트를 수용하기 위한 새 런타임입니다. Opera 발표에 따르면 GMRT는 데스크톱에서 먼저 제공되고, 이후 모바일·웹까지 source-available 접근이 확대될 예정입니다.

또 프로젝트 파일이 plain text에 가까워지고, Git과 CI 자동화에 더 잘 맞게 바뀌는 점도 중요합니다. 이 변화가 있어야 Claude Code 같은 AI 개발 에이전트도 프로젝트를 읽고, 수정하고, 빌드 흐름에 개입하기 쉬워집니다.

## 언어 확장과 3D 개선

GameMaker의 기존 언어인 GML은 유지됩니다. 대신 2026년 안에 JavaScript, TypeScript, C# 지원이 추가될 예정입니다. 이는 기존 GameMaker 사용자뿐 아니라 웹·앱·엔터프라이즈 개발 경험이 있는 개발자도 팀에 합류하기 쉽게 만드는 변화입니다.

3D 처리도 강화됩니다. GameMaker가 완전한 3D 엔진으로 바뀐다는 뜻은 아니지만, Blender의 glTF 모델 로딩, scene graph, 3D 수학 처리 개선은 2D 중심 엔진의 표현 범위를 넓혀줍니다.

## 실무자가 볼 포인트

이번 업데이트는 “AI가 게임을 대신 만들어준다”는 이야기가 아닙니다. 더 현실적인 변화는 **반복 작업을 CLI와 AI에 넘기고, 사람은 설계와 판단에 집중하는 개발 방식**입니다.

특히 작은 팀이나 1인 개발자에게는 프로젝트 이해, 버그 탐색, 빌드 설정 같은 잡무를 줄이는 효과가 있을 수 있습니다. 반대로 프로 스튜디오 입장에서는 GameMaker를 Git, 자동화 파이프라인, 다언어 팀 구조에 더 자연스럽게 넣을 수 있는지가 관건입니다.

## 정리

GameMaker의 Claude Code 통합은 단순한 AI 기능 추가가 아니라, 게임 엔진이 개발 도구 생태계 전체와 다시 연결되는 흐름입니다. 앞으로 게임 개발 도구의 경쟁력은 에디터 기능만이 아니라 **CLI, 소스 접근성, 자동화, AI 에이전트 친화성**에서 갈릴 가능성이 큽니다.

GameMaker가 이번 업데이트로 Unity나 Unreal과 같은 대형 엔진을 정면으로 따라잡는다고 보기는 어렵습니다. 하지만 2D 게임 제작 영역에서는 “가볍게 시작해서, 팀 단위 개발까지 확장하는 엔진”이라는 포지션을 더 분명히 만들고 있습니다.

원문 : <a href="https://respawn.outlookindia.com/gaming/gaming-news/gamemaker-launches-gmrt-brings-anthropics-claude-ai-to-game-dev">GameMaker Launches GMRT & Brings Anthropic's Claude AI to Game Dev</a>  
참고 : <a href="https://press.opera.com/2026/04/30/gamemaker-gmrt/">GameMaker launches GMRT: The runtime professional developers have been waiting for</a>
