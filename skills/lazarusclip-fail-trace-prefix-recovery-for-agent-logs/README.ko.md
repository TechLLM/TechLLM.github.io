# LazarusClip — fail-trace prefix recovery for agent logs

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 실패한 에이전트 실행 안에 숨어 있는 건전한 추론을 구출해내세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

최신 LLM 에이전트는 엄청난 양의 실행 트레이스를 만들어내지만, 대부분의 학습 파이프라인은 그중에서도 깔끔하게 완료된 극히 일부만을 사용합니다. 실패한 실행은 보통 도구 오류, 환각, 또는 정책 위반으로 트레이스가 중단된 경우에도, 그 직전까지 이어진 긴 유효한 추론 구간이 있었음에도 통째로 버려집니다. 이렇게 버려진 접두부(prefix)가 바로 RLHF, RFT, GRPO 스타일 학습 루프가 목마르게 찾는 고신호 데이터입니다.

LazarusClip은 Fatal-aware GRPO의 핵심 통찰을 손실 함수에서 데이터 계층으로 끌어올립니다. 트레이너 내부에서 실패 이후 토큰을 마스킹하는 대신, 완료된 트레이스를 검사하여 결과의 신뢰성이 무너지는 첫 단계를 찾아내고, 그 경계 이후의 모든 내용을 정밀하게 잘라냅니다. 살아남은 접두부는 1급(first-class) 신뢰도 점수가 매겨진 아티팩트로 반환되어, 기존의 positive-only 필터와 경쟁하지 않고 자연스럽게 결합됩니다. 이를 통해 실패한 실행 안에 숨어 있는 고품질 접두부까지 구출할 수 있는 범위를 확장합니다.

**누구를 위한 건가요.** 리플레이 버퍼, 포스트모템 디렉터리, 또는 에이전트 평가 하네스를 관리하는 ML 엔지니어, RL 연구자, 데이터 큐레이터를 위해 만들어졌습니다. GRPO, PPO, 또는 리젝션 샘플링으로 모델을 파인튜닝하면서, 실패한 트레이스에 더 많은 활용 가능한 신호가 있기를 늘 바라셨다면 LazarusClip이 그 죽은 실행의 묘지를 생산적인 학습 데이터의 원천으로 바꾸어 드립니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
python scripts/run.py --selftest
```

**예상 출력:**

```text
[PASS] tool-failure boundary is step 3
[PASS] tool-failure label is recoverable
[PASS] prefix keeps 3 steps
[PASS] tail masks 2 steps
[PASS] mask hints agree
[PASS] confidence is high
[PASS] clean trace has no boundary
[PASS] clean trace label is clean
[PASS] refusal at step 1 is poisoned
[PASS] output is deterministic
[PASS] empty steps rejected

11/11 checks passed
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
mkdir -p ~/.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
cp -r /tmp/techllm-skills/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/* ~/.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/

# 프로젝트 로컬
mkdir -p .claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
cp -r /tmp/techllm-skills/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/* .claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input FILE | --batch DIR | --selftest]
              [--judge {offline,openai,anthropic,ollama}] [--passes PASSES]
              [--min-prefix-steps MIN_PREFIX_STEPS] [--timeout TIMEOUT]
              [--output FILE] [--force] [--indent INDENT]

LazarusClip: recover the salvageable pre-failure prefix of agent traces.

options:
  -h, --help            show this help message and exit
  --input FILE          trace JSON file ('-' reads stdin)
  --batch DIR           directory of *.json traces to triage
  --selftest            run offline selftest and exit
  --judge {offline,openai,anthropic,ollama}
                        judge backend (default: offline, no network)
  --passes PASSES       self-consistency passes for confidence calibration
                        (default: 3)
  --min-prefix-steps MIN_PREFIX_STEPS
                        minimum surviving prefix length to call a trace
                        recoverable
  --timeout TIMEOUT     per-request timeout in seconds for remote judges
  --output FILE         write JSON here instead of stdout
  --force               allow --output to overwrite a file
  --indent INDENT       JSON indent (default: 2)

Example: python scripts/run.py --input
examples/input/trace_tool_failure.input.json
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 하이브리드 fatal 경계 탐지기가 LLM 판단, 일반적인 도구 오류를 위한 엄선된 정규식 어휘, 그리고 트래젝토리 길이나 도구 호출 반환 코드 같은 구조적 휴리스틱을 결합하여, 처음으로 신뢰할 수 없는 단계를 정확히 짚어냅니다.
- 복원된 트레이스는 실패 이전 서브그래프와 마스킹된 꼬리로 나뉘며, fatal_step_index, confidence, 그리고 recoverable, poisoned, ambiguous 중 하나로 제안된 라벨을 담은 스키마가 안정적인 JSON 레코드로 출력됩니다.
- 플러그인 방식의 judge 백엔드를 통해 OpenAI, Anthropic, 로컬 Ollama 모델, 또는 에어갭 환경에서 사용할 수 있는 완전 오프라인 정규식 전용 경로로 채점을 라우팅할 수 있습니다.
- 토큰 단위 마스킹 힌트가 트레이스와 함께 출력되므로, 트레이너를 다시 작성할 필요 없이 GRPO, PPO, 리젝션 샘플링 파인튜닝 루프에 바로 투입할 수 있습니다.
- 자기 일관성(self-consistency) 캘리브레이션이 N개의 독립적인 judge 패스를 실행하고 일치도 점수를 보고하여, 다운스트림 소비자가 복원된 접두부 중 어느 것을 학습에 활용할지 결정할 수 있는 원칙적인 임계값을 제공합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 회복 가능하다고 예상했던 실행에서 신뢰도 점수가 거의 0으로 나옵니다. | judge 패스들이 fatal 경계의 위치에 대해 의견이 일치하지 않았기 때문이며, 보통 도구 오류에서 복구된 뒤 부드러운 정책 드리프트가 이어지는 식으로 트레이스에 신호가 섞여 있을 때 발생합니다. | self-consistency 패스 횟수를 늘리거나, 더 강력한 judge 백엔드로 LazarusClip을 실행하여 신뢰도가 보고되기 전에 경계 투표를 안정화시키세요. |
| 에이전트가 복구한 경우에도 오프라인 모드가 모든 도구 오류를 fatal 경계로 표시합니다. | 정규식 전용 백엔드는 의도적으로 보수적으로 작동하며, LLM judge라면 고려했을 다운스트림의 결과를 인식하지 못합니다. | 가능하다면 로컬 모델 백엔드로 전환하거나, 정규식 규칙을 무시하고자 하는 특정 복구 가능한 오류 패턴을 화이트리스트에 추가하세요. |
| 복원된 접두부가 너무 짧아 파인튜닝에 유용하지 않습니다. | 트래젝토리 초반에 fatal 경계가 탐지되었기 때문이며, 종종 구조적 휴리스틱이 무해한 도구 재시도에 과도하게 반응했기 때문입니다. | 해당 도메인의 휴리스틱 가중치를 검토하고, 에이전트가 일시적인 도구 실패에서 정상적으로 복구하는 경우라면 초기 단계 패널티를 비활성화하세요. |

## 자주 묻는 질문

**실패한 실행을 단순히 걸러내는 것과 무엇이 다른가요?**

필터링은 올바른 추론까지 포함해 트레이스 전체를 버립니다. LazarusClip은 결과의 신뢰성이 무너지기 전까지의 접두부는 그대로 보존하고 그 이후만 잘라내므로, 노이즈를 늘리지 않으면서도 활용 가능한 학습 데이터셋을 크게 확장합니다.

**LazarusClip은 제 트레이너를 수정하나요?**

아닙니다. 데이터 계층에서 작동하며, 기존 GRPO, PPO, 리젝션 샘플링 루프가 바로 소비할 수 있는 마스킹 힌트와 신뢰도 점수를 출력합니다.

**트레이스를 클라우드 LLM으로 보내지 않고도 사용할 수 있나요?**

네. 완전 오프라인 정규식 전용 모드와 로컬 Ollama 모델 지원이 갖춰져 있어, 민감한 에이전트 로그는 자체 인프라에 그대로 둘 수 있습니다.

**suggested_label 필드는 무엇을 의미하나요?**

이는 거친 분류 태그입니다. 학습에 활용할 만한 깨끗한 접두부에는 recoverable, 실패의 오염이 뒤쪽으로 확산되었을 가능성이 높은 트레이스에는 poisoned, judge들이 의견 일치에 도달하지 못한 경우엔 ambiguous가 붙습니다.

**경계 탐지의 정확도는 어느 정도인가요?**

정확도는 self-consistency 패스 횟수와 judge 백엔드의 강도에 비례합니다. 운영 환경의 사용자는 보통 여러 패스를 돌리고, 단일 결과를 진실로 취급하기보다 일치도 점수를 기준으로 임계값을 정합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/` 또는 `.claude/skills/lazarusclip-fail-trace-prefix-recovery-for-agent-logs/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
