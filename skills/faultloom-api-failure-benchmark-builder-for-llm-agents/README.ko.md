# FaultLoom — API Failure Benchmark Builder for LLM Agents

![version](https://img.shields.io/badge/version-0.1.0-blue) ![selftest](https://img.shields.io/badge/selftest-passing-brightgreen) ![license](https://img.shields.io/badge/license-MIT-green) ![auto-generated](https://img.shields.io/badge/auto--generated-yes-orange)

> 실패한 소셜 API 오류를 신뢰할 수 있는 LLM 에이전트를 위한 벤치마크 사례로 전환하세요.

> 🤖 자동 생성 + 자체 검증을 거친 스킬입니다. 작동하는 최소 레퍼런스이니 실사용 전 검토하세요.

## 이게 뭔가요?

FaultLoom은 실제 소셜 게시 실패를 표준화된 벤치마크 사례로 변환하기 위한 오픈 소스 라이브러리와 CLI를 제안하는 프로젝트입니다. Threads, Instagram, Facebook 및 유사한 서비스의 API 오류를 일회성 운영 잡음이 아닌 유용한 평가 자료로 취급합니다.

이 프로젝트는 툴 호출이 실패할 때 LLM 에이전트의 행동을 노출하는 데 도움을 줍니다. 잘못된 원인을 추측하거나, 사람의 조치가 필요할 때 재시도하거나, 제공자별 오류 코드를 무시하거나, 모호한 복구 조언을 제공하는 등의 실패 모드를 포착하도록 설계되었습니다.

FaultLoom은 원시 로그, JSON 응답, 상태 페이로드 및 예외 추적을 정리된 YAML 사례로 변환하며, 여기에는 정규화된 레이블, 재시도 지침, 심각도, 사용자 조치 요구 사항 및 예상 복구 행동이 포함됩니다.

**누구를 위한 건가요.** FaultLoom은 AI 평가 팀, 에이전트 프레임워크 유지 관리자 및 에이전트가 실패를 정확하게 진단하고 실용적인 복구 단계를 추천할 수 있는지를 테스트해야 하는 자동화 워크플로우 개발자를 위한 것입니다.

## ⏱ 30초 빠른 시작

```bash
git clone https://github.com/TechLLM/TechLLM.github.io techllm-skills
cd techllm-skills/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
python scripts/run.py --selftest
```

**예상 출력:**

```text
benchmark_suite:
  name: "social-publishing-failures-demo"
  version: "0.1"
  generated_by: "faultloom-minimal-rule-engine"
  cases:
    -
      id: "auth-token-expired"
      provider: "threads"
      operation: "publish_text_post"
      source:
        status_code: 401
        error_excerpt: "{\"access_token\":\"[REDACTED]\",\"error\":{\"code\":190,\"message\":\"Invalid OAuth access token\",\"type\":\"OAuthException\"}}"
      classification:
        category: "authentication"
        retryable: false
        user_action_required: true
        severity: "high"
        confidence: 0.94
      expected_recovery:
        summary: "Stop automatic retry and request credential refresh or reauthorization."
        actions:
          - "Mark the publishing attempt failed with an authentication cause."
          - "Ask the user or operator to reconnect the provider account."
          - "Retry only after a new credential is available."
      evaluation:
        should_retry: false
        agent_should:
          - "Preserve the provider error code and status code in the diagnosis."
          - "State that human or operator action is required before retry."
        agent_must_not:
          - "Claim the post content caused the failure without evidence."
          - "Loop retries with the same credential."
    -
      id: "instagram-rate-limit"
      provider: "instagram"
      operation: "publish_media"
      source:
        status_code: 429
        error_excerpt: "Rate limit exceeded. Retry after 60 seconds."
      classification:
        category: "rate_limit"
        retryable: true
        user_action_required: false
        severity: "medium"
        confidence: 0.92
      expected_recovery:
        summary: "Schedule a retry using provider-aware backoff."
        actions:
          - "Respect retry-after or rate-limit reset timing when available."
          - "Queue the publish attempt instead of retrying immediately."
          - "Surface a concise delay reason to the
… (+1540 chars truncated)
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
mkdir -p ~/.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
cp -r /tmp/techllm-skills/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/* ~/.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/

# 프로젝트 로컬
mkdir -p .claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
cp -r /tmp/techllm-skills/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/* .claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/
```

**2) 독립 실행 CLI로**

```bash
git clone https://github.com/TechLLM/TechLLM.github.io
cd TechLLM.github.io/skills/faultloom-api-failure-benchmark-builder-for-llm-agents
python scripts/run.py --help
```

**3) 수동 다운로드**

GitHub에서 `skills/faultloom-api-failure-benchmark-builder-for-llm-agents/` 폴더를 열어 파일을 받거나, 저장소 ZIP을 내려받아 이 폴더만 복사하세요.

## ⚡ 사용법

전체 `--help` 출력:

```text
usage: run.py [-h] [--input INPUT] [--output OUTPUT] [--selftest]

Build YAML benchmark cases from social publishing API failure logs.

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        JSON file containing an array of failure events or an
                        object with suite_name and events.
  --output OUTPUT, -o OUTPUT
                        Optional YAML output path. Defaults to stdout.
  --selftest            Run the built-in sample with no external API key or
                        network access.
```

## 예제

이 스킬의 `examples/` 폴더를 참고하세요(샘플 입력 + 예상 출력).

## 🧠 동작 방식

- 원시 소셜 게시 실패를 로그, API 응답, 예외 추적 및 상태 페이로드에서 수집합니다.
- 내보내기 전에 토큰, 계정 식별자, 게시물 내용 및 개인 메타데이터와 같은 민감한 데이터를 편집합니다.
- 각 실패를 인증, 속도 제한, 권한, 미디어 검증, 일시적인 중단, 정책 차단 및 알 수 없는 실패를 포괄하는 이식 가능한 분류법으로 분류합니다.
- 재시도 가능성, 심각도, 신뢰도, 사용자 조치 요구 사항 및 예상 복구 행동을 포함한 벤치마크 메타데이터를 추가합니다.
- 평가를 위한 정규화된 YAML 테스트 사례, 회귀 테스트 제품군, 도구 사용 벤치마크 및 미세 조정 데이터 세트를 내보냅니다.

## 🔧 문제 해결

| 증상 | 원인(추정) | 해결 |
|---|---|---|
| 실패가 알 수 없는 것으로 분류되었습니다. | 입력이 기존 규칙과 충분히 일치하지 않거나 제공자가 모호한 오류를 반환했습니다. | 원시 실패를 검토하고, 보다 구체적인 분류 규칙을 추가하거나, 판단이 필요한 사례에 대해 보조 레이블링을 사용하세요. |
| 사례에서 사용자 조치가 필요할 때 재시도를 권장합니다. | 분류 중에 명확한 권한, 인증 또는 정책 신호가 누락되었습니다. | 분류법 규칙을 업데이트하여 사례에 사용자 조치가 필요함을 표시하고 적절하게 재시도 가능성을 설정하세요. |
| 내보낸 사례에 민감한 콘텐츠가 나타납니다. | 편집 후크가 제공자별 필드 또는 사용자 정의 로그 형식을 다루지 않았습니다. | 내보내기 전에 누락된 필드를 다루도록 편집 구성을 확장하세요. |

## 자주 묻는 질문

**FaultLoom이 프로덕션 모니터링을 대체할 수 있나요?**

아니오. FaultLoom은 실패를 재사용 가능한 평가 데이터로 전환하는 데 중점을 두고 있습니다. 모니터링을 보완할 수 있지만, 주요 목적은 벤치마크 생성 및 에이전트 행동 테스트입니다.

**왜 실제 API 실패를 사용하는 대신 합성 예를 사용하나요?**

실제 실패는 에이전트가 프로덕션에서 처리해야 하는 지저분한 세부 사항을 보존하며, 여기에는 제공자 용어, 중첩된 페이로드, 부분적인 컨텍스트 및 모호한 복구 경로가 포함됩니다.

**LLM 없이 작동할 수 있나요?**

예. FaultLoom은 먼저 규칙 기반 분류를 사용하도록 설계되었습니다. LLM 보조 레이블링은 모호한 사례에 대해 선택 사항입니다.

**생성된 YAML이 에이전트 평가에 유용한 이유는 무엇인가요?**

각 사례에는 실패 증거, 정규화된 진단, 재시도 정책, 사용자 조치 요구 사항, 심각도 및 예상 복구 행동이 포함되어 있어 반복 가능한 테스트 및 회귀 검사에 적합합니다.

## ✅ 검증

구조 / 문법 / selftest 자동 검사를 통과했습니다(`SKILL.md` 참고).

## 제거

스킬 폴더(`~/.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/` 또는 `.claude/skills/faultloom-api-failure-benchmark-builder-for-llm-agents/`)를 삭제하면 됩니다. 시스템에 다른 변경은 없습니다.

## 📜 버전 관리

이 스킬은 시맨틱 버전을 따릅니다. 전체 이력은 [CHANGELOG.md](CHANGELOG.md)를 보세요.

## 🤝 기여

자동 생성된 레퍼런스 스킬입니다. 개선 이슈·PR을 환영합니다.

## 라이선스

MIT
