---
title: "NVIDIA Nemotron 3 Nano Omni: 문서·오디오·비디오를 한 번에 처리하는 멀티모달 AI"
date: 2026-05-07T20:17:00+09:00
draft: false
description: "NVIDIA가 공개한 Nemotron 3 Nano Omni는 30B 파라미터(활성 3B) 구조로 문서 분석, 음성 인식, 영상 이해, GUI 에이전트까지 단일 모델로 처리한다. 동급 오픈 모델 대비 처리량 9배, 주요 벤치마크에서 Qwen3-Omni 30B를 전 영역에서 앞선다."
cover:
  image: "/images/nemotron-omni-throughput.png"
  alt: "Nemotron 3 Nano Omni vs 경쟁 모델 처리량 비교"
  caption: "멀티문서·비디오 유스케이스에서 동급 오픈 모델 대비 7.4~9.2배 높은 시스템 처리량"
tags:
  - NVIDIA
  - Nemotron
  - 멀티모달
  - LLM
  - 오픈웨이트
  - MoE
  - 문서AI
  - 음성인식
categories:
  - AI 인프라
  - LLM 소식
summary: "NVIDIA Nemotron 3 Nano Omni는 Mamba-Transformer-MoE 백본에 비전·오디오 인코더를 결합한 30B-A3B 옴니모달 모델이다. 문서, 음성, 영상, GUI 에이전트 4개 영역에서 Qwen3-Omni 30B를 앞서며, 동급 대비 최대 9.2배 처리량을 제공한다."
---

## 핵심 요약

NVIDIA가 2026년 4월 28일 **Nemotron 3 Nano Omni 30B-A3B**를 공개했습니다. 기존 Nemotron Nano V2 VL(비전-언어 모델)을 확장해 텍스트·이미지·비디오·오디오를 단일 모델에서 처리하는 완전한 옴니모달 시스템으로 진화했습니다.

핵심 숫자:
- **30B 파라미터, 활성 3B** (Mixture-of-Experts 구조)
- 동급 오픈 옴니 모델 대비 멀티문서 **7.4배**, 비디오 **9.2배** 높은 시스템 처리량
- MMLongBench-Doc **57.5** (Qwen3-Omni 30B 49.5 대비 +8p)
- VoiceBench **89.4**, HF Open ASR WER **5.95**

---

## 5가지 핵심 활용 영역

### 1. 장문 문서 분석

100페이지 이상의 계약서, 기술 논문, 재무 보고서, 규제 문서를 단일 컨텍스트에서 처리합니다. 레이아웃, 표, 수식, 페이지 간 상호참조까지 이해하는 OCR 수준을 넘은 **문서 이해**가 목표입니다.

### 2. 음성 인식 (ASR)

Parakeet-TDT-0.6B-v2 오디오 인코더를 내장해 다양한 화자, 억양, 배경 소음 조건에서 장문 오디오를 전사합니다. 단순 텍스트 변환이 아니라 오디오 토큰을 비전·텍스트 토큰과 함께 처리해 멀티모달 추론에 바로 연결됩니다.

### 3. 장시간 오디오-비디오 이해

회의 녹화, 교육 영상, 화면 녹화, 제품 데모 등 음성과 영상이 섞인 복합 콘텐츠를 함께 이해합니다. 오디오 조건에서 LLM 최대 컨텍스트는 **5시간 이상**을 지원합니다.

### 4. GUI 에이전트 (Agentic Computer Use)

스크린샷을 해석하고 UI 상태를 추적해 작업 흐름 자동화를 지원합니다. OSWorld 벤치마크에서 **47.4%**로 Qwen3-Omni(29.0%)를 크게 앞섭니다.

### 5. 범용 멀티모달 추론

텍스트, 이미지, 표, 오디오를 조합한 복합 추론, 다단계 계산, 구조화/반구조화 데이터 분석을 지원합니다.

---

## 벤치마크 비교

| 태스크 | 벤치마크 | Nemotron 3 Nano Omni | Nemotron V2 VL | Qwen3-Omni 30B |
|--------|----------|----------------------|----------------|----------------|
| 문서 이해 | OCRBenchV2-En | **65.8** | 61.2 | — |
| 문서 이해 | MMLongBench-Doc | **57.5** | 38.0 | 49.5 |
| 차트 추론 | CharXiv | **63.6** | 41.3 | 61.1 |
| GUI | ScreenSpot-Pro | 57.8 | 5.5 | **59.7** |
| GUI | OSWorld | **47.4** | 11.0 | 29.0 |
| 비디오 이해 | Video-MME | **72.2** | 63.0 | 70.5 |
| 비디오+오디오 | WorldSense | **55.4** | — | 54.0 |
| 비디오+오디오 | DailyOmni | **74.1** | — | 73.6 |
| 음성 | VoiceBench | **89.4** | — | 88.8 |
| ASR (낮을수록 좋음) | HF Open ASR WER | **5.95** | — | 6.55 |

GUI(ScreenSpot-Pro) 한 항목을 제외하면 전 영역에서 Qwen3-Omni 30B를 앞섭니다.

---

## 아키텍처: Mamba + MoE + 비전 + 오디오

![Nemotron 3 Nano Omni 아키텍처](/images/nemotron-omni-architecture.png)

### 언어 백본: Hybrid Mamba-Transformer-MoE

세 가지 레이어를 조합한 구조입니다:

- **Mamba SSM 23개**: 효율적인 장문 컨텍스트 처리
- **MoE 23개**: 전문가 128개, top-6 라우팅 + 공유 전문가 — 조건부 용량 확보
- **GQA(그룹 쿼리 어텐션) 6개**: 글로벌 표현력 유지

Mamba의 효율성과 어텐션의 표현력을 MoE로 확장하는 설계입니다.

### 비전: 동적 해상도 처리

V2 모델의 타일링 전략을 대체해 원본 종횡비 그대로 처리합니다. 이미지당 1,024~13,312 패치(16×16)를 사용하며, 최대 1840×1840 해상도에 해당합니다. OCR 문서, 재무 표, GUI 스크린샷처럼 세부 내용과 전체 구조를 함께 이해해야 하는 입력에 유리합니다.

### 비디오: Conv3D + EVS

- **Conv3D Tubelet 임베딩**: 연속 2프레임을 하나의 토큰으로 압축 → 비전 토큰 수 절반으로 감소
- **EVS(Efficient Video Sampling)**: 비전 인코더 이후 중복 정적 프레임 토큰 제거 — 정확도 유지하면서 지연 감소

두 기법을 조합해 동일 토큰 예산에서 2배 많은 프레임을 처리할 수 있습니다.

### 오디오: 네이티브 처리

Parakeet-TDT-0.6B-v2를 2-레이어 MLP 프로젝터로 백본에 연결합니다. 16kHz 샘플링, 최대 1,200초(20분) 입력 훈련, LLM 컨텍스트 기준 5시간 이상 지원. 오디오 토큰을 텍스트·비전 토큰과 동일 시퀀스에서 처리해 진정한 멀티모달 추론이 가능합니다.

---

## 처리량 비교

![처리량 비교](/images/nemotron-omni-throughput.png)

동급 인터랙티브 오픈 옴니 모델 대비:
- 멀티문서 유스케이스: **7.4배** 높은 시스템 처리량
- 비디오 유스케이스: **9.2배** 높은 시스템 처리량

MoE(활성 파라미터 3B)와 EVS·Conv3D의 토큰 압축이 효율성의 핵심입니다.

---

## 훈련 스택

- **SFT**: NVIDIA H100, 32~128 노드, Megatron-LM + Transformer Engine + Megatron Energon
- **강화학습**: NeMo-RL + NeMo Gym, B200/H100 혼합 클러스터, Ray 분산 설정
- **합성 데이터**: NeMo Data Designer로 실제 PDF에서 약 1,140만 개 합성 QA 쌍(~45B 토큰) 생성 → MMLongBench-Doc 정확도 2.19배 향상

훈련 코드 일부와 [9개의 실행 가능한 파이프라인 레시피](https://github.com/NVIDIA-NeMo/DataDesigner/tree/main/docs/assets/recipes/vlm_long_doc)가 오픈소스로 공개됩니다.

---

## 다운로드 및 리소스

| 형식 | 링크 |
|------|------|
| BF16 체크포인트 | [HuggingFace](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16) |
| FP8 체크포인트 | [HuggingFace](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8) |
| NVFP4 체크포인트 | [HuggingFace](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4) |
| 기술 리포트 | [arXiv 2604.24954](https://arxiv.org/abs/2604.24954) |

---

## 실무자가 볼 포인트

- **비용 효율**: MoE로 30B 파라미터를 유지하면서 활성 파라미터는 3B — 추론 비용이 동급 Dense 모델 대비 낮음
- **문서 AI**: 100페이지 이상 문서를 단일 컨텍스트에서 처리하는 능력은 계약서 검토, 규제 컴플라이언스, 기술 문서 파싱에 바로 적용 가능
- **GUI 에이전트**: OSWorld 47.4%는 실제 컴퓨터 사용 자동화 에이전트 구축에 충분한 수준
- **오픈웨이트**: BF16/FP8/NVFP4 세 가지 정밀도로 공개 — 온프레미스 배포와 양자화 옵션 모두 지원
- **경쟁 관계**: Qwen3-Omni 30B와 같은 규모에서 대부분 벤치마크를 앞서지만, GUI(ScreenSpot-Pro)는 Qwen3-Omni가 소폭 우위

---

**원문**: [Introducing NVIDIA Nemotron 3 Nano Omni](https://huggingface.co/blog/nvidia/nemotron-3-nano-omni-multimodal-intelligence) (Hugging Face Blog, 2026-04-28)
