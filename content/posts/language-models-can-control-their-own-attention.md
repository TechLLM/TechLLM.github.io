---
title: "언어 모델이 답을 쓰는 도중에 '전체를 볼지, 특정 부분만 볼지, 방금 쓴 내용만 볼지'를 직접 표시하게 해서 긴 문서를 더 싸게 읽게 만드는 방법이다."
date: 2026-09-30T07:32:37+09:00
draft: false
description: "저자들이 제안한 Declarative Attention(DA)은 모델이 chain-of-thought 안에 <global>, <focus>, <local> 태그를 넣어 어텐션할 영역을 직접 선언하게 하는 zero-shot 프로토콜이다. vLLM에 통합된 DA state machine이 태그를 파싱해 block-aligned KV cache mask를 동적으로 적용하고, 오프더셸프 모델 6종·15개 long-context 태스크에서 attention token을 31.1~52.0% 줄이되 정확도 손실은 1.27~2.75pp에 그친다."
tags: ["Large Language Model", "논문 분석", "논문 리뷰", "KV cache", "Declarative Attention", "Chain-of-thought"]
categories: ["논문분석"]
---


언어 모델이 답을 쓰는 도중에 '전체를 볼지, 특정 부분만 볼지, 방금 쓴 내용만 볼지'를 직접 표시하게 해서 긴 문서를 더 싸게 읽게 만드는 방법이다.

**무엇이 문제였나** — 긴 문서를 다루는 모델은 답의 한 단어를 만들 때마다 앞의 긴 입력을 거의 다시 훑어야 해서 시간이 많이 든다.
**어떻게 풀었나** — 이 논문은 모델이 답을 쓰는 중에 <global>, <focus>, <local> 같은 표시를 남기게 하고, 실행 시스템이 그 표시에 맞춰 필요한 부분만 읽게 한다.
**그래서 뭐가 좋아졌나** — 큰 모델 두 종류에서 15개 긴 문서 과제를 평가했더니 읽어야 하는 양은 31.1~52.0% 줄었고, 정답률 하락은 1.27~2.75%p였다.

> 두꺼운 책에서 답을 찾을 때 매번 처음부터 끝까지 다시 읽지 않고, 먼저 목차를 보고, 필요한 장만 펼친 뒤, 마지막 계산은 메모장만 보고 하는 것과 비슷하다. DA는 모델이 이런 선택을 글로 직접 표시하게 만든다.

## 논문 정보

Namgyu Ho, Huzama Ahmad, Woosung Koh, Se-Young Yun et al. · KAIST AI, Google DeepMind · arXiv preprint (arXiv:2609.02737) · 2026

## 왜 중요한가

긴 대화, 긴 문서, 큰 코드 저장소를 처리할 때 모델 서빙 비용의 큰 부분은 이전 내용을 다시 읽는 데서 나온다. DA는 모델을 새로 학습하지 않고도 이 읽기 비용을 줄이는 방법을 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| Attended tokens 감소율 (Gemma-4-31B) | **52.0%** | DA vs Vanilla, 15개 long-context 태스크 평균 |
| Attended tokens 감소율 (Qwen-3.6-27B) | **31.1%** | DA vs Vanilla, 15개 long-context 태스크 평균 |
| 정확도 손실 (Gemma-4-31B) | **1.27pp** | 87.01% → 85.74%, 15개 태스크 평균 |
| Roofline wall-clock 비율 (Gemma-4-31B) | **0.71×** | DA vs Vanilla, B200/MFU 40%/MBU 70% 가정 |

## 어떻게 동작하나

DA는 chain-of-thought에 <global>, <focus>, <local> 세 어텐션 모드를 태그로 삽입하도록 모델을 유도한다. <global>은 전체 컨텍스트를 훑어 위치를 잡는 단계, <focus>는 명시한 청크(약 2K 토큰)에만 어텐드해 핵심 정보를 추출하는 단계, <local>은 모델 자신의 이전 출력에만 어텐드해 자체 추론을 하는 단계다. vLLM 위에서 DA state machine이 매 디코드 스텝의 태그 전이를 파싱하고, block-aligned KV cache mask를 block table 재작성을 통해 적용한다. 이 mask는 global attention layer의 KV read만 줄이고 FlashAttention 같은 기존 커널은 그대로 활용하므로 커널 수정이 불필요하다. 6개 모델(Gemma-4-{E4B,12B,31B}, Qwen-3.5-{4B,9B}, Qwen-3.6-27B)과 RULER·LongBench v1/v2·LooGLE·ZeroSCROLLS에서 가져온 15개 long-context 태스크에 대해 추가 학습 없이 zero-shot으로 평가되었다. Roofline 분석으로 wall-clock까지 추정해, DA의 절감이 실제 latency 개선으로 이어질 수 있음을 보였다.

핵심 수식:

```
T_attn = KV bytes / (Peak BW × MBU); T_FFN = FLOPs / (Peak FLOPS × MFU)
```

T_attn은 어텐션의 메모리 바운드 비용(KV cache 읽기), T_FFN은 feed-forward·projection GEMM의 컴퓨트 바운드 비용이다. DA는 KV cache read를 줄여 T_attn을 감소시키지만, 추가 디코드 스텝 때문에 T_FFN은 증가할 수 있다.

## 한계와 주의할 점

- zero-shot 프로토콜이 vanilla 대비 31~35% 더 많은 디코드 스텝을 생성해, mask로 줄인 per-step 비용의 일부를 상쇄한다
- Qwen-3.6-27B의 qmsum·LBv2/multidoc_qa·LBv2/singledoc_qa 등 5개 소스에서는 DA의 어텐드 토큰이 vanilla를 오히려 초과한다 (생성 길이 증가 때문)
- 모델이 thinking trace 내부에서는 DA 태그를 안정적으로 발행하지 못해, 본 논문의 모든 결과는 non-thinking 모드에서만 얻어졌다
- 가장 긴 컨텍스트(128K 초과)에서는 <global> 모드 점유율이 45%까지 올라 절감 효과가 제한되며, 가장 작은 모델(Gemma-4-E4B)은 focus success rate 58%에 그쳐 정확도가 vanilla의 29% 수준으로 급락한다
- DA는 global attention layer에만 적용되고, SWA·GDN 같은 efficient layer의 고정 per-step read는 건드리지 못해(Gemma의 경우 DA attention time의 42%) 절감 폭이 모델 구조에 따라 제한된다
- 모델이 <focus> 태그를 파싱 가능한 형태로 발행하지 못해, 특히 4B~12B 소형 모델에서 집중 발생 (Gemma-4-E4B의 focus success rate 58%)
- 8K 생성 예산 안에 답을 마치지 못하는 응답이 Gemma-4-12B에서 약 6%, Qwen-3.5-4B에서도 일정 비율 발생해 평균 attended token을 부풀린다
- 128K를 넘는 컨텍스트에서 정확도가 vanilla의 약 96% 수준으로 떨어지며, 이는 mask의 정보 손실에 기인한다 (maskless ablation인 DAnm에서는 이 하락이 없다)
- <global> 모드 점유율이 45%까지 올라가면 단일 모드의 장점이 희석되어, 절대 절감량이 컨텍스트 길이에 비례해 계속 커지지는 못한다

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### RAG 재순위 단계에 DA focus 모드 도입

RAG 파이프라인에서 검색된 K개 문서 청크를 약 2K 토큰 단위로 분할하고, 답변 생성 모델이 DA의 <focus magic_chunks="N"> 태그를 통해 특정 청크에 명시적으로 어텐드하도록 한다. 논문 Section 2의 chunked tool-use 프롬프트 구조를 그대로 활용하면 별도 학습 없이 기존 모델에 적용 가능하며, K=50 이상인 대규모 검색에서 효과가 크다. 논문 Table 2의 LBv2/multidoc_qa 결과(Gemma-4-31B: 22.10M → 13.30M, 약 40% 감소)와 LBv2/singledoc_qa(20.27M → 9.34M, 약 54% 감소)에서 같은 메커니즘의 절감 효과가 보고되었다. 이 아이디어는 RAG 시스템의 재순위 단계에서 chunk별 KV cache를 미리 block table에 매핑해두고, 모델이 선언한 chunk의 block만 read하도록 attention metadata를 동적으로 구성하는 형태로 구현한다.

**적용 지점** — RAG 재순위 단계의 다중 청크 어텐션

**기대 효과** — Gemma-4-31B 기준 multidoc_qa에서 attended tokens 약 40% 감소 (22.10M → 13.30M), singledoc_qa 약 54% 감소

### 장기 컨텍스트 디코더의 KV cache 읽기 스킵 통합

vLLM의 attention metadata builder hook을 통해 매 디코드 스텝에서 모델 출력의 <focus>/<local> 태그를 파싱하고, 논문 Section 2.3이 기술한 block-aligned KV cache masking을 block table 재작성으로 적용한다. FlashAttention 커널은 변경하지 않으면서도 roofline 추정 wall-clock time을 0.71× (Gemma-4-31B) / 0.77× (Qwen-3.6-27B) 수준으로 낮출 수 있다. B200/H100 기반 high-throughput 서빙에서 특히 효과적이며, longest bin에서는 absolute token saving이 약 21M까지 증가하는 특성을 활용해 long-tail latency를 낮출 수 있다. 도입 시 모델 capability 임계 검증과 throughput 회귀 모니터링을 병행한다.

**적용 지점** — 장기 컨텍스트 LLM의 디코드 단계 KV cache 메모리 접근

**기대 효과** — Roofline wall-clock 0.71× (Gemma-4-31B), 0.77× (Qwen-3.6-27B), 컨텍스트가 길어질수록 절대 절감 폭 증가

### 에이전트 도구 호출 간 어텐션 격리

에이전틱 시스템에서 도구 호출이 누적되면 컨텍스트가 급격히 길어지는데, 논문 Section 8.1이 지적한 것처럼 retrieval이 '무엇을 컨텍스트에 넣을지'를 정한다면 DA는 '들어온 것 중 무엇을 볼지'를 정해 서로 다른 문제를 푼다. 에이전트 하네스에서 각 도구 호출 결과를 논문의 magic chunk처럼 인덱싱하고, 모델이 현재 처리 중인 도구 결과에 <focus>를 선언하도록 유도한다. 이는 컨텍스트가 자동으로 누적되는 multi-turn 워크플로우에서 KV cache read 폭증을 막는 시스템 차원의 장치 역할을 하며, Section 8.2가 제시한 'agentic 컨텍스트는 이미 자연스러운 segment를 가진다'는 전망을 직접 활용한다.

**적용 지점** — 에이전트 하네스의 도구 호출 결과 처리 단계

**기대 효과** — 에이전틱 워크플로우에서 누적 도구 결과로 인한 KV cache read 증가를 per-step 어텐드 비율로 직접 제한

### 자기검증 단계의 로컬 어텐션 전환

에이전트가 답변을 낸 뒤 self-check 루프를 돌릴 때, 논문의 <local> 모드를 적용해 모델이 지금까지 생성한 토큰에만 어텐드하도록 한다. Figure 5b는 <local> 모드가 문맥 길이에 따라 약 90~99%의 per-token attention을 절약한다고 보고한다. 이 점을 활용하면 self-verification 단계의 비용을 크게 줄이면서 검증 정확도는 유지할 가능성이 있다. 도입 시 검증 단계 직전에 mode를 <local>로 강제 전환하는 하네스 수준의 컨트롤(예: 시스템이 검증 프롬프트 앞에 <local> 태그를 prefix로 주입)이 필요하다. 이 아이디어는 task_completion 레인의 중간 검토 비용을 낮추는 표준 패턴이 될 수 있다.

**적용 지점** — 에이전트 자기검증·재검토 단계의 어텐션 스코프

**기대 효과** — <local> 모드 per-token attention 약 90~99% 절감, 긴 컨텍스트에서 효과가 더 커짐

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 오프더셸프 모델에 zero-shot DA 통합 | vLLM의 attention metadata builder에 DA state machine hook을 추가하고, paper의 chunked tool-use 프롬프트 템플릿을 서빙 시스템의 시스템 프롬프트 슬롯에 주입한다. 배포 전 자체 평가 세트로 focus success rate와 accuracy delta를 모니터링한다. | 모델 재학습 없이 long-context 응답의 어텐드 토큰을 31.1~52.0% 절감하고, roofline 기준 wall-clock을 0.71~0.77×로 낮출 잠재력을 확보 |
| Phase 2 | DA 전략 최적화를 위한 post-training | <focus>/<local> 사용 비율과 decode step 수를 보상 신호에 넣어 SFT·RL 파이프라인을 구성한다. attention cost와 accuracy를 공동 최적화하는 보상 함수를 설계하고, chunk boundary tracking 정확도를 fine-tune으로 끌어올린다. | 현재 약 31~35% 더 많은 디코드 스텝을 생성하는 zero-shot 한계를 줄여, throughput regression 없이 절감 효과를 안정화 |
| Phase 3 | KV cache offloading·sparse attention과의 시스템 통합 | DA의 span 단위 어텐션 전이를 이용해 out-of-focus 청크의 KV cache를 host memory로 spill하고, 선언된 시점에 prefetch하도록 scheduler를 확장한다. 동시에 global mode 구간에 한해 lightweight scan sparse attention을 적용해 하이브리드화한다. | 단일 GPU 메모리 한계를 넘어 1M 토큰급 컨텍스트를 호스트 메모리까지 활용하면서, reversible context compaction과 agentic 워크플로우의 비용 구조를 개선 |

---

원문 PDF: `2026-09-04-language-models-can-control-their-own-attention.pdf`
