---
title: "구글, Gemini 쿼터를 너무 빨리 소진하던 버그 여러 건 수정"
date: 2026-05-30T11:00:00+09:00
draft: false
description: "구글 VP Josh Woodward가 Gemini 사용량 한도 버그 수정을 공개했다. Omni 영상 1~2개로 전체 쿼터가 소진되던 문제, 대용량 파일 포함 요청의 과다 차감, 실패 요청 쿼터 소진 등 여러 이슈가 해결됐다."
tags: ["Gemini", "Google", "AI구독", "쿼터버그", "AI업데이트"]
cover:
  image: /images/gemini-quota-bug-fix-2026-cover.png
  alt: "Google Gemini quota bug fix"
---

## 개요

구글이 Gemini 유료 플랜 사용자들 사이에서 제기된 쿼터 과다 소진 문제를 일괄 수정했다. 구글 VP Josh Woodward가 X(트위터)를 통해 버그 수정 내역을 공개했으며, 일부 항목은 Ultra 멤버에게 보너스 생성 횟수를 추가로 제공하는 방향으로 정리됐다.

## 핵심 요약

- Omni 영상 1~2개가 전체 쿼터를 다 써버리는 버그 수정, Ultra 멤버는 Omni 영상 생성 횟수 2배로 늘어남
- 대용량 파일이 포함된 Gemini 3.1 Pro 요청이 쿼터를 과도하게 차감하던 문제 해결 — 요청당 최대 차감량 상한선 설정
- 실패한 요청은 더 이상 쿼터를 소모하지 않음
- Flash Lite 요청은 무료로 전환
- Deep Research 등 복합 기능의 쿼터 소모 내역이 더 세분화되어 표시됨
- 특정 모델 선택 시 세션을 넘어도 해당 선택이 유지됨

## 어떤 버그들이 있었나

가장 먼저 언급된 것은 **Omni 영상 쿼터 버그**다. 영상을 1~2개만 생성해도 전체 일일 쿼터가 소진되는 현상이 있었다. 이는 영상 생성 비용 계산 로직의 오류로, 수정 후 Ultra 멤버에게는 기존 대비 두 배의 Omni 영상 생성 횟수가 제공된다.

두 번째는 **Gemini 3.1 Pro + 대용량 파일 조합 문제**다. 대용량 파일이 첨부된 복잡한 요청을 처리할 때 쿼터가 기대 이상으로 많이 차감됐다. 이제는 프롬프트 한 건당 최대 차감량에 상한을 두되, 요청 자체는 정상적으로 처리된다. 즉, 같은 플랜에서 더 많은 요청을 소화할 수 있게 됐다.

**실패한 요청에 쿼터를 차감하던 문제**도 수정됐다. 오류가 발생한 요청에도 쿼터가 소모됐던 것은 사용자 입장에서 납득하기 어려운 동작이었다. 이제 요청이 실패하면 쿼터는 돌아온다.

**Flash Lite 무료 전환**도 주목할 만한 변화다. 가벼운 작업에 최적화된 Flash Lite 모델 사용이 쿼터를 전혀 소모하지 않게 됐다.

## 배경: I/O 직후 구독 개편과 맞물린 수정

이번 버그 수정은 구글이 I/O 2026에서 Gemini 앱 전면 개편과 함께 새로운 구독 체계를 발표한 직후 나왔다. 월 10달러부터 시작하는 3단계 구독 구조로 개편된 상황에서, 쿼터가 예상보다 빠르게 소진되는 경험은 유료 전환 및 유지에 부정적인 신호가 됐을 것이다. 이번 수정은 제품 신뢰도 회복 측면에서도 의미가 있다.

## 실무자가 볼 핵심 포인트

**Gemini API 또는 Gemini 앱을 업무에 쓰는 팀이라면** 이번 변경이 실질적인 비용 구조에 영향을 준다. 실패한 요청에 쿼터가 안 빠진다는 건 자동화 파이프라인에서 재시도 로직을 운영할 때 특히 유리하다.

**Flash Lite 무료화**는 가벼운 분류, 요약, 태깅 작업에 Flash Lite를 쓰는 워크플로에서 체감 효율이 올라간다는 뜻이다. 쿼터를 고가의 Pro 모델에 집중할 수 있게 된다.

**쿼터 소모 세분화 표시**는 어떤 작업이 쿼터를 많이 먹는지 추적하기 쉬워진다는 점에서 최적화 의사결정에 도움이 된다.

## 원문 출처

*원문: [Google fixes several bugs in Gemini usage limits that burned through quotas too fast](https://the-decoder.com/google-fixes-several-bugs-in-gemini-usage-limits-that-burned-through-quotas-too-fast/) — The Decoder, Matthias Bastian (2026-05-29)*
*원본 발표: [Josh Woodward via X](https://x.com/joshwoodward/status/2060171610922058142)*
