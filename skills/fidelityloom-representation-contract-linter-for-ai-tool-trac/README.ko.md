# FidelityLoom — Representation Contract Linter for AI Tool Traces

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 전문가 모델의 실패가 되기 전에 표현 손실을 감지하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

FidelityLoom은 AI 에이전트가 전문가 모델, 과학 서비스 및 도메인별 도구를 준비하고 호출할 때 구조화된 입력이 어떻게 변하는지 감사하기 위한 오픈 소스 명령줄 도구입니다. 이 도구는 일반적인 평가의 사각지점을 해결합니다: 도구가 개념적으로 올바른 요청을 받는 동안에도 텍스트 변환 중에 단위, 축, 누락 값의 의미, 배열 구조, 숫자 정밀도 또는 필드 출처와 같은 중요한 표현 세부 정보가 손실될 수 있습니다.

이 프로젝트는 원본 구조화된 입력, 생성된 도구 호출 인수 및 반환된 결과를 포함하는 JSONL 추적을 분석합니다. 추적 단계를 통해 필드를 정렬하고, 손실 변환을 감지하며, 심각도와 신뢰도를 할당하고, 사람이 읽을 수 있는 충실도 보고서와 기계가 읽을 수 있는 어댑터 권장 사항을 생성합니다. 이를 통해 라우팅 실패를 직렬화 및 모달리티 변환 실패와 분리하여 팀이 잘못된 기본 모델을 비난하는 대신 전문가 시스템 주변의 인터페이스를 개선하는 데 도움을 줍니다.

FidelityLoom은 에이전트 평가 파이프라인, 모델 게이트웨이, 도구 호출 프레임워크 및 크로스 아키텍처 증류 실험을 위해 설계되었습니다. 기본적으로 결정론적이며, 구성 가능한 도메인 계약을 지원하며, 로컬에서 사용하거나 CI 품질 게이트로 사용할 수 있습니다.

**누구를 위한 건가요.** 

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
python scripts/run.py --selftest
```

**예상 출력:**

```text
{
  "fidelity_report": {
    "schema_version": "1.0",
    "status": "fail",
    "trace_count": 1,
    "finding_count": 13,
    "severity_counts": {
      "error": 7,
      "warning": 6,
      "info": 0
    },
    "findings": [
      {
        "trace_id": "weather-array-001",
        "field": "missing_reading",
        "transition": "source->tool_args",
        "code": "zero_substitution",
        "severity": "error",
        "confidence": 1.0,
        "message": "Missing value was replaced with numeric zero."
      },
      {
        "trace_id": "weather-array-001",
        "field": "sample_id",
        "transition": "source->tool_args",
        "code": "overflow_risk",
        "severity": "warning",
        "confidence": 0.95,
        "message": "Integer 9007199254740993 exceeds the IEEE-754 safe integer range."
      },
      {
        "trace_id": "weather-array-001",
        "field": "sample_id",
        "transition": "tool_args->tool_result",
        "code": "overflow_risk",
        "severity": "warning",
        "confidence": 0.95,
        "message": "Integer 9007199254740993 exceeds the IEEE-754 safe integer range."
      },
      {
        "trace_id": "weather-array-001",
        "field": "sample_id",
        "transition": "tool_args->tool_result",
        "code": "numeric_type_coercion",
        "severity": "warning",
        "confidence": 1.0,
        "message": "Numeric value changed type from int to string."
      },
      {
        "trace_id": "weather-array-001",
        "field": "signal",
        "transition": "source->tool_args",
        "code": "flattened_array",
        "severity": "error",
        "confidence": 1.0,
        "message": "Array shape changed from [2, 2] to [4] by flattening."
      },
      {
        "trace_id": "weather-array-001",
        "field": "signal",
        "transition": "source->tool_args",
        "code": "reordered_dimensions",
        "severity": "error",
        "confidence": 1.0,
        "message": "Axis order changed 
… (+4227 chars truncated)
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
mkdir -p ~/.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
cp -r /tmp/techllm-skills/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/* ~/.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/

# 프로젝트 로컬
mkdir -p .claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
cp -r /tmp/techllm-skills/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/* .claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--contract CONTRACT] [--format {json,text}]
              [--output OUTPUT] [--fail-on {none,warning,error}] [--selftest]
              [input]

Audit representation fidelity across source, tool arguments, and tool results.

positional arguments:
  input                 JSONL trace file

options:
  -h, --help            show this help message and exit
  --contract CONTRACT   JSON contract file (default: FIDELITYLOOM_CONTRACT,
                        then inferred same-path contract)
  --format {json,text}  report format (default: json; env:
                        FIDELITYLOOM_FORMAT)
  --output OUTPUT       explicit output file; overwrites that file if it
                        exists
  --fail-on {none,warning,error}
                        return exit code 1 at or above this severity (default:
                        none)
  --selftest            run the built-in offline deterministic sample and
                        internal assertions
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 각 JSONL 레코드를 읽고 구성된 추적 봉투에 대해 소스, 호출 및 결과 추적 단계를 검증합니다.
- 데이터 유형, 배열 순위, 차원, 단위, null 마커 및 숫자 정밀도 메타데이터를 보존하면서 필드 경로를 정규화합니다.
- 정확한 경로, 선언된 매핑, 별칭 및 보수적인 구조적 일치를 사용하여 필드를 정렬합니다.
- 존재, 유형, 모양, 순서, 단위, 정밀도 및 누락 값의 의미를 비교하는 손실 감지기를 실행합니다.
- 추적, 필드, 감지기, 심각도 및 가능한 변환 경계별로 결과를 집계합니다.
- 충실도 보고서를 내보내고 관찰된 소스 계약을 보존하는 제안된 어댑터 스키마를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| — | — | — |

## 자주 묻는 질문

_—_

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/` 또는 `.claude/skills/fidelityloom-representation-contract-linter-for-ai-tool-trac/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
