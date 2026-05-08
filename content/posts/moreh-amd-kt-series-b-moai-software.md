---
title: "엔비디아 CUDA 독점을 깨겠다는 한국 스타트업에 AMD가 돈을 댔다"
date: 2023-10-26T08:00:00+09:00
draft: false
description: "한국 AI 소프트웨어 스타트업 모레(Moreh)가 AMD·KT 등으로부터 220억 원 규모 시리즈 B를 유치했다. AMD GPU로 Nvidia A100 대비 116% 높은 처리량을 달성했다고 주장한다."
cover:
  image: "/images/moreh-amd-kt-series-b-cover.jpg"
  alt: "Moreh MoAI — Korean AI software challenging Nvidia CUDA"
  caption: "Generated illustration"
tags:
  - 모레
  - Moreh
  - AMD
  - KT
  - AI인프라
  - GPU
  - 한국스타트업
  - 시리즈B
  - CUDA대항마
categories:
  - AI 산업
  - 스타트업
summary: "엔비디아 CUDA를 대체하겠다는 한국 AI 소프트웨어 스타트업 모레(Moreh)가 AMD·KT로부터 2,200만 달러 시리즈 B를 유치했다. AMD MI250으로 Nvidia A100 대비 GPU 처리량 116% 우위를 주장하며, 2,110억 파라미터 한국어 LLM 훈련도 완료했다."
---

## 핵심 요약

엔비디아 CUDA의 대항마를 만들겠다는 한국 AI 소프트웨어 스타트업 **모레(Moreh)**가 AMD, KT를 포함한 투자자들로부터 **2,200만 달러(약 300억 원) 시리즈 B**를 유치했다. 누적 투자액은 3,000만 달러.

서울·산타클라라 이중 거점의 이 회사가 만드는 것은 GPU 위에서 돌아가는 AI 소프트웨어 플랫폼 **MoAI**다. 쉽게 말해 "AMD GPU로도 엔비디아와 같은 성능을 내게 해주는 소프트웨어"다.

---

## 엔비디아 CUDA가 뭐길래

AI 모델을 훈련하고 추론하려면 GPU가 필요하다. 그런데 GPU만 있다고 끝이 아니다. GPU 위에서 딥러닝 연산을 효율적으로 돌려주는 **소프트웨어 스택**이 필요하다.

엔비디아는 이 소프트웨어를 **CUDA**라는 플랫폼으로 묶어 놨다. PyTorch, TensorFlow 같은 머신러닝 프레임워크는 사실상 CUDA 위에서만 제대로 돌아간다. AMD나 인텔 칩을 써도 이 에코시스템의 벽 때문에 호환성 문제가 생긴다. 이게 엔비디아가 AI 시장을 장악한 진짜 이유다.

모레는 이 벽을 부수겠다고 나선 것이다.

---

## MoAI: 코드 한 줄 안 바꿔도 AMD에서 돌아간다

모레의 플래그십 소프트웨어 **MoAI(Machine intelligence Of Artificial Intelligence)**는 CUDA와 비슷한 역할을 하되, AMD GPU를 비롯한 다양한 칩에서 작동한다.

핵심 가치 제안:

- PyTorch, TensorFlow 등 기존 프레임워크와 호환
- **코드 변경 없이** 기존 AI 모델을 AMD GPU에서 실행 가능
- GPU뿐 아니라 NPU(신경망처리장치) 같은 다른 AI 칩도 지원
- 소수의 GPU로 운영하던 기존 AI 소프트웨어의 한계를 대규모 인프라로 확장

---

## KT와 함께 검증한 성능 수치

KT는 2021년부터 모레와 협력해 AMD GPU + MoAI 기반 AI 인프라를 구축해왔다. 여기서 나온 수치가 흥미롭다.

> AMD MI250 Instinct + MoAI 플랫폼이 엔비디아 A100 대비 **GPU 처리량 116% 우위**를 기록

추가로 모레는 MoAI를 사용하면 대규모 AI 모델 훈련 시작에 걸리는 총 시간을 **10분의 1로 단축**할 수 있다고 주장한다.

KT는 이 검증을 거쳐 이번 시리즈 B 투자자로 참여했고, AMD도 직접 투자 라운드에 이름을 올렸다. 돈을 넣은 당사자들이 실효성을 인정했다는 의미다.

---

## 2,110억 파라미터 한국어 LLM도 훈련 완료

회사 설립 3년 차에 모레는 이미 의미 있는 레퍼런스를 쌓았다.

- **2,110억 파라미터 한국어 LLM 훈련 완료** — 오픈소스로 공개 예정
- 2021년부터 수익 발생
- 2023년 말 매출 목표 약 3,000만 달러
- 현재 직원 70명

GPU 공급 부족이 전 세계적으로 심각한 상황에서, AMD GPU를 효율적으로 활용할 수 있는 소프트웨어 스택은 데이터센터 운영자와 AI 개발자 모두에게 실질적인 대안이 된다.

---

## 왜 AMD가 직접 투자했나

AMD 입장에서 모레는 단순한 투자처가 아니다. 자사 GPU의 소프트웨어 에코시스템을 강화해주는 파트너다.

AMD 데이터센터 GPU 부문 부사장 Brad McCredie는 이렇게 말했다.

> "AMD AI 하드웨어를 지원하는 소프트웨어 생태계는 계속 성장하고 있으며, 데이터 과학자들과 AI 모델 개발자들에게 선택지를 제공하고 있다."

CUDA 락인(lock-in)을 깨려는 AMD의 전략적 이해관계와 모레의 기술 방향이 맞아떨어진 것이다.

---

## 실무자가 볼 포인트

- **엔비디아 GPU 구하기 어렵다면?** MoAI 같은 플랫폼이 AMD GPU를 대안으로 만들어주는 소프트웨어 레이어다. 인프라 선택지가 넓어진다.
- **코드 재작성 없는 마이그레이션**은 기업 입장에서 가장 현실적인 진입 장벽 제거다. CUDA 기반 코드베이스를 그대로 쓸 수 있다면 전환 비용이 거의 없다.
- 한국 스타트업이 LLM 훈련 인프라 레이어에서 글로벌 플레이어와 경쟁 중이라는 점 자체가 주목할 지점이다.

---

**원문**: [AMD and Korean telco KT back AI software developer Moreh in $22M Series B](https://techcrunch.com/2023/10/25/amd-korean-telco-kt-among-backers-in-ai-software-developer-moreh-in-22m-series-b/) — TechCrunch (2023-10-25)
