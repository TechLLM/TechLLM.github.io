---
title: "Granite Embedding Multilingual R2 — 97M으로 sub-100M SOTA, 32K 컨텍스트"
date: 2026-05-16T20:21:00+09:00
draft: false
description: "IBM이 Apache 2.0으로 공개한 다국어 임베딩 모델 R2. 97M 모델이 MTEB 다국어 검색 60.3으로 sub-100M 1위, 311M 모델은 65.2로 오픈 모델 2위. ModernBERT 기반으로 R1 대비 컨텍스트 64배(32K), 코드 검색 +19.7점."
cover:
  image: /images/granite-embedding-multilingual-r2-cover.png
  alt: "Granite Embedding Multilingual R2 다국어 임베딩 모델"
  caption: "Generated illustration"
tags: ["임베딩모델", "다국어검색", "RAG", "IBM그래나이트", "ModernBERT", "오픈소스LLM", "MTEB"]
categories: ["AI-LLM"]
---

## 개요

IBM이 Granite Embedding Multilingual R2를 Apache 2.0으로 공개했다. 97M과 311M 두 모델이다. 97M 모델은 MTEB 다국어 검색 벤치마크에서 60.3점을 기록해 sub-100M 오픈 다국어 임베딩 모델 중 1위다. 2위인 multilingual-e5-small(50.9점)과 9.4점 차이다. 311M 모델은 65.2점으로 500M 미만 오픈 모델 중 2위다. 둘 다 200개 이상 언어를 지원하고, R1 대비 64배 늘어난 32K 토큰 컨텍스트를 처리한다. 기존 다국어 임베딩 모델은 언어 커버리지를 넓히면 크기가 커지고, 소형 모델은 언어를 줄여야 했다. R2는 이 트레이드오프를 상당 부분 해소했다.

## 핵심 요약

- **97M 모델 sub-100M 1위**: MTEB 다국어 검색 60.3 — multilingual-e5-small 대비 +9.4점
- **32K 컨텍스트**: R1의 512토큰에서 64배 확장. 긴 문서를 잘라내지 않고 통째로 임베딩
- **ModernBERT 기반 재설계**: XLM-RoBERTa에서 완전히 바꿨다. 교차 어텐션, RoPE, Flash Attention 2.0
- **코드 검색 추가**: Python·Go·Java·JavaScript·PHP·Ruby·SQL·C·C++ 9개 언어
- **Matryoshka 지원(311M)**: 768→256차원 축소 시 검색 점수 -0.5점 수준 유지
- **엔터프라이즈 라이선스**: Apache 2.0, MS-MARCO 미사용, IBM 데이터 거버넌스 검수

## R1에서 무엇이 바뀌었나

R1 모델들은 XLM-RoBERTa 인코더 기반이었고 컨텍스트 창이 512토큰이었다. R2는 전면 재설계다.

**ModernBERT로 아키텍처 교체**: 최근 5년간 트랜스포머 연구 기법을 BERT 구조에 접목한 인코더다. 교번 어텐션(alternating attention)으로 긴 시퀀스 처리 효율을 높이고, 회전 위치 임베딩(RoPE)으로 위치 보간 없이 32K 컨텍스트를 지원한다. Flash Attention 2.0으로 GPU 인코딩 속도도 개선됐다. XLM-RoBERTa 기반 R1과 비교하면 동일한 파라미터 수에서 훨씬 많은 컨텍스트를 처리하면서 속도도 빠르다.

**토크나이저 교체**: XLM-RoBERTa의 25만 어휘 대신 다국어·코드 커버리지가 강한 토크나이저를 채택했다. 311M 모델은 Gemma 3 토크나이저(26만 2천 어휘), 97M 모델은 GPT-OSS 토크나이저를 18만 어휘로 가지치기한 버전을 쓴다. 토크나이저 효율은 실질적인 문제다. 32K 컨텍스트라도 태국어 한 문단에 토큰 절반을 쓰는 토크나이저라면 의미가 없다.

## 훈련 방법

**311M 모델**: 4단계 파이프라인이다. 지식 증류(Granite 3.3 Instruct + Mistral v0.2 교사 모델) → 다국어 대조 파인튜닝(52개 언어 및 코드) → 체크포인트 모델 병합 → Matryoshka 표현 학습. 모델 병합 단계에서 다국어 폭과 영어 깊이를 각각 최적화한 체크포인트를 추가 학습 없이 합쳐 강점을 동시에 잡는다.

**97M 모델**: 어휘 축소와 지식 증류를 결합했다. 26만 2천 어휘를 18만으로 줄여 임베딩 테이블 파라미터를 절약하고, Granite 4.1 8B와 Mistral Instruct 디코더 기반 교사 모델로 지식 증류를 진행했다. 결과적으로 311M 대비 3배 작으면서 검색 점수는 97% 이상 유지한다. 단순히 큰 모델을 압축한 것이 아니라, 축소된 어휘 공간에서 다국어 커버리지를 보존하면서 교사 모델의 검색 능력을 효율적으로 전이한 구조다.

## 벤치마크 주요 결과

97M 모델의 두드러진 점은 크기 대비 성능이다. MTEB 다국어 검색에서 300M급 모델인 multilingual-e5-base(52.7점)와 gte-multilingual-base(57.2점)를 모두 뛰어넘는다. 많은 프레임워크의 기본값으로 쓰이는 paraphrase-multilingual-MiniLM-L12-v2(36.6점)와는 23.7점 차이다.

R1 대비 가장 큰 향상은 LongEmbed다. 97M 모델은 +31.3점, 311M 모델은 +34.0점을 올렸다. 32K 컨텍스트의 직접적인 효과다. R1의 512토큰 제한은 법률 계약서를 첫 페이지만 보고 판단하는 것과 같았다. 코드 검색도 크게 올랐다. 97M +19.7점, 311M +15.3점이다.

추론 속도도 실용적이다. 97M 모델은 H100 GPU에서 초당 2,500건 이상 인코딩한다. multilingual-e5-small과 비슷한 처리량이면서 검색 점수는 훨씬 높다. 311M 모델은 초당 1,800건으로 jina-embeddings-v5-text-nano보다 5.5배 빠르면서 검색 점수는 더 높다(65.2 vs 63.3). 두 모델 모두 ONNX와 OpenVINO 가중치를 제공해 GPU 없는 CPU 환경에서도 최적화된 추론이 가능하다.

## Matryoshka 임베딩(311M)

311M 모델은 Matryoshka 학습을 적용해 768차원 임베딩을 512, 384, 256, 128차원으로 잘라 쓸 수 있다. 768→256차원으로 줄이면 저장 공간이 3분의 1로 줄지만 MTEB 다국어 검색 점수 손실은 0.5점(65.2→64.7)에 불과하다. 128차원에서도 63.7점으로 풀 차원 성능의 97%를 유지한다. 실질적으로 인덱스 크기와 검색 지연 시간을 줄이면서 품질 손실을 최소화할 수 있다.

참고로 311M 모델을 384차원으로 잘라 쓰면(Matryoshka 축소) 97M 모델의 기본 출력 차원과 같아지는데, 이 경우에도 311M이 97M보다 모든 벤치마크에서 높은 점수를 낸다. 인코딩 비용을 감당할 수 있다면 311M을 384차원으로 쓰는 것이 더 나은 선택이다.

## 실무자가 볼 핵심 포인트

1. **97M 모델이 300M급 경쟁자를 이긴다** — multilingual-e5-base, gte-multilingual-base를 파라미터 3배 차이로 앞선다. RAG 파이프라인에서 임베딩 모델을 고를 때 크기와 성능 트레이드오프를 다시 계산할 필요가 있다
2. **32K 컨텍스트가 LongEmbed를 결정적으로 바꿨다** — 긴 법률 문서, 기술 매뉴얼, 연구 논문을 청킹 없이 임베딩하는 워크플로우에서 R1과 체감 차이가 크다
3. **드롭인 교체로 200개 언어 지원** — LangChain, LlamaIndex, Haystack, Milvus에서 모델명 한 줄만 바꾸면 된다. 영어 전용 기본값을 쓰는 프레임워크 사용자에게 추가 코드 변경 없이 다국어 지원을 제공한다
4. **Matryoshka로 스토리지-품질 균형을 조정** — 256차원으로도 64.7점. 벡터 DB 비용이 민감한 환경에서 차원 축소가 현실적인 선택이 된다
5. **엔터프라이즈 라이선스 검수** — Apache 2.0, MS-MARCO 미사용, IBM 거버넌스 프로세스. 상업적 배포에서 라이선스 리스크를 줄이려는 팀에게 명확한 이점이다

## 원문 출처

*원문: [Granite Embedding Multilingual R2: Open Apache 2.0 Multilingual Embeddings with 32K Context — HuggingFace Blog, IBM Granite (2026. 5. 14)](https://huggingface.co/blog/ibm-granite/granite-embedding-multilingual-r2)*
