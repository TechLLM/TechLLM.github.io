---
title: "영어 풀이를 볼 때 답의 흐름이 실제로 바뀌는 지점만 찾아 그 부분을 집중해서 배우는 다국어 학습법"
date: 2026-10-05T07:34:35+09:00
draft: false
description: "RP-OPSD는 다국어 추론 전이에서 모든 토큰을 균등하게 증류하던 기존 On-Policy Self-Distillation(OPSD)의 한계를, ‘추론 피벗(reasoning pivot)’과 ‘표면 표현(surface realization)’을 나누는 토큰 단위 RPT 게이트로 해결한다."
tags: ["Large Language Model / Multilingual Reasoning", "논문 분석", "논문 리뷰", "OPSD", "Reasoning Pivot", "RPT Gate"]
categories: ["논문분석"]
---


영어 풀이를 볼 때 답의 흐름이 실제로 바뀌는 지점만 찾아 그 부분을 집중해서 배우는 다국어 학습법

**무엇이 문제였나** — 언어 모델은 영어로는 잘 풀 수 있는 문제도 저자원 언어로 풀 때 추론 흐름이 무너지는 경우가 많다.
**어떻게 풀었나** — 이 방법은 영어 풀이를 보여줬을 때 다음 단어 선택이 크게 달라지는 지점을 찾아, 그런 지점에는 영어 풀이의 도움을 강하게 주고 나머지는 원래 언어 표현을 유지하게 한다.
**그래서 뭐가 좋아졌나** — 12개 아프리카 언어를 포함한 17개 언어의 수학 추론 평가에서 기존 학습법보다 높은 성능을 보였다.

> 수학 문제를 다른 언어로 배우는 학생에게 영어 풀이 전체를 베끼게 하면 문장은 어색하고 핵심도 놓칠 수 있습니다. 대신 선생님이 ‘여기서 곱셈을 선택하는 것이 중요하다’, ‘여기서 결론이 바뀐다’처럼 풀이의 갈림길만 짚어 주면, 학생은 자기 언어로 설명하면서도 올바른 풀이 흐름을 배울 수 있습니다.

## 논문 정보

Xinye Wang, Junxiao Liu, Shujian Huang et al. · National Key Laboratory for Novel Software Technology, Nanjing University · arXiv preprint (arXiv:2608.06347v1) · 2026

## 왜 중요한가

많은 언어 모델은 영어 데이터가 많아서 영어 추론은 비교적 잘하지만, 같은 능력이 다른 언어에서는 잘 드러나지 않습니다. 이 논문은 영어 풀이 전체를 그대로 따라 하게 하지 않고, 답의 흐름을 바꾸는 핵심 결정 지점만 골라 배우게 합니다. 그래서 각 언어의 자연스러운 표현을 유지하면서도 더 나은 추론을 하도록 돕습니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| AfriMGSM 평균 pass@12 (Qwen3-4B) | **26.83%** | 12개 아프리카 언어 평균 — COPSD 21.63 대비 +5.20, EGRSD 22.68 대비 +4.15 |
| PolyMath 평균 DW-ACC (Qwen3-4B) | **31.87%** | ZHO/FRA/SWA/JPN/SPA/RUS 평균 — COPSD 29.94 대비 +1.93, EGRSD 30.16 대비 +1.71 |
| RPT 게이트 라우팅 효과 (SWA, Top 20% vs Bottom 20%) | **26.0 vs 15.6pass@12 %** | Qwen3-1.7B에서 동일한 20% 토큰 예산으로 high-gate 토큰만 증류한 TG와 low-gate 토큰만 증류한 BG 비교 — 10.4포인트 격차 |
| 영어 미도달 문제의 타깃 언어 정답 확장 (vs PCS) | **2.08×** | PolyMath 6개 타깃 언어 평균에서 English-incorrect but target-correct 문제 증가량: PCS +4.0, RP-OPSD +8.3 |

## 어떻게 동작하나

RP-OPSD는 다국어 CoT가 추론의 흐름을 바꾸는 reasoning pivot과 언어적·기호적 표현을 담당하는 surface realization으로 섞여 있다고 본다. 학생 모델은 저자원 언어 질문 x_l에서 on-policy rollout y_1:T를 만들고, 같은 모델을 stop-gradient teacher로 두 가지 방식으로 평가한다. solution-conditioned view q^+_t는 저자원 언어 질문, 영어 번역, 영어 참조 풀이, rollout prefix를 모두 보고 다음 토큰 분포를 낸다. ablated view q^-_t는 같은 질문 정보와 prefix를 보지만 영어 참조 풀이만 제거한다. 두 teacher view의 KL divergence를 PRS 점수 a_t로 계산하고, 이를 running statistics로 정규화한 뒤 sigmoid RPT gate g_t로 변환한다. gate가 높은 위치는 q^+_t에 대한 full-vocabulary KL로 privileged distillation을 강하게 받고, gate가 낮은 위치는 frozen reference policy r_t에 대한 anchoring을 받아 원래 target-language 표현을 유지한다. 학습은 500개 OpenThoughts 예시와 17개 언어별 별도 adapted model로 진행되며, AfriMGSM에서는 Qwen3-1.7B 19.07, Qwen3-4B 26.83 평균 pass@12를 달성했다.

핵심 수식:

```
q_t^+ = sg[\pi_\theta(\cdot | x_\ell, x_h, s_h, y_{<t})]
q_t^- = sg[\pi_\theta(\cdot | x_\ell, x_h, y_{<t})]
a_t = D_{KL}(q_t^+ \| q_t^-)
\tilde{a}_t = \frac{a_t - \mu_a}{\sigma_a + \epsilon}
g_t = sg\left[g_{min} + (1 - g_{min})\sigma(\beta(\tilde{a}_t - \tau))\right]
\mathcal{L}_{pivot}=\frac{1}{N}\sum_{t=1}^{T}m_t g_t D_{KL}(q_t^+\|p_t)
\mathcal{L}_{anchor}=\frac{1}{N}\sum_{t=1}^{T}m_t(1-g_t)D_{KL}(r_t\|p_t)
\mathcal{L}_{RP\text{-}OPSD}=\mathcal{L}_{pivot}+\lambda\mathcal{L}_{anchor}
```

x_l은 타깃 언어 질문, x_h는 영어 번역, s_h는 영어 참조 풀이, y_<t는 rollout prefix다. p_t는 gradient를 받는 학생 분포이고, q^+_t와 q^-_t는 같은 정책의 stop-gradient teacher view다. a_t는 영어 참조 풀이가 있을 때와 없을 때의 teacher 분포 차이, g_t는 g_min 이상 1 이하의 라우팅 가중치다. 원문 hyperparameter는 g_min=0.05, beta=2.0, tau=0.0, lambda=0.2다.

## 한계와 주의할 점

- 영어 참조 풀이 s_h가 핵심 입력이다. 논문은 target-language rationale 없이 작동한다는 장점이 있지만, 영어 풀이가 없거나 품질이 낮은 도메인에서는 PRS 신호 자체가 약해질 수 있다.
- 언어별 별도 모델을 학습한다. 원문은 17개 target language 각각에 separate adapted model을 학습한다고 명시하므로, 단일 다국어 모델 하나로 배포되는 방식은 아니다.
- Reference anchoring 계수 lambda에 민감하다. SWA에서 lambda=0.2는 pass@12 29.6으로 최적이지만, 0.5와 0.8에서는 24.8과 24.4로 하락한다.
- Ablated teacher q^-_t를 제거하고 teacher-student 차이 q^+_t || p_t로 gate를 만들면 ZHO PolyMath DW-ACC 25.49에서 23.46, SWA AfriMGSM pass@12 29.6에서 27.2로 떨어진다.
- 수학 외 일반화는 MMLU-ProX의 RUS/SPA 비수학 도메인에서만 확인되었다. overall은 RUS 34.55→36.47, SPA 36.61→38.18로 좋아졌지만, 모든 영역과 언어에 대한 일반화로 보기는 이르다.
- 수치·공식 토큰이 항상 추론 피벗은 아니다. Figure 5에서 0.8의 leading digit은 높은 gate를 받지만, 저자는 fractional continuation 선호에서 생긴 formatting effect일 수 있다고 해석한다.
- 영어 참조 풀이가 잘못되면 solution-conditioned view가 잘못된 reasoning evidence를 제공해 RPT gate와 증류 방향이 함께 왜곡될 수 있다.
- 고자원 언어에서는 gate localization의 이득이 상대적으로 작다. Table 2에서 FRA의 TG-BG 격차는 1.6포인트로, SWA의 10.4포인트보다 훨씬 작다.
- Gate는 reasoning-control pivot과 problem-conditioned state-update pivot을 잘 찾지만, x, b, frac 같은 빈번한 표면 토큰도 분석 대상에 섞일 수 있어 token-level heatmap만으로 피벗을 기계적으로 해석하면 위험하다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### RAG 청크 재순위에 ‘추론 피벗’ 게이팅 적용

RAG 파이프라인에서 각 청크를 포함했을 때와 제외했을 때의 모델 다음 응답 분포 차이를 계산하면, 논문의 PRS와 유사한 청크 단위 영향도 점수를 만들 수 있다. 차이가 큰 청크는 reasoning pivot에 해당하므로 LLM judge나 더 비싼 reranker를 적용하고, 차이가 작은 청크는 BM25나 cross-encoder 점수를 유지한다. 논문 Table 2에서 SWA Top 20% gate 토큰만 증류한 TG가 26.0, Bottom 20% BG가 15.6으로 10.4포인트 차이를 보인 것처럼, 정보가 답변 흐름을 바꾸는 위치를 구분하는 데 이 아이디어를 쓸 수 있다.

**적용 지점** — RAG 검색 재순위 단계 (rerank)

**기대 효과** — SWA Table 2의 TG-BG 10.4포인트 격차를 근거로, 추론에 실질적으로 기여하는 청크를 더 잘 골라낼 가능성이 있다.

### 에이전트 자기검사를 reasoning pivot 위치로 집중

멀티스텝 에이전트의 trajectory에서 각 step에 힌트나 검증 근거를 추가했을 때와 제거했을 때 다음 행동 분포가 얼마나 바뀌는지 비교할 수 있다. 분포 차이가 큰 step만 상세 LLM judge로 검증하고, 나머지는 형식 검사나 간단한 assertion으로 처리한다. 논문은 RPT gate가 thought-anchor receiver score와도 정렬됨을 보였고, Appendix A에서 RPT AUPRC 0.463이 surprisal 0.413, entropy 0.393, KD loss 0.387보다 높았다.

**적용 지점** — 에이전트 자기검증·재시도 단계

**기대 효과** — 검증 대상을 상위 step으로 줄이면서도 downstream reasoning에 오래 영향을 주는 thought-anchor를 더 잘 포착할 수 있다.

### 에이전트 멀티도구 호출에 ‘reasoning 영향도’ 게이트 추가

도구 호출 결과를 포함한 상태와 제외한 상태에서 다음 계획 또는 최종 답변 분포의 KL 차이를 계산하면 tool-call 단위 PRS를 만들 수 있다. 영향도가 높은 호출은 dry-run, schema assertion, 결과 재검증을 모두 수행하고, 영향도가 낮은 호출은 가벼운 검증만 수행한다. Figure 5가 보여주듯 단순히 숫자나 수식처럼 보인다고 모두 피벗은 아니므로, 호출 결과가 실제 다음 추론 상태를 바꾸는지로 판단해야 한다.

**적용 지점** — 에이전트 도구 호출 라우팅·실패 복구

**기대 효과** — 핵심 도구 호출 실패에는 복구 자원을 집중하고, 단순 포맷 변환 같은 낮은 영향도 호출의 검증 비용은 줄일 수 있다.

### OPSD 계열의 토큰 가중치 선택 기준으로 matched-view contrast 사용

기존 OPSD 변형은 teacher confidence, teacher-student disagreement, 주석 span 등을 token weighting 신호로 쓴다. RP-OPSD는 q^+_t와 q^-_t가 같은 질문 정보와 prefix를 공유하고 영어 참조 풀이 접근만 다르도록 맞춘 뒤, 그 차이를 privileged reasoning evidence의 순수한 증분 효과로 본다. Table 4에서 teacher-student 대체 점수 q^+||p_t는 ZHO PolyMath 25.49→23.46, SWA AfriMGSM 29.6→27.2로 하락했다.

**적용 지점** — OPSD 기반 자기증류 학습 일반

**기대 효과** — matched-view score가 teacher-student disagreement보다 ZHO +2.03 DW-ACC, SWA +2.4 pass@12 우위였다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | RP-OPSD 게이트 모듈 재현 | 1) Qwen3-1.7B 또는 Qwen3-4B 선택, 2) q^+_t와 q^-_t를 계산하는 matched teacher view inference 구현, 3) PRS z-score 정규화와 RPT gate 구현, 4) 500개 OpenThoughts 샘플과 언어별 LoRA 학습 설정(r=64, alpha=128)으로 Table 1 재현 | Qwen3-1.7B 기준 AfriMGSM 평균 pass@12 19.07, Qwen3-4B 기준 26.83을 재현 목표로 삼을 수 있다. |
| Phase 2 | 정확도와 언어 일관성 동시 검증 | 1) COPSD/EGRSD/M-Thinker와 같은 baseline을 같은 언어와 decoding 조건에서 비교, 2) pass@12, DW-ACC, MGSM accuracy, LC를 함께 측정, 3) lambda=0/0.2/0.5/0.8 sweep으로 anchoring 민감도 확인, 4) q^+||q^- gate와 q^+||p_t gate를 비교 | 논문 기준 RP-OPSD는 COPSD 대비 focused subset에서 MGSM accuracy 50.6→53.1, LC 84.8→88.8로 이동했다. |
| Phase 3 | 도메인 확장과 운영 비용 절감 | 1) Phi-4-mini-reasoning 같은 non-Qwen backbone에서 검증, 2) MMLU-ProX 등 비수학 도메인으로 OOD 평가, 3) 언어별 adapter 관리 비용을 줄이는 shared adapter 또는 adapter composition 실험, 4) 영어 참조 풀이 품질 필터 추가 | 논문은 Phi-4-mini에서 ZHO PolyMath 18.24→24.53, SWA PolyMath 15.20→16.85 개선을 보였고, RUS/SPA MMLU-ProX overall도 각각 34.55→36.47, 36.61→38.18로 개선했다. |

---

원문 PDF: `2026-08-09-rp-opsd-reasoning-pivot-guided-on-policy-self-distillation-for-multiling.pdf`
