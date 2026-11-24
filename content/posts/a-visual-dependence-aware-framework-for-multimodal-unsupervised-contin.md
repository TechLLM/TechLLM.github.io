---
title: "정답이 없는 그림 질문으로 모델을 계속 학습시키면서, 새 내용을 배우고 예전 그림 이해 능력도 지키는 방법"
date: 2026-11-25T07:34:23+09:00
draft: false
description: "이 논문은 정답 라벨 없이 이미지와 질문이 순차적으로 들어오는 상황에서 멀티모달 모델을 계속 학습하는 MU-CPT 설정을 제안한다. 토큰마다 실제 이미지가 예측을 얼마나 돕는지 나타내는 시각 의존도(VD)를 이용해, 이전 과제에서 시각 근거를 잃는 현상을 측정하고 새 과제 학습을 안내한다. 제안 기법 VDA는 이전 과제의 VD 구조를 보존하는 VC-OT와 새 과제에서 시각 근거가 있는 토큰을 더 학습하는 VMA를 결합한다. 6개 과제 실험에서 최종 평균 정확도(AvgAcc) 62.5%, 평균 망각(AvgF) 0.6을 보고했다."
tags: ["Multimodal Large Language Models / Continual Learning", "논문 분석", "논문 리뷰", "MU-CPT", "Visual Dependence", "cross-modal attributional forgetting"]
categories: ["논문분석"]
---


정답이 없는 그림 질문으로 모델을 계속 학습시키면서, 새 내용을 배우고 예전 그림 이해 능력도 지키는 방법

**무엇이 문제였나** — 문제: 그림과 질문의 종류가 계속 바뀌면 모델이 새 내용을 배우는 동안 예전에 배운 것을 잊을 수 있다. 정답을 모두 준비하는 것도 어렵다.
**어떻게 풀었나** — 방법: 답을 만들 때 그림이 실제로 도움이 되는 단어를 찾아 새 학습에서 더 살펴보고, 이전 과제에서 중요했던 그림 단서를 기억한다.
**그래서 뭐가 좋아졌나** — 결과: 여섯 과제 실험에서 평균 정확도 62.5%와 평균 망각 0.6을 보고했다.

> 학생이 그림을 보고 답을 배울 때, 그림을 가리면 답하기 어려워지는 단어를 표시하는 것과 비슷하다. 새 과제에서는 그런 단어에 집중하고, 예전 과제에서 그림을 보며 배운 단서도 기억한다.

## 논문 정보

Kaichen Li, Zhilin Zhu, Jianhao Huang, Zhengqin Lai, Baochen Xiong, Zibo Shao, Yaguang Song, Linhui Xiao, Xiaoshan Yang, Changsheng Xu · State Key Laboratory of Multimodal Artificial Intelligence Systems, Institute of Automation, Chinese Academy of Sciences; Pengcheng Laboratory; School of Artificial Intelligence, University of Chinese · arXiv preprint arXiv:2608.26095v1 [cs.CV] · 2026

## 왜 중요한가

현실의 이미지 질문은 분야와 상황이 계속 바뀌며, 모든 질문의 정답을 사람이 붙이기는 어렵다. 이 연구는 정답 없이 이어지는 학습에서 새 과제 적응과 이전 능력 보존을 함께 다루는 방법을 제시한다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 최종 AvgAcc | **62.5%** | 6개 과제의 최종 평균 정확도. frozen backbone은 53.9, ScPO는 58.8, SEEKR-MLLM은 60.1이다. |
| AvgLA | **63.0%** | 각 과제를 배운 직후의 평균 정확도. SEEKR-MLLM은 62.5다. |
| AvgF | **0.6점** | 이전 과제에서 잃은 평균 성능. CL-MoE는 1.8, SEEKR-MLLM은 2.9다. |
| 최종 RRAR | **4.204** | TextVQA에서 전체 과제 순서를 마친 뒤의 질문 관련 영역 주의 비율. 논문은 기준 방법 3.705, frozen backbone 3.774를 보고한다. |

## 어떻게 동작하나

논문은 TextVQA→SciVQA→StockQA→GQA→DriveLM→PMC-VQA 순서로 정답이 없는 이미지-질문 쌍을 공급하는 MU-CPT 설정을 정의한다. 각 과제를 학습한 뒤 지금까지 본 과제를 평가한다. VD는 같은 텍스트 조건에서 실제 이미지와 정보가 없는 반사실적 이미지로 토큰을 예측한 손실을 비교해 계산한다. 양수 VD는 그림이 예측을 돕는다는 뜻이다. VC-OT는 이전 과제 표본의 기준 VD와 현재 VD를 비교해, 그림에 의존하던 토큰 사이의 재분배는 시각 영역 유사도에 따라 제한하고 시각 독립 토큰으로의 이동에는 비용을 준다. 또한 전체 양수 VD 질량이 기준에서 달라지는 정도를 보존 손실에 포함한다. VMA는 새 과제에서 양수 VD가 큰 토큰의 학습 가중치를 높인다. 전체 손실은 VMA와 VC-OT 손실의 합이다. 주 실험은 Qwen2.5-VL-7B와 LoRA rank 128을 사용했고, VD 온도 τD=0.05, 버퍼 크기 1000, batch size 1, learning rate 5×10^-5를 설정했다.

핵심 수식:

```
\displaystyle \ell_t^{\mathrm{real}}(\theta)=-\log p_\theta(y_t\mid I,P,y_{<t}),\quad \ell_t^{\mathrm{null}}(\theta)=-\log p_\theta(y_t\mid I_{\mathrm{null}},P,y_{<t}),\quad D_t(\theta)=\frac{\ell_t^{\mathrm{null}}-\ell_t^{\mathrm{real}}}{\ell_t^{\mathrm{null}}+\ell_t^{\mathrm{real}}}
\displaystyle r_t^m=\tau_D\,\operatorname{Softplus}(D_t^m/\tau_D),\quad \tilde r_t^m=\frac{r_t^m}{\sum_{u=1}^{L}r_u^m},\quad m\in\{\mathrm{ref},\mathrm{cur}\}
\displaystyle C_{ij}=\begin{cases}d_{\mathrm{reg}}(i,j),&i,j\in H\\1,&i\in H,\ j\in L\\0,&i\in L\end{cases},\quad L_{\mathrm{struct}}=\langle T^*,C\rangle
\displaystyle L_{\mathrm{strength}}=\frac{\sum_{t=1}^{L}r_t^{\mathrm{cur}}-\sum_{t=1}^{L}r_t^{\mathrm{ref}}}{\sum_{t=1}^{L}r_t^{\mathrm{ref}}},\quad L_{\mathrm{VC\text{-}OT}}=L_{\mathrm{struct}}+L_{\m
```

ℓ_real과 ℓ_null은 각각 실제 이미지와 정보가 없는 반사실적 이미지에서의 토큰 예측 손실이다. D_t는 두 손실로 계산한 토큰별 시각 의존도다. r_t는 VD를 양수 질량으로 바꾼 값이고, r̃_t는 서열 안에서 정규화한 질량이다. H는 기준 모델에서 D_t>0인 토큰 집합, L은 D_t≤0인 집합이다. d_reg은 기준 모델에서 두 토큰이 주의를 두는 시각 영역의 Jensen–Shannon divergence다. T*는 기준 VD 분포에서 현재 VD 분포로 옮기는 최적 수송 계획이고, C는 그 이동 비용이다. L_strength는 전체 양수 VD 질량의 상대 변화다. sg는 역전파에서 해당 값의 기울기를 멈추는 연산이며, w_t는 새 과제 토큰의 학습 가중치다.

## 한계와 주의할 점

- 제공된 본문에는 seed별 평균, 표준편차, 신뢰구간 또는 유의성 검정이 없다. 따라서 보고된 성능 차이가 실행 간 변동성보다 안정적인지는 판단하기 어렵다.
- 주 결과는 Qwen2.5-VL-7B와 여섯 과제에 기반한다. 논문은 부록에 다른 모델 계열과 무작위 과제 순서 결과가 있다고 언급하지만, 제공된 본문에서는 해당 수치와 상세 내용을 확인할 수 없다.
- 반사실적 이미지 계산, attention 저장, Sinkhorn 반복 및 replay 학습의 구체적인 연산량과 메모리 비용은 제공된 본문에 보고되지 않았다.
- 주 결과는 한 가지 과제 순서로 제시된다. 논문은 추가 무작위 순서를 부록에서 다룬다고 밝히지만, 제공된 본문만으로는 순서 변화에 대한 결과를 검토할 수 없다.
- 정보가 없는 반사실적 이미지가 VD 측정에 적절하지 않거나 손실 차이가 다른 요인에서 생기면 VD가 왜곡될 수 있다. 그러면 그림에 의존하는 토큰과 그렇지 않은 토큰의 구분도 부정확해질 수 있다.
- VC-OT의 영역 비용은 토큰의 시각 attention 유사도를 사용한다. attention이 의미상 유사성을 잘 반영하지 못하면 이동 비용이 실제 시각 근거의 변화와 어긋날 수 있다.
- 버퍼가 이전 과제를 충분히 대표하지 못하면 기준 VD와 attention이 일부 표본에 치우쳐 보존 목표가 편향될 수 있다.
- VD 보존 제약이 새 과제 학습을 제한할 수 있다. ablation에서 L_strength와 L_struct만 사용한 구성은 AvgLA 60.3으로, VMA를 포함한 전체 모델의 63.0보다 낮았다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 토큰별 시각 의존도를 활용한 무정답 학습

논문의 VMA는 실제 이미지와 정보 없는 반사실적 이미지에서의 토큰 손실 차이로 VD를 계산한다. 양수 VD가 큰 토큰에 더 큰 가중치를 주고, 서열 단위 정규화로 평균 가중치 규모를 유지한다. 논문은 이 구성만 적용한 ablation에서 AvgAcc 51.0에서 56.9, AvgLA 61.7에서 63.8, AvgF 12.8에서 8.2로 변했다고 보고한다.

**적용 지점** — 멀티모달 모델의 정답 없는 지속 후학습

**기대 효과** — VMA 단독 ablation에서 AvgAcc는 51.0에서 56.9로, AvgLA는 61.7에서 63.8로 증가했고 AvgF는 12.8에서 8.2로 감소했다.

### 최적 수송으로 이전 시각 근거 구조 보존

회수 표본의 기준 VD와 기준 모델의 decoder attention을 저장한다. VC-OT는 그림에 의존하던 토큰 사이의 분배를 attention 영역의 Jensen–Shannon divergence에 따른 비용으로 제한하고, 시각 독립 토큰으로 의존성이 이동하는 경우에는 비용을 준다. 별도의 L_strength 항은 전체 양수 VD 질량의 상대 변화도 다룬다.

**적용 지점** — 이전 과제의 시각 근거 구조 보존

**기대 효과** — Table 4에서 VC-OT는 No Protection보다 AvgAcc 56.9에서 62.5, AvgF 8.2에서 0.6으로 개선했다. VD Strength Drift는 35.94%에서 14.27%, VD Distribution Drift는 0.1052에서 0.0385로 낮아졌다.

### RRAR로 시각 주의 변화 점검

논문은 TextVQA의 정답 영역 상자를 이용해 Relevant Region Attention Ratio(RRAR)를 분석한다. 이는 질문과 관련된 시각 영역에 배분된 attention을 전체 이미지 attention과 비교하는 지표다. 논문은 이를 온라인 품질 게이트로 평가하지 않았으므로, 운영 점검에 쓰려면 별도의 검증이 필요하다.

**적용 지점** — 멀티모달 모델의 시각 주의 평가

**기대 효과** — 전체 과제 순서 뒤 RRAR는 VDA 4.204, baseline 3.705, frozen backbone 3.774로 보고되었다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 논문의 설정과 주요 결과를 재현한다 | Qwen2.5-VL-7B, LoRA rank 128, 버퍼 크기 1000을 사용해 논문의 여섯 과제 순서를 재현한다. 실제 이미지와 반사실적 이미지의 토큰 손실, 기준 VD 및 attention 저장 과정을 점검하고, frozen backbone과 SEEKR-MLLM 결과를 비교한다. | 논문에서 보고한 조건의 재현 여부와 VD 측정 과정의 주요 실패 사례를 확인할 수 있다. |
| Phase 2 | 다른 과제 순서와 데이터 조건에서 방법을 평가한다 | 논문이 부록에서 다룬 무작위 과제 순서와 다른 데이터 흐름을 검토한다. 각 과제의 정확도, AvgAcc, AvgLA, AvgF와 TextVQA RRAR를 같은 평가 절차로 계산한다. | 제시된 과제 순서 밖에서도 성능이 유지되는지 평가할 수 있다. |
| Phase 3 | 운영 비용과 데이터 처리 조건을 측정한다 | 버퍼에 저장되는 이미지, VD, attention의 크기와 보관 기간을 확인하고, 반사실적 이미지 계산 및 replay에 따른 학습 비용을 측정한다. 제한된 평가 데이터에서 품질 변화를 관찰한 뒤 적용 가능성을 검토한다. | 실험 결과를 실제 데이터 흐름에 적용할 때 필요한 비용과 제약을 구체화할 수 있다. |

---

원문 PDF: `2026-08-27-a-visual-dependence-aware-framework-for-multimodal-unsupervised-continua.pdf`
