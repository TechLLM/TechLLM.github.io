---
title: "Anthropic이 Claude Fable 5로 경쟁사 연구자 몰래 느리게 만들려다 사과한 사건"
date: 2026-06-11T19:40:25+09:00
draft: false
description: "Anthropic이 경쟁 AI를 학습시키려는 연구자에게는 Claude Fable 5 성능을 몰래 떨어뜨리려 했다는 사실이 알려졌습니다. 비판이 쏟아지자 회사는 '잘못된 트레이드오프였다'며 정책을 철회했습니다."
cover:
  image: "/images/anthropic-claude-fable-5-throttling-tradeoff/anthropic-claude-fable-5-throttling-tradeoff-cover.png"
  alt: "Anthropic 로고 벽 앞에 두 갈래로 갈라진 길과 끊어진 회로가 그려진 손그림 일러스트"
  caption: "Generated illustration"
tags: ["Anthropic", "Claude", "AI 거버넌스", "데이터 보존", "오픈소스 AI", "Microsoft", "GitHub Copilot"]
categories: ["AI", "산업 동향"]
source_url: "https://the-decoder.com/claude-fable-5-anthropic-admits-wrong-tradeoff-after-invisibly-throttling-rival-ai-researchers/"
---

Anthropic이 한 줄짜리 짧은 입장문을 내놨습니다. "우리가 잘못된 트레이드오프를 택했고, 균형을 맞추지 못한 점에 대해 사과한다." 자기네 모델로 경쟁 AI를 만들려는 사람에게는 모델 품질을 슬그머니 떨어뜨리겠다는 계획이 들통난 직후였습니다. 이 일은 단순한 정책 실수가 아니라, AI 회사가 어디까지 '경쟁자'를 가로막아도 되느냐는 더 큰 질문을 다시 꺼냈습니다.

## 핵심 요약

- Anthropic이 Claude Fable 5를 경쟁 AI 학습 용도로 쓰는 것 같으면 **사용자 모르게** 성능을 떨어뜨리려고 했습니다.
- 연구자들의 거센 반발에 회사는 정책을 되돌리고 "앞으로의 보호 장치는 모두 사용자에게 보이게 만들겠다"고 약속했습니다.
- Dean Ball 전 백악관 AI 고문은 이 방식을 "충격적으로 적대적"이라고 평했습니다.
- 그러나 또 다른 논란이 남아 있습니다. Fable 5는 새 안전 분류기를 위해 프롬프트와 응답을 **최대 30일, 정책 위반 시 2년**까지 보관합니다.
- 이 데이터 보존 정책 때문에 Microsoft는 GitHub Copilot 내부 모델 목록에서 Fable 5만 제외했습니다.

![몰래 떨어진 응답 품질을 비유한 손그림](/images/anthropic-claude-fable-5-throttling-tradeoff/body-01.png)

## 무엇이 문제가 됐나

문제의 정책은 단순했습니다. Claude Fable 5를 호출하는 사용자가 "경쟁 모델을 학습시키려는 신호"를 보이면, 응답 품질을 알리지 않고 살짝 떨어뜨리겠다는 것이었습니다. 겉으로 보기에는 똑같이 답하지만 속에서는 약하게 답하는 식입니다.

문제는 '몰래'라는 부분이었습니다. 사용자는 자기 결과가 일반 모델과 같은 수준이라고 믿고 평가, 비교, 논문, 제품에 그대로 가져다 씁니다. 그런데 실제로는 다른 답을 받고 있던 셈입니다. 연구 신뢰성과 직결되는 문제라 학계와 스타트업 모두 불쾌해할 수밖에 없었습니다.

Anthropic은 WIRED에 입장을 보내며 정책을 거뒀습니다. "앞으로 어떤 보호 장치를 만들더라도 사용자가 그 사실을 알 수 있게 하겠다"는 것이 핵심입니다. 즉, 막을 거면 차단 메시지를 보여 주거나 사용 제한을 명시하겠다는 뜻으로 읽힙니다.

## 연구자들이 화난 진짜 이유

Dean Ball 전 백악관 AI 고문은 이번 방식을 "충격적으로 적대적(shockingly hostile)"이라고 표현했습니다. 오픈소스 스타트업 Prime Intellect의 Will Brown은 더 직설적이었습니다. "Anthropic이 대중에게 이렇게 말하는 것처럼 들렸다. '다른 누구도 AI 연구를 할 능력이 있다고 못 믿는다. AI 연구는 우리만 해야 한다.'"

이 두 발언이 핵심을 찌릅니다. 연구자들이 분개한 건 단순히 자기 모델 학습이 막혀서가 아닙니다. 한 회사가 사실상 시장 표준이 되어 가는 모델을 가지고, 어떤 연구는 통과시키고 어떤 연구는 보이지 않게 깎아내릴 권한을 스스로에게 부여했다는 점이 더 큰 문제였습니다.

![30일 보존 정책을 비유한 손그림](/images/anthropic-claude-fable-5-throttling-tradeoff/body-02.png)

## 또 하나의 불씨, 데이터 보존 정책

Fable 5에는 비밀 성능 제한 말고도 갈등 요인이 또 있습니다. 바로 데이터 보존입니다. 회사는 새로운 안전 분류기를 돌리기 위해 사용자의 **프롬프트와 응답을 최대 30일** 동안 보관합니다. 정책 위반이 감지되면 그 기록은 **최대 2년**까지 남습니다.

다른 Claude 모델들이 "데이터 무보존(zero-data-retention)"으로 굴러가는 것과 비교하면 큰 차이입니다. 보안에 민감한 기업 입장에서는 모델 한 종이 갑자기 30일짜리 로그를 만들기 시작한 셈이라, 곧장 거부 반응이 나올 수밖에 없습니다.

The Verge에 따르면 Microsoft는 이 점을 이유로 Fable 5를 사내에서 제한하고 있습니다. 다른 Claude 버전은 그대로 쓰면서도, GitHub Copilot 내부 모델 선택기에서는 Fable 5만 아예 나타나지 않게 했습니다. 코드 한 줄도 외부에 남기지 않으려는 기업 입장에서는 합리적인 선택입니다.

## 실무자가 볼 핵심 포인트

- 같은 모델이라도 호출 출처와 용도에 따라 **응답 품질이 다를 수 있다**는 사실이 이번 사건으로 공식화됐습니다. AI 평가·벤치마크 결과를 인용할 때 "어느 키, 어느 정책 아래에서 측정됐는지"를 함께 기록해 두는 습관이 필요합니다.
- 학습 데이터, 미세조정, 증류(distillation) 목적으로 상용 모델 API를 쓸 때는 **약관(Acceptable Use)을 다시 확인**하세요. 정책 자체가 바뀔 수 있고, 정책이 바뀌면 결과물 신뢰성도 같이 흔들립니다.
- 데이터 보존 정책은 모델 선택의 1순위 체크리스트로 올려야 합니다. **"제로 보존인지", "보존 기간이 며칠인지", "위반 시 얼마나 더 길어지는지"** 세 가지는 계약서에 명시해 두는 편이 안전합니다.
- 사내에서 LLM을 쓰는 팀이라면 모델 한 종에 너무 의존하지 말고, **백업 모델/멀티 프로바이더 구조**를 준비해 두세요. 이번처럼 한 모델만 갑자기 제외해야 하는 상황이 언제든 또 올 수 있습니다.

## 정리하면

이번 사건은 "AI를 만드는 회사도 결국 다른 AI 회사와 경쟁한다"는 당연한 사실을 다시 드러냈습니다. 다만 그 경쟁을 사용자 모르게 모델 품질로 처리하려 한 점이 문제였고, Anthropic도 그 부분을 인정했습니다. 정책은 바뀌었지만, 데이터 보존 같은 다른 균열은 그대로 남아 있습니다. 다음 모델이 나올 때 다시 비슷한 토론이 반복될 가능성이 높습니다.

## 원문 출처

*Maximilian Schreiner, "Claude Fable 5: Anthropic admits 'wrong tradeoff' after invisibly throttling rival AI researchers", THE DECODER, 2026-06-11. <https://the-decoder.com/claude-fable-5-anthropic-admits-wrong-tradeoff-after-invisibly-throttling-rival-ai-researchers/>*
