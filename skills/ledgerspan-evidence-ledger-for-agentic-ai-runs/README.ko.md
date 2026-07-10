# LedgerSpan — Evidence Ledger for Agentic AI Runs

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 에이전트 AI가 실제로 변경, 조작, 검증한 사항들에 대한 휴대용 증거.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

LedgerSpan은 AI 에이전트 실행, LLM 도구 및 자율 워크플로우로부터 내구성 있는 증거를 수집하기 위한 제안된 오픈 소스 CLI입니다. 이는 답변 뒤에 있는 관찰 가능한 작업, 즉 변경된 파일, 실행된 명령, 도구 활동, 생성된 아티팩트, 조작된 리소스 및 완료된 검사에 중점을 둡니다.

이는 최종 응답은 설득력 있게 들리지만 워크스페이스는 다른 이야기를 할 수 있기 때문에 중요합니다. 에이전트가 잘못된 파일을 편집했거나, 필요한 검증 단계를 건너뛰었거나, 예상된 아티팩트를 생성하지 못했거나, 참조한 리소스에 접근하지 않았을 수 있습니다.

LedgerSpan은 검토자와 평가자에게 인간이 검사할 수 있고, 벤치마크 결과와 함께 저장되거나, CI 실행에 첨부되거나, 전용 벤치마크 플랫폼을 채택하지 않고도 사용자 정의 평가 시스템에서 소비할 수 있는 휴대용 증거 패키지를 제공합니다.

**누구를 위한 건가요.** LedgerSpan은 최종 답변 텍스트만 판단하는 것이 아니라 실제 세계의 부작용을 평가해야 하는 벤치마크 작성자, 개발자 도구 팀, 문서화 자동화 유지보수자, 워크스페이스 코파일럿 빌더 및 AI 연구 그룹을 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
python scripts/run.py --selftest
```

**예상 출력:**

_이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력)._

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
mkdir -p ~/.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
cp -r /tmp/techllm-skills/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/* ~/.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/

# 프로젝트 로컬
mkdir -p .claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
cp -r /tmp/techllm-skills/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/* .claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

_이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력)._

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 에이전트 실행 전후에 워크스페이스의 스냅샷을 찍어 파일 메타데이터, 타임스탬프, 크기 및 콘텐츠 해시를 기록합니다.
- 파일 변경 사항을 분류하여 검토자가 어떤 것이 생성, 수정, 삭제, 이름 변경 또는 변경되지 않았는지 볼 수 있도록 합니다.
- 명령 로그와 도구 호출 추적을 수집하여 워크스페이스 변경 사항을 생성한 작업과 연결합니다.
- 생성된 아티팩트를 해시하여 보고서, 데이터 세트, 문서, 코드 파일 및 구조화된 출력을 신뢰성 있게 식별할 수 있도록 합니다.
- 검토, 저장, 벤치마킹 또는 다운스트림 평가를 위한 휴대용 Markdown 또는 JSON 증거 패키지를 생성합니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 증거 패키지에 워크스페이스 변경 사항이 표시되지 않습니다. | 에이전트가 워크스페이스를 수정하지 않았거나, LedgerSpan이 잘못된 실행 창 주변에서 스냅샷을 캡처했을 수 있습니다. | 증거 수집이 에이전트 실행 전에 시작되고 모든 예상 작업이 완료된 후에만 끝나는지 확인하세요. |
| 일부 도구 활동이 보고서에 누락되었습니다. | 에이전트 하네스가 LedgerSpan이 구문 분석할 수 있는 형식으로 도구 호출 추적을 내보내지 않았을 수 있습니다. | 하네스에서 구조화된 추적 내보내기를 활성화하거나 LedgerSpan이 수집할 수 있는 호환 가능한 JSON 추적을 제공하세요. |
| 생성된 아티팩트를 실행 간에 일치시킬 수 없습니다. | 아티팩트가 비결정적 콘텐츠, 타임스탬프 또는 포함된 메타데이터로 다시 생성되었을 수 있습니다. | 가능한 경우 생성된 출력을 정규화하고 파일 메타데이터 및 변경 분류와 함께 해시에 의존하세요. |

## 자주 묻는 질문

**LedgerSpan은 평가자입니까?**

그 자체로는 아닙니다. LedgerSpan은 증거를 수집하고 패키징합니다. 그런 다음 인간 검토자, 벤치마크 하네스, CI 워크플로우 또는 사용자 정의 평가자가 해당 증거가 작업을 충족하는지 여부를 결정할 수 있습니다.

**LedgerSpan이 기존 에이전트 하네스를 대체합니까?**

아니오. LedgerSpan은 기존 하네스, 도구 및 워크플로우 주변의 경량 증거 계층으로 설계되었습니다.

**왜 최종 답변만 평가하지 않습니까?**

많은 에이전트 작업은 워크스페이스가 올바르게 변경된 경우에만 성공합니다. LedgerSpan은 이러한 부작용을 시각화하여 유창하지만 불완전한 답변을 더 쉽게 감지할 수 있도록 합니다.

**출력을 CI 또는 벤치마크 파이프라인에서 사용할 수 있습니까?**

예. LedgerSpan은 보관, 검토 또는 자동화된 시스템에서 소비할 수 있는 휴대용 Markdown 또는 JSON 증거 패키지를 생성하도록 설계되었습니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/` 또는 `.claude/skills/ledgerspan-evidence-ledger-for-agentic-ai-runs/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
