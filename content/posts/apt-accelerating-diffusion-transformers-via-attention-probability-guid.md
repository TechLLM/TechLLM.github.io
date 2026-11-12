---
title: "고해상도 이미지 생성에서 가장 오래 걸리는 계산량을 줄이기 위해, 덜 중요한 계산은 생략하고 필요한 계산은 적은 비트 수로 처리하는 방법과 이를 받치는 전용 칩 설계를 제안한 논문입니다."
date: 2026-11-13T07:37:55+09:00
draft: false
description: "APT는 4K 해상도에서 전체 연산의 90% 이상을 차지하는 Diffusion Transformer의 self-attention을 가속하기 위한 소프트웨어·하드웨어 공동 설계다. Attention probability를 importance metric으로 사용해 일부 원소를 생략하거나 6-bit·12-bit 정밀도로 계산한다."
tags: ["Diffusion Transformer / Computer Architecture / Hardware Accelerator", "논문 분석", "논문 리뷰", "Diffusion Transformer", "Self-attention", "Pruning"]
categories: ["논문분석"]
---


고해상도 이미지 생성에서 가장 오래 걸리는 계산량을 줄이기 위해, 덜 중요한 계산은 생략하고 필요한 계산은 적은 비트 수로 처리하는 방법과 이를 받치는 전용 칩 설계를 제안한 논문입니다.

**무엇이 문제였나** — 이미지 해상도가 올라가면 각 부분이 서로 정보를 얼마나 살펴야 하는지 계산하는 과정이 급격히 늘어납니다.
**어떻게 풀었나** — 중요한 부분은 정확히 계산하고, 덜 중요한 부분은 생략하거나 적은 비트 수로 계산합니다.
**그래서 뭐가 좋아졌나** — 실험에서는 기존 GPU보다 생성 속도와 전기당 처리량이 크게 좋아졌고, 이미지 품질 차이는 작았습니다.

> 큰 그림을 색칠할 때 모든 칸을 똑같이 꼼꼼하게 칠할 필요는 없습니다. 눈에 잘 띄는 부분은 세밀하게 칠하고, 덜 중요한 부분은 간단히 처리하거나 생략하는 방식과 비슷합니다.

## 논문 정보

Sungyeob Yoo, Seeyeon Kim, Joonyong Park, Seunghee Han, Joo-Young Kim · KAIST · IEEE/ACM International Conference on Computer-Aided Design (ICCAD ’26) · 2026

## 왜 중요한가

고해상도 이미지 생성은 한 번의 요청에도 많은 연산 자원과 긴 대기 시간이 필요합니다. 중요도가 낮은 연산을 줄이면서 결과 품질을 유지하면 같은 장비로 더 많은 이미지를 만들거나, 전력과 처리 시간을 줄일 수 있습니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| A100 대비 최대 end-to-end 속도 향상 | **8.16×** | 4K 조건에서 보고된 최대 end-to-end 속도 향상 |
| EXION 대비 최대 end-to-end 속도 향상 | **3.01×** | 비교 대상 EXION 대비 보고된 최대 속도 향상 |
| A100 대비 최대 에너지 효율 향상 | **14.98×** | 전체 denoising pipeline의 처리량/전력 기준 최대 향상 |
| EXION 대비 최대 에너지 효율 향상 | **2.04×** | 비교 대상 EXION 대비 보고된 최대 처리량/전력 향상 |

## 어떻게 동작하나

논문은 self-attention의 QK^T와 PV 연산을 핵심 가속 대상으로 삼는다. APDT는 attention probability의 head별·timestep별 표준편차 σ_h(t)를 모델별로 한 번 오프라인 프로파일링하고, 그 범위에 α와 β로 정규화해 pruning threshold와 quantization threshold를 각각 만든다. Pruning threshold보다 작은 원소는 생략하고, 두 threshold 사이의 원소는 6-bit, quantization threshold보다 큰 원소는 12-bit으로 계산한다. 같은 식에 서로 다른 α·β 쌍을 적용하며 quantization threshold를 pruning threshold보다 높게 유지한다. 양자화는 tile 단위 symmetric uniform 방식이다. Attention 분포가 입력에 의존하므로 mask는 runtime에 생성되며, 시간적 유사성을 이용해 이전 timestep인 t+1의 high-·low-precision execution mask를 재사용한다. 품질 저하를 막기 위해 7–10 step마다 periodic refresh를 수행해 생략된 원소를 모두 low-precision mask에 되살리고, 각 head의 프로파일링된 σ가 관측 범위의 5%–10% 이상 감소하면 head별 refresh도 실행한다. TAFA는 이전 timestep의 tile 정규화 통계 l_i^(j)(t+1)와 R_i^(j)(t+1)를 현재 단계의 unnormalized exponential P'_i^(j)(t) 및 누적합과 결합해 현재 tile의 attention probability를 근사한다. 이를 이용해 threshold를 P' 위에 직접 재스케일하므로 attention probability 전체 행렬을 만들 필요가 없다. SD-MPU는 16개의 dual-precision MAC line, dynamic mask management, address translation과 tile-based dataflow를 제공하며, 전체 설계에는 3,072개의 SD-MPU가 사용된다.

핵심 수식:

```
\mathrm{threshold}_h(t)=\alpha\cdot\frac{\sigma_h(t)-\sigma_{h,\min}}{\sigma_{h,\max}-\sigma_{h,\min}}+\beta\nP_i(t)\approx l_i^{(j)}(t+1)R_i^{(j)}(t+1)\operatorname{diag}(l_i^{(j)}(t))^{-1}P_i'^{(j)}(t)
```

첫 식은 head h와 timestep t의 attention probability 표준편차 σ_h(t)를 모델별 오프라인 프로파일링에서 얻은 σ_h,min과 σ_h,max로 정규화해 임계값을 정한다. 두 임계값에는 각각 별도의 α·β 쌍을 사용한다. 두 번째 식에서 i는 query tile, j는 key-value tile이며 P'_i^(j)(t)는 타일의 unnormalized exponential 값, l_i^(j)(t)는 누적 지수합, R_i^(j)(t)는 최종 Softmax 정규화 계수이다. TAFA는 이전 timestep의 lR 값을 현재 단계의 l과 P'에 결합해 tile별 attention probability와 mask threshold를 근사한다.

## 한계와 주의할 점

- σ_h(t)는 모델마다 한 번 오프라인 프로파일링해야 하고 α·β도 모델별로 정해야 한다. 실제 입력과 프롬프트에 따라 attention 분포가 달라질 수 있으며, 프로파일링 비용과 입력별 분포 편차에 대한 민감도는 충분히 보고되지 않았다.
- TAFA와 mask 재사용은 인접 timestep 사이의 attention 분포 유사성에 의존한다. timestep 간격이 커지거나 분포가 급격히 변하면 예측 mask와 실제 중요한 원소의 대응이 나빠질 수 있으며, refresh도 이를 완전히 제거하지 못한다.
- 성능 평가는 1K·2K·4K에서 수행했지만 Table 2의 COCO 2017 정확도 측정은 1K에만 해당한다. 따라서 2K·4K의 출력 품질과 고해상도에서의 정량적 품질 저하 여부는 별도로 검증되지 않았다.
- APT는 14 nm RTL 합성과 cycle-level simulator로 평가되었고 EXION도 원 논문 사양에 따라 재구현했다. 반면 A100의 latency와 power는 실제 GPU에서 측정했으며 HBM2E 전력은 제조사 사양을 모델링했으므로 완전히 동일한 실기 비교는 아니다.
- IS와 CLIP에는 평균 및 표준편차가 제시되지만 통계적 유의성 검정이나 신뢰구간은 없다. PSNR 역시 점估计로 제시되며, batch size 1 조건의 결과가 다른 배치와 프롬프트 분포에 그대로 확장되는지는 불확실하다.
- 모든 비교 구성은 A100의 peak throughput에 맞춰 정규화되었다. 따라서 정규화 방식, 주파수, 메모리 용량과 버퍼 크기의 차이가 결과에 미치는 영향은 별도로 분리되지 않았다.
- 현재 timestep의 attention 분포가 이전 timestep과 크게 달라지면 재사용한 mask가 실제로 중요한 원소를 생략할 수 있습니다.
- head별 표준편차가 프로파일링 범위를 벗어나거나 예상보다 빠르게 변하면 σ 기반 임계값이 중요도와 맞지 않게 될 수 있습니다.
- Periodic refresh는 생략된 원소를 모두 low-precision 계산으로 되살리므로 refresh가 빈번하면 계산 절감률이 일시적으로 낮아집니다.
- 행·열 mask 압축의 보수적 복원은 원래 생략할 원소를 low-precision로 복원할 수 있어 예상한 절감 폭이 줄어듭니다.
- 불규칙한 주소 접근에서 주소 변환기와 mask 처리 throughput이 계산 유닛을 따라가지 못하면 DP-MAC 활용률이 낮아질 수 있습니다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### FlashAttention에 이전 단계 통계를 재사용하는 타일별 mask 생성 경로

FlashAttention 기반 DiT self-attention에 TAFA를 적용합니다. 이전 timestep의 tile별 l·R 통계와 현재 timestep의 P' 및 누적 l을 결합해 threshold를 재조정하고, attention probability 전체를 materialize하지 않은 상태에서 APDT mask를 생성합니다. 인접 timestep에서 변화가 큰 구간을 찾고 mask refresh를 적용합니다.

**적용 지점** — Diffusion Transformer self-attention tile 처리

**기대 효과** — 논문은 TAFA가 4K에서 naive APDT 통합 대비 on-chip memory 요구량을 최대 103.4× 줄이고, 생성된 mask가 full Softmax mask와 97% 초과 유사도를 보였다고 보고합니다.

### Head별 attention 분산을 이용한 pruning·정밀도 임계값 조정

APDT threshold 설정 지점에서 모델별 σ_h(t) 프로파일을 읽어 pruning과 quantization threshold를 각각 계산합니다. Attention이 고르게 분산된 초기 단계에는 낮은 threshold를 적용해 정보를 더 남기고, 분포가 집중된 후기 단계에는 높은 threshold를 적용해 생략과 low-precision 비율을 늘립니다. Periodic refresh와 head별 σ 변화 감지로 오래된 mask의 누적을 제한합니다.

**적용 지점** — Diffusion Transformer attention mask·정밀도 결정

**기대 효과** — 논문은 PixArt-α에서 57.34% pruning과 9.06% 12-bit 계산 비율, APT QSNR 28.5 dB를 보고했습니다. Fixed-threshold pruning과 비교한 BOPs 절감은 최대 65%입니다.

### 불규칙 mask를 처리하는 sparsity-aware dual-precision 연산 경로

SD-MPU에 mask 관리 유닛과 address translation table를 두고 attention 원소의 유효 주소만 읽습니다. 6-bit datapath를 기본으로 사용하고, high-precision mask의 원소는 6-bit MSB·LSB 분할 곱 네 개를 순차 처리해 12-bit 결과로 복원합니다. 각 SD-MPU의 16개 DP-MAC line, tile dataflow와 mask·주소 변환의 overlap을 함께 구현하고 실제 연산 유닛 활용률을 측정합니다.

**적용 지점** — 전용 추론 가속기의 sparse matrix 연산기

**기대 효과** — 논문은 APT가 A100 대비 최대 8.16× 속도와 14.98× 에너지 효율을 보였고, 4K에서 pruning과 dual-precision을 결합한 BOPs를 최대 76.4% 줄였다고 보고합니다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 대상 DiT와 입력 조건에서 품질·분포 특성을 확인 | 운영할 모델과 해상도를 정하고 head별·timestep별 attention 표준편차를 프로파일링합니다. α·β를 보정하면서 동일 prompt와 seed에서 baseline, APDT 및 full-precision 결과를 비교하고 IS·CLIP·PSNR과 육안 점검을 기록합니다. | 적용할 모델·해상도와 임계값을 정하고 profiling과 품질 검증 비용을 파악합니다. |
| Phase 2 | APDT와 TAFA를 추론 파이프라인에 통합해 근사 오류를 검증 | FlashAttention tile 처리에서 이전 timestep의 l·R 통계와 현재 단계의 partial sum을 연결하고 pruning·quantization mask를 생성합니다. 논문의 periodic refresh와 σ 변화 감지를 적용한 뒤 full Softmax mask와 mask 유사도 및 출력 품질을 비교합니다. | attention probability 전체를 저장하지 않아도 생략과 정밀도 선택이 입력별 품질을 유지하는지 확인합니다. |
| Phase 3 | 전용 하드웨어 또는 이에 준하는 구현에서 운영 성능을 평가 | mask 관리, 주소 변환, 6/12-bit MAC, tile dataflow를 구현합니다. 목표 해상도에서 end-to-end latency, 에너지, 메모리, mask 처리 overhead와 실패 사례를 측정하고, 가능하면 실제 prototype 또는 FPGA 검증을 추가합니다. | 사이클 시뮬레이션 결과가 목표 구현과 운영 환경에서도 유효한지 확인하고 비용 대비 효과가 있는 적용 범위를 정합니다. |

---

원문 PDF: `2026-08-28-apt-accelerating-diffusion-transformers-via-attention-probability-guided.pdf`
