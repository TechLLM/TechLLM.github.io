---
title: "도구를 각각 독립된 프로그램으로 실행하고, 대화와 작업 기록은 프로그램 밖의 파일에 이어 적습니다. 그 결과 하나가 멈춰도 새 프로그램이 기록을 읽고 일을 이어갈 수 있습니다."
date: 2026-10-29T07:35:00+09:00
draft: false
description: "이 논문은 언어 모델 호출을 상태 없는 순수 함수로 보고, 입력 합성과 출력 처리를 모델 밖의 작업으로 놓아 교차 단계 상태가 특정 프로세스에 묶이지 않는다는 점을 바탕으로 spatiotemporal-composability calculus의 가역성 보장을 프로세스 경계 너머로 확장한다. 네 보조정리와 정리 4.5는 추적 가능한 효과가 발생 시점에 영속 transcript에 anchor를 기록하고 각 키에 단일 writer가 있을 때 충실한 다중 프로세스 구현이 성립함을 보인다."
tags: ["LLM Agents / Distributed Systems", "논문 분석", "논문 리뷰", "프로세스", "append-only transcript", "cold switching"]
categories: ["논문분석"]
---


도구를 각각 독립된 프로그램으로 실행하고, 대화와 작업 기록은 프로그램 밖의 파일에 이어 적습니다. 그 결과 하나가 멈춰도 새 프로그램이 기록을 읽고 일을 이어갈 수 있습니다.

**무엇이 문제였나** — 도구와 대화를 한 프로그램에 몰아 두면, 그 프로그램이 멈출 때 함께 멈춥니다.
**어떻게 풀었나** — Logos는 도구를 각각 다른 프로그램으로 실행하고, 대화와 작업 기록은 계속 뒤에 덧붙여 저장합니다.
**그래서 뭐가 좋아졌나** — 도구가 도중에 멈춰도 새 프로그램이 저장된 기록부터 읽어 일을 이어갔고, 이미 기록된 작업은 다시 실행하지 않았습니다.

> 여러 사람이 각자 맡은 일을 하는 작업장에 비슷합니다. 한 사람이 잠시 자리를 비워도 작업일지에 어디까지 했는지 남아 있으면, 다른 사람이 그 지점부터 이어받을 수 있습니다.

## 논문 정보

Hanzhang Jia, Liheng Zeng, Hao Cheng, Yi Gao, Bo Ma · University of Sussex; Zhejiang Gongshang University; Shanghai Shuyuan Information Technology Co., Ltd. · AAMAS 2027 · 2027

## 왜 중요한가

도구 하나가 멈출 때 다른 도구와 세션까지 함께 멈추는 일을 줄일 수 있습니다. 또한 저장된 기록을 다시 읽어 이어갈 수 있어, 여러 도구를 사용하는 서비스를 재시작한 뒤에도 복구 절차를 관리하기 쉽습니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| 도구 호출 주기 종료 지점 재개 | **80/80세션** | 실행 중, 반환 후 저장 전, 저장 후 알림 전, 알림 후 네 종료 지점에서 모두 재개·완료했다. 기록된 효과는 반복되지 않았고 복구 후 다시 수행된 일은 기록되지 않은 부분과 같았다. |
| 연속 프로세스 종료 후 세션 재개 | **12/12세션** | 여섯 번의 프로세스 종료 후 모두 완료되었고 이전에 실행한 작업이 반복되지 않았으며, 재시작 비용은 1.36초였다. |
| 버스 홉 지연시간 | **0.215ms** | 10,000회 호출의 중앙값이었다. 99백분위는 0.377ms, 99.9백분위는 0.623ms, 최댓값은 3.045ms였다. |
| 호출·응답 완전 쌍 연결 | **3,500/3,500호출** | 200개 동시 호출자에 대한 감사에서 손실, 중복, 오귀속이 없었다. |

## 어떻게 동작하나

논문은 기존 spatiotemporal-composability calculus가插件의 조립·제거와 추적된 역함수를 다루지만, 기준 구현은 모든 구성요소와 기록을 한 프로세스에 두며 비동기 프로세스 경계에 대한 정리를 제시하지 않는다는 점에서 출발한다. 저자들은 언어 모델의 순방향 호출이 상태 없는 순수 함수이고, 여러 차례에 걸친 상태와 입력 합성·출력 처리가 모델 밖에 있다는 두 모델링 사실을 사용한다. 네 보조정리는 각각 상태 외부화, 영속 carrier를 통한 transcript 치환, 독립 효과의 복구 지역화, routing table을 통한 외부 의존성 해결을 다룬다. 정리 4.5는 되돌릴 수 있는 모든 효과가 발생 시점에 영속 transcript에 anchor를 쓰고, 각 키가 등록 단계에서 단일 writer를 가져야 한다는 두 조건 아래에서 다중 프로세스 구현이 calculus에 충실함을 보인다. Logos에서는 capability와 plugin이 프로세스이고, Go router는 등록·전달·broadcast와 routing table만 담당하며, append-only JSONL transcript가 세션 기록의 단일 기준이다. 별도의 append-only event stream은 시스템 동작을 관찰한다. E1은 호출별 응답 짝짓기, E2는 이름별 단일 등록과 충돌 거절, E3은 모든 관측자에 동일한 공급 변경 순서를 배달한다는 공학 제약이다. 실험은 AMD Ryzen 7 7435H 기반 Windows 11 단일 머신과 loopback bus에서 수행되며, 버스 지연, 동시 호출, 도구 도입·교체, router와 tool 종료, cold switching, transcript 및 event stream replay를 검증했다. 비교군에는 calculus 참조 구현을 같은 세션 코드와 같은 고장 주입 조건으로 사용했다.

핵심 수식:

```
\(g \circ f = \mathrm{id}\)\n\(\Pi(\tau') = \Pi(\tau)\)\n\(\rho(a_i) \simeq g_i\)
```

첫 식은 Definition 3.1의 식 (1)로, 단일 역함수 g가 f가 선택된 모든 상태에서 원래 상태를 복원한다는 뜻이다. 둘째 식은 Section 4.1의 식 (3)으로, 모든 추상 trace τ에 대해 그와 관찰 동등한 구현 trace τ'가 존재하여 macrostate projection Π 아래에서 점별로 같아야 한다는 충실한 assignment 조건이다. 셋째 식은 Lemma 4.2의 조건으로, 영속 저장소의 readout ρ가 각 anchor a_i에서 inverse g_i와 관찰 동등해야 하며, 이를 적용 순서대로 합성하면 carrier를 통한 복구가 Π 아래에서 제자리 복구와 같아진다는 뜻이다.

## 한계와 주의할 점

- 모든 측정은 AMD Ryzen 7 7435H 기반 Windows 11 단일 머신과 loopback bus에서 수행됐다. 논문은 private grid deployment boundary도 제시하지만 여러 머신에 걸친 측정, 네트워크 분할, 장거리 지연은 검증하지 않았고 향후 과제로 남겼다.
- 종료 지점 실험은 GLM-5.2를, 종단 및 multi-agent 실험은 DeepSeek V4 Flash를 사용한다. 시나리오마다 다른 모델도 사용했지만 80개 종료 지점 결과가 목록에 있는 모든 모델과 다양한 작업 부하에서 재현되는지는 제시되지 않았다.
- 정리의 귀납 논증은 appendix에 제시되지만 E1-E3와 비동기 계약의 완전한 형식 의미론은 없는 상태다. 특히 손실·분할·재연결의 의미론, key별 규율 검증, 공급 순서의 coverage 증명은 향후 과제로 명시됐다.
- 80개 세션의 반복 효과 없음은 추적 가능한 효과에 대한 결과다. 결제처럼 경계 밖에 두는 outward effect에 대한 exactly-once 실행을 보장하지 않으며, withholding 또는 compensation 없이는 중복 실행을 막을 수 없다.
- transcript는 plaintext 단일 원본이고 snapshot과 compaction은 향후 엔지니어링 항목이다. 장기 실행에서 파일 크기, replay 비용, 민감 정보 보호에 대한 정량 평가가 없다.
- 버스 오버로드 시 lossy stream은 가장 오래된 항목을 버릴 수 있고 control queue가 가득 차면 peer를 끊는다. 시험 부하에서는 손실이 없었지만 과부하 상황의 전체 세션 의미론은 형식적으로 검증되지 않았다.
- 도구가 결제 같은 외부 효과를 수행한 뒤 결과를 transcript에 남기기 전에 종료되면 재시도 시 그 효과가 중복될 수 있다. 논문은 이런 outward effect를 복구 경계 밖에 두고 추적하지 않는다.
- 같은 capability 이름을 여러 제공자가 동시에 등록하면 하나만 등록되고 나머지는 명시적으로 거절된다. 필요한 제공자가 없으면 호출은 명시적 오류를 받고 이후 온라인 broadcast로 활성화된다.
- router가 종료되면 노드는 직접 연결을 통해 세션을 계속 실행하지만 routing 변경과 새 호출의 처리에는 복구 창이 생긴다. 죽은 provider로 향한 호출은 명시적 오류를 반환한다.
- 연결의 lossy stream queue가 가득 차면 가장 오래된 항목을 버리고 control queue가 가득 차면 peer를 끊는다. 끊어진 노드는 다시 등록해야 하며 호출 순서와 결과 짝짓기는 global call id와 replay로 보완한다.
- 회복 지역화 논리는 효과 함수들이 서로 독립이고 공유 상태가 single-writer 또는 commutative-key 규율을 지킬 때에만 적용된다. 공유 데이터베이스나 quota처럼 이 전제를 어기는 효과는 별도 single-writer 도구로 격리하거나 경계 밖에 두어야 한다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 도구 호출을 효과 기록과 복구 경계에 연결

도구 실행기에서 외부 효과가 발생하는 지점을 Logos의 transcript 기록 지점과 연결한다. 논문의 carrier substitution처럼 복구 가능한 효과는 발생 시 anchor를 영속 기록하고 재개 시 transcript로 상태를 재구성한다. 결제처럼 되돌릴 수 없는 작업은 별도 single-writer 도구로 격리하고, 운영 제안으로 요청 식별자 기반 중복 방지나 compensation을 적용한다. 논문의 외부 효과 경계를 운영 계약으로 명시하되 중복 방지 자체의 효과는 별도로 측정해야 한다.

**적용 지점** — 도구 실행기와 외부 효과 연동 경계

**기대 효과** — 80/80 종료 지점 세션에서 transcript에 기록된 효과가 반복되지 않았다. 외부 효과 중복 방지 자체의 정량 개선치는 논문에 없다.

### capability 등록을 단일 writer와 버전 명시 계약으로 강화

도구 레지스트리의 등록 단계에서 capability 이름당 한 제공자만 허용하고 충돌 요청은 명시적으로 거부한다. 논문의 external resolution처럼 router에는 capability와 제공자의 연결만 두고, 공급자 교체는 온라인·오프라인 broadcast 순서로 전달한다. 등록 receipt와 거부 receipt를 감사 기록에 포함해 각 소비자가 같은 공급자 변경 순서를 재구성하게 한다. 구현 제안으로 버전이나 호환성 조건을 capability 계약에 추가할 수 있으나 버전 계약은 논문에서 평가되지 않았다.

**적용 지점** — 에이전트가 사용하는 capability 등록·발견 인터페이스

**기대 효과** — 100개 동시 동일 이름 등록에서 1개 성공과 99개 명시적 거절을 관찰했고, 50개 제공자의 30회 churn 동안 두 관측자가 같은 이벤트 순서를 기록했다.

### 세션별 transcript 재생을 복구 하네스의 기본 경로로 적용

에이전트 실행 하네스의 매 round 입력, tool use와 result, streamed text를 append-only transcript에 쓴다. 재시작 시 기존 메시지를 추측해 복원하지 않고 transcript를 replay해 모델에 보여준 projection이 같은지 I1~I4 검사를 통과시킨다. 세션 기록을 shard로 구분하고 노드별 복구를 독립시켜 한 세션의 종료가 다른 세션까지 중단시키지 않게 한다. 기록 용량이 커지는 경우 snapshot과 prefix 보관을 추가하되 replay 의미를 보존해야 한다.

**적용 지점** — 에이전트 실행 하네스의 세션 저장·재개 단계

**기대 효과** — 12개 세션이 6회 종료 후 재개했고, 별도 80개 세션은 네 종료 지점에서 모두 완료했으며 기록된 효과는 반복되지 않았다.

### 온라인 도구 공급 이벤트를 모델의 자발적 도구 선택으로 연결

새 provider가 온라인 상태를 broadcast하면 각 harness가 전달받은 capability 목록을 갱신한다. 모델 입력에 도구 이름을 지시하는 별도 문장을 삽입하지 않아도 새 capability가 선택 가능해진다. 공급자 교체와 offline broadcast가 같은 순서 관측 규칙을 따르도록 registration receipt와 event stream을 함께 감사한다.

**적용 지점** — 도구 등록·발견 및 모델 호출 선택

**기대 효과** — registry-update broadcast 후 첫 자율 호출까지 8.4초였고, 기본 시험 3/3회와 확장 시험 10/10회에서 성공했다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 독립 프로세스와 기록 재생의 최소 경로 확립 | 한 harness와 한 tool을 bus에 연결하고 round, input, tool use와 result, streamed text를 append-only transcript에 기록한다. 별도 event stream도 유지하고 I1~I4로 순서, 식별자 단조성, 호출별 단일 결과, projection 재구성 일치를 검사한다. | 프로세스 재시작 후 새 프로세스가 같은 기록 상태에서 세션을 복원하는지 반복적으로 검증할 수 있다. |
| Phase 2 | 등록·라우팅과 장애 격리 적용 | capability 이름별 단일 등록과 충돌 거절을 구현하고 온라인·오프라인 이벤트를 순서대로 broadcast한다. router와 tool 종료, provider 교체, 동시 호출을 주입해 재등록, 명시적 오류, 재계산, 세션별 영향 범위를 측정한다. | 도구 변경과 고장이 어느 구성요소와 세션에 영향을 주는지 정량화하고 복구 절차를 구체화할 수 있다. |
| Phase 3 | 운영 규모와 형식 검증의 범위 확대 | 동시 세션과 제공자 churn을 늘리고 transcript와 event stream을 독립 감사 근거로 유지한다. E1~E3와 key별 규율 및 공급 순서를 형식화하고, 손실·분할·재연결 의미론과 다중 머신 환경, single-writer outward effect를 별도로 검증한다. | 현재의 엔지니어링 증거를 더 넓은 장애 모델과 운영 조건에서 확인하고 보장 범위를 명시적으로 구분할 수 있다. |

---

원문 PDF: `2026-08-31-logos-an-agent-harness-on-a-cross-process-bus.pdf`
