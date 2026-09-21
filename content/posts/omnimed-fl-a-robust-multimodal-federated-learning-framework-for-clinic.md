---
title: "병원 데이터를 한곳에 모으지 않고도 X-ray와 진료 메모를 함께 써서 모델을 학습할 수 있는지 시험한 연구다."
date: 2026-09-22T07:33:04+09:00
draft: false
description: "흉부 X-ray와 합성 임상 노트를 결합해 5-class 임상 상태 분류를 수행하는 멀티모달 연합학습 프록시 벤치마크다. 3,000개 공개 흉부 영상과 3,000개 클래스 조건 합성 노트를 환자 단위가 아니라 클래스 단위로 짝지어, 8가지 융합 규칙, 3가지 초기화, 4가지 결측 텍스트 대치 규칙과 여러 연합 베이스라인을 비교한다."
tags: ["Federated Learning / Medical AI", "논문 분석", "논문 리뷰", "연합학습", "멀티모달", "라벨 편향"]
categories: ["논문분석"]
---


병원 데이터를 한곳에 모으지 않고도 X-ray와 진료 메모를 함께 써서 모델을 학습할 수 있는지 시험한 연구다.

**무엇이 문제였나** — 각 병원은 자기 데이터를 그대로 보관하고, 학습된 모델 업데이트만 서버와 주고받는다.
**어떻게 풀었나** — 연구진은 실제 환자 기록 대신 합성 메모를 만들고 공개 흉부 X-ray와 클래스 단위로 짝지어 여러 학습 방식을 비교했다.
**그래서 뭐가 좋아졌나** — 영상과 메모를 함께 쓰면 점수는 올랐지만, 병원마다 환자 종류가 심하게 다르면 성능이 크게 흔들렸고 통신 비용도 커졌다.

> 여러 병원이 시험지를 밖으로 내보내지 않고, 각자 푼 뒤 채점 결과와 풀이 방식만 공유해 공동으로 공부하는 상황과 비슷하다. 서로 가진 문제 유형이 너무 다르면 평균을 내도 모두에게 잘 맞는 공부법이 되기 어렵다.

## 논문 정보

Ayush Debnath, Ruelia Saha, Sudip Misra · Indian Institute of Technology Kharagpur, India; KTH Royal Institute of Technology, Sweden; SRM University-AP, India · arXiv preprint (2609.10364v1, cs.LG) · 2026

## 왜 중요한가

의료 데이터는 민감해서 쉽게 모을 수 없다. 이 연구는 데이터를 옮기지 않는 학습 방식에서 영상과 텍스트를 함께 쓰면 어떤 이득과 비용이 생기는지 보여준다. 다만 합성 메모와 클래스 단위 짝짓기를 쓴 프록시 실험이라 실제 진단 성능이나 배포 가능성을 증명한 것은 아니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 멀티모달 Macro-F1 (Dataset B, α=1, K=5) | **0.906** | 텍스트 단독 0.880, 영상 단독 0.737 대비. Dataset B branch-cost 비교의 단일 시드 결과 |
| 클라이언트 수 확대 시 F1 손실 (α=5, K=3→20) | **0.067F1** | 통신량은 6.7배 증가하지만 α=5 행에서 평균 F1 변화는 작음 |
| 라벨 분포 편향 F1 손실 | **0.27F1** | 4×3 grid에서 label skew가 만든 최대 Macro-F1 손실 |
| 양방향 통신량 (K=20) | **183.5GiB** | K=3에서 27.5 GiB, K=5에서 45.9 GiB, K=10에서 91.8 GiB로 선형 증가 |

## 어떻게 동작하나

3,000장의 공개 흉부 X-ray 또는 절차적으로 생성한 X-ray 스타일 이미지와 3,000개의 클래스 조건 합성 임상 노트를 5개 클래스(Normal, Pneumonia, COVID-19, Pleural Effusion, Cardiomegaly)로 구성한다. Dataset B 영상은 공개 흉부 방사선 데이터에서 오며, 노트는 실제 EHR이 아니라 observation, symptom, context, indicator 슬롯을 섞어 만든 템플릿 문장이다. 텍스트는 DistilBERT [CLS] 벡터를 R^256으로 사영하고, 영상은 ViT-Base/16 평균 풀링 토큰을 R^512로 사용한다. 8가지 융합 규칙(비어텐션 3종, 어텐션 기반 5종) 뒤에 2-layer 5-class MLP를 붙인다. K=3,5,10,20 클라이언트와 Dirichlet α=0.1,1,5 격자를 사용하고, 기준 설정은 K=5, α=1이다. 각 라운드에서 서버가 θ를 보내고 클라이언트는 AdamW로 3 local epochs를 학습한 뒤 sample-weighted update를 반환하며, 총 8 rounds를 수행한다. 로컬 손실은 focal loss, label-smoothed cross-entropy, entropy-diversity 항, confidence penalty로 구성되고 class-balanced sampler와 함께 collapse를 막는 구성요소로 평가된다.

핵심 수식:

```
V_{\text{nom}} = 2 K T |\theta| b
```

명목 양방향 연합 트래픽. K=nominal 클라이언트 수, T=라운드 수(8), |θ|=학습 파라미터 수(153,935,621), b=바이트/파라미터(FP32=4). 모델 상태는 615,742,484 bytes이며 K=3/5/10/20에서 27.5/45.9/91.8/183.5 GiB다. 직렬화, secure aggregation, 압축, 알고리즘별 추가 상태는 제외된다.

## 한계와 주의할 점

- 합성 노트는 실제 환자 EHR이 아니며, 영상과 노트도 환자 단위가 아니라 클래스 단위로만 짝지어져 실제 임상 쌍의 불일치와 결측을 반영하지 못한다
- 각 클래스 영상이 서로 다른 공개 코퍼스에서 오므로 질병 라벨과 데이터 출처가 일부 교락된다
- 두 시드만 사용해 FedProx–FedAvg의 0.075 차이처럼 표준편차 안에 들어오는 비교는 통계적 우위를 말하기 어렵다
- 실험은 단일 H100 NVL에서 순차 시뮬레이션으로 수행되어 지연, 동시성, straggler, dropout, 기관별 하드웨어 차이를 반영하지 않는다
- HIPAA·GDPR 맥락의 데이터 로컬리티를 제공하지만, differential privacy나 secure aggregation을 구현해 프라이버시를 증명한 것은 아니다
- α=0.1, K=5에서 SCAFFOLD–AdamW adaptation은 0.070±0.015로 local-only 0.297보다도 낮아졌고, 저자들은 AdamW control-variate adaptation 문제로 해석했다
- anti-collapse 전체 스택은 severe skew에서 minimum diversity 0.90을 유지하지만 F1은 0.683±0.089로, sampler와 entropy-diversity를 모두 제거한 0.758±0.016보다 낮았다
- 8개 fusion rule의 평균 F1은 0.636~0.759 범위지만 per-rule 표준편차가 0.000~0.167이라 융합 규칙 순위를 확정하기 어렵다
- P-FIN-style uncertainty-weighted aggregation은 0.706±0.089로 probabilistic imputation과 평균이 같고 seed별 0.770→0.643으로 흔들려 불확실성 모델링이 분산을 줄였다고 보기 어렵다

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 연합 분류 헤드에 class-balanced sampler와 diversity guard를 분리해 적용하기

논문 Eq. (2)의 entropy-diversity 항과 class-balanced sampler는 severe skew에서 minimum predicted-class diversity를 0.90까지 유지했지만 F1은 0.683±0.089로 낮았다. sampler 제거, entropy-diversity 제거, 둘 다 제거한 경우 F1은 각각 0.716±0.055, 0.726±0.035, 0.758±0.016이고 diversity는 0.70~0.80으로 떨어졌다. 따라서 로컬 손실 함수에서 두 장치를 독립 토글로 두고, F1뿐 아니라 predicted-class diversity를 함께 모니터링한다.

**적용 지점** — 연합학습 분류 모델의 로컬 손실 함수와 샘플러

**기대 효과** — 심각한 분포 편향에서 다섯 클래스 예측 커버리지를 유지할 수 있지만, 약 0.075 F1 수준의 정확도 비용 가능성을 함께 관리

### 연합학습 오케스트레이터에 통신량 예산 기반 클라이언트 상한 두기

오케스트레이터는 매 라운드 전체 K를 무조건 참여시키기보다 Eq. (3) V_nom=2KT|θ|b로 비용을 계산하고 참여 클라이언트 수를 제한한다. 논문 설정에서 K=3/5/10/20의 양방향 명목 트래픽은 27.5/45.9/91.8/183.5 GiB이며, α=5에서 K=3→20은 6.7배 통신량 증가와 0.067 F1 손실 사례를 보였다. 적용 지점은 연합학습 스케줄러의 라운드별 클라이언트 샘플링 정책이다.

**적용 지점** — 연합학습 오케스트레이터의 라운드당 클라이언트 샘플링 정책

**기대 효과** — 성능 변화가 작은 구간에서 통신량을 선형으로 늘리는 결정을 피하고, K=20 기준 183.5 GiB 명목 트래픽을 사전 통제

### 검색 단계에서 코사인 유사도와 라벨 일치율을 분리 측정하기

RAG 검색기를 도입하기 전, 학습 말뭉치에 피팅한 TF-IDF 벡터와 FAISS exact inner-product 검색으로 top-1 same-label accuracy, precision@5, top-1 cosine similarity를 분리해 기록한다. 논문은 Dataset B 검증 질의에서 top-1 same-label accuracy 0.540, same-label precision@5 0.468, mean top-1 cosine similarity 0.707을 보고했다. 코사인 유사도가 높아도 라벨 일치율이 낮을 수 있으므로, 템플릿 기반 합성 말뭉치에서는 어휘적 가까움과 임상적 같은 라벨을 구분해야 한다.

**적용 지점** — RAG 회수 단계의 코퍼스 수준 sanity check

**기대 효과** — 템플릿/합성 코퍼스에서 라벨 일치 0.540과 코사인 0.707의 격차를 탐지해 검색 품질 과신 방지

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 프록시 데이터에서 단일 모달 기준선 재현 | DistilBERT 텍스트 경로와 ViT 영상 경로를 논문 설정(K=5, α=1, 8 rounds, 3 local epochs)에 맞춰 먼저 재현한다. Dataset B branch-cost 비교의 텍스트 0.880, 영상 0.737은 실제 진단 성능이 아니라 같은 프록시 조건의 기준선으로만 사용한다. | 멀티모달을 켜기 전에 데이터 분할, 라운드 실행, 모델 상태 전송량, 단일 모달 학습 안정성을 확인한다. |
| Phase 2 | 멀티모달 융합과 severe skew 안정성 평가 | 멀티모달 경로를 추가하고 α=0.1, K=5에서 FedAvg, FedProx, FedMME-style, SCAFFOLD–AdamW adaptation을 비교한다. 논문 값은 local-only 0.297, FedAvg 0.662±0.074, FedProx 0.737±0.085, FedMME-style 0.647±0.080, SCAFFOLD–AdamW 0.070±0.015다. anti-collapse 구성은 F1만 높이는 장치가 아니라 diversity guard로 별도 평가한다. | 라벨 편향에서 어떤 연합 방식이 무너지는지, 클래스 다양성을 지키기 위해 어느 정도 정확도 비용을 감수하는지 판단한다. |
| Phase 3 | 기관 수 확장과 통신량 최적화 | K=3,5,10,20과 α=0.1,1,5 격자로 확장하되 Eq. (3)으로 통신량을 미리 계산한다. K=20은 183.5 GiB이고 α=5에서 K=3→20은 6.7배 트래픽에 0.067 F1 손실 사례를 보였다. 실제 운영 전에는 secure aggregation, 압축, 비동기 집계, dropout 처리를 별도로 더한다. | 성능을 크게 올리지 못하는 클라이언트 수 확대를 피하고, 라운드당 참여 기관 수와 통신 예산을 현실적으로 정한다. |

---

원문 PDF: `2026-09-10-omnimed-fl-a-robust-multimodal-federated-learning-framework-for-clinical.pdf`
