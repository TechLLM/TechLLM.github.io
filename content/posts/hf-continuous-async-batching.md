---
title: "LLM 추론 속도를 공짜로 24% 높이는 법 — 비동기 연속 배칭"
date: 2026-05-16T08:27:00+09:00
draft: false
description: "GPU가 멀쩡히 켜져 있는데 24%는 그냥 낭비된다. CUDA 스트림과 이벤트로 CPU·GPU를 동시에 돌리는 비동기 연속 배칭의 원리를 처음부터 설명한다."
cover:
  image: /images/hf-continuous-async-batching-cover.png
  alt: "비동기 연속 배칭 커버 이미지"
  caption: "Generated illustration"
tags: ["LLM추론", "GPU최적화", "CUDA", "배칭", "HuggingFace", "연속배칭", "추론최적화"]
categories: ["AI-LLM"]
---

## 개요

H200 GPU는 시간당 5달러다. 하루 쓰면 120달러. 그런데 기본 설정으로 돌리면 GPU의 24%는 그냥 논다. HuggingFace 팀이 CUDA 스트림과 이벤트만으로 이 낭비를 없애는 방법을 공개했다. 모델을 바꿀 필요도, 새 커널을 짤 필요도 없다.

## 핵심 요약

- **동기식 배칭의 근본 문제**: CPU와 GPU가 번갈아 작동하며 서로를 기다린다 → 총 실행 시간의 24%가 GPU 유휴
- **CUDA 스트림**: GPU 작업을 독립 큐에 넣으면 CPU가 즉시 돌아온다 (default stream이 이를 막았던 이유 포함)
- **CUDA 이벤트**: 스트림 간 의존성을 GPU가 직접 관리한다 — CPU 블로킹 없이 협업이 보장된다
- **비동기 배칭 핵심**: GPU가 배치 N을 처리하는 동안 CPU는 배치 N+1을 준비한다
- **이중 버퍼링 + 메모리 풀**: 경쟁 조건과 VRAM 낭비를 한꺼번에 해결한다

## 왜 GPU가 24%나 놀고 있나

### 동기식 배칭의 구조

연속 배칭(continuous batching)은 GPU 유휴를 줄이는 기술이다. 그런데 기본 구현을 **동기식**으로 돌리면 다른 종류의 낭비가 생긴다.

동작 방식은 이렇다:

1. CPU가 다음 배치를 준비한다 (요청 선택, KV 캐시 업데이트, 입력 텐서 구성)
2. CPU → GPU로 입력 전송
3. GPU가 forward pass 실행 (토큰 생성)
4. GPU → CPU로 결과 반환
5. 1로 돌아가 반복

문제는 3번과 4번 사이, 4번과 1번 사이에 있다. GPU가 계산하는 동안 CPU는 기다린다. CPU가 배치를 준비하는 동안 GPU는 기다린다. 둘이 동시에 일하는 순간이 없다.

HuggingFace 팀이 8B 모델로 배치 크기 32, 8K 토큰을 생성하며 프로파일링한 결과, **총 300.6초 중 24.0%인 72초가 GPU 유휴**였다. 이 수치가 의미하는 것 — CPU 오버헤드를 없애면 300초가 228초로 줄어든다. 공짜로 얻는 24% 속도 향상이다.

## CUDA 스트림: 동시성의 기반

### 스트림이란

CUDA 스트림은 GPU 작업들의 순서 있는 큐다. 같은 스트림 안에서는 순서대로 실행된다. 다른 스트림에 있는 작업끼리는 서로 독립적으로 동시에 돈다.

### default stream이 동시성을 죽이는 이유

PyTorch에서 스트림을 명시하지 않으면 모든 작업이 **default stream**으로 간다. default stream은 특수하다 — 다른 모든 스트림이 flush될 때까지 기다린다. 반대로 다른 스트림의 작업도 default stream을 기다린다. 결국 default stream을 쓰면 동시성이 불가능하다.

비동기 실행을 하려면 non-default stream을 써야 한다. non-default stream에 작업을 넣으면 CPU가 즉시 제어권을 돌려받는다. GPU는 백그라운드에서 돈다.

### 3개 스트림 구조

연속 배칭에서 필요한 GPU 작업은 세 종류다:

- **H2D 스트림**: CPU → GPU 입력 전송 (Host-to-Device)
- **Compute 스트림**: 모델 forward pass
- **D2H 스트림**: GPU → CPU 결과 전송 (Device-to-Host)

각각 독립 스트림으로 분리한다.

## CUDA 이벤트: 스트림 간 협조

스트림을 분리하면 새 문제가 생긴다. H2D 전송이 끝나기 전에 compute가 시작되거나, compute가 끝나기 전에 D2H가 시작될 수 있다. 실행 결과가 엉망이 된다.

**CUDA 이벤트**가 이를 해결한다. 이벤트는 스트림에 꽂는 마커다. GPU가 그 마커에 도달하면 이벤트가 완료 상태로 바뀐다. 다른 스트림은 이 이벤트를 기다리도록 설정한다. CPU가 아니라 GPU가 직접 순서를 관리한다.

실제 적용:

```
h2d_stream → [H2D 전송] → record(h2d_done)
compute_stream → wait(h2d_done) → [forward pass] → record(compute_done)
d2h_stream → wait(compute_done) → [D2H 전송] → record(d2h_done)
CPU → d2h_done.synchronize()  ← 여기서만 블로킹
```

CPU는 모든 작업을 큐에 넣고 바로 돌아온다. GPU가 이벤트 체인을 따라 순서를 보장한다. CPU가 블로킹되는 지점은 마지막 결과를 읽을 때 한 곳뿐이다.

## 비동기 배칭: 빈 시간 채우기

이제 CPU는 GPU 실행 중에 자유롭다. 이 시간에 **다음 배치(N+1)를 준비**하면 된다.

GPU가 배치 N을 처리하는 동안 CPU가 배치 N+1의 요청 선택, KV 캐시 업데이트, 입력 텐서 준비를 끝낸다. GPU가 배치 N을 끝내면 바로 N+1로 넘어간다. 대기 없이.

### 이중 버퍼링: 경쟁 조건 방지

문제가 하나 있다. 배치 N과 N+1이 같은 GPU 메모리 버퍼를 쓰면 CPU가 N+1을 쓰는 도중 GPU가 N을 읽다가 데이터가 망가진다 (race condition).

해결책은 **두 개의 슬롯(A, B)을 번갈아 쓰는 것**이다. GPU가 슬롯 A로 배치 N을 처리하는 동안 CPU는 슬롯 B에 배치 N+1을 준비한다. 다음 스텝에서 역할이 바뀐다.

### 메모리 풀: VRAM 낭비 방지

슬롯이 두 개면 CUDA 그래프도 두 개 필요하다 (각 슬롯에 하나씩). 각 그래프가 자체 메모리를 갖게 두면 VRAM이 두 배가 된다.

해결책은 **메모리 풀**이다. 두 그래프가 같은 풀에서 할당받게 한다. 두 그래프가 동시에 돌지 않으므로 실제 VRAM 사용량은 하나 쓸 때와 거의 같다. 초기화 시점에 두 번 캡처하는 비용만 추가된다.

## 실무자가 볼 핵심 포인트

1. **GPU 유휴 24%는 구조적 낭비다** — 모델이나 하드웨어 문제가 아니라 동기식 스케줄링 문제다. 고치는 비용은 거의 없다. 기존 코드 구조만 바꾸면 된다
2. **default stream 하나가 모든 동시성을 죽인다** — PyTorch 코드에서 스트림을 명시하지 않으면 기본 동기화가 깔린다. 비동기 배칭의 첫 번째 조건은 non-default stream 사용이다
3. **이벤트가 핵심** — 스트림 분리만으로는 부족하다. 의존성 체인을 GPU에 알려줘야 올바른 순서가 보장된다. CPU 블로킹 없이 GPU가 직접 조율한다
4. **이중 버퍼링은 표준 패턴** — 슬롯 A/B 교대 사용은 연속 배칭뿐 아니라 모든 비동기 GPU 파이프라인에 들어맞는다. 메모리 풀로 VRAM 추가 비용도 최소화된다
5. **Transformers 라이브러리에 이미 들어있다** — 직접 짤 필요 없이 HuggingFace transformers 코드를 보고 바로 적용하면 된다

## 원문 출처

*원문: [Unlocking asynchronicity in continuous batching — HuggingFace Blog, Rémi Ouazan Reboul 외 (2026. 5. 14)](https://huggingface.co/blog/continuous_async)*
