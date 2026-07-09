# MaskLoom — Distributional Bias Probing for LLM and Agent Failures

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 무작위 마스킹 진단을 통해 불안정한 LLM 및 에이전트 결정을 조사합니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

MaskLoom은 LLM, RAG 시스템 및 도구 사용 에이전트가 불안정하거나 편향된 선택을 하는 이유를 이해하기 위한 진단 도구 키트입니다. 실패한 예를 하나씩 수동으로 조사하는 대신 동일한 입력의 여러 마스킹 변형을 실행하고 출력 분포의 변화를 측정합니다.

이 방법은 두 가지 일반적인 실패 모드를 구분하는 데 도움이 됩니다. 시스템에 필요한 지식이 부족하거나 오해의 소지가 있는 단서, 문장, 답 선택 또는 도구 설명에 과도하게 가중치를 둘 수 있습니다. 이러한 구별은 올바른 수정이 원인에 따라 달라지기 때문에 중요합니다.

MaskLoom은 이러한 조사를 구조화된 보고서로 변환하여 평가 파이프라인, 회귀 테스트, 대시보드 및 인간 검토 워크플로를 지원합니다.

**누구를 위한 건가요.** MaskLoom은 AI 엔지니어, 평가 팀, RAG 빌더, 에이전트 개발자 및 모델 또는 에이전트 동작이 프롬프트, 컨텍스트, 후보, 경로 또는 도구에 따라 어떻게 변하는지에 대한 실질적인 증거가 필요한 연구원을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "schema_version": "maskloom.report.v1",
  "probe": {
    "trials_requested": 12,
    "trials_completed": 12,
    "mask_probability": 0.25,
    "seed": 1337,
    "selector": "builtin"
  },
  "input_summary": {
    "prompt_token_count": 5,
    "candidate_count": 3
  },
  "baseline": {
    "selected_id": "billing",
    "scores": {
      "billing": 3.0,
      "support": 2.0,
      "sales": 2.0
    }
  },
  "selection_distribution": [
    {
      "id": "billing",
      "count": 8,
      "rate": 0.6667
    },
    {
      "id": "support",
      "count": 2,
      "rate": 0.1667
    },
    {
      "id": "sales",
      "count": 2,
      "rate": 0.1667
    }
  ],
  "sensitive_spans": [
    {
      "source": "candidate:support",
      "token": "login",
      "masked_count": 2,
      "changed_count": 2,
      "change_rate": 1.0
    },
    {
      "source": "candidate:billing",
      "token": "receipt",
      "masked_count": 3,
      "changed_count": 2,
      "change_rate": 0.6667
    },
    {
      "source": "prompt",
      "token": "refund",
      "masked_count": 3,
      "changed_count": 2,
      "change_rate": 0.6667
    },
    {
      "source": "candidate:billing",
      "token": "handle",
      "masked_count": 5,
      "changed_count": 3,
      "change_rate": 0.6
    },
    {
      "source": "candidate:support",
      "token": "support",
      "masked_count": 5,
      "changed_count": 3,
      "change_rate": 0.6
    },
    {
      "source": "prompt",
      "token": "invoice",
      "masked_count": 7,
      "changed_count": 4,
      "change_rate": 0.5714
    },
    {
      "source": "candidate:support",
      "token": "route",
      "masked_count": 4,
      "changed_count": 2,
      "change_rate": 0.5
    },
    {
      "source": "candidate:billing",
      "token": "invoice",
      "masked_count": 2,
      "changed_count": 1,
      "change_rate": 0.5
    },
    {
      "source": "candidate:billing",
      "token": "refund",
      "masked_count": 2,
      "changed_count":
… (+17770 chars truncated)
```

## 요구 사항

| Key | Value |
|---|---|
| 파이썬 | 3.9+ |
| 의존성 | 파이썬 표준 라이브러리만 |
| API 키 | 필요 없음 |

## 📦 설치

**1) Claude Code / OpenClaw 스킬로**

```bash
# 개인용 (모든 프로젝트에서 사용)
git clone https://github.com/TechLLM/TechLLM.github.io /tmp/techllm-skills
mkdir -p ~/.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
cp -r /tmp/techllm-skills/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/* ~/.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/

# 프로젝트 로컬
mkdir -p .claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
cp -r /tmp/techllm-skills/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/* .claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: mask-probe [-h] [--input INPUT] [--output OUTPUT] [--trials TRIALS]
                  [--mask-probability MASK_PROBABILITY] [--seed SEED]
                  [--command-template COMMAND_TEMPLATE] [--selftest]

Run deterministic MaskLoom masking probes for LLM, RAG, or agent selection
failures.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Path to probe input JSON.
  --output OUTPUT, -o OUTPUT
                        Write JSON report to this path instead of stdout.
  --trials TRIALS       Number of masking trials to run.
  --mask-probability MASK_PROBABILITY
                        Probability of masking each token span in prompt and
                        candidates.
  --seed SEED           Random seed for deterministic masking.
  --command-template COMMAND_TEMPLATE
                        Optional local command template. Supported
                        placeholders: {prompt}, {masked_prompt},
                        {candidates_json}, {masked_candidates_json},
                        {trial_json}.
  --selftest            Run the built-in sample probe with no API key.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 프롬프트, 검색된 컨텍스트, 후보 답변 또는 도구 설명의 무작위 마스킹 변형을 생성합니다.
- 대상 모델, 파이프라인 또는 에이전트를 반복된 탐색 시험에 걸쳐 다시 실행합니다.
- 관찰된 선택을 집계하여 동작이 안정적으로 유지되는지 또는 특정 후보로 수렴되는지 보여줍니다.
- 마스킹이 출력을 변화시키는 정도를 측정하여 어떤 토큰이나 범위가 민감한지 추정합니다.
- 감사, CI 검사, 실험 추적 및 검토 워크플로를 위한 JSON 우선 보고서를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 탐색 결과가 노이즈가 있거나 일관성이 없습니다. | 대상 시스템이 비결정적일 수 있고, 탐색 횟수가 너무 적거나, 마스킹된 범위가 너무 거칠 수 있습니다. | 시도 횟수를 늘리고, 가능한 경우 모델의 무작위성을 줄이며, 더 작거나 더 표적화된 마스킹 단위를 사용하세요. |
| 보고서가 많은 편향 의심 후보를 표시합니다. | 후보 세트에 중복된 증거, 중복된 단어 또는 형식 차이로 인한 선택 인공물이 포함될 수 있습니다. | 후보 형식을 정규화하고, 거의 중복된 항목을 제거하고, 탐색을 다시 실행하여 민감도 패턴이 유지되는지 확인하세요. |
| 마스킹이 작업을 너무 많이 변경합니다. | 일부 마스킹된 범위가 오해의 소지가 있는 단서를 분리하는 대신 필수 정보를 제거할 수 있습니다. | 더 좁은 마스킹을 사용하고, 작업에 중요한 구조를 보존하며, 마스킹되지 않은 기준선과 결과를 비교하세요. |

## 자주 묻는 질문

**MaskLoom은 평가 벤치마크인가요?**

아니오. 이는 진단 도구 키트입니다. 대상 시스템의 불안정하거나 편향된 동작을 설명하는 데 도움이 되지만, 작업 수준의 정확성, 안전성 또는 신뢰성 평가를 대체하지는 않습니다.

**에이전트 및 도구와 함께 작동할 수 있나요, 단순한 LLM 프롬프트만 가능한가요?**

예. 명령 템플릿 실행 모델은 로컬 스크립트, API 래퍼, 에이전트 실행기, 벤치마크 하니스 및 도구 라우팅 시스템을 탐색하도록 설계되었습니다.

**선택 분포 보고서는 저에게 무엇을 말해줍니까?**

시스템이 마스킹된 시험에서 각 후보, 경로, 도구, 답변 또는 작업을 선택하는 빈도를 보여줍니다. 큰 변화는 부서지기 쉬운 의사 결정 또는 특정 단서에 대한 과도한 의존성을 드러낼 수 있습니다.

**민감한 토큰이 항상 모델이 잘못되었다는 것을 의미하나요?**

아니오. 민감한 토큰은 합법적인 증거일 수 있습니다. MaskLoom은 동작이 변화하는 위치를 강조하여 검토자가 해당 민감도가 유용한 정보인지 아니면 오해의 소지가 있는 편향인지를 결정할 수 있도록 합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/` 또는 `.claude/skills/maskloom-distributional-bias-probing-for-llm-and-agent-failu/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
