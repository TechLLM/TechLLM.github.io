---
title: "Gemini CLI, 이제 Antigravity CLI로 전환된다"
description: "Google이 Gemini CLI를 공식 종료하고 Antigravity CLI로 전환한다. 6월 18일부터 일반 사용자 요청 처리 중단 — 전환 타임라인과 달라지는 점을 정리했다."
date: 2026-05-20T07:56:00+09:00
draft: false
tags: ["GeminiCLI", "AntigravityCLI", "Google", "AI개발도구", "터미널에이전트"]
cover:
  image: /images/gemini-cli-to-antigravity-cli-cover.png
  alt: "Gemini CLI에서 Antigravity CLI로 전환"
---

## 개요

2025년 출시 이후 100,000개 GitHub 스타, 6,000개 이상의 머지된 PR을 기록한 Gemini CLI가 막을 내린다. Google이 2026년 5월 19일 공식 블로그를 통해 **Gemini CLI를 Antigravity CLI로 전환**한다고 발표했다.

단순한 리브랜딩이 아니다. 멀티 에이전트 시대에 맞춰 아키텍처 자체를 재설계한 새 플랫폼으로의 이전이다.

## 핵심 요약

- **전환 대상**: Gemini CLI → [Antigravity CLI](http://antigravity.google/blog/introducing-google-antigravity-cli)
- **서비스 종료일**: 2026년 6월 18일 (일반 사용자 기준)
- **기업 고객**: 현행 유지, 변경 없음
- **지금 당장**: Antigravity CLI 다운로드 및 사용 가능

---

## 왜 전환하는가

Gemini CLI는 터미널에서 에이전트 작업이 가능하다는 걸 증명했다. 그런데 사용자들의 요구가 달라졌다. 단일 에이전트 하나가 처리하는 수준을 넘어서, **여러 에이전트가 서로 통신하며 복잡한 문제를 나눠 푸는 워크플로**가 필요해진 것이다.

Google 측 설명은 명확하다: 에너지를 분산하지 않고, 멀티 에이전트 현실에 맞게 설계된 단일 플랫폼에 집중하겠다는 것. 그 플랫폼이 **Google Antigravity**다.

---

## Antigravity CLI의 달라진 점

Gemini CLI의 핵심 기능은 그대로 이식된다. Agent Skills, Hooks, Subagents, Extensions(이제 Antigravity 플러그인으로). 달라진 건 내부 구조다.

**주요 개선 사항:**

| 항목 | 내용 |
|---|---|
| 실행 속도 | Go 언어로 재작성 — 더 빠르고 반응성 향상 |
| 비동기 워크플로 | 여러 에이전트를 백그라운드에서 동시 실행 가능 |
| 통합 아키텍처 | Antigravity 2.0 데스크톱 앱과 동일한 에이전트 하네스 공유 |

비동기 워크플로 부분이 핵심이다. 대규모 리팩터나 여러 주제 조사를 터미널 세션을 잠그지 않고 백그라운드에서 처리할 수 있다.

---

## 전환 타임라인

### 일반 사용자 (Google AI Pro / Ultra / 무료 플랜)

- **지금**: Antigravity CLI 다운로드 가능
- **2026년 6월 18일**: Gemini CLI 및 Gemini Code Assist IDE 확장의 요청 처리 중단
- **Gemini Code Assist for GitHub**: 동일 날짜부터 새 조직 설치 불가, 이후 수 주 내 요청 처리 중단

### 기업 고객 (Gemini Code Assist Standard / Enterprise)

- **변경 없음** — 최신 Gemini 모델 접근 및 업데이트 계속 지원
- Antigravity CLI도 지금 바로 Google Cloud 프로젝트에서 사용 가능

---

## 마이그레이션 방법

Google이 [공식 마이그레이션 문서](http://antigravity.google/docs/gcli-migration)를 제공하고 있다. 향후 몇 주 내에 영상 튜토리얼도 추가 예정이다.

커뮤니티 피드백은 [Antigravity CLI GitHub 포럼](https://github.com/google-antigravity/antigravity-cli)에서 받고 있다.

---

## 실무자가 볼 핵심 포인트

- **6월 18일이 데드라인**: 무료/Pro/Ultra 사용자는 그 전에 Antigravity CLI로 전환해야 한다
- **기업 고객은 여유 있음**: 기존 라이선스 그대로 유지되므로 급하지 않다
- **기능 1:1 호환은 아님**: 출시 초기엔 일부 기능 차이 있을 수 있으니 마이그레이션 전 문서 확인 필수
- **Go 기반 재작성**: 속도 개선이 체감될 가능성 높음
- **Antigravity 2.0과 통합**: 데스크톱 앱과 동일 하네스를 공유하므로, 앞으로의 개선이 자동 반영됨

---

원문 : <a href="https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/">An important update: Transitioning Gemini CLI to Antigravity CLI — Google Developers Blog</a>
