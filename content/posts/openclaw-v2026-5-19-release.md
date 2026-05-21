---
title: "OpenClaw v2026.5.19 출시 — 개인 AI 어시스턴트가 한 꺼풀 더 깊어졌다"
date: 2026-05-21T11:00:00+09:00
draft: false
description: 173개의 커밋을 담긴 이번 업데이트는 Mac 앱 UX 개편, 새로운 스킬 추가, Gateway 성능 최적화, 그리고 QA-Lab 대폭 확장이 눈길을 끈다.
tags:
  - OpenClaw
  - AI Assistant
  - Release
  - Mac App
  - Skills
  - Gateway
  - Codex
  - QA
categories: ["AI-LLM", "OpenClaw"]
---

지난 5월 20일, OpenClaw가又一个大型アップデート를 выпусти했어요. **v2026.5.19**는 무려 173개의 커밋을 담고 있으며, QA-Lab 강화, Mac 앱 UX 개편, 새로운 스킬 추가, 그리고 Gateway 성능 최적화까지 광범위한 변화가 이루어졌어요.

솔직히 말하면, 이번 업데이트는 개발자 분들한테는 **"우와, 이거 놓치면 손해"** 수준의含金量이고, 일반 사용자한테도 **"어? 앱이 더 빨라지고 편해졌어?"** 하고 체감할 수 있는 부분이 제법 있어요.

---

## 🍎 Mac 앱 — 설정 페이지가 통째로 Redesign

가장 눈길을 끄는 변화 중 하나는 Mac 앱 설정 페이지의 완전한 Redesign이에요.

- **카드 기반 레이아웃**으로 통일
- 권한·음성·스킬·크론·실행·디버그 팬 모두 깔끔하게 정리
- 네이티브 사이드바 주변 스페이싱도改善
- 음성 인식 언어와 웨이크 프레이즈 설정도 나머지 설정과 같은 컴팩트 카드 형태로 통일

기존에 설정 페이지가 여기저기 다른 느낌이었는데, 이번에ようやく、一贯したデザイン语言로整合했네요. Mac 유저분들이라면 업데이트 후 직접 확인해 보시길 — 확실히 더 산뜻해졌어요.

---

## 🛠️ 새로운 스킬들 — 밈 메이커, Python 디버깅, 다이어그램 생성

스킬 생태계도 두툼해졌어요.

### 🎨 meme-maker 스킬
- 큐레이션된 밈 템플릿 검색
- 로컬 SVG/PNG 렌더링
- Imgflip 호스티드 렌더링
- Know Your Meme 출처 링크까지

"이 밈 어디서 왔지?" 할 때 Know Your Meme 연동되는 게 웃기면서도実用的이네요.

### 🐍 Python 디버깅 스킬
- `pdb`, `breakpoint()` 지원
- Post-mortem 인스펙션
- `debugpy` 리모트 어태치까지

AI 어시스턴트에서 바로 Python 디버깅할 수 있다니, 개발자분들에겐 꽤 좋은 소식이에요.

### 📊 그 외 추가된 스킬
- **Node inspector debugging** — 노드 디버깅을 스킬로 통합
- **Fused diagram generation** — 다이어그램 생성 워크플로우
- **Throwaway spike** — 빠른 프로토타이핑용 스파이크 워크플로우

---

## 🐳 Docker/Podman — Python 패키지도 설치 가능

이건 꽤 많은 분들한테 필요했을 기능이에요.

- `OPENCLAW_IMAGE_APT_PACKAGES` — 런타임 중립적 apt 패키지 설치용 (새로운 표준)
- `OPENCLAW_IMAGE_PIP_PACKAGES` — Python 패키지 설치용 (새로 추가)
- 기존 `OPENCLAW_DOCKER_APT_PACKAGES`는 레거시 fallback으로 유지

로컬 이미지 빌드할 때 Python 패키지까지一并管理할 수 있다니, 특히 데이터 처리나 ML 파이프라인 연동하는 분들한테 유용하겠어요.

---

## ⚡ Gateway 성능 — 재시작 속도와 레이턴시 개선

@samzong 시리즈로 Gateway 성능 개선이 이어졌어요.

- **시작 로그와 플러그인 서비스가 채널 사이드카와 오버랩** — 재시작 후 ready 상태까지의 레이턴시 감소
- `/readyz` 사이드카 게이팅은 유지하면서도 속도는 향상
- 재시작 추적에 스타트업 프로브, 설정, 런타임, 리소스 카운트 비용 명시

재시작이 잦은 분들한테는 체감 속도가 꽤 좋아졌을 거예요.

---

## 📱 Android — Talk Mode가 실시간 Gateway 릴레이 음성 세션으로

Android 쪽도 큰 변화가 있었어요.

- 실시간 Gateway 릴레이 음성 세션으로 전환
- 스트리밍 마이크 입력
- 실시간 오디오 재생
- 도구 결과 브릿징
- 화면 내 트랜스크립트 표시

이제 Android에서도 더 자연스러운 음성 대화가 가능해졌다고 생각하면 돼요.

---

## 📱 Telegram — 포럼 토픽 개선

Telegram 관련 수정도 제법 많아요.

- 포럼 토픽이 형제 토픽 트래픽을 블로킹하지 않도록 — topic-aware lanes로 라우팅 분리
- 큐에 쌓인 포럼 토픽 후속 메시지가 이전 abort 신호를 상속하지 않도록 수정
- allowlisted 네이티브 DM 초안 미리보기 지원 (일시적 도구 진행 중에만 표시)

Telegram으로 Active하게 쓰시는 분들한테는 버그 픽스가 제법 느껴질 거예요.

---

## 🧪 QA-Lab 대폭 확장 — 100-Turn 시나리오까지

이 업데이트에서 가장 많은 변화를 담은 부분이 바로 QA-Lab이에요.

- **20-Turn + 선택적 100-Turn 런타임 패리티 시나리오** 추가
- Standard tier와 Soak tier 메타데이터 분리
- Codex-vs-Pi 토큰 효율성 아티팩트 레인 추가
- 런타임 도구 픽스처 커버리지 `--tools`로 리포트
- Personal-agent 승인 거절 시나리오 (로컬 읽기拒否가 깔끔하게 처리되는지 검증)
- Personal-agent 작업 팔로우 스루 시나리오 (pending/blocked/done 상태 리포트)
- "드림 쉐도우 트라이얼" 시나리오 — MEMORY.md 변형 없이 메모리 프로모션 평가 가능

개발팀 입장에서는 이번 QA-Lab 확장이产品质量 보장 체계를 한 단계 더 올려놓은 느낌이에요.

---

## 🔧 그 외 눈에 띄는 변경사항

| 영역 | 내용 |
|------|------|
| **Codex** | `/codex plugins list, enable, disable` — 설정 파일 편집 없이 플러그인 관리 가능 |
| **Browser** | 모달 다이얼로그 스냅샷 표면화, `--dialog-id`로 응답 가능 |
| **Browser CLI** | `--timeout-ms`로 장기 실행 페이지 함수 타임아웃 제어 |
| **Memory** | 큰 chunk 테이블이 Node.js 메인 스레드를 수 초간 핀닝하던 문제 해결 |
| **Obsidian 스킬** | 공식 obsidian CLI 사용으로 변경 (서드파티 obsidian-cli 非지원) |
| **Proxy** | HTTPS 관리 포워드 프록시 엔드포인트 + TLS CA 신뢰 지원 |
| **CLI** | 65535 초과 포트 번호 사전 거부 (Gateway 바인딩 전에 검증) |

---

## 특히 주목할 점

솔직히 평소、开发자분들이나 AI 어시스턴트 생태계를 깊이 파고드는 분들한테 이 업데이트의 진짜 값어치는 **QA-Lab의 확장**과 **Gateway 성능 개선**에 있다고 봐요.

다만 Mac 앱 설정 Redesign, Telegram 개선, Android 음성 세션刷新 등은日常 이용자분들한테도 곧바로 체감될 변화예요.

업데이트는 `openclaw update run` 또는 [GitHub 릴리스 페이지](https://github.com/openclaw/openclaw/releases/tag/v2026.5.19)에서 직접 확인하실 수 있어요.

---

원문 : <a href="https://github.com/openclaw/openclaw/releases/tag/v2026.5.19">Release openclaw 2026.5.19 · openclaw/openclaw</a>
