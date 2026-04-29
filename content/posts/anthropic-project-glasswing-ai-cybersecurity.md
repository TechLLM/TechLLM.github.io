---
title: "AI가 제로데이를 사냥하기 시작했다: Anthropic Project Glasswing의 진짜 의미"
date: 2026-04-29T22:21:00+09:00
draft: false
description: "Anthropic의 Project Glasswing 발표를 한국어로 번역·해설했다. Claude Mythos Preview가 보여준 AI 기반 취약점 탐지 능력과 사이버보안 산업의 변화를 핵심 인사이트 중심으로 정리한다."
cover:
  image: "/images/anthropic-project-glasswing-cover.jpg"
  alt: "Anthropic Project Glasswing 원문 대표 이미지"
  caption: "Source: Anthropic"
tags:
  - Anthropic
  - ProjectGlasswing
  - ClaudeMythos
  - Cybersecurity
  - AIAgent
  - ZeroDay
  - AI안전
  - TechLLM
categories:
  - AI Security
  - AI Agent
---

출처: Anthropic  
문서유형: 번역·해설  
#Anthropic #ProjectGlasswing #ClaudeMythos #Cybersecurity #ZeroDay #AIAgent

![Anthropic Project Glasswing 원문 대표 이미지](/images/anthropic-project-glasswing-cover.jpg)

## 핵심 요약

Anthropic이 **Project Glasswing**을 발표했습니다. AWS, Apple, Google, Microsoft, NVIDIA, Cisco, CrowdStrike, Linux Foundation, JPMorganChase 등 주요 기업이 참여하는 사이버보안 협력 프로젝트입니다.

핵심은 아직 일반 공개되지 않은 프론티어 모델 **Claude Mythos Preview**입니다. Anthropic은 이 모델이 이미 수천 개의 고위험 취약점을 찾아냈고, 주요 운영체제와 웹 브라우저에서도 새로운 취약점을 발견했다고 설명합니다.

이 발표가 중요한 이유는 단순히 “AI가 보안도 잘한다”가 아닙니다. 이제 AI가 인간 최상위 보안 전문가에 가까운 수준으로 **취약점을 찾고, 익스플로잇을 구성하고, 방어자가 먼저 패치할 수 있게 돕는 단계**에 들어섰다는 신호입니다.

## Project Glasswing은 무엇인가

Project Glasswing은 세계의 핵심 소프트웨어를 AI로 더 안전하게 만들기 위한 방어 중심 프로젝트입니다. Anthropic은 Claude Mythos Preview 접근 권한을 주요 파트너와 40개 이상의 추가 조직에 제공해, 이들이 자사 시스템과 오픈소스 인프라를 점검하고 보완할 수 있게 합니다.

Anthropic은 이 프로젝트에 최대 **1억 달러 규모의 Mythos Preview 사용 크레딧**을 제공하고, 오픈소스 보안 조직에도 **400만 달러를 직접 기부**한다고 밝혔습니다. 단순한 모델 발표가 아니라, 방어자들이 공격자보다 먼저 AI 사이버 역량을 확보하도록 산업 전체를 움직이려는 시도입니다.

## Claude Mythos Preview가 보여준 위험한 능력

Anthropic에 따르면 Mythos Preview는 지난 몇 주 동안 수천 개의 zero-day 취약점을 찾아냈습니다. 여기에는 주요 운영체제, 주요 웹 브라우저, 그리고 중요한 소프트웨어들이 포함됩니다.

공개된 사례도 꽤 충격적입니다.

- OpenBSD에서 27년 된 취약점을 발견했습니다.
- FFmpeg에서 16년 된 취약점을 찾아냈습니다. 해당 코드는 자동 테스트 도구가 500만 번이나 실행했지만 문제를 잡지 못했던 부분입니다.
- Linux kernel에서는 여러 취약점을 연결해 일반 사용자 권한에서 전체 시스템 장악으로 이어지는 경로를 찾아냈습니다.

Anthropic은 관련 취약점을 유지보수자에게 보고했고, 공개 가능한 일부는 이미 패치됐다고 설명합니다.

## AI 보안의 본질: 공격자도 같은 능력을 갖게 된다

이 발표를 낙관적으로만 보면 안 됩니다. 같은 능력은 공격자에게도 강력한 무기가 됩니다. Anthropic이 Project Glasswing을 “긴급한 방어 프로젝트”로 설명하는 이유도 여기에 있습니다.

지금까지 고급 취약점 탐지는 매우 숙련된 보안 전문가의 영역이었습니다. 하지만 프론티어 AI 모델이 코드를 읽고, 취약점을 추론하고, 익스플로잇까지 구성할 수 있게 되면 비용과 진입장벽이 급격히 낮아집니다.

이는 사이버 공격의 빈도와 속도를 바꿀 수 있습니다. 과거에는 취약점 발견부터 악용까지 시간이 걸렸지만, AI가 들어오면 그 창이 훨씬 짧아질 수 있습니다. CrowdStrike가 “취약점 발견과 공격 사이의 창이 몇 달에서 몇 분으로 줄어들 수 있다”고 경고한 것도 이 맥락입니다.

## 방어자가 먼저 AI를 써야 하는 이유

다행히 같은 능력은 방어에도 쓸 수 있습니다. AI는 거대한 코드베이스를 읽고, 오래 숨어 있던 취약점을 찾고, 패치 방향을 제안하고, 보안팀이 놓친 경로를 탐색할 수 있습니다.

Project Glasswing의 방향은 분명합니다. 공격자에게 AI 사이버 능력이 퍼지기 전에, 방어자들이 먼저 이 능력을 확보해야 한다는 것입니다. 특히 오픈소스 유지보수자는 거대한 현대 소프트웨어 생태계의 기반을 책임지지만, 전담 보안팀을 갖기 어려운 경우가 많습니다. Mythos급 모델이 유지보수자에게 “보안 보조자”가 될 수 있다면 파급력은 큽니다.

Anthropic은 Alpha-Omega, OpenSSF, Apache Software Foundation 등에 기부를 진행하며 오픈소스 보안 대응 역량도 강화하겠다고 밝혔습니다.

## 성능 수치가 말하는 것

Anthropic은 Mythos Preview가 CyberGym 같은 보안 평가에서 Claude Opus 4.6보다 뚜렷하게 앞선다고 설명합니다. 예를 들어 Cybersecurity Vulnerability Reproduction에서 Mythos Preview는 **83.1%**, Opus 4.6은 **66.6%**를 기록했습니다.

또한 SWE-bench, Terminal-Bench, BrowseComp 같은 여러 코딩·에이전트 평가에서도 높은 성능을 보였다고 합니다. 중요한 점은 이 성능이 단순 코딩 점수에 그치지 않고, 실제 취약점 탐지와 익스플로잇 구성으로 이어졌다는 것입니다.

즉, 앞으로 보안 모델의 경쟁력은 “코드를 잘 고친다” 수준이 아니라 **복잡한 시스템을 읽고, 공격 경로를 찾고, 방어 패치를 돕는 agentic security 능력**으로 평가될 가능성이 큽니다.

## TechLLM 관점: 이제 보안도 하네스 싸움이다

이 발표는 우리 TechLLM/OpenClaw 관점에서도 중요한 힌트를 줍니다. 모델 자체의 능력도 중요하지만, 실제 가치는 모델을 어떤 하네스 안에 넣느냐에서 나옵니다.

Mythos Preview가 강력한 이유는 단순히 모델이 똑똑해서만이 아닙니다. 취약점 탐지, 바이너리 테스트, 로컬 분석, 보고, 공개 전 조율, 패치 검증까지 이어지는 **방어 워크플로우**에 들어갔을 때 가치가 생깁니다.

우리 시스템에 적용하면 다음 방향이 중요합니다.

첫째, 블로그·위키 자동화에서도 “생성”보다 “검증 루프”를 강화해야 합니다. AI가 만든 지식 노트나 글은 원문 링크, 수치, 주장, 리스크, 적용점을 자동으로 확인해야 합니다.

둘째, 코드 작업용 에이전트에는 보안 훅이 더 필요합니다. 단순히 테스트 통과가 아니라 의존성 취약점, 위험 명령, 비밀키 노출, 외부 전송 여부를 점검하는 루프가 있어야 합니다.

셋째, 오픈소스나 개인 프로젝트도 AI 보안 보조자를 붙일 수 있는 시대가 옵니다. 대기업만이 아니라 작은 프로젝트도 정기적으로 코드와 설정을 점검하는 자동화가 필요해질 수 있습니다.

## 리스크와 한계

Anthropic은 Mythos Preview를 일반 공개하지 않겠다고 했습니다. 그만큼 위험한 능력이라는 뜻입니다. 방어 목적의 사용도 중요하지만, 모델이 생성할 수 있는 위험 출력물을 감지하고 차단하는 safeguard가 먼저 필요합니다.

또한 수천 개의 취약점을 찾았다는 발표는 강력하지만, 모든 세부 정보가 즉시 공개되는 것은 아닙니다. 실제 산업적 효과는 파트너들이 얼마나 많은 취약점을 수정하고, 공개 가능한 교훈을 얼마나 공유하느냐에 달려 있습니다.

## 정리: AI 사이버보안은 이미 임계점을 넘었다

Project Glasswing은 단순한 파트너십 발표가 아닙니다. AI가 사이버보안에서 공격과 방어 양쪽의 판을 바꾸기 시작했다는 신호입니다.

앞으로 중요한 질문은 “AI가 취약점을 찾을 수 있나?”가 아닙니다. 이미 그럴 수 있다는 증거가 나오고 있습니다. 더 중요한 질문은 이것입니다.

**공격자보다 방어자가 먼저, 더 안전하게, 더 넓게 이 능력을 배치할 수 있는가?**

AI가 제로데이를 사냥하는 시대가 열렸다면, 보안의 기본값도 바뀌어야 합니다. 사람이 가끔 점검하는 방식으로는 부족합니다. 지속적으로 읽고, 찾고, 검증하고, 패치하는 AI 기반 방어 루프가 새로운 표준이 될 가능성이 큽니다.

원문 : <a href="https://www.anthropic.com/glasswing">Project Glasswing: Securing critical software for the AI era</a>
