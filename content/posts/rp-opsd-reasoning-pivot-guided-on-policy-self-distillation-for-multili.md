---
title: "영어 풀이를 참고하되, 모든 단어가 아니라 '풀이 방향을 바꾸는 순간'에만 강하게 배우게 하는 다국어 학습법"
date: 2026-08-09T07:37:24+09:00
draft: false
description: "기존 다국어 추론 전이 기법은 모든 토큰에 비슷한 증류 신호를 주기 때문에, 추론 상태를 실제로 바꾸는 결정적 토큰과 단순 표현 토큰을 구분하지 못한다. RP-OPSD는 동일 정책을 두 교사 시야로 평가한다. 하나는 영어 문제 번역과 영어 reference solution을 보고, 다른 하나는 영어 문제 번역만 본다."
cover:
  image: "/images/rp-opsd-reasoning-pivot-guided-on-policy-self-distillation-for-multili/_page_3_Diagram_0.jpeg"
  alt: "RP-OPSD 전체 파이프라인: on-policy target-language rollout, 두 teacher view 비교, PRS/RPT gate 계산, routed distillation과 reference anchoring 적용"
  caption: "논문 원문 발췌"
tags: ["Large Language Model / Multilingual Reasoning", "논문 분석", "논문 리뷰", "On-Policy Self-Distillation", "Reasoning Pivot", "Privileged Reasoning Sensitivity"]
categories: ["논문분석"]
---


영어 풀이를 참고하되, 모든 단어가 아니라 '풀이 방향을 바꾸는 순간'에만 강하게 배우게 하는 다국어 학습법

**무엇이 문제였나** — 문제: 기존 방법은 목표 언어 답변의 모든 단어를 비슷하게 가르쳐서, 중요한 계산·판단 지점과 단순 말투를 구분하지 못한다.
**어떻게 풀었나** — 해결: 영어 풀이를 본 모델과 보지 않은 모델의 다음 단어 예측 차이를 비교해, 풀이가 실제로 바뀌는 지점을 찾는다.
**그래서 뭐가 좋아졌나** — 결과: 중요한 지점은 영어 풀이에서 배우고, 나머지 표현은 목표 언어답게 유지해 여러 언어의 수학 추론 점수를 높였다.

> 수학 선생님이 풀이 전체를 빨간펜으로 고치는 대신, '여기서 속도가 1.25배가 되면 시간은 0.8배가 된다'처럼 답을 가르는 부분만 표시해 주는 것과 비슷하다. 조사나 문장부호 같은 표현은 학생의 언어 습관을 유지하게 둔다.

## 논문 정보

Xinye Wang, Junxiao Liu, Shujian Huang · National Key Laboratory for Novel Software Technology, Nanjing University · arXiv preprint · 2026

## 왜 중요한가

영어에서는 잘 푸는 모델도 한국어, 스와힐리어 같은 다른 언어에서는 풀이 과정을 놓칠 수 있다. 이 논문은 영어 풀이의 도움을 무작정 전체 문장에 덮어씌우지 않고, 계산 방향이나 결론을 정하는 핵심 순간에만 쓰는 방법을 제안한다. 그래서 목표 언어 표현을 덜 망가뜨리면서 추론 능력을 옮길 수 있다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| AfriMGSM 평균 (Qwen3-1.7B) | **19.07%** | 12개 아프리카 언어 pass@12, Base 9.90 대비 +9.17pt, COPSD 16.70 대비 +2.37pt |
| AfriMGSM 평균 (Qwen3-4B) | **26.83%** | 12개 아프리카 언어 pass@12, Base 20.30 대비 +6.53pt, COPSD 21.63 대비 +5.20pt |
| PolyMath 평균 (Qwen3-1.7B) | **17.97%** | ZHO/FRA/SWA/JPN/SPA/RUS DW-ACC, Base 14.87 대비 +3.10pt, COPSD 15.99 대비 +1.98pt |
| PolyMath 평균 (Qwen3-4B) | **31.87%** | ZHO/FRA/SWA/JPN/SPA/RUS DW-ACC, Base 28.50 대비 +3.37pt, COPSD 29.94 대비 +1.93pt |

## 어떻게 동작하나

RP-OPSD는 먼저 저자원 또는 목표 언어 질문 x^ℓ에서 학생 모델 πθ가 직접 생성한 rollout y1:T를 사용한다. 각 응답 위치 t에서 학생 분포 p_t는 x^ℓ와 이전 생성 토큰 y<t에 조건화된다. 같은 정책을 stop-gradient teacher로 두 번 평가해 q_t^+와 q_t^-를 만든다. q_t^+는 목표 언어 질문, 영어 번역 x^h, 영어 reference reasoning trace s^h, 같은 rollout prefix를 모두 보고, q_t^-는 같은 질문 정보와 prefix를 보되 영어 reference trace만 제거한다. 두 teacher view의 forward KL인 a_t = D_KL(q_t^+ || q_t^-)가 PRS 점수다. 이 점수는 completion token running mean과 standard deviation으로 z-score 정규화되고, sigmoid 기반 RPT gate g_t로 변환된다. 높은 gate 위치에는 q_t^+ 기준 full-vocabulary distillation을 적용하고, 낮은 gate 위치에는 frozen reference policy r_t 기준 anchoring을 적용한다. 모든 teacher, reference, score, gate 값은 detach되고 gradient는 학생 분포 p_t에만 흐른다. 이 구조는 영어 풀이가 실제로 다음 추론 상태를 바꾸는 위치에 transfer를 집중하고, 나머지 위치에서는 목표 언어 표현을 보존하도록 설계됐다.

![RP-OPSD 전체 파이프라인: on-policy target-language rollout, 두 teacher view 비교, PRS/RPT gate 계산, routed distillation과 reference anchoring 적용](/images/rp-opsd-reasoning-pivot-guided-on-policy-self-distillation-for-multili/_page_3_Diagram_0.jpeg)
*RP-OPSD 전체 파이프라인: on-policy target-language rollout, 두 teacher view 비교, PRS/RPT gate 계산, routed distillation과 reference anchoring 적용*

별도 teacher network를 만들지 않고 같은 정책의 solution-conditioned view와 ablated view를 비교해 routing signal을 만든다.

핵심 수식:

```
a_t = D_{\mathrm{KL}}(q_t^+ \parallel q_t^-), \quad \tilde{a}_t = \frac{a_t-\mu_a}{\sigma_a+\epsilon}, \quad g_t = \mathrm{sg}\left[g_{\min} + (1-g_{\min})\sigma\{\beta(\tilde{a}_t-\tau)\}\right], \quad \mathcal{L}_{\mathrm{pivot}} = \frac{1}{N}\sum_{t=1}^{T} m_t g_t D_{\mathrm{KL}}(q_t^+ \parallel p_t), \quad \mathcal{L}_{\mathrm{anchor}} = \frac{1}{N}\sum_{t=1}^{T} m_t(1-g_t)D_{\mathrm{KL}}(r_t \parallel p_t), \quad \mathcal{L}_{\mathrm{RP\text{-}OPSD}} = \mathcal{L}_{\mathrm{pivot}} + \lambda\mathcal{L}_{\mathrm{anchor}}
```

q_t^+: 영어 번역과 영어 reference trace를 모두 본 solution-conditioned teacher view. q_t^-: 영어 번역은 보지만 reference trace는 보지 않는 ablated teacher view. a_t: PRS 점수. \tilde{a}_t: running statistics로 정규화한 PRS. g_t: stop-gradient RPT gate. p_t: gradient를 받는 학생 next-token distribution. r_t: frozen reference policy의 target-language anchoring distribution. m_t: response completion mask, N=Σ_t m_t. β: gate sharpness, τ: threshold, g_min: 최소 gate 값. λ: reference anchoring coefficient이며 논문 기본값은 0.2다.

## 실험 결과

![표면 표현 차이는 같은 추론 상태를 유지할 수 있지만, pivot drift는 이후 풀이를 망가뜨릴 수 있다는 동기 예시](/images/rp-opsd-reasoning-pivot-guided-on-policy-self-distillation-for-multili/_page_0_Diagram_3.jpeg)
*표면 표현 차이는 같은 추론 상태를 유지할 수 있지만, pivot drift는 이후 풀이를 망가뜨릴 수 있다는 동기 예시*

다국어 CoT 전이에서 모든 토큰이 같은 중요도를 갖지 않으며, 추론 상태를 바꾸는 지점만 따로 찾아야 한다.

## 한계와 주의할 점

- 영어 reference solution 품질에 의존한다. 풀이가 틀리거나 불완전하면 잘못된 reasoning signal이 q_t^+에 들어간다.
- 영어 문제 번역 x^h가 두 teacher view 모두에 들어가므로, 번역 품질이 낮으면 PRS가 reasoning sensitivity보다 입력 왜곡을 반영할 수 있다.
- λ 값에 민감하다. SWA에서 λ=0.2는 29.6 pass@12지만 λ=0.5는 24.8, λ=0.8은 24.4로 낮아진다.
- PRS가 항상 순수 추론 변화만 잡지는 않는다. Figure 5에서 0.8t의 leading digit처럼 formatting preference도 높은 gate를 받을 수 있다.
- 훈련 중 q_t^+, q_t^-, frozen reference r_t 등 추가 full-vocabulary forward KL 평가가 필요해 계산·메모리 비용이 커진다.
- Appendix E의 MMLU-ProX 표는 제시된 값만 보면 RUS는 동일하고 SPA도 overall이 동일해, 비수학 일반화 주장은 본문 표현보다 약하게 해석해야 한다.
- 형식/표기 pivot 오탐: fractional form과 decimal form 선택처럼 추론보다 표현 형식 차이가 큰 PRS를 만들 수 있다.
- 과도한 reference anchoring: λ가 너무 크면 target-language 보존은 강해지지만 privileged reasoning transfer가 약해질 수 있다.
- 낮은 품질의 reference trace 전이: 영어 풀이가 문제 해결에 부적절하면 high-gate 위치에서 잘못된 분포를 학생에게 증류한다.
- 저자원 언어 prompt/번역 취약성: x^h와 language-specific instruction이 불안정하면 q_t^+와 q_t^-의 matched contrast 가정이 약해진다.
- single-run ablation 한계: Table 4의 matched-view 우위는 방향성 근거지만 저자도 통계적 유의성을 주장하지 않는다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 검색 문서의 추론 중요도를 PRS 방식으로 재순위화

다국어 RAG에서 각 후보 문서에 대해 포함 prompt와 제외 prompt의 다음 응답 분포를 비교하고 KL 차이를 문서의 reasoning contribution score로 쓸 수 있다. 이는 RP-OPSD가 q_t^+와 q_t^-의 matched contrast로 privileged reasoning evidence의 효과를 측정한 것과 같은 발상이다. 논문 Table 2에서 high-gate token을 고른 TG가 random RG와 bottom BG보다 SWA/FRA 모두 높았다는 점은, 단순 노출량보다 위치 선택이 중요하다는 근거다.

**적용 지점** — RAG 재순위 단계, 다국어 검색 시스템의 후보 문서 점수화

**기대 효과** — 정량 이득은 별도 검증이 필요하지만, 원문 Table 2의 TG > RG > BG 결과는 reasoning-sensitive 위치 선택의 유용성을 뒷받침한다.

### 에이전트 중간 단계의 피벗 여부로 자기검증 트리거

장기 추론 에이전트가 CoT를 생성할 때 PRS 또는 이를 근사한 경량 점수로 reasoning-control pivot과 state-update pivot을 찾고, 그 지점에서만 self-check, branch, verifier 호출을 실행한다. 원문 Section 4.2는 '所以', '因此', '但' 같은 reasoning-control token과 '梯形', '线段DE', square-root operator 같은 problem-conditioned token이 high-gate로 잡힌다고 보고한다.

**적용 지점** — 장기 CoT 생성 에이전트의 자기검증 트리거

**기대 효과** — 원문은 호출 절감률을 측정하지 않았으므로 정량 수치는 별도 실험이 필요하다. 기대효과는 검증 비용을 reasoning-sensitive step에 집중하는 것이다.

### 에이전트 자기교정을 피벗 위치에만 적용

실패 trace의 각 위치에 대해 reference-conditioned view와 ablated view의 차이를 계산하고, gate가 높은 위치에서만 targeted correction을 적용한다. Appendix B에서 matched-view score D_KL(q_t^+ || q_t^-)를 teacher-student score D_KL(q_t^+ || p_t)로 바꾸면 ZHO PolyMath가 25.49에서 23.46, SWA AfriMGSM이 29.6에서 27.2로 떨어졌다. 이는 교정 위치를 teacher-student disagreement가 아니라 privileged evidence의 incremental effect로 잡는 편이 낫다는 근거다.

**적용 지점** — 장기 에이전트 trace의 자기교정/리플레이 단계

**기대 효과** — 표면 표현 mismatch를 과도하게 고치는 부작용을 줄일 가능성이 있다. 실제 정확도 이득은 task별 재평가가 필요하다.

### 추론 피벗 예측으로 긴 사고 토큰 예산 배분

Long-CoT 모델은 모든 위치에 같은 sampling budget을 쓰는 경우가 많다. RP-OPSD의 gate를 라우터로 쓰거나 경량 predictor로 근사하면, high-PRS 위치에서만 beam, verifier, self-consistency, tool call을 늘리고 low-gate 표면 토큰은 빠르게 생성할 수 있다. Figure 5의 time-rescaling 사례처럼 핵심은 25%나 1.25라는 숫자 자체가 아니라 t/1.25 = 0.8t로 넘어가는 연산 지점이다.

**적용 지점** — Long-CoT 모델의 추론 예산 동적 할당

**기대 효과** — 원문은 추론 비용 절감률을 보고하지 않는다. 기대효과는 계산 예산을 형식 토큰보다 reasoning pivot에 우선 배정하는 것이다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 단일 저자원 언어 PoC | SWA 500건 OpenThoughts 형식 데이터로 Base/COPSD/RP-OPSD를 비교하고, λ=0, 0.2, 0.5, 0.8 및 β·τ 민감도를 확인한다. AfriMGSM SWA pass@12와 gate heatmap을 함께 본다. | 논문 조건에서는 Qwen3-1.7B SWA가 Base 13.2, COPSD 26.0, RP-OPSD 29.6 pass@12를 기록했으므로, 단일 언어에서 재현 가능성과 gate 품질을 빠르게 점검할 수 있다. |
| Phase 2 | 여러 언어와 운영 데이터로 확장 | 3-5개 언어에서 영어 reference solution, 문제 번역, target-language instruction 품질을 관리하고, LC와 accuracy를 함께 모니터링한다. hard-gate TG/RG/BG 분석으로 gate가 실제 transfer utility를 정렬하는지 확인한다. | 언어별로 reasoning transfer와 language consistency가 함께 유지되는지 검증하고, 불필요한 영어식 표현 침투를 조기에 발견한다. |
| Phase 3 | 수학 외 도메인 검증과 비용 최적화 | 규칙 기반 업무, 코딩, 논리 추론 등 reference solution이 있는 도메인에서 PRS/RPT gate가 의미 있는 pivot을 찾는지 평가한다. teacher-view forward 비용을 줄이기 위한 캐싱, LoRA, checkpointing, 경량 gate predictor를 실험한다. | RP-OPSD의 선택적 전이 아이디어를 실제 서비스 학습 파이프라인에 맞게 비용과 품질 기준으로 조정할 수 있다. |

---

원문 PDF: `2026-08-09-rp-opsd-reasoning-pivot-guided-on-policy-self-distillation-for-multiling.pdf`
