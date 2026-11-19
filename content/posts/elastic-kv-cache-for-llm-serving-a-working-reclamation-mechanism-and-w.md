---
title: "긴 입력을 처리할 때 필요한 메모리를 답을 만드는 동안 잠시 빌려 쓰고, 다음 긴 입력 전에 돌려주는 방법을 만들었다. 하지만 입력을 나눠 읽으면 메모리를 더 확보하면서도 첫 답이 거의 늦어지지 않았다."
date: 2026-11-20T07:34:44+09:00
draft: false
description: "이 논문은 vLLM의 prefill 활성화 메모리를 decode 중 KV 캐시에 빌려주고 다음 prefill 전에 돌려주는 CUDA VMM 기반 기법을 구현했다. 하지만 긴 prompt를 처리한 실험에서 chunk 8192는 chunk 32768보다 median TTFT가 약 1% 느리면서 KV capacity는 375K 대 314K tokens로 더 컸다. Elastic 방식의 KV capacity는 364K tokens로 chunk 8192보다 작았다."
tags: ["Large Language Model / LLM Serving", "논문 분석", "논문 리뷰", "KV cache", "prefill", "decode"]
categories: ["논문분석"]
---


긴 입력을 처리할 때 필요한 메모리를 답을 만드는 동안 잠시 빌려 쓰고, 다음 긴 입력 전에 돌려주는 방법을 만들었다. 하지만 입력을 나눠 읽으면 메모리를 더 확보하면서도 첫 답이 거의 늦어지지 않았다.

**무엇이 문제였나** — 큰 입력을 처리할 메모리를 미리 비워 두면, 그동안 답을 만드는 데 쓸 수 있는 공간이 줄어든다.
**어떻게 풀었나** — 논문은 답을 만드는 동안 그 공간을 빌려 쓰고, 다음 큰 입력을 읽기 전에 돌려주는 방법을 만들었다.
**그래서 뭐가 좋아졌나** — 실험에서는 입력을 작은 묶음으로 나눠도 첫 답 시간이 거의 늘지 않았고, 이 방법보다 더 많은 메모리를 쓸 수 있었다.

> 큰 주문을 위해 접시를 미리 비워 두는 식당을 떠올려 보자. 주문이 없을 때는 그 접시를 다른 손님에게 빌려줄 수 있지만, 큰 주문 전에 다시 가져와야 한다. 이 연구는 큰 주문을 여러 번에 나눠 준비해도 기다리는 시간이 거의 늘지 않는다면, 접시를 빌려주고 돌려받는 장치가 꼭 필요하지 않을 수 있음을 보여준다.

## 논문 정보

Sathishkumar Sivashanmugam · Amazon Web Services · arXiv:2608.23658v1 [cs.AR] · 2026

## 왜 중요한가

GPU 메모리는 동시에 처리할 요청 수와 입력할 수 있는 문서 길이를 제한한다. 이 연구는 긴 입력용 공간을 복잡하게 빌려 쓰기 전에 입력을 나눠 처리하는 방법이 충분한지 비교해, 메모리와 응답 속도를 함께 고려할 때의 선택지를 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Median TTFT (chunk 8192) | **4.97s** | 긴 prompt 실험에서 chunk 32768은 4.91초, Elastic은 4.90초였다. |
| KV capacity (chunk 8192) | **375K tokens** | 같은 비교에서 chunk 32768은 314K, Elastic은 364K tokens였다. |
| Elastic decommit latency | **3.8ms** | CUDA graphs가 켜진 live controller에서 측정한 reserve 해제 시간. reserve는 3.09 GiB였다. |
| Prefill reserve share (7B TP1) | **16% of KV** | 논문은 7B TP4에서 2.7%, 32B TP4에서 7.7%라고 보고했다. |

## 어떻게 동작하나

논문은 vLLM의 시작 시점 메모리 할당에서 큰 prefill을 위한 활성화 메모리가 고정 예약되고, decode 중에는 사용되지 않아도 KV cache에 쓸 수 없는 문제를 다룬다. 제안 기법은 CUDA VMM으로 layer마다 하나의 연속된 가상 주소 범위를 두 physical handle로 뒷받침한다. 기본 handle은 계속 연결하고, elastic handle은 scheduler가 다음 batch를 확인해 decode-only 구간에 연결하며 prefill 전에 해제한다. top elastic block-id 범위를 연결 상태에 따라 제한하고, phase 경계에서는 drain, sync, hysteresis를 사용한다. attention kernel과 driver patch는 바꾸지 않는다. 28개 layer에서 3.09 GiB reserve를 전환한 측정에서 단순 create_and_map 방식의 commit은 약 180 ms, contiguous-VA 방식은 commit 약 30 ms와 decommit 약 3 ms였다. CUDA graphs가 켜진 live controller에서는 decommit 3.8 ms, recommit 23.8 ms였다. 전체 reserve를 고정적으로 KV에 넣으면 62K-token prefill burst에서 약 2.3 GiB 활성화 메모리가 부족해 OOM이 발생했지만, dynamic 방식은 prefill 전에 4.4 ms로 해제해 같은 burst를 처리했다. 큰 prefill 뒤 torch caching allocator가 메모리를 보유해 recommit이 OOM을 낸 문제는 empty_cache() 호출로 해결했다. 결정 실험은 NVIDIA A100-SXM4-40GB 한 장, Qwen2.5-7B-Instruct float16, vLLM 0.23.0, gpu_memory_utilization=0.9 환경에서 했다. 40개 background decode sequence를 유지하면서 약 25K-token foreground prompt 6개를 1.5초 간격으로 넣고 TTFT를 측정했다. chunk 8192는 median 4.97초, max 6.07초, KV capacity 375K tokens였고, chunk 32768은 각각 4.91초, 5.79초, 314K tokens였다. Elastic은 4.90초, 5.76초, 364K tokens였다. 논문은 반복 횟수, 신뢰구간, p-value를 보고하지 않았다. 논문이 제시한 설명은 prefill이 compute bound이고 decode가 sequence당 step마다 약 한 token을 처리하므로 작은 chunk가 prefill을 크게 굶기지 않는다는 것이다.

핵심 수식:

```
C_{\mathrm{KV}}(m)+R(m)\approx C_{\mathrm{fixed}},\quad C_{\mathrm{KV}}(t)=C_{\mathrm{base}}+R_{\mathrm{elastic}}\mathbf{1}_{\text{decode-only}}
```

논문 본문은 이 관계를 설명하지만 해당 수식을 명시적으로 제시하지 않는다. 따라서 본문 설명을 요약한 기호화다. m은 max_num_batched_tokens, C_KV는 KV capacity, R은 prefill activation reserve, C_fixed는 고정 GPU 메모리 예산을 뜻한다. C_base는 항상 매핑된 영역, R_elastic은 decode-only일 때 추가로 KV에 연결되는 영역, 지시함수는 그 구간에서만 1이다.

## 한계와 주의할 점

- 주요 실험은 NVIDIA A100-SXM4-40GB 한 장, Qwen2.5-7B-Instruct float16, vLLM 0.23.0에 한정되어 다른 GPU, 모델, 소프트웨어 조합으로의 일반화는 확인되지 않았다.
- 결정적 TTFT 비교는 약 25K-token prompt 6개로 이뤄졌으며 반복 횟수와 신뢰구간, p-value가 보고되지 않아 약 1% 차이의 안정성과 통계적 유의성을 판단하기 어렵다.
- 논문의 부정적 결과는 prefill이 compute bound이고 decode가 step마다 sequence당 약 한 token이라는 조건에서 관찰됐다. 작은 chunk가 prefill throughput을 실제로 제한하는 다른 부하에서는 결과가 달라질 수 있다.
- elastic allocator와 scheduler 제어에는 추가 구현 복잡성이 따른다. 논문은 큰 prefill 뒤 torch caching allocator가 freed memory를 보유해 recommit에서 OOM이 난 사례를 보고하고 empty_cache()로 해결했다.
- 논문에서 reserve는 7B TP1의 KV 대비 16%에서 7B TP4의 2.7%로 감소했다. util=0.97 설정도 expandable_segments 없이는 48-prompt prefill burst에서 OOM이 발생했고, 이를 켠 경우에도 여유가 0.04~0.15 GiB였다.
- 전체 reserve를 고정적으로 KV에 넣으면 62K-token prefill burst에 필요한 약 2.3 GiB 활성화 공간이 부족해 OOM이 발생한다. 논문이 제시한 OOM-safe 고정 회수량은 약 1.2 GiB, 6% gain이다.
- 큰 prefill 뒤 torch caching allocator가 메모리를 보유하면 첫 recommit에서 OOM이 발생할 수 있다. 논문에서는 cuMemCreate 전에 empty_cache()를 호출해 해결했다.
- CUDA graphs에서 mapping이나 block-id 상태를 잘못 관리하면 캡처된 실행과 실제 elastic 영역 상태가 맞지 않을 수 있다. 논문은 그래프와 prefix caching을 켠 상태에서 작동 및 bit-identical generation을 확인했지만, 별도 회귀 검증은 실제 배포 구성에서 필요하다.
- gpu_memory_utilization=0.97에서는 expandable_segments 없이 48-prompt prefill burst가 OOM을 일으켰고, 해당 설정을 켜도 여유는 0.04~0.15 GiB였다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### prefill chunk 조정으로 KV capacity 확보

서빙 환경에서 chunk 8192와 32768을 같은 부하로 비교하고 median·max TTFT, KV capacity, OOM을 기록한다. 논문의 decisive test에서는 8192가 median 4.97초, max 6.07초, KV 375K tokens였고 32768은 각각 4.91초, 5.79초, 314K tokens였다. 이 결과가 자체 부하에서도 유지된다면 작은 chunk를 기본 설정 후보로 삼을 수 있다.

**적용 지점** — LLM serving scheduler의 prefill chunk 설정

**기대 효과** — 논문 실험에서 chunk 8192는 median TTFT 4.97초와 KV capacity 375K tokens를 기록했다. chunk 32768의 KV capacity는 314K tokens였다.

### decode 중 reserve를 임시로 KV에 연결

논문은 layer별 contiguous virtual address range에 base와 elastic physical handle을 두고, scheduler의 다음 batch 정보를 이용해 elastic 영역을 map·unmap했다. top block-id 범위를 연결 상태에 따라 제한했다. 3.09 GiB reserve를 live controller에서 해제하는 데 3.8 ms, 다시 연결하는 데 23.8 ms가 걸렸다. 다만 결정 실험에서 elastic KV capacity는 364K tokens로 chunk 8192의 375K보다 낮았으므로 적용 가치는 부하별로 측정해야 한다.

**적용 지점** — GPU KV allocator와 scheduler phase boundary

**기대 효과** — 논문은 3.09 GiB reserve의 live controller 전환 비용으로 decommit 3.8 ms, recommit 23.8 ms를 보고했다.

### recommit 전에 allocator cache 처리

논문은 큰 prefill 뒤 torch caching allocator가 해제된 메모리를 보유해 첫 recommit에서 OOM이 난 사례를 기록했다. cuMemCreate 전에 empty_cache()를 호출해 해결했다. 해당 allocator 경로를 사용하는 구현에서는 같은 순서와 OOM 처리를 부하 테스트에서 검증할 수 있다.

**적용 지점** — GPU KV allocator의 recommit 경로

**기대 효과** — 논문에서 확인한 recommit OOM 원인을 점검하고 empty_cache() 처리로 같은 실패를 막을 수 있는지 검증한다.

### reserve 비율과 tensor parallelism을 적용 판단에 반영

논문은 reserve가 7B TP1에서 KV 대비 16%, 32B TP4에서 7.7%, 7B TP4에서 2.7%라고 보고했다. 이 수치만으로 적용을 결정하기보다는 해당 구성에서 작은 chunk의 TTFT 비용과 KV 부족을 함께 측정해야 한다. 결정 실험에서는 chunk 8192가 elastic보다 더 많은 KV capacity를 제공했다.

**적용 지점** — LLM serving 구성별 allocator 선택

**기대 효과** — tensor parallelism에 따라 달라지는 reserve 비율을 구성 선택에 반영하고, 실제 부하에서 chunk 조정과 elastic 방식의 결과를 비교한다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 작은 prefill chunk가 실제 부하에서도 충분한지 확인 | 논문과 같은 A100, Qwen2.5-7B-Instruct, vLLM 0.23.0 환경에서 chunk 8192와 32768을 비교한다. 약 25K-token prompt와 background decode 부하를 재현하고 반복 측정, 신뢰구간, OOM 여부를 기록한다. | 논문에서 보고한 median TTFT 4.97초 대 4.91초와 KV capacity 375K 대 314K tokens를 기준으로 자체 부하에서 chunk 조정이 충분한지 평가한다. |
| Phase 2 | elastic-VMM 전환을 serving 경로에서 검증 | layer마다 연속 가상 주소 범위와 base·elastic physical handle을 구성하고, elastic 영역을 2 MiB 단위로 매핑·해제한다. scheduler의 다음 batch 예측, block-pool gate, CUDA graphs, prefix caching 조건에서 전환과 prefill burst 처리를 점검한다. recommit 전 allocator cache 처리도 검증한다. | 논문은 3.09 GiB reserve에 대해 live controller에서 decommit 3.8 ms, recommit 23.8 ms를 보고했다. 이 재현 결과와 오류 처리를 확인해 구현 가능성과 실제 성능상 이득을 구분한다. |
| Phase 3 | 같은 요청 부하에서 세 설정을 비교 | chunk 8192, chunk 32768, Elastic(auto)을 같은 요청 trace와 CUDA graphs·prefix caching 조건에서 비교한다. TTFT, KV capacity, prefill·decode 구간, OOM을 측정하고 낮은 TP와 TP4 결과를 구분한다. | chunk 조정만으로 latency와 capacity가 충분히 개선되는지 확인하고, elastic 경로의 이득이 측정된 조건에서만 적용 여부를 판단한다. |

---

원문 PDF: `2026-08-27-elastic-kv-cache-for-llm-serving-a-working-reclamation-mechanism-and-why.pdf`
