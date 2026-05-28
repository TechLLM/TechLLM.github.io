---
title: "MONET: 이미지 생성 AI 연구의 문턱을 낮추다 — 104.9M 오픈 데이터셋 공개"
date: 2026-05-28T23:55:00+09:00
draft: false
description: "Jasper AI가 29억 장에서 정제한 1억 499만 장 규모의 오픈 텍스트-이미지 데이터셋 MONET과 단일 GPU로 훈련 가능한 nano-t2i를 공개했다. 폐쇄적 대형 AI 연구소의 독점을 깨는 이 릴리즈가 이미지 생성 연구에 미칠 파급력을 분석한다."
cover:
  image: "/images/monet-massive-open-dataset-text-to-image-research-cover.png"
  alt: "MONET 오픈 이미지 데이터셋"
  caption: "Generated illustration"
tags: ["MONET", "text-to-image", "오픈데이터셋", "diffusion-model", "Jasper-AI", "이미지생성", "데이터셋"]
categories: ["dataset", "image-generation"]
---


## 핵심 요약

- **Jasper AI**, 29억 장 이미지에서 정제한 **1억 499만 장** 규모의 오픈 텍스트-이미지 데이터셋 **MONET** 공개 (Apache 2.0)
- **6단계 필터링 파이프라인** — 미적 품질·안전·중복제거·도메인 필터링까지 체계적 정제
- 이미지당 **최대 5개 캡션** (원본 웹 캡션 + 4종 VLM 생성 캡션)으로 텍스트-이미지 정렬 극대화
- **합성 이미지 13% 혼합**이 최적 성능 구간 확인 — 100% 합성 시 품질 급락 (FID 15.0 vs ~7–8)
- **4.1B 파라미터 모델**이 GenEval 0.74 달성, DALL-E 3·FLUX.1 Dev(12B) 초과

---

## 왜 MONET이 필요했나

DALL-E, Stable Diffusion, Midjourney 같은 이미지 생성 모델은 텍스트만 입력하면 거의 모든 장면을 만들어낸다. 그런데 이 모델들을 훈련하려면 고품질 이미지와 상세한 설명이 짝을 이룬 대규모 데이터가 필수다.

기존 오픈 데이터셋인 **LAION-5B**는 규모는 컸지만 중복·저품질 이미지·유해 콘텐츠·형편없는 캡션으로 가득했다. 그 결과 소수의 거대 AI 연구소만이 실제로 경쟁력 있는 이미지 모델을 훈련할 수 있었고, 학술 연구자나 소규모 팀은 배제된 채였다. 기술이 비밀이어서가 아니라, **훈련 데이터가 없어서**.

MONET은 이 재현성 격차를 정면으로 공략한다. 오픈·필터링·중복제거·다중 캡션 구조를 갖춘, 대규모 텍스트-이미지 모델 사전훈련에 특화된 최초의 공개 데이터셋이다.

---

## 6단계 정제 파이프라인: 29억 → 1억 499만 장

MONET은 인터넷 전체 이미지 컬렉션을 거대한 깔때기에 통과시키는 방식으로 만들어졌다.

![MONET 필터링 파이프라인](https://cdn-uploads.huggingface.co/production/uploads/652d98b939b7a1b6c84506cb/wZGLOzMOuX9xTbSB_BjWR.png)

**Stage 1 — 미적 사전 필터링**: LAION·COYO 소스에서 512×512px 미만이거나 미적 점수 5.0 이하인 이미지를 즉시 제거. 285억 장 → 약 1억 2100만 장으로 축소.

**Stage 2 — 안전 필터링**: 3종 NSFW 분류기의 앙상블로 하나라도 플래그가 달리면 제거. 전체 1.8%만 추가 제거됐으나, 핵심 안전망 역할.

**Stage 3 — 중복 제거**: 지각 해싱(perceptual hashing)으로 완전 복사본을 제거하고, SSCD 임베딩으로 색조 변경·워터마크 추가·크롭 등 유사 복사본까지 탐지. 2600만 장 이상 제거.

**Stage 4 — 도메인 필터링 & 거버넌스**: Getty·Shutterstock·Dreamstime 등 스톡 사진 공급사 이미지 및 가시적 워터마크 이미지 제거.

이 결과 최종 **1억 499만 장**의 고품질 샘플이 남는다.

---

## 이미지당 최대 5개 캡션: 다중 VLM 캡셔닝

최근 AI 연구에서 밝혀진 반직관적 사실: 텍스트 설명의 품질이 이미지 품질만큼, 때로는 그 이상으로 중요하다.

원본 웹 캡션은 대부분 `photo.jpg`나 `아름다운 석양` 수준의 짧고 노이즈 섞인 대체 텍스트다. MONET은 이를 4종 비전-언어 모델(VLM)이 생성한 설명으로 보강해 이미지당 **최대 5개 캡션**을 제공한다.

![MONET 다중 캡셔닝 예시](https://cdn-uploads.huggingface.co/production/uploads/652d98b939b7a1b6c84506cb/Ok4KdQRkEUaqGLCeMDwl1.png)

단일 AI가 아닌 4종 캡셔너를 조합한 이유는 명확하다. 하나의 모델에만 의존하면 고유한 사각지대가 생기고, 여러 캡셔너를 혼합하면 실제 사용자 프롬프트의 다양한 스타일에 더 강건하게 일반화된다.

훈련 시에는 매 스텝마다 5개 캡션 중 하나를 랜덤 샘플링해 모델이 다양한 프롬프트 스타일에 노출되도록 설계됐다.

---

## 합성 데이터 혼합 실험: 최적 비율 13%

MONET의 흥미로운 설계 결정 중 하나는 실제 이미지와 AI 생성 이미지를 혼합한다는 점이다.

합성 데이터 비율을 달리해 FID 점수(낮을수록 현실적)를 측정한 실험 결과, 약 50% 부근에서 최적 성능이 나타났다.

![합성 데이터 비율 vs FID](https://cdn-uploads.huggingface.co/production/uploads/652d98b939b7a1b6c84506cb/Sd5xQdEqHn7znynRd9RKh.png)

100% 합성 데이터에서 FID가 15.0으로 급락한 결과는 **"AI가 자기 자신을 먹는" 문제**를 보여준다. AI가 만든 이미지만으로 훈련하면 오류가 피드백 루프를 타고 증폭되어 품질이 빠르게 저하된다. MONET의 13% 합성 비율은 텍스트-이미지 정렬을 개선하는 이점을 누리면서도 합성 데이터 포화 위험을 피하는 균형점이다.

---

## 벤치마크: 4.1B 모델이 12B를 이겼다

![GenEval 벤치마크](https://cdn-uploads.huggingface.co/production/uploads/652d98b939b7a1b6c84506cb/kVPsLjFDpM4tSlxKHPPf7.png)

GenEval 벤치마크(객체·색상·수량·공간 관계 정확도 평가)에서 MONET 기반 4.1B 모델은 **0.74**를 달성했다. 12B 파라미터의 DALL-E 3·FLUX.1 Dev를 오픈 데이터만으로 앞선 결과다.

DPG 벤치마크(복잡한 장문 프롬프트 테스트)에서도 **85.56** 기록으로 DALL-E 3·SD3·FLUX.1 Dev를 상회했다. 가장 큰 모델(Qwen-Image 20B, Z-Image 6B)과의 격차는 파라미터 수와 추가 파인튜닝에 기인하며, MONET 자체 품질 문제가 아니다.

---

## nano-t2i: 단일 GPU, 며칠 만에 훈련

MONET과 함께 **nano-t2i**도 공개됐다. 복잡한 인프라 없이 단일 GPU에서 며칠 만에 경쟁력 있는 디퓨전 모델을 처음부터 훈련할 수 있는 최소 코드베이스다. 데이터셋과 코드베이스를 결합하면 연구자들이 생산 수준의 텍스트-이미지 모델을 훈련하는 데 필요한 모든 요소가 갖춰진다.

---

## 한계점

- **지리·문화적 편향**: Common Crawl 기반 소스 특성상 유럽·북미 컨텍스트 과잉 대표. 피부 톤도 Fitzpatrick 3–4 편중.
- **영어 전용 캡션**: 다국어 이미지 생성이나 교차언어 검색에는 별도 번역 파이프라인 필요.

---

## 실무자가 볼 핵심 포인트

- **데이터 품질이 규모를 이긴다**: 4.1B 모델이 12B 모델을 앞선 결과는 정제된 오픈 데이터가 폐쇄적 대규모 데이터를 실질적으로 대체할 수 있음을 증명한다.
- **재현 가능한 연구 기반 확보**: MONET + nano-t2i 조합으로 학술 연구자·스타트업도 상업 수준 이미지 모델 훈련 진입 장벽이 대폭 낮아졌다.
- **합성 데이터 혼합 비율 참고**: 13% 합성 비율이 최적이라는 실험 결과는 다른 생성 모델 훈련에도 바로 적용 가능한 기준점이 된다.
- **다중 캡셔닝 전략 채택 가치**: 단일 VLM 캡셔닝보다 4종 VLM 혼합이 훈련 성능에 유의미한 차이를 만든다.
- **Apache 2.0 라이선스**: 상업적 사용도 자유. [HuggingFace에서 바로 다운로드](https://huggingface.co/datasets/jasperai/monet) 가능.

---

*원문 출처: [MONET: Lowering the bar for World-Class Image Generation research](https://huggingface.co/blog/jasperai/monet) — Jasper AI (Benjamin Aubin, Gonzalo Quintana, Onur Tasar, Sanjeev Sreetharan, Czerwinska, Damien Henry, Clément Chadebec)*
