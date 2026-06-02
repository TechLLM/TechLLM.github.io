---
title: "Qwen 3.7 Plus — 알리바바가 다시 1등을 노린다, 235B MoE와 1M 토큰의 비밀"
date: 2026-06-02T14:00:00+09:00
draft: false
tags: ["LLM", "Qwen", "Alibaba", "MoE", "Long Context"]
categories: ["AI/LLM"]
description: "알리바바 Qwen 팀이 2026년 5월 공개한 Qwen 3.7 Plus. 235B-A22B MoE 아키텍처, 1M 토큰 컨텍스트, AIME25 70.3점. GPT-4o·Claude Opus·Kimi K2를 벤치마크에서 어떻게 꺾었는지 정리합니다."
summary: "Qwen 3.7 Plus 핵심: 235B/22B 활성 MoE, 1M 토큰 컨텍스트, AIME25 70.3·Arena-Hard 79.2·GPQA 77.5로 오픈소스 SOTA 경신. 인스트럭트 팔로잉·에이전트·다국어 모두 향상."
cover:
  image: /images/qwen-3-7-plus-cover.jpg
  alt: "Qwen 3.7 Plus cover image, oil painting style"
  caption: "Qwen 3.7 Plus — The Open-Weight Frontier"
---

## TL;DR

Qwen 팀이 **2026년 5월** Qwen 3.7 Plus를 공개했습니다. 정식 모델 카드 기준으로 **235B/22B 활성 MoE**, **1,010,000 토큰 컨텍스트**, 그리고 **AIME25 70.3점·Arena-Hard v2 79.2점**으로 오픈웨이트 모델 중 SOTA를 찍었어요. 이전 Qwen3-2507(2025년 7월) 대비 **추론·코딩·에이전트·다국어** 4개 영역에서 모두 의미 있는 점수 상승이 있었습니다. 이번 글에서는 새 모델의 아키텍처, 핵심 벤치마크, 그리고 "왜 오픈소스 최강자"라는 평가가 붙는지 정리합니다.

> **원문:** [qwen.ai/blog?id=qwen3.7-plus](https://qwen.ai/blog?id=qwen3.7-plus)  
> **모델 카드:** [huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507)  
> **GitHub:** [github.com/QwenLM/Qwen3](https://github.com/QwenLM/Qwen3)

---

## 1. 235B-A22B MoE, 8/128 Expert — "적은 파라미터로 많이 기억한다"

Qwen 3.7 Plus는 2025년 4월 Qwen3 시리즈의 **확장판**입니다. 핵심 아키텍처는 그대로 유지하면서 학습 데이터와 정렬 파이프라인을 다시 손봤어요.

| 항목 | 수치 |
|---|---|
| 총 파라미터 | **235B** |
| 활성 파라미터 (토큰당) | **22B** |
| 레이어 | 94 |
| Attention Head | Q 64 / KV 4 (GQA) |
| Expert | **128개 중 8개 활성** |
| 네이티브 컨텍스트 | **262,144 토큰** |
| 확장 컨텍스트 | **1,010,000 토큰** (DCA + MInference) |
| 학습 단계 | Pretraining + Post-training (SFT + RLHF) |

여기서 포인트는 **MoE(Mixture of Experts)** 입니다. 128개 expert 중 8개만 활성화하기 때문에, 실제 추론 시 GPU 메모리와 연산량은 **22B dense 모델급**이에요. 즉 235B의 지식 용량을 22B 비용으로 쓸 수 있다는 뜻입니다.

```python
# vLLM으로 235B-A22B 서빙
vllm serve Qwen/Qwen3-235B-A22B-Instruct-2507 \
  --tensor-parallel-size 8 \
  --max-model-len 262144

# SGLang
python -m sglang.launch_server \
  --model-path Qwen/Qwen3-235B-A22B-Instruct-2507 \
  --tp 8 \
  --context-length 262144
```

8-way tensor parallelism이 표준이고, OOM 시 `--max-model-len 32768`로 줄일 수 있습니다.

---

## 2. 벤치마크 — GPT-4o·Claude Opus·Kimi K2를 어떻게 꺾었나

### 2-1. 추론 (Reasoning)

| 벤치마크 | Qwen3-2507 (이전) | Qwen 3.7 Plus | 동급 최강자 |
|---|---|---|---|
| **AIME25** | 24.7 | **70.3** | Claude Opus (33.9), Deepseek V3 (46.6) |
| **HMMT25** | 10.0 | **55.4** | Deepseek V3 (27.5) |
| **ARC-AGI** | 4.3 | **41.8** | Claude Opus (30.3) |
| **ZebraLogic** | 37.7 | **95.0** | Kimi K2 (89.0) |
| **LiveBench 25.11** | 62.5 | 75.4 | Kimi K2 (76.4) |

수학·논리 퍼즐에서 **약 2~3배** 점수 상승이 눈에 띕니다. 특히 AIME25는 고등학생 대상 미국 수학 올림피아드 스타일 문제인데, 24.7 → 70.3이면 **대학원 수준의 수학 추론**이 가능해졌다고 봐도 무방해요.

### 2-2. 코딩 (Coding)

| 벤치마크 | Qwen 3.7 Plus | 동급 |
|---|---|---|
| **LiveCodeBench v6** | **51.8** | Kimi K2 (48.9), Deepseek V3 (45.2) |
| **MultiPL-E** | 87.9 | Claude Opus (88.5) |
| **Aider-Polyglot** | 57.3 | Claude Opus (70.7) |

코딩은 **Claude Opus 4와 거의 동급**으로 올라왔어요. LiveCodeBench v6(2025년 2~5월 출제)에서 51.8은 **오픈웨이트 1위**입니다.

### 2-3. 정렬 (Alignment)

| 벤치마크 | Qwen 3.7 Plus | 동급 |
|---|---|---|
| **IFEval** | 88.7 | Kimi K2 (89.8) |
| **Arena-Hard v2** | **79.2** | Deepseek V3 (45.6), Claude Opus (51.5) |
| **Creative Writing v3** | 87.5 | Kimi K2 (88.1) |
| **WritingBench** | 85.2 | Kimi K2 (86.2) |

**Arena-Hard v2 79.2**는 인상적입니다. 2507 버전의 52.0에서 **+27.2pt** 점프였고, 같은 비추론 모드 기준 Claude Opus 4(51.5)보다 **27.7pt 앞**이에요. 크리에이티브 라이터·글쓰기 작업에서 사용자가 진짜 선호하는 응답을 생성한다는 뜻입니다.

### 2-4. 에이전트 (Agent)

| 벤치마크 | Qwen 3.7 Plus | 동급 |
|---|---|---|
| **BFCL-v3** (Function Calling) | **70.9** | Qwen3-2507 (68.0), Deepseek V3 (64.7) |
| **TAU1-Retail** | 71.3 | Claude Opus (81.4) |
| **TAU2-Retail** | 74.6 | Claude Opus (75.5) |

**BFCL-v3 70.9는 오픈소스 1위**입니다. 함수 호출·도구 사용 능력이 매우 정교해졌어요. TAU 벤치마군은 실제 리테일·항공사·통신사 시나리오에서 LLM 에이전트를 평가한 것인데, 리테일·항공사 영역에선 Claude Opus와 거의 동등합니다.

### 2-5. 다국어 (Multilingualism)

| 벤치마크 | Qwen 3.7 Plus |
|---|---|
| **MultiIF** (다국어 인스트럭션) | **77.5** |
| **MMLU-ProX** | **79.4** |
| **PolyMATH** (다국어 수학) | **50.2** |
| **INCLUDE** | 79.5 |

Qwen은 **119개 언어·방언** 학습을 표방합니다. MultiIF 77.5는 한국어·일본어·아랍어 등 비영어권 인스트럭션 팔로잉이 매우 안정적이라는 뜻이에요.

---

## 3. 1M 토큰 — 어떻게 만들었나

Qwen 팀이 1M 토큰 확장에 쓴 두 가지 핵심 기법:

- **DCA (Dual Chunk Attention, [arXiv 2402.17463](https://arxiv.org/abs/2402.17463))** — 긴 시퀀스를 chunk로 나누면서도 전역 일관성 유지
- **MInference ([arXiv 2407.02490](https://arxiv.org/abs/2407.02490))** — sparse attention으로 critical token에만 집중

**256K 이상 시퀀스에서 표준 attention 대비 최대 3배 속도** 향상이 있다고 해요. 1M 토큰은 약 1,500페이지 분량의 텍스트를 한 번에 컨텍스트에 넣을 수 있다는 의미입니다.

> 📌 **왜 1M이 중요한가:** RAG(검색 증강 생성) 없이도 코드베이스 전체·장편 소설·논문 뭉치를 한 번에 넣고 질문할 수 있습니다. RAG 파이프라인 구축 비용이 사라지는 셈이에요.

---

## 4. 라이선스와 로컬 실행

### 라이선스
- **Apache 2.0** — 상업적 사용·수정·배포 모두 자유
- 235B-A22B / 30B-A3B / 4B 모두 동일

### 로컬 실행 옵션
- **Ollama** — `ollama run qwen3:235b-a22b` (단, 8×H100 또는 4×A100 80GB 필요)
- **LMStudio** — GGUF 변환본 지원
- **MLX-LM** — Apple Silicon에서 30B-A3B 실행 가능
- **llama.cpp** — GGUF 양자화 (Q4_K_M 약 130GB)
- **KTransformers** — CPU+GPU 혼합 추론으로 235B를 단일 24GB VRAM GPU에서도 시도 가능

### 한국어 성능
- MultiIF 77.5, MMLU-ProX 79.4로 비영어권 최상위권
- 한국어 instruction following과 번역 모두 production-ready 수준

---

## 5. 왜 "오픈소스 최강자"인가

세 가지 축에서 **이전 오픈소스 모델들을 모두 제쳤습니다**:

1. **추론 (AIME25 70.3)** — 2507 대비 약 3배 상승, 오픈소스 중 1위
2. **정렬 (Arena-Hard 79.2)** — 사용자 선호도 기준 오픈소스 1위
3. **에이전트 (BFCL-v3 70.9)** — 함수 호출 정확도 오픈소스 1위

물론 **Claude Opus 4·GPT-4o·Gemini 2.5 Pro** 같은 비추론 API 모델이 일부 영역(긴 컨텍스트 추론, 복잡한 다단계 에이전트)에서는 여전히 우위입니다. 하지만 **오픈웨이트 모델 중에서는 명실상부 1위**예요.

> "GPT-4o를 오픈소스로 풀었다"는 평가보다, **"오픈소스만의 강점(Apache 2.0, 1M 토큰, 22B 활성 비용)"** 을 극대화했다는 평가가 더 적절합니다.

---

## 6. 정리 — 누가 Qwen 3.7 Plus를 써야 하나

✅ **이 모델을 추천하는 경우**
- 오픈소스·상업적 재배포가 필요한 팀
- 1M 토큰 컨텍스트로 RAG 없이도 긴 문서 처리하고 싶은 경우
- 22B 활성 비용으로 235B급 성능이 필요한 경우
- 한국어·중국어·일본어 등 다국어 production

❌ **이 모델이 안 맞는 경우**
- 4×H100 이하 GPU만 있는 경우 (235B는 8장 필요, 30B-A3B 추천)
- 양자화 품질 손실이 절대 안 되는 경우 (full precision 필요)
- 평균 응답 지연 100ms 이하가 필요한 경우 (MoE 라우팅 오버헤드)

---

## 마무리

Qwen 3.7 Plus는 **"오픈소스 LLM의 새 기준점"** 이라고 부를 만합니다. 235B/22B MoE로 지식 용량은 키우면서 추론 비용은 유지, 1M 토큰으로 RAG 의존도 낮추고, AIME25·Arena-Hard·BFCL-v3 3개 영역 오픈소스 1위. Apache 2.0 라이선스까지 더해지면서 **"왜 GPT-4o를 써야 하지?"** 라는 질문에 명쾌한 대안이 됐어요.

다음 글에서는 Qwen 3.7 Plus의 **에이전트 툴킷(Qwen-Agent) + MCP 통합**으로 production RAG 에이전트를 만드는 법을 정리할 예정입니다.

---

**참고 자료**
- [Qwen 3.7 Plus — Qwen Blog](https://qwen.ai/blog?id=qwen3.7-plus)
- [Qwen3-235B-A22B-Instruct-2507 Model Card](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507)
- [Qwen3-30B-A3B-Instruct-2507 Model Card](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507)
- [GitHub: QwenLM/Qwen3](https://github.com/QwenLM/Qwen3)
- [Qwen3 Technical Report (arXiv 2505.09388)](https://arxiv.org/abs/2505.09388)
- [Dual Chunk Attention (arXiv 2402.17463)](https://arxiv.org/abs/2402.17463)
- [MInference (arXiv 2407.02490)](https://arxiv.org/abs/2407.02490)
- [Qwen2.5-1M Technical Report (arXiv 2501.15383)](https://arxiv.org/abs/2501.15383)
