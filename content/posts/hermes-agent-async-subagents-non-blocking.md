---
title: "Hermes Agent, 비동기 서브에이전트로 부모 채팅이 더 이상 멈추지 않는다"
date: 2026-06-16T20:59:00+09:00
draft: false
description: "Nous Research가 Hermes Agent에 비동기 서브에이전트 기능을 추가했습니다. 위임한 작업이 백그라운드에서 돌아가는 동안 부모 채팅은 그대로 살아 있고, 도중에 지시를 끼워 넣거나 결과만 모아오는 것도 가능해졌습니다. 어떻게 동작하는지, 동기 모드와 뭐가 다른지 정리했습니다."
cover:
  image: "/images/hermes-agent-async-subagents-non-blocking/hermes-agent-async-subagents-non-blocking-cover.png"
  alt: "Hermes Agent 비동기 서브에이전트 개념 일러스트"
  caption: "Hand-drawn cover for Hermes Agent async subagents"
tags: ["Hermes Agent", "Nous Research", "서브에이전트", "AI 에이전트", "비동기 위임"]
categories: ["AI"]
source_url: "https://www.marktechpost.com/2026/06/16/hermes-agent-adds-asynchronous-subagents-so-delegated-work-no-longer-blocks-the-parent-chat/"
ShowToc: true
TocOpen: false
---

## 개요

지금까지 Hermes Agent에서 서브에이전트한테 일을 시키면, 그 일이 끝날 때까지 부모 채팅은 그대로 얼어 있었습니다. 리서치 한 건 던져 놓고 그 사이에 다른 질문을 이어가고 싶어도 방법이 없었죠. 이번 업데이트는 정확히 이 문제를 해결합니다. `delegate_task_async`로 일을 넘겨 두면 백그라운드에서 돌아가고, 그 동안 부모 채팅에서는 다른 작업을 그대로 진행할 수 있습니다.

![Hermes Agent 비동기 서브에이전트 안내 이미지](/images/hermes-agent-async-subagents-non-blocking/source-hero.png)

## 핵심 요약

- Nous Research가 Hermes Agent에 `async_delegation` 툴셋을 추가했습니다. 부모 채팅을 멈추지 않고 서브에이전트에게 일을 위임할 수 있게 됐습니다.
- 핵심 도구는 여섯 가지입니다. `delegate_task_async`, `check_task`, `steer_task`, `collect_task`, `cancel_task`, `list_tasks`로 위임-감시-개입-회수-취소가 가능합니다.
- 각 서브에이전트는 부모와 완전히 분리된 환경에서 돕니다. 대화 히스토리도, 터미널 세션도, 툴셋도 따로입니다. 부모에는 최종 요약만 돌아옵니다.
- 동기 모드는 빠른 fan-out에, 비동기 모드는 오래 걸리는 작업에 적합합니다. 같은 세션 안에서만 살아있다는 한계는 아직 남아 있습니다.
- 기존 사용자는 `hermes update` 한 줄로 곧바로 사용할 수 있습니다.

## 본문

### 부모 채팅이 멈추던 옛날 방식

기존 동기 위임은 단순합니다. `delegate_task`를 호출하면 자식 에이전트가 전부 끝날 때까지 부모는 그 안에서 대기합니다. 채팅창은 한 줄도 더 나가지 않습니다. 한꺼번에 여러 자식을 띄울 수는 있지만 동시 실행 수는 `delegation.max_concurrent_children`(기본값 3)로 막혀 있습니다.

빠르게 갈래 나누고 결과만 받아오면 되는 작업, 예를 들어 "이 폴더 안 파일 다섯 개를 동시에 요약해" 같은 fan-out에는 이쪽이 더 깔끔합니다. 어차피 결과가 곧 오니까 굳이 부모를 풀어줄 이유가 없죠. 문제는 "10분짜리 리서치"처럼 시간이 좀 걸리는 일을 시킬 때입니다. 그 사이에 다른 이야기를 하고 싶어도 방법이 없습니다.

### 새로 들어온 비동기 툴셋

이번 업데이트(GitHub issue #5586)는 동기 도구는 그대로 두고 비동기 짝을 추가하는 방식입니다. 핵심 도구만 추리면 이렇습니다.

- `delegate_task_async`: 백그라운드 자식 에이전트를 띄우고 `task_id`만 즉시 돌려줍니다. 호출은 바로 끝납니다.
- `check_task`: 블로킹 없이 현재 상태와 최근 출력 일부만 들여다봅니다.
- `steer_task`: 돌아가는 도중에 지시를 끼워 넣습니다. "이번엔 2024년 이후 자료만 보라"는 식으로요.
- `collect_task`: 자식이 끝날 때까지 기다렸다가 전체 결과를 가져옵니다.
- `cancel_task`: 진행 중인 작업을 중단시킵니다.
- `list_tasks`: 지금 세션에서 살아 있는 비동기 작업 목록을 확인합니다.

코드로 보면 차이가 더 분명합니다. 동기 방식은 호출이 끝나야 다음 줄로 넘어가지만,

```python
delegate_task(tasks=[
    {"goal": "Research topic A", "toolsets": ["web"]},
    {"goal": "Fix the build", "toolsets": ["terminal", "file"]},
])
```

비동기 방식은 던져 놓고 다른 일을 하다가 필요할 때 결과를 모읍니다.

```python
t1 = delegate_task_async(goal="Research topic A")
t2 = delegate_task_async(goal="Research topic B")
check_task(t1["task_id"])
steer_task(t2["task_id"], "Use post-2024 sources only")
results = [collect_task(t["task_id"]) for t in (t1, t2)]
```

### 서브에이전트는 깨끗하게 따로 산다

비동기든 동기든, 자식 에이전트의 격리 모델은 똑같습니다. 자식은 부모의 대화 히스토리를 못 봅니다. 터미널 세션도 따로 갖고, 툴셋도 따로 받습니다. 부모로 돌아오는 건 최종 요약 한 덩어리뿐입니다. 부모 컨텍스트가 자식 작업 로그로 도배되는 일이 없으니 길게 가는 대화에서 토큰 관리가 한결 편해집니다.

내부적으로는 같은 `AIAgent` 머신을 in-process 스레드로 재사용합니다. API 키, 프로바이더 설정, 레이트 리밋 분산용 자격증명 풀까지 부모 것을 그대로 물려받습니다. 새 프로세스를 띄우는 게 아니라서 시작이 빠른 대신, 지속성은 한정적입니다. 현재 비동기 작업은 같은 세션 안에서만 유효합니다. 채팅을 닫으면 사라지죠. 세션 사이를 넘어가는 영속화는 GitHub issue #4949의 ACP(Agent Continuation Protocol)에서 따로 다루는 중입니다.

### 어디에 잘 맞나

세 가지 시나리오가 곧바로 떠오릅니다.

먼저 "오래 걸리는 리서치를 끼고 다른 일 하기"입니다. 시장 조사 한 건을 백그라운드에 던져 두고, 본 채팅에서는 발표 초안을 잡습니다. 끝나면 `collect_task`로 결과만 끌어옵니다.

다음은 "병렬 접근법 평가"입니다. 같은 질문을 검색 백엔드 세 개에 동시에 던지고, 자식들이 서로 영향 받지 않는 상태로 각자 답을 만들게 둡니다. 컨택스트 오염 없는 깨끗한 A/B/C 비교가 됩니다.

마지막은 "백그라운드 코딩"입니다. 여러 파일을 건드리는 리팩터링을 자식에게 맡기고, 부모는 다른 파일 리뷰를 계속합니다. 진행 상황은 `/agents` 오버레이(별칭 `/tasks`)에서 트리 형태로 한눈에 봅니다.

## 실무자가 볼 핵심 포인트

- 일의 성격에 따라 동기/비동기를 골라 쓰세요. 결과를 바로 모아야 하는 fan-out이면 동기, 분 단위 이상 걸리는 작업이면 비동기가 낫습니다.
- `steer_task`는 의외로 강력합니다. 위임만 하고 손 떼는 게 아니라, 중간에 방향을 잡아 줄 수 있다는 점이 동기 모드에는 없는 장점입니다.
- 자식 에이전트의 격리 모델 덕분에 부모 컨텍스트가 깨끗하게 유지됩니다. 장기 대화에서 토큰 비용을 아끼고 싶다면 적극적으로 위임을 분리하세요.
- 세션을 닫으면 비동기 작업이 사라진다는 점은 운영 관점에서 분명한 한계입니다. ACP가 들어오기 전까지는 "같은 창에서 끝까지 본다"는 전제가 필요합니다.
- 도입 비용은 거의 없습니다. `hermes update` 한 줄이면 끝이고, 기존 동기 도구는 그대로 살아 있으니 점진적으로 옮겨가도 됩니다.

## 원문 출처

[원문 보기](https://www.marktechpost.com/2026/06/16/hermes-agent-adds-asynchronous-subagents-so-delegated-work-no-longer-blocks-the-parent-chat/) — Michal Sutter, MarkTechPost, 2026-06-16
