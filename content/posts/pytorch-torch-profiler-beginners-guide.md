---
title: "PyTorch 프로파일링 입문: torch.profiler로 GPU 병목을 읽는 법"
date: 2026-05-30T20:18:00+09:00
draft: false
description: "HuggingFace 팀이 공개한 PyTorch 프로파일링 시리즈 1편. torch.profiler 기본 설정부터 프로파일러 테이블·트레이스 해석, 오버헤드 바운드와 컴퓨트 바운드의 차이까지 행렬 곱셈 예제로 쉽게 설명한다."
tags: ["PyTorch", "프로파일링", "GPU최적화", "머신러닝", "딥러닝"]
cover:
  image: /images/pytorch-torch-profiler-beginners-guide-cover.png
  alt: "PyTorch torch.profiler beginner guide"
---

## 개요

"프로파일링을 못 하면 최적화도 못 한다." HuggingFace 팀이 시작한 *Profiling in PyTorch* 시리즈의 첫 번째 글이다. 가장 단순한 연산인 행렬 곱셈(matmul)과 편향 덧셈(bias add)에서 출발해, `torch.profiler`가 돌려주는 테이블과 트레이스를 어떻게 읽는지 처음부터 설명한다. GPU 최적화의 첫 관문인 오버헤드 바운드와 컴퓨트 바운드 개념도 실제 숫자로 체감할 수 있다.

## 핵심 요약

- `torch.profiler`는 **프로파일러 테이블**(시간 통계)과 **트레이스**(실행 시간 순서)를 동시에 제공한다
- 작은 행렬(64×64)에서 GPU는 전체 시간의 1% 미만만 쓴다 — 나머지는 CPU의 커널 준비·발사 오버헤드
- 행렬을 4096×4096으로 키우면 CPU와 GPU 시간이 비슷해지며 컴퓨트 바운드로 전환된다
- `record_function`으로 코드 구간에 이름을 붙이면 트레이스에서 바로 찾을 수 있다
- 트레이스는 Perfetto UI에 JSON을 업로드하거나 `uvx trace-util`로 시각화한다
- 시리즈는 nn.Linear → MLP → LLM으로 점진적으로 확장 예정

## torch.profiler 기본 세팅

프로파일링할 함수를 정의한 뒤 세 가지를 추가하면 된다.

**① 함수 어노테이션**
```python
def step():
    with torch.profiler.record_function("matmul_add"):
        return fn(x, w, b)
```
`record_function`은 선택 사항이지만, 트레이스에서 해당 구간을 이름으로 바로 찾을 수 있어 강력히 권장한다.

**② 프로파일러 컨텍스트 매니저**
```python
with torch.profiler.profile(
    activities=[
        torch.profiler.ProfilerActivity.CPU,
        torch.profiler.ProfilerActivity.CUDA,
    ],
) as prof:
    for _ in range(5):
        step()
        prof.step()
```
GPU가 워밍업될 수 있도록 같은 연산을 여러 번 반복하는 것이 권장된다.

**③ 결과 내보내기**
```python
# 통계 테이블
prof.key_averages().table(sort_by="cuda_time_total", row_limit=15)

# 시간 순서 트레이스
prof.export_chrome_trace(trace_path)
```

## 프로파일러 테이블 읽기

테이블은 각 이벤트가 CPU·GPU에서 얼마나 걸렸는지 요약한다. 두 가지 개념을 구분하는 것이 핵심이다.

- **Self 시간**: 해당 이벤트 자체의 시간 (하위 이벤트 제외)
- **Total 시간**: 해당 이벤트 + 모든 하위 이벤트 포함

64×64 행렬에서의 결과:
```
Self CPU time total:  2.314ms
Self CUDA time total: 23.104us
```

GPU가 CPU 대비 0.001배 시간을 쓴다. GPU는 거의 놀고 있는 셈이다. 작은 행렬은 GPU가 너무 빨리 계산을 끝내버려서, 오히려 **CPU가 커널을 준비하고 발사하는 시간이 병목**이 된다. 이것이 오버헤드 바운드다.

4096×4096으로 키우면:
```
Self CPU time total:  4.908ms
Self CUDA time total: 4.495ms
```

두 숫자가 비슷해졌다. GPU가 충분히 바빠졌다는 뜻이고, 이제는 **GPU 연산 자체가 병목**인 컴퓨트 바운드 상태가 됐다. 최적화가 의미 있으려면 컴퓨트 바운드 상태에서 시작해야 한다.

## 트레이스 읽기

트레이스 JSON을 [Perfetto UI](https://ui.perfetto.dev)에 올리거나 `uvx trace-util traces -b traces` 명령으로 링크를 생성할 수 있다.

트레이스에는 두 개의 레인이 있다.
- **CPU 레인**: Python 호출부터 커널 발사까지의 흐름
- **GPU 레인**: 실제 커널 실행 시간

막대 너비가 지속 시간이고, 수직 중첩이 호출 계층이다. CPU 레인과 GPU 레인 사이의 **빈 공간이 유휴 시간**이다. 64×64 트레이스를 보면 GPU 레인이 대부분 비어 있고, CPU 레인에는 커널을 준비하는 이벤트가 가득하다.

WASD 키로 트레이스를 탐색할 수 있다.

## 오버헤드 바운드를 이해하는 것이 왜 중요한가

LLM 추론이나 학습 루프를 최적화할 때, 아무리 커널을 바꿔봐도 성능이 나아지지 않는 경우가 있다. 이미 오버헤드 바운드라면 커널 최적화는 의미가 없다. 병목이 CPU의 커널 발사 오버헤드에 있기 때문이다.

반대로, 이미 컴퓨트 바운드라면 `torch.compile`이나 플래시 어텐션 같은 커널 수준 최적화가 효과를 낸다. **프로파일러 없이는 어느 상태인지 알 수 없다.**

## 실무자가 볼 핵심 포인트

**AI 인프라·모델 서빙 엔지니어**에게 이 시리즈는 필독이다. 작은 배치 사이즈, 짧은 시퀀스, 가벼운 모델에서 추론이 느린 원인은 대부분 오버헤드 바운드다. `torch.profiler` 한 번 돌리고 테이블에서 Self CUDA time을 보면 현재 상태를 바로 판단할 수 있다.

**연구자와 ML 엔지니어**에게는 `record_function` 습관을 들이는 것이 첫 번째다. 실험 코드에 이름을 붙여두면 나중에 트레이스를 볼 때 어디를 봐야 하는지 즉시 알 수 있다.

시리즈 2편에서는 `nn.Linear`와 소형 MLP로 확장하고, 트레이스로 최적화를 유도한다. 3편은 LLM + transformers다. 순서대로 따라가면 실제 LLM 추론 최적화까지 연결된다.

## 원문 출처

*원문: [Profiling in PyTorch (Part 1): A Beginner's Guide to torch.profiler](https://huggingface.co/blog/torch-profiler) — Aritra Roy Gosthipaty, Sayak Paul, Sergio Paniego, Rémi Ouazan Reboul, Pedro Cuenca / HuggingFace Blog (2026-05-29)*
