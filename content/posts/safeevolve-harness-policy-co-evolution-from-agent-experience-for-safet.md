---
title: "에이전트가 실제 작업 중 겪은 실패와 회복 사례를 모아, 외부의 안전 규칙과 모델의 판단 습관을 함께 고치는 방법이다."
date: 2026-10-10T07:33:10+09:00
draft: false
description: "LLM 에이전트의 안전성을 위해 외부 하네스(안전 프롬프트·계층형 스킬 뱅크)와 내부 정책(모델 파라미터)을 함께 진화시키는 경험 주도형 공진화 프레임워크를 제안한다. 완료된 on-policy 궤적에서 추출한 안전 신호를 bounded·versioned 하네스 업데이트와 2단계 SFT-RL 정책 최적화에 번갈아 투입한다."
tags: ["Agent Safety Alignment / LLM Agent", "논문 분석", "논문 리뷰", "Agent Harness", "Policy Optimization", "Indirect Prompt Injection"]
categories: ["논문분석"]
---


에이전트가 실제 작업 중 겪은 실패와 회복 사례를 모아, 외부의 안전 규칙과 모델의 판단 습관을 함께 고치는 방법이다.

**무엇이 문제였나** — 문제: 도구를 쓰는 AI 에이전트는 웹페이지·이메일·파일·도구 응답에 숨어 있는 나쁜 지시나, 사용자의 위험한 요청에 끌려갈 수 있다.
**어떻게 풀었나** — 해결: 작업 기록을 살펴 안전 실패를 분류하고, 외부 안전 매뉴얼을 조금씩 고친 뒤, 모델도 그 매뉴얼을 실제 행동에서 쓰도록 다시 학습시킨다.
**그래서 뭐가 좋아졌나** — 결과: 주입 공격 성공률과 유해 요청 수행이 줄었고, 정상 작업 능력은 대체로 유지되거나 일부 개선되었다.

> 에이전트를 신입사원, 하네스를 사내 매뉴얼, 정책을 일하는 습관이라고 보면 된다. 실수 사례가 쌓이면 회사는 매뉴얼을 고치고, 신입은 그 매뉴얼을 보고 다시 훈련받아 실제 행동도 바뀐다. 매뉴얼만 좋아지고 사람이 못 따라가도 문제이고, 사람만 훈련받고 매뉴얼이 낡아도 문제라서 둘을 함께 고친다는 생각이다.

## 논문 정보

Qinghua Mao, Wanying Qu, Dadi Guo, Leitao Yuan, Qingyu Liu, Yu Li, Guanxu Chen, Yanwei Fu, Xi Lin, Xia Hu, Dongrui Liu · Shanghai AI Laboratory, SJTU, Fudan University, HKUST, Zhejiang University · arXiv preprint arXiv:2609.02786 · 2026

## 왜 중요한가

AI 에이전트가 검색, 이메일, 예약, 파일 처리 같은 실제 도구를 대신 쓰게 되면 최종 답변만 안전하면 충분하지 않다. 중간 도구 호출이나 실행 과정에서도 위험한 행동을 피해야 한다. SafeEvolve는 배포 뒤에 쌓이는 실제 실행 경험을 이용해 안전 규칙과 모델 행동을 같이 개선하는 한 가지 실험적 방법을 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| AgentDojo ASR (Qwen3.5-4B) | **2.37% → 0.79%%** | 환경 주입 공격 성공률(Base 대비 약 3배 감소) |
| AgentHarm 유해 점수 (Qwen3.5-4B) | **56.45 → 12.27score** | 악의적 멀티스텝 요청 준수 점수(낮을수록 안전) |
| AgentHarm 거부율 (Qwen3.5-4B) | **28.98% → 83.83%%** | 유해 요청에 대한 명시적 거부 비율 |
| AgentDojo 정상 효용 (Qwen3-4B-Instruct-2507) | **44.33% → 60.82%%** | 공격 부재 시 정상 작업 완료율 |

## 어떻게 동작하나

SafeEvolve는 완료된 on-policy 궤적을 안전 경험으로 재사용해 외부 하네스와 내부 정책을 함께 개선하는 루프다. 하네스 측은 rollout 증거를 안전 프롬프트와 계층형 SkillBank 같은 컴포넌트 단위의 bounded mutation으로 바꾸고, parent와 candidate를 같은 작업 패널에서 비교하는 accept-reject gate로 안전·효용·실행 품질을 검증한다. 정책 측은 진화된 하네스에서 검색된 스킬을 컨텍스트로 넣어 harness-use SFT로 먼저 사용법을 익히게 하고, 이후 verifier-decomposed reward로 GRPO를 수행해 멀티스텝 실행 중 안전 판단을 내재화한다. 매 라운드의 새 rollout은 다시 실패 버킷, 회복 사례, 메타데이터로 요약되어 다음 하네스 업데이트의 근거가 된다.

핵심 수식:

```
R(τ | z) = { U(τ), if z = clean; S(τ), if z = query; λ_U U(τ) + λ_S S(τ) + λ_US U(τ)S(τ), if z = injection }
Â_i = (R(τ_i | z(x)) - μ_x) / (σ_x + ε),  μ_x = (1/G) Σ_j R(τ_j | z(x))
J_policy(θ) = E[min(ρ_i,t(θ)Â_i, clip(ρ_i,t(θ), 1-ε, 1+ε)Â_i) - β_KL D_KL(π_θ || π_ref)]
```

R(τ | z)는 task type z(x) ∈ {clean, query, injection}에 따라 달라지는 trajectory reward다. U(τ)는 작업 완료 utility, S(τ)는 안전 점수이며, environment injection에서는 utility와 safety를 동시에 만족시키기 위해 U, S, U·S 항을 결합한다. Appendix A.5는 λ_U=0.25, λ_S=0.5, λ_US=0.25를 모든 backbone과 training run에 고정한다고 보고한다. Â_i는 같은 task에서 샘플링한 G개 trajectory의 group-relative advantage이고, J_policy는 clipping과 KL 정규화를 포함한 GRPO/PPO-style 목적함수다.

## 한계와 주의할 점

- 환경 주입 보상 가중치 λ_U=0.25, λ_S=0.5, λ_US=0.25는 모든 backbone과 training run에 고정되어 있어, 다른 도메인에서는 보상 균형 재조정이 필요할 수 있다.
- 온라인 하네스 업데이트(Tab. 7)는 일부 attacked utility를 올리기도 하지만, 전반적으로 안전성 회귀가 두드러진다. 예를 들어 Qwen3.5-4B online skill evolution은 AgentHarm harmful score를 12.27에서 27.02로 악화시키고 refusal을 83.83에서 62.99로 낮춘다.
- Qwen3-4B online skill evolution에서는 AgentHarm refusal이 fixed evolved skills의 71.93에서 6.29로 크게 떨어져, 학습 중 빠른 하네스 갱신에는 강한 global gate가 필요함을 보여준다.
- Cross-policy transfer(Fig. 6)는 가능하지만 비대칭적이다. 1.7B target은 AgentDyn utility를 거의 회복하지 못하고, 8B target은 안전성은 좋아져도 attacked utility가 떨어질 수 있다.
- Held-out ASB(Tab. 8)에서 SafeEvolve는 세 공격군 모두 최저 ASR을 달성하지만, DPI ASR은 71.92%로 여전히 높아 직접 주입 공격 일반화에는 한계가 남는다.
- SkillBank가 26개에서 47개로 커지고 최대 prompt length가 4096 tokens로 제한되어 있어, 장기 운영에서는 검색 우선순위·병합·만료 정책이 중요하다.
- 결합형 하네스(진화된 prompt+skills)가 단일 컴포넌트보다 항상 우월하지 않다. Tab. 5에서 Qwen3.5-4B evolved skills의 AgentDojo U-Attack은 60.72지만 prompt+skills는 59.91이고, ASR도 0.92에서 1.03으로 악화된다.
- 온라인 skill evolution은 새 실패를 빠르게 흡수할 수 있지만 malicious-query safety를 무너뜨릴 수 있다. Qwen3-4B에서 harmful score는 15.47에서 41.04로 악화되고 refusal은 71.93에서 6.29로 하락한다.
- 온라인 prompt evolution은 Qwen3.5-4B에서 AgentDojo U-Attack을 41.97에서 45.13으로 높이지만, AgentDyn ASR을 4.96에서 10.67로 악화시키고 AgentHarm refusal을 57.06에서 47.56으로 낮춘다.
- Fig. 7의 failure-bucket 분석은 accepted skill updates가 execution-recovery failure를 줄이지만 safe-but-incomplete behavior를 소폭 늘릴 수 있음을 보여준다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 계층형 안전 SkillBank에 Bounded Component Evolution 적용

에이전트의 safety prompt와 SkillBank를 수정 가능한 component로 보고, rollout에서 failure bucket과 recovery evidence를 모아 proposer가 한 번에 하나의 component만 bounded mutation하도록 제한한다. parent와 candidate를 같은 task panel에서 paired evaluation하고, accept-reject gate를 통과한 편집에 parent hash, target failure bucket, rollback condition, supporting evidence를 붙인다. 이는 원문 Eq. 5–8 및 Algorithm 1의 harness evolution 절차에 해당한다.

**적용 지점** — 에이전트 하네스(시스템 프롬프트·도구·메모리) 설정 및 진화 단계

**기대 효과** — 정책을 고정해도 Qwen3.5-4B evolved skills는 AgentDojo ASR 2.37%→0.92%, AgentHarm harmful score 56.45→16.80을 달성한다(Tab. 2).

### Verifier-Decomposed Safety-Utility 보상으로 RL 단계 안정화

단일 reward 대신 clean은 U(τ), malicious-query는 S(τ), environment-injection은 λ_U U(τ)+λ_S S(τ)+λ_US U(τ)S(τ)를 사용한다. Appendix A.5의 고정값은 λ_U=0.25, λ_S=0.5, λ_US=0.25다. 같은 task의 G개 rollout로 group-relative advantage를 계산하고, clipping과 KL regularization이 포함된 objective로 정책을 갱신한다. 이는 원문 Eq. 11–13에 해당한다.

**적용 지점** — 에이전트 RL 학습 루프의 보상 정의·그룹 샘플링·정책 갱신 단계

**기대 효과** — Qwen3.5-4B 기준 SafeEvolve는 GRPO 대비 AgentDojo utility 30.93→61.86, ASR 1.77→0.79, AgentHarm harmful score 63.82→12.27로 개선된다(Tab. 1).

### 에피소드별 메타데이터 기반 Skill Retrieval과 Dynamic Priority

Retrieve(S*, x, m_x, h_1)로 user task, metadata, tools, initial context에 맞는 skill을 고른다. General skills는 항상 후보가 되고, task-specific skills는 metadata match로, common-mistake skills는 environment injection, ambiguous identifier, missing argument, premature final answer 같은 trigger로 우선순위를 받는다. prompt budget을 넘으면 dynamically evolved skills와 가까운 metadata match를 먼저 유지한다.

**적용 지점** — 장기 기억·스킬 회수 단계(RAG 검색 또는 메모리 retrieval)

**기대 효과** — Tab. 3에서 default retrieval은 AgentHarm harmful 16.80/refusal 76.97이지만, no skill-bank retrieval은 harmful 56.45/refusal 28.98로 떨어진다. Dynamic priority 제거도 harmful 32.03/refusal 64.00으로 악화된다.

### 정책 내부화를 위한 Harness-Use SFT Cold Start

진화된 harness 하에서 rollout을 다시 수집하고 task-typed safety 및 utility verifier를 통과한 trajectory만 남긴다. system instructions, user messages, rendered skills, tool observations는 context로 사용하고 assistant response와 tool-call turns만 loss에 포함한다. 원문 Eq. 10과 Algorithm 1 line 3–4의 HarnessUseSFT 단계다.

**적용 지점** — 에이전트 정책 fine-tuning의 cold-start 단계

**기대 효과** — Fig. 3은 model-only RL이 AgentDojo utility under attack과 AgentHarm harmful score에서 불안정한 결과를 낼 수 있음을 보여준다. Coevo-Skill은 AgentDojo ASR 0.79와 AgentHarm harmful 12.27을 달성해 evolved harness 사용 학습의 중요성을 뒷받침한다.

### Failure-Bucket Attribution을 진화 수락 신호로 채택

rollout을 ask-info, immediate stop after injection detection, max-turn, no-progress loop, invalid tool call, safe-but-incomplete 같은 failure bucket으로 분류하고, parent와 candidate의 paired 변화량을 본다. Gate는 hard safety floor와 clean/attacked utility 회귀를 먼저 확인하고, 통과한 후보는 reward improvement와 failure reduction을 함께 고려한다. 원문 Fig. 7과 Appendix A.4의 Harness Evolution Gate Details에 근거한다.

**적용 지점** — 자기 개선·자동 진화 시스템의 후보 평가/품질 게이트 단계

**기대 효과** — Fig. 7은 accepted skillbank update 뒤 execution-recovery failure가 주로 줄고, 감소가 attacked settings에서 많이 발생함을 보여준다. 단, safe-but-incomplete behavior가 소폭 증가하는 trade-off도 함께 감시해야 한다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 — Safety Harness Evolution | 도메인별 안전 프롬프트와 계층형 SkillBank를 rollout 증거로부터 버전 관리하며 구축한다. | (1) 베이스 정책으로 rollout을 수집해 success category, failure bucket, metadata를 집계한다. (2) proposer가 한 번에 하나의 컴포넌트(prompt 또는 skill)만 targeted mutation하도록 제한한다. (3) parent와 candidate를 같은 internal rollout panel에서 비교한다. (4) safety, clean-task utility, execution quality가 gate를 통과한 편집만 versioned component change로 게시한다. | 정책 학습 없이도 Qwen3.5-4B에서 evolved skills는 AgentDojo ASR을 2.37에서 0.92로, AgentHarm harmful score를 56.45에서 16.80으로 낮춘다(Tab. 2). |
| Phase 2 — Harness-Use SFT Cold Start | 모델이 진화된 prompt와 retrieved skills를 받았을 때 언제 참고하고 어떻게 실행할지 먼저 익히게 한다. | (1) 진화된 harness 하에서 rollout을 수집하고 verifier-approved trajectories만 Dsft로 유지한다. (2) system instructions, user messages, rendered skills, tool observations는 context로 쓰고 assistant response와 tool-call turn만 loss에 포함한다. (3) 짧은 cold-start SFT로 RL 시작점을 안정화한다. | 원문 Fig. 3은 verifier reward만으로 RL을 수행하면 AgentDojo U-Attack이 크게 떨어지고 AgentHarm harmful score가 악화될 수 있음을 보인다. cold-start는 evolved harness guidance를 정책이 실제로 쓰게 만드는 준비 단계다. |
| Phase 3 — Harness-Augmented RL with Veri | clean/query/injection task type별로 분해된 reward를 사용해 안전과 효용을 동시에 내재화한다. | (1) 매 rollout에서 safety prompt와 episode-level skill subset을 context로 넣는다. (2) 같은 task의 G개 trajectory에 대해 task-typed reward와 group-relative advantage를 계산한다. (3) clip ε=0.2, KL coefficient 0.01의 GRPO-style objective로 정책을 업데이트한다. (4) 최근 rollout evidence를 다시 harness evolution의 근거로 축적한다. | Qwen3.5-4B에서 SafeEvolve는 AgentDojo ASR 0.79%, AgentHarm harmful score 12.27, refusal 83.83%를 달성하며, held-out ASB에서도 GRPO보다 낮은 ASR을 보인다. |

---

원문 PDF: `2026-09-03-safeevolve-harness-policy-co-evolution-from-agent-experience-for-safety.pdf`
