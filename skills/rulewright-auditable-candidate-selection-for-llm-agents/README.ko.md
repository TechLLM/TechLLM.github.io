# Rulewright — Auditable Candidate Selection for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> LLM 후보 선택을 명시적이고 검사 가능하며 재현 가능하게 만듭니다.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

Rulewright는 LLM 후보 선택을 더 쉽게 이해하고 감사할 수 있도록 제안된 라이브러리와 CLI입니다. 이를 통해 조용한 모델 선택을 대신하여 나중에 검사할 수 있는 가시적인 선택 과정으로 대체할 수 있습니다.

모델에게 한 단계의 불투명한 과정으로 최상의 문서, 도구, 답변 또는 행동을 선택하도록 요청하는 대신, Rulewright는 작업을 두 단계로 분리합니다. 먼저, 구조화된 비교 정책을 생성합니다. 그런 다음 해당 정책을 각 후보에 적용하고 기계가 읽을 수 있는 선택 결과를 반환합니다.

이렇게 하면 팀이 개인적인 추론 텍스트를 저장하지 않고도 지속 가능한 결정 추적을 얻을 수 있습니다. 에이전트 행동이 디버깅, 모델 버전 간 비교, 재현 또는 나중에 설명이 필요할 때 유용합니다.

**누구를 위한 건가요.** Rulewright는 후보 선택이 설명 가능하고 반복 가능하며 검토에 안전해야 하는 검색 시스템, 도구 라우팅 에이전트, 답변 평가자, 데이터 세트 큐레이션 파이프라인 및 기타 LLM 워크플로를 구축하는 팀을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/rulewright-auditable-candidate-selection-for-llm-agents
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "selected_ids": [
    "doc-rules-first"
  ],
  "top_score": 0.775
}
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
mkdir -p ~/.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents
cp -r /tmp/techllm-skills/skills/rulewright-auditable-candidate-selection-for-llm-agents/* ~/.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/

# 프로젝트 로컬
mkdir -p .claude/skills/rulewright-auditable-candidate-selection-for-llm-agents
cp -r /tmp/techllm-skills/skills/rulewright-auditable-candidate-selection-for-llm-agents/* .claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/rulewright-auditable-candidate-selection-for-llm-agents
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/rulewright-auditable-candidate-selection-for-llm-agents/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--rules-in RULES_IN]
              [--rules-out RULES_OUT] [--matrix-out MATRIX_OUT]
              [--selected-out SELECTED_OUT] [--selftest]

Generate auditable candidate-selection artifacts for LLM agents.

options:
  -h, --help            show this help message and exit
  --input INPUT         JSON file containing query and candidates.
  --rules-in RULES_IN   Replay with an existing rules.yaml file.
  --rules-out RULES_OUT
                        Write generated rules.yaml to this path.
  --matrix-out MATRIX_OUT
                        Write decision_matrix.json to this path.
  --selected-out SELECTED_OUT
                        Write selected_ids.json to this path.
  --selftest            Run the built-in sample without external services.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 사용자 쿼리와 후보 집합이 선택 컨텍스트로 제공됩니다.
- Rulewright는 차원, 가중치, 제약 조건 및 거부 조건을 포함하는 명시적인 비교 정책을 생성합니다.
- 각 후보는 저장된 정책에 대해 별도의 결정 단계에서 평가됩니다.
- 결과는 점수, 증거 및 통과/실패 판단이 포함된 구조화된 결정 행렬입니다.
- 선택된 후보 식별자가 기계가 읽을 수 있는 형태로 반환되어 다운스트림 시스템에서 사용됩니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 실행 간에 선택이 일관성 없어 보입니다. | 비교 정책이 매번 다시 생성되어 모델이 점수 매기기 전에 기준을 변경할 수 있습니다. | 재현을 위해 저장된 규칙 아티팩트를 사용하여 후보가 동일한 정책에 대해 평가되도록 합니다. |
| 높은 점수를 받은 후보가 여전히 거부됩니다. | 정책에 가중치 점수보다 우선하는 하드 제약 조건 또는 거부 조건이 포함될 수 있습니다. | 규칙 아티팩트와 결정 행렬을 검사하여 어떤 조건이 거부되었는지 확인합니다. |
| 결정 추적이 해석하기 어렵습니다. | 생성된 정책이 너무 광범위하거나 모호하거나 도메인별 기준이 누락되었을 수 있습니다. | 선택 컨텍스트를 구체화하여 규칙 생성 단계에서 더 명확한 기대치와 제약 조건을 갖도록 합니다. |

## 자주 묻는 질문

**왜 규칙 생성을 후보 점수 매기기에서 분리하나요?**

단계를 분리하면 적용 전에 선택 기준이 명확해집니다. 이를 통해 예기치 않은 선택을 디버깅하고, 모델 간의 행동을 비교하며, 이후에 결정을 재현하는 것이 더 쉬워집니다.

**Rulewright는 모델 추론을 저장하나요?**

아니요. 목표는 개인적인 연쇄적 사고 텍스트가 아닌 규칙, 점수, 증거 참조 및 선택된 식별자와 같은 구조화된 아티팩트를 보존하는 것입니다.

**같은 규칙을 재사용할 수 있나요?**

네. 저장된 규칙을 사용하여 동일한 후보를 다시 평가하거나 동일한 정책 하에서 변경된 후보 집합을 점수 매길 수 있습니다.

**어떤 종류의 후보를 순위를 매길 수 있나요?**

Rulewright는 문서, 도구, 생성된 답변, 제안된 행동, 데이터 세트 레코드 또는 구조화된 메타데이터와 콘텐츠로 표현할 수 있는 모든 후보 객체를 위해 설계되었습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/` 또는 `.claude/skills/rulewright-auditable-candidate-selection-for-llm-agents/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
