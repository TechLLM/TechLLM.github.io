---
title: "에이전트에게 ZeroGPU를 주면: AI 앱을 자율로 만들고 배포하는 법"
date: 2026-05-29T17:14:00+09:00
draft: false
description: "HuggingFace ZeroGPU와 AI 코딩 에이전트를 결합하면 월 9달러로 바이럴 AI 데모 앱을 자율 배포할 수 있다. Victor Mustar가 단일 에이전트 세션으로 LongCat 영상 Space를 2시간 만에 만든 실전 레시피."
tags: ["ZeroGPU", "HuggingFace", "AI에이전트", "Claude Code", "자율배포"]
cover:
  image: /images/zerogpu-autonomous-agent-deploy-cover.png
  alt: "AI agent autonomously deploying on ZeroGPU"
---

## 개요

월 9달러짜리 HuggingFace PRO 구독 하나가 AI 에이전트에게 GPU 인프라 전체를 쥐여줄 수 있다면? Victor Mustar는 그 조합으로 단 한 번의 에이전트 세션에서 LongCat 영상 아바타 Space를 2시간 만에 만들어 배포했다. 에이전트가 533개의 셸 명령을 실행하며 빌드·진단·수정·검증 루프를 완전히 혼자 돌렸다.

## 핵심 요약

- HuggingFace PRO($9/월)가 ZeroGPU Space 10개 + 하루 40분 Blackwell GPU를 제공한다
- ZeroGPU는 함수 실행 중에만 GPU를 붙이기 때문에 유휴 시간에는 비용이 0이다
- 에이전트에게 킥오프 프롬프트 + 운영 Gist 링크만 주면 배포부터 검증까지 자율 진행된다
- `hf` CLI + `gradio_client` 조합이 에이전트의 배포-검증 루프를 가능하게 한다
- 트래픽이 폭발해도 HuggingFace 인프라가 알아서 스케일한다

## ZeroGPU가 다른 이유

일반 클라우드 GPU는 사용하든 안 하든 24시간 과금된다. ZeroGPU는 다르다. 추론 함수에 데코레이터 하나를 붙이면 GPU가 그 함수가 실행되는 동안만 붙었다가 빠진다.

```python
import spaces

@spaces.GPU(duration=120)
def generate(image, audio, prompt):
    return pipe(image, audio, prompt)
```

사용자 입장에서는 무료다. 익명 사용자는 하루 2분, 무료 계정은 5분, PRO는 40분의 GPU 쿼터를 각자 소모한다. 개발자 돈이 나가는 게 아니다. 데모가 바이럴이 돼도 청구서 폭탄이 없다. 이게 핵심이다.

## 에이전트를 풀어놓는 레시피

준비물은 세 가지다.

1. **HuggingFace PRO** ($9/월): ZeroGPU Space 호스팅 + Blackwell GPU 쿼터
2. **코딩 에이전트**: Codex CLI, Claude Code, Cursor 등 `/goal` 을 지원하는 것
3. **데모할 모델**: 이 사례에서는 `meituan-longcat/LongCat-Video-Avatar-1.5`

`hf` CLI 설치 후 에이전트에게 이 프롬프트를 넣는다.

```
/goal Build a ZeroGPU Space demoing <MODEL_CARD_URL>.

First, read https://gist.github.com/gary149/2aba2962375fa9ca56bb9ef53f00b73d.
These are the operational rules for iterating on HF Spaces.

Use the hf CLI to create the Space and clone it locally.

The deployed Space is your AI lab. Work autonomously: push, diagnose, fix,
repeat. Verify every change by calling the live API.

Success = a Space that loads, runs the model on ZeroGPU, and returns a valid
result via the API.
```

핵심 문장은 두 개다. "배포된 Space가 너의 AI 랩이다"와 "라이브 API를 실제로 호출해서 검증해라." 이 두 줄이 에이전트에게 배포 루프와 검증의 소유권을 넘긴다. 인간이 중간에 개입할 필요가 없어진다.

## Gist 링크가 하는 일

킥오프 프롬프트에 붙은 Gist 링크가 에이전트 동작의 핵심 규칙을 가르친다.

- **빌드는 느리고, 로그 읽기는 빠르다** → 추측하지 말고 로그로 반복하라
- **반복 사다리**: 핫 리로드 → 개발 모드 SSH → 선택적 업로드 → 전체 리빌드
- **ZeroGPU 패턴**: 모델을 모듈 레벨에서 cuda에 올리고, 추론 함수에만 `@spaces.GPU`를 달고, 10B 이상 LLM은 4-bit NF4로 양자화
- **검증**: `gradio_client.Client`로 배포된 API를 직접 호출하고 출력 파일을 확인

이 규칙 셋이 없으면 에이전트는 빌드가 완료됐는지 모른 채 잘못된 가정으로 계속 수정하다 헤맨다.

## 실제로 에이전트가 한 일

Victor의 세션에서 에이전트는 약 2시간 동안 533개의 셸 명령을 실행했다.

- 로그 조회: 97회
- Space 상태 확인: 50회
- 선택적 업로드: 18회
- Space 재시작: 12회

그리고 매 변경마다 `gradio_client.Client(...).predict(...)` 로 라이브 API 응답 시간을 측정했다. 결과는 DBCache(CacheDiT의 캐싱 기법)로 생성 속도를 186초 → 121초(35% 향상)로 줄이고, Gradio 6.10 + 8단계 DMD2 INT8 DiT를 적용하고, 예시 캐싱으로 로드 시간을 80초 → 1.3초로 단축했다. xlarge 인스턴스 전환 여부는 에이전트가 문서를 직접 읽고 트레이드오프(쿼터 2배, 큰 큐, 풀 Blackwell)를 먼저 정리한 뒤 배포했다.

최종 청구: 토큰 1,834,906개, 약 2시간 2분. GPU 비용은 여전히 월 9달러다.

## 실무자가 볼 핵심 포인트

이 워크플로는 AI 데모를 반복 빠르게 만들어야 하는 모든 개발자에게 즉시 쓸 수 있다.

**비용 구조가 근본적으로 다르다.** 유휴 시간에 청구가 없고, 바이럴이 돼도 비용이 선형으로 늘지 않는다. 클라우드 GPU를 직접 빌려 Demo를 운영할 때의 가장 큰 위험(갑자기 터지면 청구서 폭발)이 사라진다.

**에이전트 루프가 배포-검증 사이클에 딱 맞다.** `hf` CLI와 `gradio_client`는 에이전트가 셸에서 직접 쓸 수 있는 도구다. 라이브 API를 직접 호출해 검증하는 방식은 에이전트의 "실행 → 관찰 → 수정" 루프와 자연스럽게 맞물린다.

**커뮤니티 분배가 내장되어 있다.** 트렌딩 Space는 HuggingFace 홈페이지에 노출된다. 별도 마케팅 없이 잠재적 사용자에게 도달할 수 있다.

한계는 있다. ZeroGPU는 Gradio SDK와 PyTorch 2.8+, Python 3.10/3.12 조합에서만 동작한다. FastAPI나 커스텀 프레임워크를 쓰고 싶다면 이 스택이 맞지 않는다. 하지만 AI 데모 앱이라는 유스케이스에서는 이 제약이 거의 문제가 되지 않는다.

## 원문 출처

*원문: [Give your agents ZeroGPU to ship viral AI apps autonomously](https://huggingface.co/blog/victor/building-zerogpu-spaces-autonomously) — Victor Mustar / HuggingFace Blog (2026-05-26)*
