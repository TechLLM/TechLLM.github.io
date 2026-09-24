---
title: "AI가 코드를 고칠 때, 자기가 만든 엉성한 테스트로 자기를 통과시킬 수 있으니 테스트 만드는 역할과 코드 고치는 역할을 나누고 테스트를 중간에 못 바꾸게 하자는 논문이다."
date: 2026-09-25T07:33:16+09:00
draft: false
description: "EXECCRITIC는 코딩 에이전트에서 테스트 작성과 소스 코드 수정을 분리하는 test–verify–revise 프레임워크다. Test 에이전트가 이슈와 저장소를 보고 회귀 테스트 번들(test patch, 실행 명령, 행동 계약)을 만들고, fail-closed harness가 베이스 코드에서 깨끗하게 실패하는 테스트만 채택해 동결한다. Repair 에이전트는 이 고정 테스트의 실행 피드백만 보고 소스 코드만 수정한다."
tags: ["AI Agents / Code Generation / Software Engineering", "논문 분석", "논문 리뷰", "Test agent", "Repair agent", "fail-closed harness"]
categories: ["논문분석"]
---


AI가 코드를 고칠 때, 자기가 만든 엉성한 테스트로 자기를 통과시킬 수 있으니 테스트 만드는 역할과 코드 고치는 역할을 나누고 테스트를 중간에 못 바꾸게 하자는 논문이다.

**무엇이 문제였나** — 먼저 한 에이전트가 문제를 확인할 테스트를 만든다.
**어떻게 풀었나** — 그 테스트가 버그 있는 코드에서는 실패하는지 확인한 뒤 고정한다.
**그래서 뭐가 좋아졌나** — 다른 에이전트는 그 테스트 결과를 보며 코드만 고치고, 최종 정답 여부는 숨겨진 공식 평가가 판단한다.

> 학생이 답안도 쓰고 채점 기준도 마음대로 바꾸면 자기에게 유리하게 채점할 수 있다. 이 방법은 시험 전에 채점 기준을 따로 정해 잠가 두고, 학생은 답안만 고치게 하는 방식에 가깝다.

## 논문 정보

Leitian Tao, Baolin Peng, Haorui Wang, Hang Wang, Hao Cheng, Wenlin Yao, Qianhui Wu, Tao Ge, Sharon Li, Jianfeng Gao · University of Wisconsin–Madison, Microsoft Research, Georgia Tech · arXiv preprint (arXiv:2609.09133) · 2026

## 왜 중요한가

코딩 에이전트가 스스로 만든 쉬운 테스트만 통과하고 실제 문제는 못 고치는 일이 생길 수 있다. EXECCRITIC는 채점 기준에 해당하는 테스트를 먼저 따로 만들고, 코드를 고치는 동안 그 기준을 바꾸지 못하게 해서 자기검증의 신뢰도를 높인다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Test 에이전트 Base-to-Gold 성공률 | **62.2%%** | Qwen3.5-35B-A3B 베이스 22.2%에서 SFT+RL 학습 후 +40.0pp |
| 전체 시스템 해결율 (SWE-bench Verified) | **72.6%%** | 학습된 Qwen Test+Repair 조합, 원래 no-test 베이스라인 61.2% 대비 +11.4pp |
| Trained Repair no-test Round-0 | **68.3%%** | Repair RL 학습만 했을 때 첫 시도 해결율, 베이스 Repair 61.2% 대비 +7.1pp |
| Trained Repair + Oracle F2P | **77.6%%** | 학습된 Repair가 privileged Oracle F2P 피드백을 사용할 때의 참고 성능, no-test 61.2% 대비 +16.4pp |

## 어떻게 동작하나

EXECCRITIC는 두 단계로 구성된다. Learn to Test 단계에서 Test 에이전트는 이슈와 베이스 저장소를 보고 저장소-네이티브 테스트 패치, 정확한 실행 명령, JSON 행동 계약으로 된 Test bundle을 만든다. harness는 이 번들을 검증하고 베이스 코드에서 깨끗하게 실패하는 첫 제출을 채택한다. Gold 패치와 후보 패치 실행 결과는 학습 보상과 오프라인 분석에만 쓰이며, 평가 시 Repair 단계 진입 여부를 고르는 데 쓰지 않는다. Test to Improve 단계에서는 채택된 테스트 번들을 동결하고 Repair 에이전트가 최대 5회의 feedback-guided revision 동안 소스 패치만 수정한다. 테스트가 PASS하면 controller가 즉시 해당 패치를 제출하고, 끝까지 통과하지 못하면 마지막 후보를 제출한다. 학습은 역할별로 분리된다. Test는 DeepSeek-V4-Flash-0731의 5K trajectory로 SFT한 뒤 GRPO로 학습하며, 보상은 Base-to-Gold 성공과 후보 패치에 대한 balanced accuracy를 반영한다. Repair는 별도 GRPO로 학습하며, 고정된 Oracle F2P 테스트 피드백과 공식 평가 결과를 이용하고 Round-0 정답 보상 1.5가 revision 후 정답 보상 1.0보다 크다. 최종 generated-test 배포 조건에서는 학습된 Qwen Test와 Repair 에이전트를 조합하며 GPT-5.6이나 Oracle 피드백을 사용하지 않는다.

핵심 수식:

```
Qx(b) = Bx(b)Gx(b)
BAx(b) = 1/2(TPR + TNR)
rT_x(b) = -0.2 if no valid submission; 0 if Bx(b)=0 or Gx(b)=0; 0.2 if Qx(b)=1 and BAx(b)<0.8; 0.5 if Qx(b)=1 and 0.8<=BAx(b)<1; 1.0 if Qx(b)=1 and BAx(b)=1
rR_x(pt) = 0 if invalid terminal patch; 0.1 if selected training test fails; 0.2 if selected test passes but official evaluator fails; 1.0 if selected test and official evaluator pass after revision; 1.5 if both pass at Round 0
```

Bx(b)는 Test bundle b가 베이스 저장소 RB에서 깨끗하게 실패하면 1, Gx(b)는 Gold 패치가 적용된 저장소 RG에서 통과하면 1이다. Qx(b)는 두 조건을 모두 만족하는 Base-to-Gold 성공 지표다. BAx(b)는 후보 Repair 패치에서 정답 패치를 통과시키는 비율(TPR)과 오답 패치를 실패시키는 비율(TNR)의 평균이다. rT_x는 Test 에이전트 보상이고, rR_x는 Repair 에이전트의 terminal reward로 selected training test 결과, 공식 평가 결과, Round-0 여부를 반영한다.

## 한계와 주의할 점

- Test와 Repair를 별도 정책으로 학습하므로 현재 형태에서는 단일 체크포인트 배포가 아니며, 두 역할과 harness를 함께 운영해야 한다.
- 학습된 Qwen Test 에이전트(62.2%)는 GPT-5.6-sol(87.8%)보다 25.6pp 낮아 test quality 개선 여지가 크다.
- Python-only post-training 뒤 교차언어 Base-to-Gold 성능이 고르지 않다(Python 62.2%, Rust 66.7%, C++ 58.3%, C 26.1%, Java 2.4%).
- Base-gate 실패 시 feedback-guided repair를 시작하지 않고 Round-0 패치를 제출하므로, 해당 케이스에서는 test–verify–revise의 이점을 얻지 못한다.
- SWE-bench Pro에서는 GPT-5.6 generated test의 개선이 +0.7pp에 그쳐, 단일 generated bundle이 넓은 행동 범위를 충분히 덮지 못할 수 있다.
- Oracle F2P 결과는 privileged reference feedback이지 이론적 상한선은 아니다.
- Test 에이전트가 베이스에서 깨끗하게 실패하는 테스트를 만들지 못하면 Base-gate failure가 되어 feedback-guided repair가 시작되지 않는다.
- Test가 잘못된 행동 계약을 코드로 만들면 Repair 에이전트가 그릇된 요구사항을 만족하는 방향으로 수정할 수 있다(Base Qwen 테스트가 61.2%를 57.3%로 떨어뜨린 사례).
- 후보 패치 실행 중 운영 오류가 생기면 해당 Test trajectory는 advantage=0으로 마스킹되어 학습 신호가 사라진다.
- 로컬 generated test PASS는 공식 평가 통과를 보장하지 않으며, 논문도 공식 evaluator가 최종 권한을 가진다고 명시한다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### RAG/재순위 단계에 "검증자 동결" 패턴 적용

EXECCRITIC의 핵심은 Test 에이전트가 만든 검증 기준을 Repair 에이전트가 수정할 수 없게 동결하는 것이다. 검색 결과 재순위 단계에서도 같은 에이전트가 평가 기준과 순위를 모두 만들면 자기 선택에 유리한 기준을 만들 수 있다. 별도 평가자 에이전트가 검증 질문/기준을 만들고 고정한 뒤, 재순위 에이전트는 기준을 바꾸지 않고 후보 순위만 조정하도록 분리할 수 있다.

**적용 지점** — RAG 재순위 단계, 검색 품질 자기검증

**기대 효과** — 코드 repair에서 no-test 61.2%에서 trained Test+Repair 72.6%로 오른 것처럼, 자기검증 기준을 고정하면 검증 신뢰도 향상을 기대할 수 있음

### Base-gate 폴백을 자기검증 시스템에 안전망으로 도입

EXECCRITIC는 Test 에이전트가 베이스에서 깨끗하게 실패하는 테스트를 만들지 못하면 Base-gate failure로 표시하고 feedback-guided repair를 시작하지 않는다. 자기검증을 쓰는 도구 사용 에이전트에서도 검증자가 최소한의 실패 사례를 만들지 못하면 검증 루프를 멈추고 첫 시안, 별도 평가, 또는 사람 검토로 넘기는 안전장치를 둘 수 있다.

**적용 지점** — 에이전트 자기검증 단계, 코드/문서 자동 검토

**기대 효과** — 검증 실패가 잘못된 수정 루프로 이어지는 것을 막고, Base-gate 실패 케이스를 전체 평가 분모에 남겨 성능 착시를 줄임

### Direct-solve 보너스로 첫 시도 정확도 우선순위화

EXECCRITIC의 Repair 보상은 Round-0에서 selected test와 official evaluator를 모두 통과하면 1.5, revision 후 통과하면 1.0을 준다. 보너스가 없는 T2I는 Round-0 66.4%, 최종 71.4%였고, full T2I는 Round-0 68.3%, 최종 72.6%였다. 자기수정 시스템에서도 첫 답변을 대충 내고 나중에 고치는 전략을 막으려면 direct-solve 보상을 크게 둘 수 있다.

**적용 지점** — 자기수정 단계가 있는 코드/문서/계획 에이전트

**기대 효과** — Table 3: full T2I가 no direct bonus 대비 Round-0 +1.9pp, final +1.2pp

### 후보 balanced accuracy 보상으로 검증자 역할 학습

Test 에이전트 보상은 Base-to-Gold만 보지 않고 후보 Repair 패치에 대한 TPR/TNR 평균인 balanced accuracy도 반영한다. Qx(b)=1일 때 BA<0.8은 0.2, 0.8<=BA<1은 0.5, BA=1은 1.0을 받는다. 리뷰어/필터 역할을 학습시킬 때도 맞는 것만 통과시키는 능력과 틀린 것을 거부하는 능력을 함께 보상하면 통과 편향을 줄일 수 있다.

**적용 지점** — 자기검증 에이전트, 후보 생성 후 필터/리뷰어 역할

**기대 효과** — Test RL 후 Qwen Base-to-Gold가 22.2%에서 62.2%로 상승하고 Codex-5.3 61.0%와 비슷한 수준에 도달

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | Test/Repair 분리 harness 구축 및 베이스라인 측정 | 1) 이슈+저장소 입력으로 베이스에서 깨끗하게 실패하는 회귀 테스트 번들을 생성하는 Test 모듈 구현 2) 테스트 동결 + Repair 모듈에 bounded feedback만 반환하는 harness 구현 3) 동일 백본으로 no-test 베이스라인과 generated-test 피드백 조건을 모두 측정 | 현재 환경에서 테스트 피드백이 도움이 되는지 해로운지(-3.9pp vs +4.1pp)를 정량적으로 판별 가능 |
| Phase 2 | 역할별 RL 학습 파이프라인 적용 | 1) Test SFT(교사 모델 5K trajectory) 이후 GRPO(Base-to-Gold + 후보 balanced accuracy 보상) 2) Repair GRPO(Round-0 보너스 1.5 vs revision 보상 1.0, 고정 Oracle F2P 피드백) 3) DAPO-style dynamic sampling으로 보상 분산이 있는 issue group 중심 학습 | 학습된 Test와 Repair 조합으로 SWE-bench Verified에서 61.2%→72.6%, +11.4pp 성능 향상 가능 |
| Phase 3 | 한계 보강 및 운영 효율화 | 1) SWE-bench Pro처럼 넓은 행동 검증이 필요한 케이스를 위한 multi-check bundle 탐색 2) Java/C 등 약한 언어를 위한 추가 데이터와 post-training 3) 평균 추가 13턴 수준의 revision 비용을 기준으로 latency와 비용 제한 설정 4) 역할 조건화를 통한 shared-weight 또는 단일 체크포인트 학습 연구 | Oracle F2P 참고 성능과의 5.0pp 격차를 줄이고 다국어/장기 시나리오로 적용 범위 확장 |

---

원문 PDF: `2026-09-09-execcritic-learn-to-test-test-to-improve-for-coding-agents.pdf`
