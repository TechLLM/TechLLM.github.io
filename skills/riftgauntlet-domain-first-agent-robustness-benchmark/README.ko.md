# RiftGauntlet — Domain-First Agent Robustness Benchmark

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 에이전트가 무너지는 지점을 드러내고, 모든 실패를 재현 가능한 안전장치로 바꾸세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

RiftGauntlet는 조건이 예상에서 벗어날 때 에이전트가 얼마나 안정적으로 동작하는지 테스트하기 위한 오픈소스 벤치마크입니다. 도메인 변화, 불완전한 맥락, 손상된 관찰값, 도구 장애, 지연, 그리고 순서가 뒤바뀐 이벤트 등으로 인한 실패를 평가합니다.

평균 점수 하나로 약점을 가리는 대신, RiftGauntlet는 어떤 도메인과 교란(perturbation) 구간에서 에이전트나 라우터가 무너지는지를 보여줍니다. 또한 시스템이 기록된 신뢰도, 회피(abstention), 위험 신호를 통해 그러한 실패를 인식하는지 여부도 측정합니다.

이렇게 도출된 실패 구간은 결정론적인 회귀 테스트 픽스처가 되어, 팀이 약점을 재현하고 이후 개발 과정에서 같은 문제가 다시 나타나는 것을 방지하는 데 도움이 됩니다.

**누구를 위한 건가요.** RiftGauntlet는 도구를 사용하는 에이전트, 라우터, 병렬 에이전트 워크플로, 그리고 적응형 계획 시스템을 구축하는 팀에 도움이 됩니다. 특히 배포 전에 견고성에 대한 근거가 필요한 연구원, 평가 엔지니어, 플랫폼 팀에 유용합니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/riftgauntlet-domain-first-agent-robustness-benchmark
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "domains": [
    {
      "baseline_samples": 1,
      "baseline_success_rate": 1.0,
      "baseline_successes": 1,
      "domain": "finance",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 2,
      "perturbed_success_rate": 0.0,
      "perturbed_successes": 0,
      "robustness_delta": -1.0,
      "source_domains": [
        "finance"
      ]
    },
    {
      "baseline_samples": 1,
      "baseline_success_rate": 1.0,
      "baseline_successes": 1,
      "domain": "support",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 2,
      "perturbed_success_rate": 0.0,
      "perturbed_successes": 0,
      "robustness_delta": -1.0,
      "source_domains": [
        "support"
      ]
    },
    {
      "baseline_samples": 1,
      "baseline_success_rate": 1.0,
      "baseline_successes": 1,
      "domain": "travel",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 2,
      "perturbed_success_rate": 0.0,
      "perturbed_successes": 0,
      "robustness_delta": -1.0,
      "source_domains": [
        "travel"
      ]
    },
    {
      "baseline_samples": 0,
      "baseline_success_rate": null,
      "baseline_successes": 0,
      "domain": "unknown",
      "matched_baseline_success_rate": 1.0,
      "perturbed_samples": 1,
      "perturbed_success_rate": 1.0,
      "perturbed_successes": 1,
      "robustness_delta": 0.0,
      "source_domains": [
        "finance"
      ]
    }
  ],
  "failure_detection": {
    "auroc_proxy": 0.5,
    "failure_cases": 6,
    "scorable_cases": 7,
    "score_sources": {
      "abstention": 2,
      "confidence": 3,
      "risk_score": 2
    },
    "success_cases": 1
  },
  "schema_version": "1.0",
  "slices": [
    {
      "baseline_success_rate": 1.0,
      "domain": "travel",
      "perturbations": [
        "delay"
      ],
      "robustness_delta": -1.0,
      "samples": 1,
      "scenario": "delayed-result",
      "source_domains": [
        "travel"
      ],
      
… (+3946 chars truncated)
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
mkdir -p ~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark
cp -r /tmp/techllm-skills/skills/riftgauntlet-domain-first-agent-robustness-benchmark/* ~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/

# 프로젝트 로컬
mkdir -p .claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark
cp -r /tmp/techllm-skills/skills/riftgauntlet-domain-first-agent-robustness-benchmark/* .claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/riftgauntlet-domain-first-agent-robustness-benchmark
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/riftgauntlet-domain-first-agent-robustness-benchmark/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--spec SPEC] [--worst-limit WORST_LIMIT]
              [--output OUTPUT] [--fixtures-dir FIXTURES_DIR] [--force]
              [--selftest]

Replay JSONL agent traces under declarative perturbations and report domain-
first robustness metrics. No network or API key is required.

options:
  -h, --help            show this help message and exit
  --input INPUT         path to a JSONL trace file
  --spec SPEC           path to a JSON perturbation specification
  --worst-limit WORST_LIMIT
                        number of worst slices to rank (default: env
                        RIFTGAUNTLET_WORST_LIMIT or 5)
  --output OUTPUT       write the report to this file instead of stdout
  --fixtures-dir FIXTURES_DIR
                        export worst slices as regression fixture JSON files
  --force               allow explicitly requested output or fixture files to
                        be overwritten
  --selftest            run the offline built-in sample and verify stable
                        metrics
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 실제로 모델을 호출하지 않고, 이식 가능한 JSONL 실행 트레이스를 그대로 재실행합니다.
- 도구 결과와 관찰값 시퀀스에 결측, 형식 오류, 지연, 중복, 잘림, 순서 뒤바뀜 등 선언적 교란을 적용합니다.
- 도메인과 교란 구간별로 결과를 묶어, 교란을 적용하지 않은 기준선 대비 성공률을 비교합니다.
- 성능, 샘플 수, 성능 저하를 기준으로 약한 구간을 순위 매겨, 중요한 실패가 묻히지 않도록 합니다.
- 기록된 신뢰도, 회피, 위험 점수를 바탕으로 실패 탐지 품질을 추정하고, 약한 구간을 결정론적인 회귀 테스트 픽스처로 내보냅니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 교란이 적용될 사례를 찾지 못합니다. | 명세(spec)가 트레이스에 실제로 존재하지 않는 이벤트, 도메인, 관찰값 구조를 대상으로 하고 있습니다. | 트레이스 기록에 의도한 도메인 레이블과 이벤트 유형이 포함되어 있는지 확인하고, 교란 기준을 기록된 구조에 맞게 조정하세요. |
| 실패 탐지 결과를 사용할 수 없거나 신뢰할 수 없습니다. | 트레이스에 일관된 신뢰도, 회피, 위험 점수가 없거나, 기록 간에 점수의 방향성이 서로 다릅니다. | 평가 대상인 모든 트레이스에 대해 명확하게 정의된 신호 하나를 기록하고, 그 의미와 척도를 도메인 전체에서 일관되게 유지하세요. |
| 평가할 때마다 가장 성능이 낮은 구간이 달라집니다. | 트레이스 세트, 교란 선택, 무작위화, 또는 구간 정의가 안정적이지 않습니다. | 고정된 입력과 결정론적인 교란 설정을 사용하고, 회귀 테스트 픽스처에 정확한 구간 정의를 보존하세요. |
| 어떤 구간은 심각해 보이지만 샘플이 매우 적습니다. | 낮은 성공률이 충분한 근거 없이 도출된 것입니다. | 성능과 함께 샘플 수를 함께 검토하고, 더 representative한 트레이스를 수집하며, 샘플이 부족한 구간을 결론적인 증거로 다루지 마세요. |

## 자주 묻는 질문

**RiftGauntlet는 실제 모델이나 도구 호출이 필요한가요?**

아닙니다. 기록된 실행 트레이스를 재실행하고 그 관찰값을 변형하기 때문에, 오프라인에서도 반복 가능한 평가가 가능합니다.

**왜 도메인 단위와 구간(slice) 단위 결과를 함께 보고하나요?**

집계된 평균 점수는 드문 도메인이나 조건에서 발생하는 치명적인 실패를 가릴 수 있기 때문입니다. 구간 단위 보고는 이러한 약점을 가시화합니다.

**실패 탐지 AUROC 프록시(proxy)는 무엇을 측정하나요?**

기록된 신뢰도, 회피, 위험 신호가 평가된 트레이스들에서 성공 실행과 실패를 얼마나 잘 구분하는지를 추정합니다.

**에이전트나 라우팅 전략을 서로 비교할 수 있나요?**

네. 동일한 트레이스와 교란 정의를 사용해 평가된 시스템들은 기준 성능, 견고성 저하, 최약 구간, 실패 인식 수준으로 비교할 수 있습니다.

**회귀 테스트 픽스처는 어떤 도움이 되나요?**

관찰된 약점의 결정론적인 예시를 보존해 두어, 지속적 통합 환경에서 특정 도메인의 실패가 다시 나타나는지를 감지할 수 있게 해줍니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/` 또는 `.claude/skills/riftgauntlet-domain-first-agent-robustness-benchmark/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
