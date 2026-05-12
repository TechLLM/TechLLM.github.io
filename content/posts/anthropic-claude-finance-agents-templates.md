---
title: "Anthropic, 금융 업무용 Claude 에이전트 10종 공개 — 피치북부터 월말 결산까지"
date: 2026-05-12T16:44:00+09:00
draft: false
description: "Anthropic이 피치북 작성·KYC 심사·월말 결산 등 금융 실무 10개 영역을 자동화하는 Claude 에이전트 템플릿을 공개했다. Claude Cowork·Claude Code 플러그인과 Managed Agents 쿡북 형태로 제공되며, Excel·PowerPoint·Word·Outlook add-in과 결합해 분석가 워크플로 전체를 잇는다."
cover:
  image: "/images/anthropic-claude-finance-agents-templates-cover.jpg"
  alt: "Anthropic이 공개한 금융 서비스용 Claude 에이전트 템플릿 10종을 표현한 일러스트"
  caption: ""
tags: ["Claude", "Anthropic", "AI에이전트", "금융AI", "ManagedAgents", "KYC", "재무모델링", "Excel"]
categories: ["AI"]
---

## 핵심 요약

- Anthropic이 금융 서비스용 Claude 에이전트 템플릿 **10종**을 공개했다 — 리서치·클라이언트 커버리지 5종, 재무·운영 5종.
- 각 템플릿은 **Claude Cowork·Claude Code 플러그인**, 또는 **Claude Managed Agents 쿡북** 두 형태로 즉시 도입할 수 있다.
- Claude **Excel·PowerPoint·Word add-in**이 정식 출시됐고 Outlook도 곧 합류한다. 모델·덱·메모 간 컨텍스트가 끊김 없이 이어진다.
- Dun & Bradstreet, FactSet, Moody's MCP 앱 등 새 커넥터와 파트너가 추가되며 거버넌스 기반 실시간 데이터 접근이 확대됐다.
- Claude Opus 4.7이 Vals AI Finance Agent 벤치마크에서 **64.37%**로 업계 1위를 기록했다.

## 왜 이번 발표가 의미 있나

Anthropic은 이번 발표에서 새로운 모델보다 **금융 업무 형태에 맞춘 에이전트 패키지**에 무게를 두었다. 단일 LLM의 성능 향상이 아니라 분석가·트레이더·컴플라이언스가 매일 반복하는 작업 단위에 맞춰 스킬·데이터·서브에이전트가 묶여 있다는 게 핵심이다. Vals AI Finance Agent 벤치마크에서 Claude Opus 4.7이 **64.37%**로 1위에 오른 점도 같은 방향을 가리킨다. 모델만 좋아진 게 아니라 모델·도구·데이터 결합 결과가 경쟁 모델보다 앞서 있다는 신호다.

이런 패키지가 의미를 갖는 이유는 금융권 도입 장벽이 모델 정확도가 아니라 **데이터 거버넌스·감사 가능성·기존 도구와의 통합**에 있기 때문이다. 한 가지를 만족해도 나머지 두 개가 막히면 PoC에서 끝났다. 이번 발표는 그 세 축을 동시에 묶어 시장에 던졌다.

## 무엇이 달라졌나 — 에이전트 템플릿 10종

Anthropic이 2026년 5월 5일 공개한 [Agents for financial services](https://www.anthropic.com/news/finance-agents)는 단순한 모델 출시가 아니라 **참조 아키텍처(reference architecture)** 묶음이다. 각 템플릿은 ① 작업용 스킬, ② 거버넌스 기반 데이터 커넥터, ③ 서브에이전트(예: 컴파러블 선택, 방법론 검증)를 한 묶음으로 패키징해 제공한다. 회사는 자체 모델링 컨벤션·리스크 정책·승인 흐름에 맞춰 그대로 변형해 쓰면 된다.

**리서치 / 클라이언트 커버리지** 5종은 분석가 업무를 직접 단축한다.

- **Pitch builder** — 타겟 리스트 작성, 컴파러블 분석, 피치북 초안까지.
- **Meeting preparer** — 미팅·콜 전 클라이언트·상대방 브리프 자동 정리.
- **Earnings reviewer** — 실적 발표 트랜스크립트·필링 분석, 모델 업데이트, 투자 논지 변동 플래깅.
- **Model builder** — 필링·데이터 피드·분석가 입력에서 재무 모델 생성·유지.
- **Market researcher** — 섹터·이슈어 동향 추적, 뉴스·리서치 합성, 크레딧·리스크 검토용 항목 플래깅.

**재무 / 운영** 5종은 백오피스 부담을 흡수한다.

- **Valuation reviewer** — 컴파러블·방법론·회사 검토 표준에 맞춰 평가 검증.
- **General ledger reconciler** — 총계정원장 조정과 NAV 계산을 books of record 기준으로 검증.
- **Month-end closer** — 월말 결산 체크리스트 실행, 분개 작성, 결산 보고서 산출.
- **Statement auditor** — 재무제표의 일관성·완전성·감사 준비도 검토.
- **KYC screener** — 엔티티 파일 조립, 원천 문서 검토, 컴플라이언스 에스컬레이션 패키징.

전체 템플릿은 [Anthropic financial services GitHub 마켓플레이스](https://github.com/anthropics/financial-services)에서 플러그인·쿡북 형태로 받을 수 있다.

## 두 가지 운영 모드 — 분석가 옆에 두거나, 야간에 돌리거나

같은 템플릿이지만 운영 방식은 두 갈래다.

**Plugin 모드 (Claude Cowork / Claude Code)** — 분석가 데스크톱에서 소프트웨어 옆에 붙어 동작한다. 예컨대 Pitch builder에 타겟 리스트를 주면, Excel 컴파러블 모델 + PowerPoint 피치북 초안 + Outlook 커버 노트까지 한 번에 돌려준다.

**Claude Managed Agent 모드** — 동일 템플릿이 Claude Platform에서 자율 실행된다. 딜 북 전체나 야간 스케줄을 처리할 때 유리하다. 멀티 아워에 걸친 장기 세션, 툴별 권한 제어, 자격증명 볼트, 컴플라이언스·엔지니어가 모든 툴 호출과 결정을 검사할 수 있는 **Claude Console 감사 로그**가 함께 따라온다.

두 모드 모두 최종 결과가 고객에게 나가거나 파일링되기 전 사람이 **검토·반복·승인**하는 단계를 명시적으로 유지한다.

## Microsoft 365 전 영역에 들어온 Claude

Claude Excel·PowerPoint·Word add-in이 일반 출시됐고 Outlook용도 곧 추가된다. 핵심은 단순 자동화가 아니라 **컨텍스트 연속성**이다. Excel에서 시작한 모델을 PowerPoint 덱으로 옮길 때, 분석가가 다시 설명할 필요 없이 Claude가 동일한 작업 맥락을 그대로 가져간다.

- Outlook — 이메일 트리아지, 미팅 조율, 자기 톤에 맞춘 응답 초안.
- Excel — 필링·데이터 피드 기반 재무 모델 빌딩, 연결된 워크북 간 수식 감사, 민감도 분석.
- PowerPoint — 수치가 바뀌면 자동으로 갱신되는 덱 작성.
- Word — 사내 템플릿에 맞춘 크레딧 메모 편집.

추가로 Claude Cowork의 **Dispatch** 기능으로 텍스트·음성을 통해 자리를 떠난 사이에도 분석가의 로컬 파일에서 작업을 계속 시키고 결과만 받아볼 수 있다.

## 데이터 파트너 — 거버넌스 위에 얹은 실시간 액세스

Claude는 이미 FactSet, S&P Capital IQ, MSCI, PitchBook, Morningstar, Chronograph, LSEG, Daloopa 등 시장 데이터·리서치 플랫폼과 거버넌스 기반으로 연결돼 있다. 이번에 신규 추가된 커넥터·MCP 앱은 다음과 같다.

- **Dun & Bradstreet** — 글로벌 기업 신원 검증의 표준 D-U-N-S 데이터.
- **Fiscal AI** — 공모주 펀더멘털 실시간 커버리지.
- **Financial Modeling Prep** — 주식·ETF·암호화폐·외환·원자재의 실시간 시세·재무·필링·트랜스크립트.
- **Guidepoint / Third Bridge** — 컴플라이언스 검토 완료된 전문가 인터뷰 트랜스크립트.
- **IBISWorld** — 산업별 매출·재무비율·리스크 점수·비용 구조·전망.
- **SS&C Intralinks** — DealCenter AI 데이터룸 접근(실사 Q&A, 딜 활동 추적).
- **Verisk** — 손해보험 데이터(언더라이팅·클레임·리스크 분석).
- **Moody's MCP 앱** — 600만+ 공·사기업 신용 등급·데이터.

Moody's가 MCP 앱 형태로 들어왔다는 점은 의미가 크다. 커넥터가 데이터 접근을 제공한다면, MCP 앱은 **공급자의 자체 UI·도구를 Claude 안에 직접 임베드**한다.

## 실제 도입 사례

발표문에 첨부된 인용은 단순 마케팅 멘트가 아니라 운영 변화를 시사한다. Citadel의 Atte Lahtiranta는 "분석가가 Claude for Excel로 커버리지 모델을 만들고 업데이트하며, 노이즈에서 신호를 분리하고 자체 작업을 압박 테스트한다"고 밝혔다. FIS의 Stephanie Ferris는 "AML 조사를 며칠에서 분 단위로 압축하는 에이전트를 함께 만들고 있다"고 언급했다. Walleye Capital은 400명 헤지펀드 직원 **전원**이 Claude Code를 사용한다고 공개했다.

## 실무자가 볼 핵심 포인트

| 구분 | 시사점 |
|------|--------|
| **도입 속도** | 참조 아키텍처 제공으로 PoC가 아닌 **수일 단위 실제 업무 적용** 가능 |
| **인간 검토 유지** | 두 운영 모드 모두 클라이언트 전달·파일링 전 명시적 사람 승인 단계 보존 |
| **컨텍스트 연속성** | Excel·PowerPoint·Word·Outlook 간 작업 맥락 자동 이전 — 재설명 비용 제거 |
| **거버넌스** | Managed Agents의 툴별 권한·자격증명 볼트·전체 감사 로그가 컴플라이언스 요구 충족 |
| **데이터 신뢰성** | Moody's·D&B 등 1차 데이터 소스가 MCP·커넥터로 직접 접근 — 환각 위험 감소 |
| **모델 선택 기준** | Vals AI Finance Agent 벤치마크 64.37%의 Claude Opus 4.7이 금융 업무 기준선 |

금융 IT 부문에서 봐야 할 것은 단일 LLM 성능이 아니라 **에이전트 + 데이터 + 사람 검토 루프**의 총체적 워크플로 변화다. 이번 발표는 그 세 축이 모두 한 번에 갖춰진 첫 패키지에 가깝다.

## 원문 출처

*원문: [Agents for financial services](https://www.anthropic.com/news/finance-agents) — Anthropic, 2026.05.05*
