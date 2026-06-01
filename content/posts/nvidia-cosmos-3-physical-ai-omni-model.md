---
title: "NVIDIA Cosmos 3 — 로보틱스·자율주행을 위한 첫 오픈 옴니모델"
date: 2026-06-01T17:19:00+09:00
draft: false
description: "NVIDIA가 2026년 6월 1일 Cosmos 3를 공개했다. Mixture-of-Transformers(MoT) 아키텍처로 세계 생성·물리 추론·행동 생성을 단일 모델에 통합한 첫 오픈 물리적 AI 기반 모델이다. Hugging Face에서 오늘 바로 사용 가능하다."
tags: ["NVIDIA", "Cosmos3", "물리적AI", "로보틱스", "자율주행", "세계모델", "MoT", "멀티모달"]
cover:
  image: /images/nvidia-cosmos-3-physical-ai-omni-model-cover.png
  alt: "NVIDIA Cosmos 3 — 물리적 AI를 위한 오픈 옴니모델"
---

## 개요

NVIDIA가 2026년 6월 1일 Cosmos 3를 공개하고 Hugging Face에 올렸다. 물리적 AI(Physical AI)를 위한 세계 기반 모델(World Foundation Model)의 새로운 전환점이다. 핵심은 단일 통합 아키텍처 — 이전 Cosmos 버전들이 각각 다른 모델로 처리하던 세계 생성, 물리 추론, 행동 생성을 하나의 모델 한 번의 포워드 패스로 처리한다.

## 핵심 요약

- **Mixture-of-Transformers(MoT)** 아키텍처 — 텍스트·이미지·영상·오디오·행동을 단일 모델 처리
- 이전 Cosmos: 생성(Predict)·전환(Transfer)·이해(Reason)·정책(Policy) 각각 별도 모델 → Cosmos 3: 단일 모델
- **AR + DM 하이브리드**: 자동회귀(추론/이해) + 확산(생성) 토큰이 공동 어텐션으로 상호작용
- **두 크기**: Cosmos 3 Nano (8B, RTX PRO 6000급), Cosmos 3 Super (32B, Hopper/Blackwell)
- Hugging Face Diffusers `Cosmos3OmniPipeline` 통합, 코드 몇 줄로 바로 실행
- 물리적 AI 커뮤니티를 위한 합성 데이터(SDG) 6종 데이터셋 동시 공개

## MoT 아키텍처: 단일 모델이 모든 모달리티를 처리하는 방법

Cosmos 3의 핵심 혁신은 Mixture-of-Transformers 아키텍처다.

각 모달리티는 전용 인코더를 거친다 — 시각 이해는 ViT, 시각·오디오 생성은 VAE, 행동은 도메인 인식 벡터. 인코딩 후 공유 표현 공간으로 투사된다.

입력 시퀀스는 두 서브시퀀스로 분리된다:
- **AR(자동회귀) 서브시퀀스**: 다음 토큰 예측 방식으로 추론과 이해를 담당
- **DM(확산) 서브시퀀스**: 반복적 디노이징으로 생성을 담당

AR과 DM 토큰은 각 트랜스포머 레이어에서 별도 파라미터 세트를 사용하지만 공동 어텐션(joint attention)을 통해 상호작용한다. 이 구조 덕분에 아키텍처 변경 없이 VLM, 비디오 생성기, 순방향/역방향 다이나믹스 모델, 로봇 정책 중 어느 역할로도 원활하게 전환된다.

## 지원 입출력 조합

| 입력 | 출력 | 애플리케이션 |
|------|------|-------------|
| 텍스트·이미지·영상 | 영상 | 비디오 모델 |
| 텍스트·영상 | 텍스트 | Vision Language Model |
| 행동·이미지·텍스트 | 영상 | 순방향 다이나믹스 모델 |
| 텍스트·영상 | 행동 | 역방향 다이나믹스 모델 |
| 이미지·텍스트 | 영상 + 행동 | 정책 모델 |

## 모델 크기와 접근성

**Cosmos 3 Nano** (8B): 워크스테이션급 GPU(RTX PRO 6000)에서 실행 가능. Hugging Face `nvidia/Cosmos3-Nano` 에서 다운로드.

**Cosmos 3 Super** (32B): 대규모 합성 데이터 생성과 연구용. NVIDIA Hopper·Blackwell GPU에서 실행. `nvidia/Cosmos3-Super`.

Hugging Face Diffusers 라이브러리에 통합돼 `Cosmos3OmniPipeline`으로 기존 파이프라인에 바로 연결할 수 있다:

```python
from diffusers import Cosmos3OmniPipeline
pipe = Cosmos3OmniPipeline.from_pretrained(
    "nvidia/Cosmos3-Nano", torch_dtype=torch.bfloat16, device_map="cuda"
)
result = pipe(prompt=prompt, num_frames=1, height=720, width=1280)
```

## 합성 데이터 6종 동시 공개

Cosmos 3 출시와 함께 물리적 AI 커뮤니티를 위한 합성 데이터셋 6종을 Hugging Face에 공개했다:

- **Embodied-Robot-Scenes**: 로봇 시뮬레이션 데이터
- **Physical-Interaction-Scenes**: Isaac Sim 물리 시뮬레이션
- **Spatial-Reasoning**: 구현된 공간 추론 데이터
- **Digital-Human-Scenes**: 합성 인간 동작 데이터
- **Autonomous-Driving-Scenarios**: 자율주행 시뮬레이션
- **Warehouse-Operations-Scenes**: 창고 환경 데이터

이 데이터셋들은 세계 기반 모델 학습과 평가를 위해 NVIDIA 팀들이 직접 생성한 것들이다.

## 실제 활용 시나리오

NVIDIA가 강조하는 세 가지 핵심 유스케이스:

**로보틱스**: 빨래 접기 같은 물체 조작 태스크의 픽-앤-플레이스 시나리오 영상 생성 및 정책 학습.

**자율주행**: 고속도로 위 예상치 못한 장애물 등 롱테일 시나리오 시뮬레이션. 실제 주행 데이터로 커버하기 어려운 엣지 케이스를 합성 데이터로 보완.

**스마트 공간**: 창고 안전 시나리오 데이터 생성 — 작업자 동선, 위험 상황 시뮬레이션.

## 실무자가 볼 핵심 포인트

**로보틱스 엔지니어**에게 Cosmos 3의 핵심 가치는 단일 모델로 순방향 다이나믹스(행동→결과 예측)와 역방향 다이나믹스(결과→행동 추론)를 모두 처리한다는 점이다. 별도 모델을 조합하던 파이프라인 복잡도가 크게 줄어든다.

**자율주행 데이터 팀**에게 Autonomous-Driving-Scenarios 데이터셋과 Cosmos 3 Super의 SDG 능력은 실제 주행으로 수집하기 어려운 롱테일 시나리오를 대규모로 생성하는 현실적 경로다.

**AI 연구자**라면 Cosmos Framework GitHub에서 포스트트레이닝 스크립트를 확인할 것. 자체 데이터로 파인튜닝해 특정 로봇이나 환경에 특화된 모델을 만들 수 있는 구조가 갖춰져 있다. Nano 크기라면 워크스테이션 한 대로도 실험 가능하다.

**인프라 관점**에서 8B Nano 모델이 RTX PRO 6000급에서 동작한다는 것은 엔터프라이즈 워크스테이션 수준의 하드웨어로 물리적 AI 파이프라인을 시험해볼 수 있다는 뜻이다. 32B Super는 연구·프로덕션 SDG 용도다.

## 원문 출처

*원문: [Welcome NVIDIA Cosmos 3: The First Open Omni-model for Physical AI Reasoning and Action](https://huggingface.co/blog/nvidia/cosmos-3-for-physical-ai) — Asawaree B., Atharva Joshi / Hugging Face Blog (2026-06-01)*
