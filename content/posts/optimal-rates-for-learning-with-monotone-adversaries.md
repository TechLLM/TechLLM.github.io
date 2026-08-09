---
title: "훈련 데이터를 본 뒤 정답이 맞는 예시만 더 넣어도, 데이터의 순수한 무작위성이 깨져서 어떤 학습법도 일반적인 경우에는 로그만큼 더 느리게 배울 수 있음을 증명한 논문입니다."
date: 2026-08-10T07:40:08+09:00
draft: false
description: "본 논문은 깨끗한 i.i.d. 표본을 본 뒤, 정답 라벨을 유지한 예시만 추가하는 monotone adversary가 학습 난이도를 얼마나 높이는지 minimax 관점에서 규명한다. VC 차원 d=0에서는 위험이 0이고, d=1에서는 모든 삽입 예산 m에 대해 Θ(1/n)이 가능하지만, d≥2에서는 알려진 유한 예산들에 대한 최악의 경우 최적 위험률이 Θ((min{d,n}/n)·log(en/min{d,n}))로 증가한다."
tags: ["Theoretical Machine Learning (Learning Theory)", "논문 분석", "논문 리뷰", "Monotone Adversary", "VC dimension", "Littlestone dimension"]
categories: ["논문분석"]
---


훈련 데이터를 본 뒤 정답이 맞는 예시만 더 넣어도, 데이터의 순수한 무작위성이 깨져서 어떤 학습법도 일반적인 경우에는 로그만큼 더 느리게 배울 수 있음을 증명한 논문입니다.

**무엇이 문제였나** — 문제: 실제 데이터셋은 수집 후 사람이 보거나 규칙으로 다듬는 경우가 많고, 그러면 표본이 처음 뽑힌 무작위 표본처럼 행동하지 않을 수 있습니다.
**어떻게 풀었나** — 해결: 이 논문은 '정답 라벨을 가진 예시만 추가한다'는 제한된 조작만으로도 VC 차원 2 이상에서는 최적 오류율에 로그 요인이 반드시 붙는다는 하한을 보입니다.
**그래서 뭐가 좋아졌나** — 결과: VC 차원 1은 예외적으로 Θ(1/n)을 유지하지만, VC 차원 2 이상과 Littlestone 차원 2 이상에서는 단순한 ERM의 로그 손실이 실제 최적률과 일치합니다.

> 시험 문제를 무작위로 받아 연습해야 하는데, 누군가 먼저 그 문제들을 보고 비슷한 정답 문제를 더 섞어 넣는 상황을 생각하면 됩니다. 문제의 정답은 모두 맞지만, 어떤 문제가 원래 뽑힌 문제인지 모르게 되면 실제 시험 범위를 파악하기가 더 어려워집니다. 이 논문은 그 어려움이 문제 종류의 복잡도에 따라 정확히 얼마나 커지는지 계산합니다.

## 논문 정보

Anay Mehrotra · Stanford University · arXiv preprint · 2026

## 왜 중요한가

데이터 정제나 증강은 보통 도움이 되는 과정으로 여겨지지만, 이 논문은 데이터를 본 뒤 이루어지는 선택이 표본의 대칭성을 깨뜨리면 학습의 근본 한계가 달라질 수 있음을 보여줍니다. 라벨이 모두 맞더라도, 어떤 예시가 원래 표본이고 어떤 예시가 나중에 들어온 것인지 모르면 학습자는 더 어려운 통계 문제를 풀게 됩니다.

## 핵심 지표

| 지표 | 값 | 설명 |
|---|---|---|
| VC d≥2 최적 위험률 | **Θ((min{d,n}/n)·log(en/min{d,n}** | Theorem 3.1: 알려진 유한 삽입 예산 m들에 대한 sup_m minimax expected error rate |
| Clean PAC 위험 | **Θ(min{1,d/n})** | 삽입이 없는 i.i.d. 데이터에서 VC 차원 d≥1 클래스의 표준 minimax expected error |
| VC d=1 위험 상한 | **1/(n+1)** | Proposition 3.14: VCdim(H)≤1에서 consensus rule이 모든 m≥0에 대해 보장하는 expected error 상한 |
| VC d=1 위험 하한 | **1/(2e(n+1))** | Proposition 3.4 및 Theorem 3.1: VC 차원 1에서 모든 학습자에 대한 하한 |

## 어떻게 동작하나

논문은 Larsen-Pabbaraju-Shetty(LPS26)가 도입한 monotone adversary 모델에서 minimax expected error를 분석한다. 적대자는 n개의 깨끗한 i.i.d. 표본을 본 뒤 정확히 m개의 예시를 추가하며, 모든 추가 예시는 같은 target hypothesis로 올바르게 라벨링된다. 학습자는 섞인 전체 표본만 보고, 원래 분포에서 새로 뽑힌 테스트 점의 라벨을 예측한다. d≥2 하한의 핵심은 projective plane으로 만든 VC dimension 2 클래스에서 두 target hypothesis u_p와 v_L이 특정 checker 점에서만 의미 있게 다르지만, 적대자가 같은 최종 labeled multiset U^f를 만들 수 있게 하는 식별불가능성 구성이다. 누락된 checker가 존재할 확률을 coupon-collector식으로 하한하고, q를 n/log(en) 규모로 선택해 log(en)/n 하한을 얻는다. d≥3은 이 VC dimension 2 블록을 Cartesian product로 여러 개 합쳐 차원과 위험을 함께 증폭한다. d=1은 별도 현상으로, f-representation과 leave-one-out 논법을 이용한 improper consensus rule이 모든 m에 대해 1/(n+1) expected error를 달성한다. Littlestone dimension 결과는 checker-only 변형과 product construction을 통해 같은 rate를 d_L에 대해 재현한다.

핵심 수식:

```
R(n,0)=0,\quad R(n,1)=\Theta\!\left(\frac{1}{n}\right),\quad \forall d\ge 2,\quad R(n,d)=\Theta\!\left(\frac{\min\{d,n\}}{n}\log\frac{en}{\min\{d,n\}}\right)
```

R(n,d)=sup_{m∈N_0} R(n,m,d)는 학습자가 정확한 삽입 예산 m을 알고 있을 때의 minimax expected error를, 유한한 모든 예산 m에 대해 다시 최악화한 값이다. d=0에서는 모든 가설이 같은 classifier라 위험이 0이다. d=1에서는 모든 m≥0에 대해 1/(2e(n+1)) ≤ R(n,m,1) ≤ 1/(n+1)이다. d≥2의 lower bound는 모든 고정 m에 대한 명제가 아니라, n과 d에 따라 커질 수 있는 finite witness budget m(n,d)에 의해 달성된다. 같은 형태의 수식은 Littlestone dimension d_L에 대해서도 성립한다.

## 한계와 주의할 점

- d≥2 lower bound는 finite projective plane 및 product construction이라는 특수한 worst-case 클래스에 의해 증명되므로, 구조가 좋은 실제 분포에서 같은 손실이 관측된다는 뜻은 아니다.
- 로그 분리는 bounded budget m=O(1)에서는 필연적이지 않다. Remark 3.2는 이 경우 Θ(min{1,d/n}) clean rate가 가능하다고 설명한다.
- 결과는 binary classification 중심이며, partial 또는 multiclass concept class에서 vanishing rate가 가능한지는 논문이 open question으로 남긴다.
- Theorem 3.1의 rate를 효율적으로 달성할 수 있는지에 대한 계산 복잡도 문제는 미해결이다.
- 모든 분포와 target을 최악화하는 minimax 결과이므로, 도메인 분포 가정이 강한 응용에서는 더 나은 rate가 가능할 수 있다.
- m=O(1) 또는 n에 비해 매우 작은 삽입 예산: 로그 페널티를 그대로 적용하면 과도하게 비관적일 수 있다.
- 라벨 오류, 라벨 뒤집기, 테스트 포인트를 본 뒤의 poisoning처럼 monotone 조건을 벗어나는 공격: 본 모델의 보장은 직접 적용되지 않는다.
- VC 또는 Littlestone 차원이 실제 모델 복잡도를 잘 대표하지 않는 설정: bound가 vacuous하거나 실측 성능과 거리가 날 수 있다.
- 효율적 구현이 필요한 대규모 학습: minimax rate는 통계적 가능성을 말하지만, 최적 학습자의 계산 효율성은 별도 문제다.
- 데이터 정제가 삭제·재가중치·필터링을 포함하는 경우: 논문 모델은 예시 추가를 다루므로 해당 파이프라인에 적용하려면 별도 모델링이 필요하다.

## 시스템 적용 아이디어

논문의 기법을 비슷한 구조를 가진 시스템에 옮길 때의 적용 지점이다.

### 데이터 의존성 환경에서 ERM을 기준 학습기로 설정

LPS26의 ERM upper bound와 본 논문의 matching lower bound(Theorem 3.1, Theorem 3.15)를 결합하면, monotone 삽입 환경의 최악 경우에는 ERM이 Θ((min{d,n}/n)·log(en/min{d,n})) rate로 점근적으로 최적이다. 이는 clean PAC 환경에서 더 정교한 learner가 ERM보다 로그 요인을 개선하는 고전적 그림과 다르다. 단, 이는 통계적 rate에 관한 statement이며 계산 효율성은 별도로 검토해야 한다.

**적용 지점** — 정답 라벨 예시가 사후적으로 추가되는 이진 분류 학습

**기대 효과** — 복잡한 learner가 minimax rate를 개선할 수 없다는 이론적 근거를 제공. 구체적 계산 비용 절감률은 구현에 따라 달라진다.

### 삽입 예산이 작을 때 subset majority 사용

Remark 3.2는 n ≥ 8(m+1), t=⌊n/(4(m+1))⌋일 때 모든 t-원소 부분집합에 clean learner를 실행하고 majority vote를 취하면 risk O(d(m+1)/n)을 얻는다고 설명한다. 특히 m=O(1)이면 clean rate Θ(min{1,d/n})와 같은 차수의 성능이 가능하다. 따라서 삽입 예산이 작고 알려져 있으면 worst-case sup_m rate를 그대로 적용하지 않는 것이 맞다.

**적용 지점** — 삽입 예산 m이 작고 사전에 알려진 데이터 추가 파이프라인

**기대 효과** — m=O(1)에서 로그 요인을 피하고 O(d/n) 차수의 expected error를 회복할 수 있다.

### VC 차원 1 클래스용 consensus rule 적용

Proposition 3.14는 f-representation과 leave-one-out 논법을 결합한 improper consensus rule이 VCdim(H)≤1 클래스에서 모든 m≥0에 대해 expected error 1/(n+1)을 달성함을 보인다. Proposition 3.4의 1/(2e(n+1)) 하한과 맞물려 d=1의 최적률은 Θ(1/n)이다. 단순 threshold류 문제에서는 ERM이 항상 이 보장을 주는 것은 아니므로, 해당 구조가 확인되면 consensus rule을 우선 검토할 수 있다.

**적용 지점** — VC 차원 1인 이진 분류 문제

**기대 효과** — 모든 삽입 예산 m에 대해 1/(n+1) expected error 상한 보장.

### Littlestone 기반 online-to-batch 보장 재검토

Theorem 3.3은 Littlestone dimension d_L에 대해서도 d_L=0,1의 예외를 제외하면 Θ((min{d_L,n}/n)·log(en/min{d_L,n})) rate가 최적임을 보인다. 특히 로그 손실은 VC와 Littlestone dimension이 모두 2인 고정 클래스에서도 발생한다. 온라인 학습 가능성이 있는 클래스라고 해서, 사후 삽입된 오프라인 데이터셋에서도 같은 expected error rate가 유지된다고 가정하면 안 된다.

**적용 지점** — 온라인 학습 보장을 오프라인 큐레이션 데이터 학습에 전이하려는 시스템

**기대 효과** — clean online-to-batch rate를 과신하는 설계 오류를 방지하고 로그 보정이 필요한 regime을 식별한다.

## 단계별 도입 로드맵

| 단계 | 목표 | 액션 | 기대 효과 |
|---|---|---|---|
| Phase 1 | 데이터 추가 과정의 모델 적합성 점검 | 후처리 단계가 예시 추가인지, 라벨이 target과 일치한다고 볼 수 있는지, 삽입 예산 m이 n,d와 함께 커지는지 구분 | Theorem 3.1을 적용할 수 있는 경우와 bounded-budget 예외를 분리한다. |
| Phase 2 | 복잡도 regime별 학습 전략 선택 | VC 차원 1이면 consensus rule 검토, VC 차원 2 이상이면 ERM의 O((min{d,n}/n)log(en/min{d,n})) upper bound를 기준선으로 사용, m=O(1)이면 subset-majority 방식 검토 | 불필요하게 clean PAC rate를 기대하지 않고, 실제 보장 가능한 rate에 맞춰 학습기를 선택한다. |
| Phase 3 | 실측 손실과 이론 rate 비교 | n 증가에 따른 expected error 감소가 d/n인지 (d/n)log(en/d)인지 모니터링하고, 삽입 예산이 커지는 파이프라인은 추가 예시 수를 제한하거나 표본 원천을 분리 | 최악 이론 bound가 실제 시스템에서 얼마나 보수적인지 확인하고 파이프라인을 조정한다. |

---

원문 PDF: `2026-08-10-optimal-rates-for-learning-with-monotone-adversaries.pdf`
