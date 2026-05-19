---
title: "DeepInfra, Hugging Face Inference Provider로 합류하다"
date: 2026-05-07T11:00:00+09:00
draft: false
description: "업계 최저 수준의 토큰 단가를 내세운 서버리스 AI 추론 플랫폼 DeepInfra가 Hugging Face Hub의 공식 Inference Provider로 합류했습니다. DeepSeek V4 Pro, Kimi-K2.6 등 100개 이상의 모델을 HF 토큰 하나로 바로 사용할 수 있습니다."
cover:
  image: "/images/deepinfra-hf-welcome.jpg"
  alt: "DeepInfra on Hugging Face Inference Providers"
  caption: "DeepInfra가 Hugging Face Hub의 공식 Inference Provider로 합류했다"
tags:
  - DeepInfra
  - HuggingFace
  - InferenceProvider
  - LLM
  - 서버리스AI
  - DeepSeek
  - API
  - AI 개발 & 인프라
  - LLM & 모델
categories: ["AI-LLM"]
summary: "DeepInfra가 Hugging Face Inference Provider로 합류했다. HF 토큰 하나로 DeepSeek V4 Pro, Kimi-K2.6 등 100개 이상의 오픈웨이트 모델을 OpenAI 호환 API로 호출할 수 있으며, PRO 플랜은 매월 $2 크레딧을 전체 Provider에서 공유 사용한다."
---

## 핵심 요약

2026년 4월 29일, **DeepInfra**가 Hugging Face Hub의 공식 Inference Provider로 합류했습니다. 이제 Hugging Face 계정 하나로 DeepInfra가 서비스하는 100개 이상의 모델을 추가 설정 없이 바로 호출할 수 있습니다.

![DeepInfra on Hugging Face](/images/deepinfra-hf-welcome.jpg)

---

## DeepInfra란?

[DeepInfra](https://deepinfra.com)는 서버리스 AI 추론 플랫폼으로, 업계 최저 수준의 토큰 단가를 강점으로 내세웁니다. LLM 텍스트 생성 외에도 텍스트→이미지, 텍스트→비디오, 임베딩 등 다양한 태스크를 지원하며, 현재 100개 이상의 모델을 운용하고 있습니다.

이번 Hugging Face 통합의 초기 릴리즈에서는 **텍스트 생성 및 대화형 태스크**를 우선 지원하며, 이미지·비디오·임베딩 등 추가 태스크는 순차 출시 예정입니다.

---

## 지원 모델

초기 통합으로 접근 가능한 주요 모델:

| 모델 | 파라미터 | 비고 |
|------|---------|------|
| DeepSeek V4 Pro | 862B | 최신 DeepSeek 추론 모델 |
| Kimi-K2.6 | 1.1T | Moonshot AI 멀티모달 |
| GLM-5.1 | 754B | Zhipu AI 텍스트 생성 |

Hugging Face 모델 허브에서 `inference_provider=deepinfra` 필터로 전체 목록을 확인할 수 있습니다.

---

## 사용하는 두 가지 방법

### 1. HF 토큰으로 라우팅 (추가 가입 불필요)

Hugging Face 계정만 있으면 됩니다. 요금은 HF 계정에 직접 청구되며, DeepInfra 단가 그대로 적용됩니다 (별도 마크업 없음).

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Pro:deepinfra",
    messages=[{"role": "user", "content": "피보나치 함수를 메모이제이션으로 구현해줘"}],
)
print(completion.choices[0].message)
```

JavaScript도 동일한 구조입니다:

```javascript
import { OpenAI } from "openai";

const client = new OpenAI({
    baseURL: "https://router.huggingface.co/v1",
    apiKey: process.env.HF_TOKEN,
});

const result = await client.chat.completions.create({
    model: "deepseek-ai/DeepSeek-V4-Pro:deepinfra",
    messages: [{ role: "user", content: "피보나치 함수를 메모이제이션으로 구현해줘" }],
});
```

### 2. DeepInfra API 키 직접 사용

DeepInfra 계정의 API 키를 HF 계정 설정에 등록하면, 요청이 DeepInfra로 직접 전달되고 DeepInfra 계정에 청구됩니다.

---

## 요금 구조

- **라우팅 방식**: DeepInfra 기본 단가 그대로, HF 계정 청구 (마크업 없음)
- **직접 키 방식**: DeepInfra 계정에 직접 청구
- **PRO 플랜**: 매월 $2 상당의 Inference 크레딧 제공 — DeepInfra 포함 전체 Provider에서 사용 가능

---

## 에이전트 하네스 통합

HF Inference Providers는 주요 에이전트 프레임워크에 이미 통합되어 있습니다. OpenClaw, Pi, OpenCode, Hermes Agents 등에서 DeepInfra 모델을 별도 설정 없이 바로 사용할 수 있습니다.

---

## 실무자가 볼 포인트

- **비용**: DeepInfra는 업계 최저 단가 중 하나로 알려져 있습니다. HF 라우팅을 쓰면 마크업 없이 동일 단가를 HF 계정 하나로 관리할 수 있습니다.
- **OpenAI 호환 API**: `base_url`만 바꾸면 기존 OpenAI 클라이언트 코드를 그대로 재사용할 수 있습니다.
- **모델 선택 폭**: DeepSeek, Kimi, GLM 계열 대형 모델을 단일 엔드포인트로 전환하며 쓸 수 있습니다.
- **향후 확장**: 텍스트→이미지, 임베딩 등 추가 태스크 지원이 예정되어 있습니다.

---

## 결론

DeepInfra의 HF Inference Provider 합류로, 100개 이상의 오픈웨이트 모델을 HF 토큰 하나와 OpenAI 호환 API로 접근할 수 있게 됐습니다. 특히 비용 민감한 프로젝트에서 DeepInfra의 낮은 단가와 HF PRO 크레딧을 조합하면 실질적인 이점이 있습니다.

---

**원문**: [DeepInfra on Hugging Face Inference Providers](https://huggingface.co/blog/inference-providers-deepinfra) (Hugging Face Blog, 2026-04-29)
