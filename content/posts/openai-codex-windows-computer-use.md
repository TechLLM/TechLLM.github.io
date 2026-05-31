---
title: "OpenAI Codex, Windows PC 자율 제어 — 버그 사냥·앱 테스트를 사람 없이 한다"
date: 2026-05-31T10:04:31+09:00
draft: false
description: "OpenAI가 Codex의 Computer Use 기능을 Windows 11로 확장했다. AI가 사용자 없이도 PC의 앱·파일·리소스를 직접 조작해 버그를 찾고 앱을 테스트한다. 모바일에서도 iPhone·Android로 원격 시작·모니터링이 가능하다."
tags: ["OpenAI", "Codex", "ComputerUse", "AI에이전트", "Windows", "자율에이전트"]
cover:
  image: /images/openai-codex-windows-computer-use-cover.png
  alt: "OpenAI Codex Windows Computer Use autonomous agent"
---

## 개요

OpenAI가 Codex의 Computer Use 기능을 Windows 11로 확장했다. 4월 macOS, 5월 모바일에 이어 세 번째 플랫폼이다. 이제 AI가 사용자가 자리를 비운 상태에서도 PC의 앱, 파일, 기타 리소스를 직접 조작해 버그를 찾고 앱을 테스트하고 작업을 검토한다.

## 핵심 요약

- Codex Computer Use가 Windows 11 지원 추가 — 4월 macOS, 5월 모바일에 이은 세 번째 플랫폼
- 사용자가 자리를 비워도 AI가 PC 앱·파일·리소스를 직접 조작
- Codex 설정에서 토글 하나로 활성화, `@computer` · `@Paint` 등 명령으로 특정 프로그램 지정 가능
- iPhone·Android ChatGPT 앱에서 Windows 작업을 원격으로 시작·모니터링
- OpenAI의 업무·일상 통합 '슈퍼앱' 전략의 일환

## 무엇이 달라지나

Codex Computer Use의 핵심은 **사람의 개입 없는 자율 PC 조작**이다. AI가 화면을 보고 앱을 클릭하고 파일을 열고 코드를 실행하는 것을 사용자 없이 수행한다.

Windows 11에서 가능한 작업:

- **버그 헌팅**: 앱을 실행해 오류를 재현하고 로그를 분석
- **앱 테스트**: 기능별 시나리오를 자동으로 실행하고 결과 확인
- **작업 검토**: 파일을 열어 내용을 확인하고 피드백 생성

Codex 설정에서 Computer Use를 활성화하면 된다. `@computer`로 PC 전체를 지정하거나, `@Paint`처럼 특정 앱을 타겟으로 명령을 내릴 수 있다.

## 모바일에서 원격 제어

iPhone과 Android의 ChatGPT 앱을 통해 Windows 머신의 Codex 작업을 원격으로 시작하거나 모니터링할 수 있다. 자리를 비운 상태에서 긴 작업을 걸어두고, 이동 중에 진행 상황을 확인하는 워크플로가 가능해진다.

## 플랫폼 확장 타임라인

| 시점 | 플랫폼 |
|------|--------|
| 2026년 4월 | macOS Computer Use 출시 |
| 2026년 5월 | iOS·Android 모바일 접근 추가 |
| 2026년 5월 말 | Windows 11 Computer Use 확장 |

## OpenAI의 슈퍼앱 전략

Codex의 급속한 확장은 OpenAI가 업무·일상을 통합하는 '슈퍼앱' 구축 계획의 일부다. ChatGPT가 이 앱에 흡수될 가능성도 있지만, 브랜드 파워를 고려하면 Codex라는 이름 아래 ChatGPT를 묻기는 어렵다는 시각도 있다. Codex는 주로 개발자 도구로 인식되기 때문이다.

현재까지의 행보를 보면 OpenAI는 모델 중심이 아닌 **에이전트 플랫폼** 중심으로 제품을 재편하고 있다. Codex가 그 실험의 선봉이다.

## 실무자가 볼 핵심 포인트

**개발자와 QA 엔지니어**에게 이번 업데이트는 즉각적인 실용성이 있다. 테스트 케이스 실행, 버그 재현, 로그 분석을 야간이나 휴식 시간에 AI에게 맡기고 결과만 확인하는 워크플로가 가능해진다. 기존 CI/CD 파이프라인과 별도로, UI 레이어까지 포함한 실제 앱 동작 테스트를 자동화할 수 있다는 점이 차별점이다.

**운영 관점**에서는 접근 제어가 중요해진다. AI가 PC를 자율 조작한다는 것은 파일 시스템, 앱, 네트워크 리소스에 AI가 직접 접근한다는 뜻이다. 업무용 PC에 적용하기 전에 어떤 범위까지 허용할지 명확한 정책이 필요하다.

현재는 Codex 사용자 대상 기능이다. 일반 ChatGPT 사용자로의 확대 여부와 시점이 다음 관전 포인트다.

## 원문 출처

*원문: [OpenAI's Codex can now operate your Windows PC autonomously, hunting bugs and testing apps on its own](https://the-decoder.com/openais-codex-can-now-operate-your-windows-pc-autonomously-hunting-bugs-and-testing-apps-on-its-own/) — Matthias Bastian / The Decoder (2026-05-30)*
