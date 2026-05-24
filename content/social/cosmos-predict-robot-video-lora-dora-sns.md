---
title: "Cosmos Predict 2.5 로봇 영상 LoRA/DoRA SNS 콘텐츠"
date: 2026-05-24T21:39:06+09:00
draft: false
description: "Cosmos Predict 2.5 로봇 영상 LoRA/DoRA 글을 위한 Threads 문안과 Instagram 카드뉴스 구성"
---

# SNS Content — Cosmos Predict Robot Video LoRA/DoRA

블로그 URL: https://techllm.github.io/posts/cosmos-predict-robot-video-lora-dora/
대표 이미지: https://techllm.github.io/images/cosmos-predict-robot-video-lora-dora-cover.png

## Threads

**P1**
> 로봇 AI에서 진짜 병목은 모델보다 데이터일 수 있습니다.
>
> NVIDIA가 Cosmos Predict 2.5를 LoRA/DoRA로 파인튜닝한 글의 핵심은 단순합니다.
>
> 거대한 비디오 월드 모델 전체를 다시 학습하지 않고, 92개 로봇 조작 영상만으로 도메인에 맞는 합성 영상을 만들 수 있느냐.
>
> 답은 꽤 현실적인 쪽으로 가고 있습니다.

**P2**
> 핵심은 LoRA/DoRA 어댑터입니다.
>
> VAE, 텍스트 인코더, DiT 기본 가중치는 동결하고,
> attention projection과 feed-forward 계층에 작은 어댑터만 붙입니다.
>
> rank 32 기준 학습 가능한 파라미터는 약 5천만 개.
> 전체 2B 모델을 흔드는 대신, 로봇 조작 도메인에 필요한 방향만 덧붙이는 구조입니다.

**P3**
> 흥미로운 건 결과 해석입니다.
>
> 파인튜닝 후 Sampson Error, 물리적 타당성, 지시 준수 점수가 좋아졌습니다.
> 다만 이것이 바로 실제 로봇 정책 성능 향상을 보장하진 않습니다.
>
> 합성 데이터는 대체재가 아니라 보조 엔진입니다.
>
> 정리 글:
> https://techllm.github.io/posts/cosmos-predict-robot-video-lora-dora/
>
> #AI #Robotics #LoRA #DoRA #WorldModel

## Instagram Caption

**전문가형**
```
로봇 AI에서 가장 비싼 건 모델이 아니라 데이터일 수 있습니다.

NVIDIA가 공개한 Cosmos Predict 2.5 파인튜닝 글은
92개 로봇 조작 영상만으로
LoRA/DoRA 어댑터를 학습해 합성 로봇 영상을 만드는 흐름을 보여줍니다.

핵심은 전체 2B 모델을 다시 학습하지 않는 것입니다.

• VAE, 텍스트 인코더, DiT 기본 가중치는 동결
• DiT 일부 계층에 LoRA/DoRA 어댑터만 주입
• rank 32 기준 약 5천만 개 파라미터만 학습
• 단일 80GB GPU에서도 실험 가능한 구조
• 파인튜닝 후 기하 일관성, 물리 타당성, 지시 준수 점수 개선

다만 합성 영상이 좋아졌다고
바로 실제 로봇 정책 성능이 좋아진다고 볼 수는 없습니다.

중요한 질문은 하나입니다.
“이 합성 데이터가 실제 로봇 실패율을 줄이는가?”

전체 해설은 TechLLM 블로그에 정리했습니다.
🔗 https://techllm.github.io/posts/cosmos-predict-robot-video-lora-dora/
```

## Instagram 카드뉴스 구성

1. 로봇 AI의 병목은 데이터다
2. Cosmos Predict 2.5를 로봇 영상에 맞게 조정
3. 전체 모델 대신 LoRA/DoRA 어댑터만 학습
4. 92개 영상으로 합성 로봇 궤적 생성
5. 지표는 좋아졌지만 실제 정책 전이는 별도 검증
6. 결론: 합성 데이터는 대체재가 아니라 보조 엔진

## Hashtags

#AI #Robotics #RobotLearning #WorldModel #VideoGeneration #CosmosPredict #NVIDIA #LoRA #DoRA #SyntheticData #PhysicalAI #AI개발 #로봇AI #TechLLM

## 카드뉴스 이미지

`content/social/cards/cosmos-predict-robot-video-lora-dora/card-01~06.png`
