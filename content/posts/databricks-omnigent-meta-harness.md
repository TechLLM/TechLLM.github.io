---
title: "Databricks가 푼 Omnigent — Claude Code·Codex·Pi를 한 세션에 묶는 메타 하네스"
date: 2026-06-14T17:10:15+09:00
draft: false
description: "Databricks가 오픈소스로 공개한 Omnigent는 Claude Code, Codex, Pi 같은 코딩 에이전트를 하나의 인터페이스 아래로 끌어모으는 메타 하네스다. 세션 공유, 비용 정책, OS 샌드박스까지 한 자리에서 다룬다."
tags: ["Databricks", "Omnigent", "AI에이전트", "메타하네스", "ClaudeCode", "Codex", "Pi", "오픈소스", "AgentSDK"]
categories: ["AI · LLM"]
source_url: "https://www.marktechpost.com/2026/06/13/databricks-open-sources-omnigent-a-meta-harness-that-composes-governs-and-shares-ai-agents-across-claude-code-codex-and-pi/"
cover:
  image: /images/databricks-omnigent-meta-harness/databricks-omnigent-meta-harness-cover.png
  alt: "Omnigent 메타 하네스를 표현한 핸드드로잉 일러스트"
  caption: "Generated illustration"
---

## 개요

Claude Code, Codex, Pi를 동시에 띄워 놓고 작업해 본 적이 있다면 익숙한 풍경이 있습니다. 한쪽 창에서 코드를 받고, 다른 창에 붙여 넣고, 다시 검색 도구로 옮겨가는 식의 반복 노동이죠. Databricks가 6월 13일 공개한 오픈소스 프로젝트 **Omnigent**는 이 문제를 정면으로 다룹니다. 여러 에이전트를 갈아끼울 수 있는 부품처럼 두고, 그 위에 한 겹을 더 얹어 작업·정책·협업을 한 자리에서 처리하자는 발상입니다. 라이선스는 Apache 2.0이고, 알파 단계로 풀렸습니다.

## 핵심 요약

- **Omnigent는 “메타 하네스”**입니다. Claude Code, Codex, Pi 같은 개별 하네스를 한 단계 위에서 묶고, 셋 다 같은 인터페이스로 다루도록 만듭니다.
- 모델·하네스·기법을 **한 줄짜리 변경으로 교체**할 수 있습니다. 코드를 다시 짜지 않아도 워커가 바뀝니다.
- **상태를 기억하는 정책 레이어**가 들어 있습니다. 비용이 100달러 넘으면 멈추고, npm 패키지 설치 직후 git push는 사람 승인 없이는 못 나가게 막는 식입니다.
- **세션 자체를 URL로 공유**합니다. 동료가 같은 세션에 붙어 코드에 코멘트하거나, 흐름을 포크해서 다른 방향을 시도할 수 있습니다.
- Polly(병렬 오케스트레이터)와 Debby(Claude+GPT 두 머리 브레인스토밍) 같은 **예제 에이전트**가 같이 들어 있어 패턴을 바로 따라해 볼 수 있습니다.

## 하네스 위에 또 하나의 층을 얹다

하네스는 모델을 감싸서 에이전트로 만들어 주는 껍질입니다. Claude Code, Codex, Pi가 대표적이죠. 문제는 엔지니어 한 명이 보통 네다섯 개를 동시에 굴린다는 점입니다. 코딩 에이전트 결과를 검색 도구에 다시 넣고, 그걸 Docs와 Slack으로 옮기는 일이 종일 이어집니다. 각 하네스는 자기 세션만 이해하니, 흐름은 사람이 직접 손으로 이어 붙여야 합니다.

Omnigent는 그 위에 공통의 한 층을 깝니다. 메시지와 파일을 받고, 텍스트와 툴 호출을 내보내는 인터페이스는 어차피 비슷합니다. 그러니 하네스 안에서 모델을 어떻게 부르든 상관없이, 바깥쪽은 똑같이 다루자는 겁니다. 결과적으로 하네스가 **부품**이 됩니다. 모델과 인프라는 사용자가 가져오고, 그 위에서 Omnigent가 여러 에이전트를 워커로 동시에 굴립니다.

![Omnigent 메타 하네스 스크린샷](/images/databricks-omnigent-meta-harness/source-screenshot.png)

## 작동 방식 — 러너와 서버

구조는 단순합니다. **러너**가 어떤 에이전트든 샌드박스 세션으로 감싸 통일된 API를 노출합니다. **서버**는 정책과 공유를 맡습니다. 세션 하나는 터미널, 데스크톱 앱, 모바일, 웹 API에서 동일하게 보입니다. 명령 한 번에 터미널에서 세션이 뜨고, 동시에 localhost:6767에 로컬 웹 UI도 같이 켜집니다. 핸드폰으로 같은 세션을 열어도 메시지·서브 에이전트·터미널·파일이 한쪽으로 어긋나지 않습니다.

CLI는 `omnigent`과 `omni` 두 이름으로 깔리는데 같은 명령입니다. 처음 실행할 때 환경에 이미 깔린 모델 자격증명을 알아서 잡습니다.

## 세 가지 핵심 — 조합·통제·협업

Databricks 팀은 이 프로젝트의 가치를 세 단어로 정리합니다.

**조합(Composition)**. 모델·하네스·기법을 코드 수정 없이 갈아끼우는 능력입니다. Claude Code에서 Codex, Pi, 직접 만든 에이전트로 옮겨가는 데 한 줄이면 됩니다.

**통제(Control)**. 프롬프트로 “하지 마세요”라고 부탁하는 방식이 아니라, 하네스 바깥에서 상태를 들고 있는 정책으로 막습니다. 누적 비용이 100달러를 넘기면 잠시 멈추거나, 에이전트가 새로 npm 패키지를 설치한 직후의 `git push`는 사람 승인을 받아야만 통과시키는 식입니다. 이 규칙은 서버 전체, 에이전트별, 세션별로 쌓을 수 있고 더 엄격한 쪽이 이깁니다.

**협업(Collaboration)**. 세션 URL을 던지면 동료가 같은 화면에 붙습니다. 옆에서 지켜보고, 채팅으로 끼어들고, 파일에 코멘트를 답니다. 마음에 들지 않으면 세션을 포크해서 다른 방향으로 끌고 갈 수도 있습니다. 복사-붙여넣기로 흐름이 끊기던 협업 방식이 사라지는 셈입니다.

이 모든 동작을 받쳐주는 게 **Omnibox** 샌드박스입니다. OS 접근을 통제하고, 네트워크 요청을 가로채 변형합니다. 예컨대 GitHub 토큰을 에이전트에게 직접 노출하지 않고, 승인된 요청에 한해 egress 프록시에서만 주입할 수 있습니다.

## 같이 들어 있는 예제 에이전트

저장소에는 두 가지 예제가 함께 풀려 있습니다.

- **Polly**는 코드를 직접 쓰지 않는 오케스트레이터입니다. 계획을 세우고, 병렬 git worktree에서 코딩 서브 에이전트들에게 일을 나눠 던집니다. 각 diff는 작성자와 다른 벤더의 리뷰어에게 자동으로 넘어갑니다. 결과만 받아 머지하면 끝입니다.
- **Debby**는 머리 두 개짜리 브레인스토밍 파트너입니다. 한쪽은 Claude, 다른 쪽은 GPT. 질문 하나에 두 답을 나란히 보여 주고, `/debate`를 치면 서로 반박을 주고받다가 결론을 좁힙니다.

이 패턴을 살짝 비틀면 응용이 넓어집니다. 비싼 프런티어 모델이 가이드를 잡고 값싼 오픈소스 모델이 작업을 처리하게 한다거나, 계획·검색·코드 생성 단계마다 다른 LLM을 붙이는 흐름도 같은 구조로 가능합니다.

## 설치와 커스텀 에이전트

설치 요건은 Python 3.12 이상, Node.js 22 LTS, tmux입니다. 한 줄로 끝납니다.

```bash
curl -fsSL https://omnigent.ai/install.sh | sh
omni setup
```

자격증명은 네 가지를 받습니다. 자체 API 키, Claude/ChatGPT 구독, OpenAI·Anthropic 호환 게이트웨이, Databricks 워크스페이스입니다. 세션 도중 `/model` 명령으로 모델을 갈아탈 수 있습니다.

커스텀 에이전트는 짧은 YAML 파일 하나입니다. 프롬프트, 사용할 하네스, 도구, 서브 에이전트를 선언하고 `omnigent run`으로 실행합니다. 정책도 같은 방식으로 YAML에 적습니다. 비용 5달러를 하드 캡으로 두고 3달러에서 한 번 묻게 만드는 식의 구성이 기본 예제로 제공됩니다.

## 실무자가 볼 핵심 포인트

**플랫폼 엔지니어**라면 “에이전트 하나에 종속되지 않는 인터페이스”라는 그림이 가장 매력적입니다. 사내에서 모델·하네스가 자주 바뀌는 환경이면, 워커 교체 비용을 한 줄로 줄이는 효과가 큽니다.

**보안·거버넌스 담당자**는 정책 레이어가 프롬프트 바깥에 있다는 점을 눈여겨봐야 합니다. “부탁하는” 가드레일이 아니라 상태를 들고 있는 규칙이라, 비용 상한·승인 흐름·민감 토큰 격리를 감사 가능한 형태로 남길 수 있습니다.

**개발팀 리드**가 챙겨 볼 부분은 Polly 패턴입니다. 작성자와 다른 벤더가 리뷰하는 구조는, 단일 모델의 버릇을 다른 모델이 잡아 주는 자연스러운 견제 장치가 됩니다.

**연구·실험 조직**은 Debby처럼 두 모델을 나란히 굴리며 토론시키는 패턴을 그대로 갖다 쓸 수 있습니다. 단일 모델 답에 의존하지 않고 가설을 흔드는 데 적합한 도구입니다.

다만 알파 단계라는 점은 잊지 말아야 합니다. Omnigent Server의 MCP 지원 같은 로드맵 항목은 아직 들어오지 않았고, 사외망 팀은 서버를 직접 띄워야 합니다. 모델과 인프라도 가져와야 하니, 곧바로 프로덕션에 얹기보다 내부 PoC로 시작하는 편이 안전합니다.

## 원문 출처

*원문: [Databricks Open-Sources Omnigent: a Meta-Harness that Composes, Governs, and Shares AI Agents Across Claude Code, Codex, and Pi](https://www.marktechpost.com/2026/06/13/databricks-open-sources-omnigent-a-meta-harness-that-composes-governs-and-shares-ai-agents-across-claude-code-codex-and-pi/) — Asif Razzaq, MarkTechPost (2026-06-13)*
