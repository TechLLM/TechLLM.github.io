---
title: "깃허브, 무료 AI 모델 놀이터 'GitHub Models' 접는다 — 6월 16일부로 신규 가입 차단, Azure AI Foundry로 이주"
date: 2026-06-19T23:13:33+09:00
draft: false
description: "깃허브가 2024년에 선보였던 무료 AI 모델 플레이그라운드 GitHub Models를 단계적으로 종료합니다. 6월 16일부터 신규 사용자에게 노출이 막혔고, 기존 사용자는 당분간 그대로 쓸 수 있습니다. 후속 경로는 Azure AI Foundry. 무료로 GPT-4o와 Llama를 비교하던 시대가 닫히고, 모델 선택이 다시 '클라우드 구매 결정'으로 돌아가는 분위기입니다."
cover:
  image: "/images/github-models-retire-azure-ai-foundry/github-models-retire-azure-ai-foundry-cover.png"
  alt: "GitHub Models 종료와 Azure AI Foundry 이주를 표현한 일러스트"
  caption: "GitHub Models 종료, 다음은 Azure AI Foundry"
tags: ["GitHub", "Azure AI Foundry", "GitHub Models", "AI 모델 비교", "개발자 도구"]
categories: ["AI"]
source_url: "https://news.google.com/rss/articles/CBMilwFBVV95cUxOY0NBZ19RdzBfcTluTmwwZ3ZUaFQ3ME5VXzM1MklIYV9SeEI1VVItRVlQZllUY1V0Tmd4SWQ4UVE2TmRFRmNzVGZibm1WRkZMRi1oYjZtWlN4RVpwSlUwX3RFcXhJQi04TWhCTzl2QTlJcWhWNGY5dGk5Sk91bHZYTm9HemVPUDNPdWRMQ3FQOVBVU2ZGZTNV?oc=5"
ShowToc: true
TocOpen: false
---

## 개요

깃허브가 자기네 무료 AI 모델 플레이그라운드 GitHub Models를 슬슬 정리하기 시작했습니다. DevOps.com이 6월 19일 보도한 내용에 따르면, 6월 16일부로 GitHub Models는 신규 고객에게 더 이상 노출되지 않습니다. 한 번도 써 본 적이 없는 조직이라면 이제 메뉴 자체가 보이지 않고, 새로 시작할 방법도 없다는 뜻입니다.

이미 쓰고 있던 팀은 아직 당장 바뀌는 건 없습니다. 플레이그라운드도, API도, 등록된 모델도 그대로 돌아갑니다. 다만 깃허브 쪽 메시지는 분명합니다. 이번 조치가 "최종 종료를 향한 첫걸음"이고, 구체적인 종료 일정은 곧 공개될 예정이라는 겁니다.

![GitHub Models 종료와 Azure AI Foundry 이주를 표현한 일러스트](/images/github-models-retire-azure-ai-foundry/github-models-retire-azure-ai-foundry-cover.png)

## 핵심 요약

- **변경 시점**: 2026년 6월 16일부터 신규 가입 차단. 기존 사용자는 당분간 유지, 최종 종료 일정은 별도 공지 예정.
- **사라지는 기능**: 깃허브 안에서 무료로 GPT-4o·GPT-4o mini·Llama 3.1·Cohere Command·Mistral Large 2 같은 모델을 한 API 키로 호출하고, 프롬프트를 코드처럼 관리하며 모델끼리 나란히 비교하던 워크플로우.
- **대체 경로**: Azure AI Foundry. 더 넓은 모델 카탈로그를 제공하지만, Azure 계정·결제·자원 프로비저닝이 필요한 유료 플랫폼입니다.
- **타격받는 쪽**: Azure 자격 증명 없이 깃허브 계정만으로 모델을 실험하던 1인 개발자와 소규모 팀. 모델 비교가 다시 '구매 결정'으로 무거워집니다.
- **메시지**: 마이크로소프트가 모델 평가 도구를 Azure AI Foundry 우산 아래로 통합하면서, 어시스트 코딩(코파일럿)과 모델 평가가 별도의 과금 서비스로 분리되는 흐름이 뚜렷해졌습니다.

## 본문

### 깃허브 모델은 어떤 자리였나

2024년에 처음 공개됐을 때 GitHub Models의 콘셉트는 단순했습니다. 깃허브 계정 하나만 있으면 메타 Llama 3.1, OpenAI GPT-4o와 GPT-4o mini, Cohere Command, Mistral Large 2 같은 주요 모델을 무료로 만져 볼 수 있게 해 주는 일종의 놀이터였습니다. 별도 가입도, Azure 자원 생성도, Hugging Face에서 모델 내려받기도 필요 없었습니다.

깃허브가 강조한 포인트는 세 가지였습니다. 첫째, 단일 API 키 하나로 여러 모델을 호출한다. 둘째, 프롬프트를 코드처럼 깃 저장소에서 관리한다. 셋째, 같은 화면에서 모델을 나란히 놓고 평가한 다음 그대로 운영 환경으로 넘어간다. 다시 말해 '실험에서 배포까지 한 곳에서'가 슬로건이었습니다.

이 구조의 매력은 결국 '진입 마찰이 거의 0'이라는 점이었습니다. 새 클라우드 계정을 트지 않고도, 결제 카드를 등록하지 않고도, GPT-4o와 Llama를 같은 입력으로 돌려 보고 누가 더 나은지 눈으로 비교할 수 있었으니까요.

### 왜 지금 닫는가, 그리고 그다음은 Azure AI Foundry

깃허브는 새로 AI 모델을 써 보려는 개발자들에게 Azure AI Foundry로 가라고 안내하고 있습니다. 사실 이 흐름이 갑자기 튀어나온 건 아닙니다. GitHub Models는 처음부터 "운영용 플랫폼이 아니라 출발점"으로 포지셔닝됐습니다. 깃허브에서 가볍게 시험하고, 규모를 키워야 할 때 Azure로 옮긴다 — 이 진로가 디자인 단계에 박혀 있었습니다.

이번 발표는 그 갈래길을 공식화한 것에 가깝습니다. 마이크로소프트는 AI 도구를 Azure AI Foundry라는 단일 우산 아래로 모으는 중입니다. 깃허브에 흩어져 있던 모델 평가 기능을 Foundry로 끌어와야 카탈로그도 넓히고, 과금도 일관되게 잡을 수 있기 때문입니다.

문제는 사용자 입장에서 체감하는 무게가 다르다는 점입니다. 이미 깃허브와 Azure를 함께 쓰고 있던 팀이라면 이번 이주는 절차적인 작업으로 끝납니다. 그러나 'Azure 자격 증명을 만들고 싶지 않아서' GitHub Models를 골랐던 팀에는 새 마찰이 추가됩니다. Azure AI Foundry는 분명 더 강력한 플랫폼이지만, 온보딩이 가볍지 않고 무료도 아닙니다.

### 모델 평가가 다시 '구매 결정'으로 돌아간다

The Futurum Group의 미치 애슐리(Mitch Ashley) VP는 이번 변화를 단순한 기능 종료 이상으로 봅니다. 그가 짚은 핵심은 이렇습니다. "모델 실험이 개발자가 일하는 저장소 안에서 빠져나와, 다시 클라우드 프로비저닝 뒤로 옮겨 갑니다." 그 결과 어시스트 코딩(코파일럿 같은 기능)과 모델 평가는 별개의 과금 가능한 플랫폼 서비스로 분리되고, 모델 비교의 무대는 Azure AI Foundry가 가져갑니다.

이 분리가 만들어 내는 실질적인 결과도 그가 정리해 줍니다. "계정 없이도 모델 선택을 실증적으로 유지하던 팀들은, 이제 평가를 어디서 할지 결정해야 합니다. 작은 팀과 1인 개발자에게 모델 선택은 다시 클라우드 구매 결정이 되고, 나란히 놓고 비교하는 일은 Foundry로 옮겨 가거나 슬그머니 사라질 겁니다."

조금 더 풀어 보면 이런 얘기입니다. GitHub Models 시절에는 '오늘 이 작업에 어떤 모델이 가장 잘 맞지?'를 5분짜리 실험으로 끝낼 수 있었습니다. 그런데 그 5분짜리 비교를 위해 Azure 구독을 새로 트고 자원을 프로비저닝해야 한다면, 작은 팀은 그냥 익숙한 모델 하나로 굳혀 버릴 가능성이 높습니다. 무료 비교가 사라지면, 결국 'GPT를 안 쓰는 사람은 안 쓰고, 쓰는 사람은 그대로 쓰는' 관성이 강해진다는 뜻입니다.

### 흐름을 한 줄로 정리하자면

진입 장벽을 낮춰 주던 무료 개발자 도구가 결국 상용 플랫폼에 흡수되는 패턴은 이번이 처음이 아닙니다. GitHub Models는 자기 역할을 다했습니다. 한 세대의 개발자에게 '여러 모델을 같이 써 보는 경험'을 처음 안겨 줬으니까요. 다만 이제 마이크로소프트는, 그렇게 길러 낸 사용자들을 실제로 매출이 잡히는 Azure 위로 옮기려 하고 있습니다.

## 실무자가 볼 핵심 포인트

- **지금 당장 할 일**: 기존 GitHub Models 사용자라면 오늘 급하게 옮길 필요는 없습니다. 다만 팀 내부에서 "최종 종료까지 우리는 어떻게 갈 것인가"를 한 번 논의해 두는 게 좋습니다. 깃허브가 종료 일정을 추가 공지하기로 한 만큼, 시기가 정해진 다음에 부랴부랴 움직이지 말고 미리 마이그레이션 책임자를 정해 두세요.
- **API 코드 정리 우선순위**: GitHub Models 엔드포인트로 직접 호출하던 스크립트, 노트북, CI 파이프라인을 목록화하세요. Azure AI Foundry로 옮길 때 가장 손이 많이 가는 게 인증·엔드포인트·모델 ID 차이입니다. 호출부를 추상 레이어로 한 번 감싸 두면 나중에 마이그레이션이 훨씬 가볍습니다.
- **신규 시작이라면 처음부터 Foundry**: 새로 모델 실험을 시작하는 단계라면 GitHub Models는 이제 선택지가 아닙니다. Azure AI Foundry 문서를 먼저 1~2시간 정독하고 들어가세요. "기능은 같지만 셋업이 무겁다"는 점이 가장 큰 함정입니다.
- **모델 비교 문화 지키기**: 무료 비교판이 사라지면 자칫 '익숙한 모델 하나에 묶이는' 관성이 생깁니다. 작은 팀일수록 분기마다 30분이라도 의식적으로 모델 비교 시간을 떼어 두는 습관이 필요합니다. 이왕이면 표준 평가 프롬프트를 깃 저장소에 박아 두고, 어떤 플랫폼에서 돌리든 같은 테스트셋으로 측정하세요.
- **비용 관점에서 다시 보기**: GitHub Models는 사실상 마이크로소프트가 사용자 학습 비용을 대신 내준 셈이었습니다. 이번 이주로 그 보조금이 끝나는 만큼, AI 실험 예산을 0에서 다시 잡아야 합니다. 작은 팀일수록 월 5만~10만 원 수준의 실험 예산 라인을 따로 떼어 두는 게 현실적입니다.

## 원문 출처

[원문 보기](https://news.google.com/rss/articles/CBMilwFBVV95cUxOY0NBZ19RdzBfcTluTmwwZ3ZUaFQ3ME5VXzM1MklIYV9SeEI1VVItRVlQZllUY1V0Tmd4SWQ4UVE2TmRFRmNzVGZibm1WRkZMRi1oYjZtWlN4RVpwSlUwX3RFcXhJQi04TWhCTzl2QTlJcWhWNGY5dGk5Sk91bHZYTm9HemVPUDNPdWRMQ3FQOVBVU2ZGZTNV?oc=5)
