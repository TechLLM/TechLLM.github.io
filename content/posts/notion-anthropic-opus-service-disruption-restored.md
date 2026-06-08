---
title: "Notion, Anthropic Opus 4.7·4.8 장애로 일시 차단 12시간 만에 복구 — AI 의존 리스크가 드러난 하루"
date: 2026-06-08T08:49:00+09:00
draft: false
description: "Notion이 Anthropic Opus 4.7·4.8 모델의 성능 저하를 감지하자 모든 Anthropic 모델을 일시 차단했다가 약 12시간 뒤 복구했다. Anthropic은 짧은 인프라 이슈로 다중 Claude 모델에 에러율이 올랐다고 인정했다. Notion 헤드 오브 프로덕트 Max Schoening은 GitHub·AWS도 겪는 일상적 장애라고 정리했지만, X에서 1,200회 리포스트가 일어나며 SaaS의 단일 AI 벤더 의존 리스크가 다시 도마 위에 올랐다."
tags: ["Notion", "Anthropic", "Claude", "Opus", "AI장애", "SaaS의존성", "MaxSchoening", "AI인프라"]
categories: ["AI · LLM"]
source_url: "https://techcrunch.com/2026/06/07/notion-restores-access-to-anthropic-after-service-disruption/"
cover:
  image: /images/notion-anthropic-opus-service-disruption-restored/notion-anthropic-opus-service-disruption-restored-cover.png
  alt: "Notion과 Anthropic 사이 데이터 흐름이 일시 끊겼다가 다시 이어지는 모습을 표현한 핸드드로잉 일러스트"
  caption: "Generated illustration"
---

## 개요

Notion이 일요일 새벽 Anthropic의 Opus 4.7·4.8 모델이 성능 저하를 보이자 자사 제품 안의 Anthropic 모델을 모두 비활성화했다가, 약 12시간 뒤 다시 켰다. Anthropic은 "짧은 인프라 이슈로 다중 Claude 모델에 에러율이 올랐다"고 인정했고, Notion 헤드 오브 프로덕트 Max Schoening은 "GitHub·AWS도 겪는 일시적 서비스 장애"라고 정리했다. 단순한 다운타임 한 건이지만, X에서만 약 1,200회 리포스트가 일어나며 SaaS 제품이 특정 AI 벤더에 얼마나 깊이 묶여 있는지를 그대로 노출시킨 사건이 됐다.

## 핵심 요약

- Notion이 Anthropic Opus 4.7·4.8 모델의 성능 저하를 감지하고 Anthropic 모델 전체를 자사 제품에서 일시 비활성화했다.
- 약 12시간 뒤 Notion이 Anthropic 접근을 복구했고, Anthropic은 "짧은 인프라 이슈로 다중 Claude 모델 에러율이 일시적으로 올랐다"고 공식 인정했다.
- Notion 헤드 오브 프로덕트 Max Schoening은 "Notion·GitHub·AWS 모두 겪는 일시적 서비스 장애"라며 사건을 보편적 인프라 이슈로 위치시켰다.
- Notion의 최초 공지가 X에서 약 1,200회 리포스트되며 SaaS와 AI 벤더 종속 문제에 대한 광범위한 논의를 촉발했다.
- AI 기능을 핵심 제품 경험으로 통합한 SaaS는 모델 벤더 한 곳의 짧은 장애가 곧바로 제품 가용성 저하로 이어진다는 점이 다시 확인됐다.

## 12시간 동안 일어난 일

일요일 아침, Notion은 사내 모니터링에서 Anthropic Opus 4.7과 4.8 모델의 응답 품질·실패율이 정상 범위를 벗어났다는 신호를 잡았다. Notion은 곧 "Anthropic의 Opus 4.7·4.8 모델이 성능 저하를 겪고 있다"고 공지하면서, 안전 차원에서 Notion 안의 모든 Anthropic 모델 접근을 일시적으로 차단했다.

장애를 인식한 시점부터 약 12시간 뒤, Notion은 Anthropic 모델 접근을 복원했다. 이 사이 Anthropic 측은 "짧은 인프라 이슈로 다중 Claude 모델에 일시적으로 에러율이 올랐고, 이슈는 해결됐다"는 입장을 내놨다. 단일 모델 한두 개가 아니라 복수의 Claude 모델이 동시에 영향을 받은 인프라 단의 사건이었다는 점이 핵심이다.

Notion 헤드 오브 프로덕트 Max Schoening은 사후에 "이번 성능 저하는 일시적 서비스 장애였다. 이런 일은 일어난다. Notion에도, GitHub에도, AWS에도 일어난다"고 정리했다. 사건의 무게를 과장하지 않고 보편적 인프라 이슈로 자리매김하려는 메시지였지만, 이미 X 타임라인에는 Notion의 원 공지가 약 1,200회 리포스트되며 빠르게 퍼진 뒤였다.

## 작은 장애가 큰 신호로 읽히는 이유

12시간의 다운타임 자체는 클라우드 업계 기준으로 보면 그리 특이하지 않다. 그럼에도 이번 사건이 주목을 끈 이유는 두 가지다.

첫째, Notion이 AI 기능을 마케팅의 전면에 내세운 대표적 SaaS라는 점이다. AI 기반 요약·작성·검색이 더 이상 부가 기능이 아니라 제품 경험의 중심에 위치한 회사에서, 모델 벤더가 한 번 흔들리면 곧바로 사용자 경험 저하로 이어진다.

둘째, Notion이 단순히 "에러가 줄어들 때까지 기다리는" 대신 Anthropic 모델 전체를 의도적으로 차단했다는 점이다. 이는 모델 품질이 떨어진 상태에서 잘못된 결과를 사용자에게 그대로 노출하느니, 차라리 그 경로 자체를 끊는다는 운영 원칙이 작동한 결과다. 같은 사고가 일어났을 때 자사 제품은 어디서 멈추도록 설계돼 있는지, 다시 한 번 점검해 볼 거리를 던진다.

## 실무자가 볼 핵심 포인트

**SaaS 프로덕트 리더**라면 이번 사건을 "Anthropic이 장애를 냈다"가 아니라, "단일 모델 벤더에 묶인 경험은 그 벤더가 흔들리면 제품 전체가 흔들린다"는 사례로 받아들여야 한다. AI 기능이 핵심 경험으로 들어와 있다면, 모델 단위가 아니라 벤더 단위 SLO를 다시 계산할 시점이다.

**플랫폼·SRE 담당자**에게는 멀티 모델 폴백 설계가 더 이상 보너스 기능이 아니라는 신호다. Opus 4.7·4.8이 동시에 영향을 받은 인프라 이슈였다는 점에서, 같은 벤더 내 다른 모델로 폴백하는 전략만으로는 부족할 수 있다. 다른 벤더의 동급 모델로 자동 전환하는 경로와, 그 전환이 일어났을 때 사용자에게 어떻게 보이는지를 미리 정의해 두는 편이 낫다.

**제품 디자이너**는 AI 기능이 "조용히 죽는" 시나리오를 UI에 명시적으로 반영해야 한다. Notion이 차단을 택했다는 사실은 곧 사용자 화면 어딘가에서 AI 호출이 비활성 상태가 됐다는 의미다. 그 상태를 자연스럽게 알리는 빈 상태(empty state)·대체 흐름이 없다면, 사용자는 제품 자체가 망가졌다고 받아들이게 된다.

**커뮤니케이션·PR 담당자**에게는 Schoening의 대응이 참고할 만한 모델이다. 장애를 부정하지 않으면서도 GitHub·AWS와 같은 카테고리로 위치시켜 사건의 일상성을 강조하는 화법은, 같은 일이 자사에서 일어났을 때 메시지 톤을 잡는 데 그대로 응용할 수 있다.

## 원문 출처

- [Notion Restores Access to Anthropic After Service Disruption — TechCrunch](https://techcrunch.com/2026/06/07/notion-restores-access-to-anthropic-after-service-disruption/)
