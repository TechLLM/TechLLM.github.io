# TraceLoom — Positive Execution Trace Miner for Agent Routing

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 검증된 에이전트의 성공을 라우팅 준비가 된 학습 데이터로 변환하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

TraceLoom은 성공적인 LLM 에이전트 실행을 깨끗하고 재사용 가능한 데이터셋으로 전환하기 위한 제안된 오픈 소스 CLI입니다. 검증을 통과한 추적에 중점을 두어, 팀이 이미 작동하는 워크플로우에서 배울 수 있도록 합니다.

실패 분류학, 부정적인 롤아웃 레이블 또는 모든 나쁜 행동에 대한 상세한 패널티부터 시작하는 대신, TraceLoom은 완료된 실행에서 긍정적인 신호를 추출합니다. 어떤 도구가 어떤 순서로 사용되었는지, 어떤 파일이나 컨텍스트 소스가 중요한지, 그리고 성공과 관련된 조건이 무엇인지를 식별하는 데 도움을 줍니다.

출력은 실용적인 다운스트림 사용을 위해 설계되었습니다: 민감한 프롬프트, 개인 파일 내용 또는 내부 시스템 세부 정보를 노출하지 않으면서 라우터, 프롬프트 선택기, 정책 휴리스틱, 검색 계획자 및 평가 워크플로우를 개선합니다.

**누구를 위한 건가요.** TraceLoom은 이미 실행 로그와 검증 결과를 생성하는 AI 에이전트를 구축, 평가 또는 운영하는 팀을 위한 것입니다. 특히 에이전트 플랫폼 엔지니어, 평가 팀, 응용 연구원 및 실제 성공적인 실행에서 라우팅 준비가 된 학습 데이터를 원하는 오픈 소스 유지 관리자에게 유용합니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/traceloom-positive-execution-trace-miner-for-agent-routing
python scripts/run.py --selftest
```

**예상 출력:**

```text
{"task_id":"task-alpha","run_id":"run-001","success_condition":"passed=true; score=1.0","tool_sequence":["file.read","search.query","file.write","test.run"],"tool_calls":[{"order":2,"tool":"file.read","argument_summary":{"path":"src/router.py"}},{"order":3,"tool":"search.query","argument_summary":{"query":{"chars":23,"words":3},"top_k":3}},{"order":4,"tool":"file.write","argument_summary":{"content":{"redacted":true,"chars":30},"path":"src/router.py"}},{"order":5,"tool":"test.run","argument_summary":{"command":{"program":"python","arg_count":3,"chars":37}}}],"file_patterns":{"read":["src/router.py"],"write":["src/router.py"],"touched":["src/router.py"]},"retrieval_paths":[{"order":1,"source":"docs/router-policy.md","query_summary":{"chars":26,"words":3}}],"routing_signals":{"tool_count":4,"retrieval_count":1,"file_count":1,"normalized_tool_path":"file.read>search.query>file.write>test.run"}}
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
mkdir -p ~/.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing
cp -r /tmp/techllm-skills/skills/traceloom-positive-execution-trace-miner-for-agent-routing/* ~/.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/

# 프로젝트 로컬
mkdir -p .claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing
cp -r /tmp/techllm-skills/skills/traceloom-positive-execution-trace-miner-for-agent-routing/* .claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/traceloom-positive-execution-trace-miner-for-agent-routing
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/traceloom-positive-execution-trace-miner-for-agent-routing/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--traces TRACES] [--graders GRADERS]
              [--format {jsonl,csv}] [--output OUTPUT] [--min-score MIN_SCORE]
              [--selftest]

Mine verified successful LLM agent traces into positive routing datasets.

options:
  -h, --help            show this help message and exit
  --traces TRACES       Path to execution trace JSONL input.
  --graders GRADERS     Path to grader or verifier JSON input.
  --format {jsonl,csv}  Output format. Defaults to TRACELOOM_OUTPUT_FORMAT or
                        jsonl.
  --output OUTPUT       Optional output file path. Defaults to stdout.
  --min-score MIN_SCORE
                        Minimum score for success when score is present.
                        Defaults to TRACELOOM_MIN_SCORE or 1.0.
  --selftest            Run on built-in mock data with no API key or external
                        files.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 실행 추적 기록과 채점자 또는 검증자 결과를 수집합니다.
- 완료된 작업을 검증 결과와 일치시킵니다.
- 성공적인 실행을 필터링한 후 라우팅 신호를 추출합니다.
- 도구 시퀀스, 정규화된 도구 이름, 인자 패턴, 파일 사용, 검색 경로 및 성공 조건을 요약합니다.
- 라우터 학습, 프롬프트 선택, 분석 또는 평가 워크플로우에 적합한 구조화된 데이터셋을 내보냅니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 성공적인 추적이 내보내지지 않았습니다. | 추적 기록이 검증 결과와 일치하지 않거나, 검증 데이터가 어떤 실행도 통과한 것으로 표시하지 않을 수 있습니다. | 입력 간에 작업 식별자가 일관적인지 확인하고, 성공적인 결과가 검증 결과에 표현되어 있는지 확인하세요. |
| 데이터셋에서 도구 이름이 일관적이지 않게 나타납니다. | 다른 에이전트 또는 로깅 계층이 동일한 도구를 다른 이름으로 기록할 수 있습니다. | 일관된 정규화 전략을 사용하여 동등한 도구가 안정적인 이름 아래에 그룹화되도록 하세요. |
| 내보낸 행에 예상보다 적은 세부 정보가 포함되어 있습니다. | TraceLoom은 민감한 프롬프트, 원시 파일 내용 또는 개인 내부 컨텍스트에 의존하지 않도록 설계되었습니다. | 소스 추적에서 사용 가능한 메타데이터를 검토하고, 마이닝하기 전에 로그에 안전한 라우팅 관련 필드를 포함하세요. |

## 자주 묻는 질문

**왜 TraceLoom은 성공적인 실행에만 집중하나요?**

성공적인 실행은 더 깨끗하고 신뢰하기 쉬운 신호를 제공합니다. 이는 팀이 먼저 완전한 실패 레이블링 시스템을 설계할 필요 없이 어떤 경로, 도구, 파일 및 검색 선택이 검증된 결과를 이끌었는지 보여줍니다.

**이것을 모델 학습에 사용할 수 있나요?**

네, 내보낸 JSONL 또는 CSV 데이터는 라우터 학습, 프롬프트 선택, 휴리스틱 조정, 검색 계획 및 평가 분석을 지원할 수 있습니다. 이는 전체 롤아웃 평가를 대체하는 것이 아니라 에이전트 결정 시스템을 위한 구조화된 학습 데이터로 의도되었습니다.

**TraceLoom은 개인 프롬프트나 파일 내용을 저장해야 하나요?**

아니오. 이 프로젝트는 요약, 메타데이터, 도구 순서, 파일 상호작용 패턴, 검색 경로 및 성공 조건을 중심으로 설계되어, 팀이 민감한 내용을 노출하지 않고도 유용한 라우팅 데이터를 마이닝할 수 있습니다.

**이것은 대규모 에이전트 팀에만 유용한가요?**

아니오. 소규모 팀은 어떤 워크플로우가 작동하는지 이해하는 데 사용할 수 있고, 대규모 팀은 라우팅, 정책 및 평가 개선을 위한 반복 가능한 데이터셋을 구축하는 데 사용할 수 있습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/` 또는 `.claude/skills/traceloom-positive-execution-trace-miner-for-agent-routing/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
