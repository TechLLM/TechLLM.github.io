---
title: "진짜 컴퓨터 프로그램 16개를 마우스 조작과 명령어 조작을 함께 연습할 수 있는 훈련장으로 만들고, 그 기록으로 AI를 가르친 연구다."
date: 2026-09-28T07:32:30+09:00
draft: false
description: "실제 데스크톱 소프트웨어 16종을 GUI와 CLI 양쪽으로 조작 가능한 하이브리드 환경으로 자동 변환하는 파이프라인(CUA-Universe)을 제시한다. App-Forge·Task-Weave·Path-Steer 세 단계로 환경 구축, 과제 합성, 궤적 수집을 자동화하고, 이 데이터로 학습한 9B 모델은 CUA-Verse에서 Score +39.3점, OSWorld에서 SR +16.8점, OSWorld-MCP에서 Score +7.84점을 얻으면서 스텝과 토큰 사용량도 줄였다."
tags: ["Computer-Use Agent / Agent Training", "논문 분석", "논문 리뷰", "GUI", "CLI", "POMDP"]
categories: ["논문분석"]
---


진짜 컴퓨터 프로그램 16개를 마우스 조작과 명령어 조작을 함께 연습할 수 있는 훈련장으로 만들고, 그 기록으로 AI를 가르친 연구다.

**무엇이 문제였나** — 기존 컴퓨터 사용 AI는 화면을 보며 클릭만 하느라 오래 걸리거나, 명령어만 쓰다가 화면 상태를 놓치는 문제가 있었다.
**어떻게 풀었나** — 이 논문은 Blender, LibreOffice, VLC, VS Code 같은 실제 앱을 설치하고, 각 앱에서 쓸 수 있는 명령어 도구를 찾아 붙인 뒤, 화면 조작과 명령어를 섞어 푸는 과제를 자동으로 만든다.
**그래서 뭐가 좋아졌나** — 그 데이터로 9B 모델을 학습하자 성공률은 오르고, 같은 일을 끝내는 데 필요한 단계 수와 토큰 수는 줄었다.

> 연습용 사무실을 자동으로 만드는 것과 비슷하다. 문서 편집기, 영상 편집기, 코드 편집기 같은 실제 도구를 준비해 두고, AI가 버튼을 누를 때와 명령어를 칠 때를 스스로 배울 수 있게 작업 기록을 모아 가르친다.

## 논문 정보

Haoting Shi, Wenhao Wang, Weicheng Fang, Yaozhong Liang, Tian Jin, Pengxiang Zhao, Guangyi Liu, Siheng Chen, Yanfeng Wang · Shanghai Jiao Tong University, Zhejiang University · arXiv preprint (arXiv:2609.05374) · 2026

## 왜 중요한가

사람은 실제 업무에서 화면을 보며 메뉴를 찾다가도, 정확하거나 반복적인 작업은 명령어·스크립트로 처리한다. 이 연구는 AI도 그런 방식으로 훈련할 수 있게 실제 소프트웨어 기반의 환경과 데이터를 자동으로 만드는 방법을 보여준다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| CUA-Verse Score | **+39.3pts** | Qwen3.5-9B base 0.189에서 Ours 0.582로 상승 |
| OSWorld SR | **+16.8pts** | Ours GUI-only 23.4%에서 GUI+CLI 40.2%로 상승 |
| OSWorld-MCP Score | **+7.84pts** | 보지 못한 MCP 도구 인터페이스로 일반화한 점수 개선 |
| CUA-Verse 토큰 | **−60%** | Qwen3.5-9B base 대비 에피소드당 토큰 사용량 감소 |

## 어떻게 동작하나

CUA-Universe는 실제 데스크톱 소프트웨어를 환경-데이터 파이프라인으로 바꾼다. App-Forge는 설치 에이전트가 VM에 앱을 설치·검증하고, 네이티브 CLI·스크립팅 API·생성된 agent-native CLI를 발견하거나 래핑해 GUI와 같은 파일 상태를 공유하는 명령어 표면을 만든다. Task-Weave는 실제 시드 파일 위에서 재사용 가능한 조작을 추상화하고, 연산 사슬을 합성한 뒤 ReAct-style 검토자가 실행 가능성과 모호성을 확인해 과제를 남긴다. Path-Steer는 각 단계에서 에이전트가 스크린샷과 CLI 반환값을 관찰하고 GUI 행동 또는 CLI 행동을 고르는 POMDP로 문제를 다루며, 배치·정밀 작업은 CLI, 시각·레이아웃 작업은 GUI에 유리하다는 가벼운 실행 prior로 rollout을 유도한다. 최종적으로 VLM judge 점수 0.75 이상인 궤적만 학습 데이터로 보존했고, 총 4,923 episodes와 235,408 step records를 Qwen3.5-9B에 LoRA로 3 epoch 학습했다.

핵심 수식:

```
τ = (instr, s₀, V),   aₜ ∈ A_gui ∪ A_cli,   V(ζ) ∈ [0,1]
```

τ는 지시문 instr, 시드 초기 상태 s₀, 검증기 V로 이루어진 과제 튜플이다. aₜ는 매 단계의 GUI 또는 CLI 행동이며, V(ζ)는 궤적 ζ에 대해 0~1 점수를 주는 VLM judge이다.

## 한계와 주의할 점

- 모든 합성 과제가 단일 애플리케이션 안에서만 동작하며, 여러 앱을 가로지르는 워크플로우는 후속 과제로 남아 있다.
- 수집된 궤적은 SFT 용도로만 사용되어 정책이 데이터 생성 백본의 상한에 묶일 수 있고, RL 단계는 아직 적용하지 않았다.
- 작업 성공 판정을 VLM Judge에 의존하므로 라벨 노이즈가 남을 수 있다. 다만 human validation에서 acceptance precision 99.0%, Cohen's κ=0.94를 보고했다.
- App-Forge는 오픈소스이거나 충분히 스크립트 가능한 Linux 데스크톱 앱을 전제로 하며, 폐쇄소스·모바일·비데스크톱 환경 확장은 검증되지 않았다.
- 평가와 데이터 필터링에 GPT-5.4 VLM judge를 사용하므로 판정 모델에 대한 의존성이 있다.
- Path-Steer가 항상 지역적 시행착오를 없애는 것은 아니다. VLC 사례에서도 초반 CLI 파라미터 시도는 실패했지만, ffmpeg 대안으로 전환해 최종 성공했다.
- Path-Steer 없이 GUI 중심으로 진행하면 VLC 사례처럼 필터 설정 단계에서 반복 탐색에 빠져 과제를 끝내지 못할 수 있다.
- 3D·공간 도메인(Blender, Godot)에서는 시각적·공간적 조작 비중이 커서 Ours의 점수가 Audacity·OBS보다 낮게 나온다.
- 시드 파일의 실제 객체나 메타데이터와 합성 지시문이 맞지 않으면 ReAct 검토 단계에서 모호하거나 이미 충족된 과제로 폐기될 수 있다.
- GUI-only 모드에서는 VS Code 사례처럼 60-action budget을 모두 쓰고도 정확한 설정 파일 변경을 완료하지 못할 수 있다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 도구 호출 에이전트에 모달리티 선택 사전(Path-Steer) 주입

장기 작업 에이전트의 실행 단계에서 작업 연산 사슬을 분석해 배치·정밀 작업은 CLI/도구 호출로, 시각 확인·레이아웃 선택은 GUI로 라벨링한 guidance를 넣는다. 논문에서는 Path-Steer가 데이터 생성 rollout에만 사용되고 평가 시에는 guidance field가 비어 있다고 명시한다.

**적용 지점** — 에이전트 rollout 시 모달리티 선택 단계

**기대 효과** — Kimi K2.5에서 Accept Rate 0.44→0.51, 평균 스텝 26.68→22.75, 평균 토큰 385,107→331,988, 평균 비용 $0.31→$0.26(Table 3).

### 시드 파일 기반 과제 합성 + ReAct 검토자 결합

RAG나 문서 QA 데이터 생성에서도 실제 사용자 문서나 프로젝트 파일을 seed로 두고, operation abstraction → task instantiation → agentic refinement 절차를 적용할 수 있다. ReAct-style 검토자는 과제가 이미 충족되었는지, 모호한지, 실행 가능한지 확인하고 필요하면 지시문과 guidance를 수정한다.

**적용 지점** — RAG/문서 QA 학습 데이터 생성 파이프라인

**기대 효과** — CUA-Universe는 VLM score ≥0.75를 통과한 4,923 verified episodes만 학습에 사용해 실행 가능한 데이터로 후훈련했다.

### 결정적 CLI 출력을 self-verification 신호로 활용

GUI 화면은 외부 파일 편집 뒤 stale할 수 있으므로, 파일 기반 작업에서는 CLI 성공 출력과 산출물 증거를 1차 검증 신호로 쓰고 최종 스크린샷을 보조 신호로 쓰는 듀얼 게이트를 둔다. 논문의 VLM judge prompt도 파일 기반 편집에서는 CLI output과 exported artifact evidence를 authoritative하게 보라고 지시한다.

**적용 지점** — 에이전트 종료 조건·self-verification 단계

**기대 효과** — VS Code 예시에서 GUI+CLI는 5 CLI calls + 12 GUI actions로 reward 1을 얻었고, GUI-only는 60 GUI actions 후 reward 0이었다(Figure 8).

### 응용 프로그램별 CLI 표면 자동 발견·래핑 어댑터

대상 앱의 네이티브 바이너리(cvlc 등), 스크립팅 API(bpy, LibreOffice UNO, GIMP Script-Fu 등), 그리고 agent-native CLI를 단일 JSON 반환 레지스트리로 통합한다. GUI와 CLI가 같은 프로젝트 상태를 공유하도록 어댑터가 stale view를 재동기화한다.

**적용 지점** — 에이전트 도구 레지스트리·계약 정의 단계

**기대 효과** — 16개 앱에 약 404개의 agent-visible commands를 구축했다. OSWorld 재사용 앱 8종은 151개, CUA-Universe 확장 앱 8종은 253개 명령을 포함한다(Figure 5).

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 단일 앱 하이브리드 인터페이스 구축 | App-Forge 방식으로 우선 OSWorld 8종 앱에 CLI 표면을 추가하고, 시드 풀과 GUI/CLI 공유 상태 어댑터를 마련한다. VLM judge 검증은 Appendix F.1처럼 acceptance precision 99.0% 수준까지 확인한다. | GUI-only 환경 대비 스텝과 토큰 감소 효과를 재현할 수 있다. |
| Phase 2 | 하이브리드 과제 합성·검증 자동화 | Task-Weave의 operation abstraction, task instantiation, agentic task refinement 절차를 내부 앱 카탈로그에 맞게 구성하고, 실제 시드 파일 기반 과제를 만든다. | 손으로 만든 과제보다 큰 규모의 실행 가능한 하이브리드 시나리오를 확보한다. |
| Phase 3 | 에이전트 학습·강화 루프 확장 | 9B급 베이스 모델에 LoRA SFT를 적용하고, 논문 한계에서 제안한 것처럼 per-task verifier를 보상으로 쓰는 RL 단계를 후속으로 도입한다. 데이터 생성은 128-core CPU 서버 기준 약 1.3~1.5 calendar days로 보고되었다. | 단일 앱 환경에서 시작해 더 넓은 앱과 워크플로우로 확장할 수 있는 기반을 만든다. |

---

원문 PDF: `2026-09-07-cua-universe-a-scalable-and-dynamic-environment-for-hybrid-gui-cli-agent.pdf`
