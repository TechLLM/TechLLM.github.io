---
title: "0.7K 파라미터로 어둠을 깨우다 — 맨체스터대 학부생이 만든 초경량 저조도 보정 AI 'MultiNeX'"
date: 2026-06-14T16:22:00+09:00
draft: false
description: "맨체스터대 학부 3학년이 CVPR 2026에 발표한 MultiNeX는 0.7K~45K 파라미터로 PairLIE(330K), ZeroDCE(80K)를 앞서는 저조도 이미지 보정 모델이다. Retinex 이론과 컴팩트 신경망을 결합한 실시간 엣지 AI 레시피."
tags: ["MultiNeX", "LowLightEnhancement", "Retinex", "CVPR2026", "엣지AI"]
categories: ["AI · LLM"]
cover:
  image: /images/multinex-ultra-lightweight-llie-manchester/multinex-ultra-lightweight-llie-manchester-cover.png
  alt: "맨체스터대 학부생이 만든 초경량 저조도 이미지 보정 AI MultiNeX"
---

## 개요

학부 3학년 프로젝트에서 시작된 모델이 CVPR 2026에 올라갔습니다. 맨체스터대 컴퓨터과학과 알렉산드루 브라테아누가 만든 **MultiNeX**는 어두컴컴한 사진을 다시 살리는 저조도 이미지 보정(LLIE) 모델입니다. 흥미로운 점은 크기입니다. 가장 작은 nano 버전은 파라미터가 **0.7K**, 표준 버전도 **45K**에 불과합니다. 그런데 같은 체급의 PairLIE(330K), ZeroDCE(80K)보다 결과가 더 좋습니다.

## 핵심 요약

- 맨체스터대 학부생 알렉산드루 브라테아누가 3학년 연구과제로 시작한 모델이 CVPR 2026에 채택되었습니다
- nano 버전 0.7K 파라미터, 라이트 버전 45K 파라미터 — PairLIE(330K)·ZeroDCE(80K)보다 한참 가볍습니다
- 고전 색채이론(Retinex)을 신경망으로 다시 풀어, 이미지를 조명(illumination)과 반사(reflectance)로 분해해 학습합니다
- 작은 네트워크가 "재구성"이 아닌 "보정"에만 집중하도록 문제를 다시 짠 점이 핵심입니다
- 자율주행·보안카메라·드론처럼 실시간성과 전력 효율이 같이 필요한 분야에 바로 쓸 수 있는 설계입니다

![MultiNeX 구조 다이어그램 — 맨체스터대 Tingting Mu](/images/multinex-ultra-lightweight-llie-manchester/multinex-source-diagram.png)

## 왜 LLIE를 다시 풀어야 했나

야간 거리, 어두운 실내, 역광 — 카메라가 가장 약한 순간입니다. 빛이 부족하면 색이 무너지고, 디테일이 사라지고, 노이즈가 올라옵니다. 최근 몇 년 사이 저조도 보정 모델은 인상적인 결과를 내고 있지만, 대부분 거대한 트랜스포머나 무거운 U-Net 기반입니다. 모델이 크면 결과는 좋아도 실시간 처리가 어렵고, 엣지 디바이스에는 들어가지도 못합니다.

문제는 결국 효율입니다. 더 작은 모델로, 더 빠르게, 비슷한 수준의 화질을 만들 수 있을까. 이 질문이 MultiNeX의 출발점이었습니다.

## Retinex를 다시 꺼낸 이유

연구팀이 택한 길은 의외로 "고전 회귀"입니다. **Retinex 이론**은 인간의 색지각을 설명하기 위해 1970년대 에드윈 랜드가 제안한 개념으로, 우리가 보는 이미지를 두 가지 성분으로 나눠서 봅니다.

- **Illumination** — 장면에 비치는 빛
- **Reflectance** — 사물 표면의 본래 색

어두운 사진은 조명 성분이 망가져 반사 성분까지 같이 무너진 상태입니다. Retinex는 둘을 따로 떼어내 조명만 보정하면 원래의 색과 구조를 더 잘 복원할 수 있다는 아이디어를 줍니다. MultiNeX는 이 고전적 분해를 현대 신경망에 다시 박아 넣었습니다. 그것도 아주 가벼운 형태로.

브라테아누는 인터뷰에서 이렇게 정리했습니다.

> "더 나은 문제 정의가 더 효율적인 모델을 만든다고 믿었습니다. 고전 색채이론과 Retinex 원리에 빛과 색의 다중 기술(multiple descriptions of light and colour)을 결합하면, 작은 네트워크가 자신의 제한된 용량을 '보정 그 자체'에 집중할 수 있습니다."

## 0.7K 파라미터가 만들어내는 차이

숫자로 보면 체급 차이가 분명합니다.

| 모델 | 파라미터 수 | 비고 |
| --- | --- | --- |
| PairLIE | 330,000 | 기존 lightweight LLIE |
| ZeroDCE | 80,000 | 잘 알려진 경량 베이스라인 |
| **MultiNeX (lite)** | **45,000** | 표준 버전 |
| **MultiNeX (nano)** | **700** | 초경량 버전 |

nano 버전은 ZeroDCE보다 약 100배, PairLIE보다 약 470배 작습니다. 그런데 같은 벤치마크에서 더 나은 성능을 냅니다. 모바일·임베디드 SoC에서도 어렵지 않게 돌릴 수 있는 수준입니다.

## 무엇을 잘 하고, 무엇이 아직 어려운가

논문에서 강조하는 강점은 세 가지입니다. 조명 보정, 디테일 복원, 색 충실도. 그것도 실시간 비용으로 해냅니다.

대신 한계도 명확합니다.

- 강한 스펙트럼 왜곡이 있는 장면(특정 파장이 무너진 조명)
- 렌즈 플레어가 심한 야경
- 인공조명과 자연광이 섞인 복합 조명

이런 케이스에는 아직 약합니다. 연구팀은 이걸 풀기 위해 톤매핑·곱셈형 잔차(multiplicative residuals) 같은 대안 정식화, 그리고 같은 원리를 *intrinsic image decomposition*, 색 항상성(color constancy), 수중 영상 보정, 안개 제거 같은 인접 분야로 확장하는 작업을 이어가고 있습니다.

## 자율 시스템과 "어둠 속에서 보는 능력"

지도교수 팅팅 무(Tingting Mu) 부교수의 말이 인상적입니다.

> "저조도 이미지 보정은 차세대 AI의 기반인 월드 모델링(world modelling)에 필수적입니다. 표준적인 시각 가정이 깨지는 실제 환경에서, 안정적이고 예측 가능한 표현을 만들 수 있어야 합니다."

다시 말해, 자율주행차·드론·로봇이 밤에도 똑같이 "보고 판단"하려면, 어둠 속에서 안정된 영상을 뽑아내는 단계가 먼저입니다. 그리고 그 단계는 가능한 한 적은 전력으로 끝내야 합니다. MultiNeX가 가는 방향은 정확히 그 지점입니다.

## 실무자가 볼 핵심 포인트

- **엣지·온디바이스에 들어갈 수 있다** — 45K·0.7K급이면 모바일 NPU·MCU도 부담이 거의 없습니다. 카메라 ISP 단에 LLIE를 박는 그림이 현실적으로 가능합니다.
- **문제를 다시 정의하면 모델은 작아진다** — "재구성"이 아니라 "보정"으로 범위를 좁히고, Retinex로 사전지식을 주입한 게 핵심입니다. 큰 모델로 통째로 풀려는 습관을 한 번 되짚어 볼 만합니다.
- **CV 보정 → 인접 분야 이식 가능성** — 색 항상성, 수중 영상, 안개 제거처럼 "조명/매질이 왜곡하는 영상" 문제군 전체로 확장 시도가 진행 중입니다. LLIE 하나만 보지 말고 그 다음 응용까지 같이 봐 두면 좋습니다.
- **고전 이론 + 신경망 조합** — 모든 걸 데이터로 푸는 대신, 검증된 분석적 prior를 신경망에 결합하면 같은 파라미터로 더 좋은 결과가 나옵니다. 비전 외 분야에도 시사점이 큽니다.
- **학부 연구의 가능성** — 코드 한 줄을 처음 짤 때부터 CVPR을 노릴 필요는 없지만, 잘 정의된 문제와 좋은 지도교수 한 명이 있으면 학부생도 SOTA 모델을 낼 수 있다는 사례입니다.

## 원문 출처

- 제목: *Multinex: An ultra lightweight AI model advancing low light image enhancement*
- 발표: IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) 2026
- 저자: Alexandru Brateanu, Dr Tingting Mu (The University of Manchester)
- 원문: <https://www.technology.org/2026/06/14/multinex-an-ultra-lightweight-ai-model-advancing-low-light-image-enhancement/>
- 출처 다이어그램: University of Manchester / Tingting Mu
