---
title: "Colab에서 QwenPaw 에이전트 워크스페이스 만들기 — 커스텀 스킬·멀티 프로바이더·스트리밍 API까지"
date: 2026-06-14T08:06:00+09:00
draft: false
description: "Colab 노트북 한 권으로 QwenPaw 에이전트 서버를 띄우고, 인증 콘솔·커스텀 스킬·OpenAI·DeepSeek·Gemini 멀티 프로바이더·스트리밍 REST API를 한 번에 붙이는 실전 튜토리얼을 한국어로 정리합니다."
cover:
  image: "/images/qwenpaw-agent-workspace-tutorial/source-hero.png"
  alt: "QwenPaw 에이전트 워크스페이스 튜토리얼 메인 이미지 — Marktechpost"
  caption: "이미지 출처: Marktechpost"
tags: ["QwenPaw", "AI 에이전트", "Colab", "스트리밍 API", "커스텀 스킬", "OpenRouter", "DashScope", "Cloudflare Tunnel"]
categories: ["LLM-info"]
---

## 개요

Marktechpost가 6월 13일에 올린 튜토리얼은 **QwenPaw**라는 에이전트 프레임워크를 Colab 한 권으로 끝까지 구동하는 방법을 다룹니다. 단순히 패키지 설치만 알려주는 글이 아닙니다. 인증이 걸린 웹 콘솔, 사용자 정의 스킬, 5개 모델 프로바이더 자동 선택, 스트리밍 REST API 테스트, 그리고 Cloudflare 임시 터널까지 한 노트북 안에서 다 묶었습니다.

읽고 보니 흥미로운 지점이 한두 군데가 아닙니다. 워크스페이스, 스킬, 프로바이더, 보안 가드를 어떤 폴더 구조로 분리해야 깔끔한지 보여주는 일종의 '레이아웃 레퍼런스'에 가깝습니다. AI 에이전트를 사내에 띄워보려는 팀이라면 이 노트북을 그대로 옮겨두기만 해도 시작점이 됩니다.

## 핵심 요약

- **Colab 한 권 = 풀스택 에이전트 서버**. 워킹 디렉터리·시크릿·로그·워크스페이스를 `/content/qwenpaw_colab` 아래에 분리합니다.
- **인증 콘솔 자동 셋업**. `secrets.token_urlsafe(18)`로 18자 비밀번호를 자동 생성, 파일에 한 번만 저장합니다. 재시작해도 그대로 씁니다.
- **프로바이더 5종 자동 선택**. OpenAI → OpenRouter → DashScope → DeepSeek → Gemini 순으로 키를 찾고, 먼저 발견된 한 곳만 활성화합니다.
- **스킬은 마크다운 한 장**. `SKILL.md` 하나로 에이전트 행동 규칙이 정의됩니다. 예시는 "research_brief" 스킬.
- **스트리밍은 SSE**. `/api/console/chat`에 POST하면 `data: ...` 라인이 흘러오고, 코드가 텍스트를 walking 방식으로 추출합니다.
- **선택적 공개 노출**. `cloudflared` 바이너리를 받아 임시 트라이클라우드 URL을 띄울 수 있습니다.
- **보안 가드 세 가지**. 툴 가드, 파일 가드, 스킬 스캐너가 기본 켜져 있고 모드는 `warn`입니다.

## 본문

### 디렉터리부터 명확히 갈라놓습니다

튜토리얼은 첫 셀에서 `ROOT = /content/qwenpaw_colab` 아래에 다섯 폴더를 만듭니다.

- `working/` — 설정·에이전트 정의
- `secrets/` — API 키와 프로바이더 자격 정보
- `logs/` — 앱 로그
- `working/workspaces/default/` — 에이전트의 작업 공간

여기서 중요한 부분은 환경 변수 세팅입니다. `QWENPAW_AUTH_ENABLED=true`, `QWENPAW_TOOL_GUARD_ENABLED=true`, `QWENPAW_SKILL_SCAN_MODE=warn`을 기본값으로 잡아두니, 처음부터 안전한 상태에서 출발합니다. 비밀번호는 `secrets/.colab_ui_password`에 저장되고 다음 실행에서도 재사용됩니다. 노트북을 다시 돌릴 때마다 새 비번을 외울 필요가 없다는 뜻입니다.

### 프로바이더는 키 하나만 있으면 됩니다

가장 마음에 든 부분이 모델 프로바이더 자동 선택입니다. 코드가 정해 둔 후보 순서대로 환경 변수와 Colab `userdata`를 둘 다 확인합니다.

1. `OPENAI_API_KEY` → OpenAI / `gpt-4o-mini`
2. `OPENROUTER_API_KEY` → OpenRouter / `openai/gpt-4o-mini`
3. `DASHSCOPE_API_KEY` → DashScope / `qwen-plus`
4. `DEEPSEEK_API_KEY` → DeepSeek / `deepseek-chat`
5. `GEMINI_API_KEY` → Google Gemini / `gemini-2.5-flash`

먼저 잡힌 키 하나가 곧장 활성 프로바이더가 됩니다. `secrets/providers/builtin/<id>.json`과 `active_model.json`에 동시에 기록되고, 에이전트 프로파일의 `active_model`에도 박힙니다. 즉 처음 한 번만 키를 넣어주면 다음부터는 노트북이 알아서 같은 모델을 끌어옵니다.

### 커스텀 스킬은 정말 마크다운 한 장입니다

`workspaces/default/skills/research_brief/SKILL.md` 파일 하나가 새 스킬 등록의 전부입니다. 본문에는 프런트매터(`name`, `description`)와 절차, 출력 스타일이 들어갑니다. 튜토리얼이 예시로 만든 `research_brief`는 다음 흐름을 갖습니다.

1. 사용자 목적을 한 문장으로 다시 쓰고
2. 핵심 엔티티·전제·제약을 짚고
3. 로컬 워크스페이스 파일부터 뒤지고
4. 검증된 사실과 추론을 분리해서
5. "답변 / 근거 / 위험 / 다음 단계" 4개 섹션으로 묶어 반환합니다.

코드 한 줄 없는 마크다운인데 에이전트의 응답 형태가 잡힌다는 게 핵심입니다. 사내 KB 분석, 상품 분석, 논문 요약 같은 반복 업무는 SKILL.md 폴더만 추가해 두면 됩니다.

### 서버는 `qwenpaw app`, 그리고 포트 폴링으로 헬스체크

서버 구동은 의외로 간결합니다. `qwenpaw app --host 0.0.0.0 --port 8088 --log-level info`를 `subprocess.Popen`으로 띄우고, PID를 파일에 적어 다음 실행에서 깔끔하게 회수합니다. 헬스체크는 `socket.create_connection()`을 1초 간격으로 120초까지 폴링합니다. 이 패턴은 Hugo, Streamlit, FastAPI 같은 다른 서버 띄울 때도 그대로 재활용할 수 있습니다.

### 공개 URL은 Cloudflare Tunnel로 30초 안에

`ENABLE_QWENPAW_TUNNEL=1`이면 `cloudflared` 바이너리를 자동으로 받아 트라이클라우드(`*.trycloudflare.com`) 임시 URL을 만들어줍니다. 튜토리얼 코드는 로그 파일에서 `https://...trycloudflare.com` 토큰을 직접 긁어서 출력합니다. 발표회·데모용으로 잠깐 공개할 때 부담이 적습니다. 단, 인증은 같은 사용자명/비번 그대로니까 공개 링크 = 누구나 시도 가능이라는 점을 잊지 말아야 합니다.

### 스트리밍 API: SSE를 안전하게 풀어내는 패턴

`qwenpaw_chat()` 함수는 `requests.post(..., stream=True)`로 SSE 라인을 읽습니다. `data:`로 시작하는 라인만 잡고, `[DONE]`을 만나면 종료합니다. 재미있는 부분은 응답 본문을 그대로 신뢰하지 않고 `walk()`라는 작은 재귀 함수로 `text`, `content`, `message`, `delta` 키를 전부 훑는다는 점입니다. 응답 스키마가 살짝 달라도 안 깨집니다. 모델 백엔드를 갈아끼울 때 자주 마주치는 골치를 미리 피해둔 셈입니다.

![QwenPaw 콘솔 스크린샷 — 출처 기사](/images/qwenpaw-agent-workspace-tutorial/source-console.png)

## 실무자가 볼 핵심 포인트

- **워크스페이스를 폴더 단위로 분리**하면, 에이전트가 자기 컨텍스트 안에서만 움직입니다. 사내 자료 유출 리스크가 줄어듭니다.
- **스킬 = SKILL.md**라는 규약은 코드를 새로 짜지 않고도 시나리오를 늘릴 수 있다는 뜻입니다. PM·도메인 전문가도 직접 행동 규칙을 정의할 수 있습니다.
- **프로바이더 자동 선택 로직**은 그대로 사내 도구에 옮겨도 좋습니다. 키 한 개로 시작하고, 추후 키가 바뀌어도 노트북·앱 코드를 건드리지 않아도 됩니다.
- **스트리밍 응답을 walk()로 추출**하는 패턴은 OpenAI·DeepSeek·Gemini가 서로 살짝 다른 SSE 스키마를 쓸 때 견고합니다. 직접 만든 챗 UI에 그대로 옮겨 쓸 수 있습니다.
- **보안 가드 3종을 끄지 마세요**. `tool_guard`, `file_guard`, `skill_scanner`는 기본값 그대로 둡니다. 운영 환경에서는 `skill_scan_mode`를 `block`으로 올리는 게 안전합니다.

## 원문 출처

- 원문: [How to Build a QwenPaw Agent Workspace with Custom Skills, Model Providers, Console Access, and Streaming API Testing](https://www.marktechpost.com/2026/06/13/how-to-build-a-qwenpaw-agent-workspace-with-custom-skills-model-providers-console-access-and-streaming-api-testing/) — Marktechpost, Sana Hassan, 2026-06-13
- 노트북 코드: [qwenpaw_agent_workspace_tutorial_Marktechpost.ipynb](https://github.com/MARKTECHPOST-AI-MEDIA-INC/AI-Agents-Projects-Tutorials/blob/main/Agentic%20AI%20Codes/qwenpaw_agent_workspace_tutorial_Marktechpost.ipynb)
- 프레임워크: [QwenPaw GitHub](https://github.com/agentscope-ai/QwenPaw)
