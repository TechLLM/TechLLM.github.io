---
title: "AI 코딩 에이전트의 망각을 끝내다 — agentmemory"
date: 2026-05-17T00:03:50+09:00
draft: false
description: "세션이 끝나면 모든 것을 잊는 AI 코딩 에이전트의 고질적 문제를, GitHub 10K 스타 오픈소스 agentmemory가 해결한다. 4-Tier 메모리 파이프라인과 하이브리드 검색으로 토큰 92% 절감, 검색 정확도 95.2%를 달성한 구조를 분석한다."
cover:
  image: "/images/agentmemory-persistent-memory-ai-coding-agents.png"
  alt: "AI 코딩 에이전트의 영구 메모리 시스템 agentmemory"
  caption: "Generated illustration"
tags:
  - AgentMemory
  - AI Agent
  - MCP
  - ClaudeCode
  - 영구메모리
categories:
  - AI Agent
---

매 세션마다 같은 아키텍처를 재설명하고, 같은 버그를 다시 발견하고, 같은 코딩 컨벤션을 재학습시키는 데 질려본 사람이라면 주목할 만한 프로젝트가 나왔다. **agentmemory** — Claude Code, Cursor, Codex CLI, Gemini CLI 등 모든 AI 코딩 에이전트에 영구 메모리를 붙여주는 오픈소스 엔진이다. 출시 직후 GitHub 10K 스타를 넘겼고, Karpathy의 LLM Wiki 패턴을 확신 점수·수명 주기·지식 그래프·하이브리드 검색으로 확장한 구현체로 평가받고 있다.

## 핵심 요약

- **세션 간 기억 유지**: 에이전트가 세션 종료 후에도 코드 구조, 결정 사항, 선호도를 기억하여 다음 세션에 자동 주입
- **4-Tier 메모리 파이프라인**: Working → Episodic → Semantic → Procedural 단계로 기억을 압축·강화·소멸시키는 인간 기억 모방 구조
- **하이브리드 검색**: BM25 + 벡터 + 지식 그래프를 RRF 융합으로 결합, LongMemEval-S R@5 **95.2%** 달성
- **토큰 92% 절감**: 연간 ~$10 비용으로 전체 컨텍스트 붙여넣기 대비 92% 토큰 절감
- **제로 외부 DB**: SQLite + iii-engine만으로 동작, Postgres·Redis·Qdrant 불필요
- **범용 에이전트 지원**: Claude Code, Cursor, Codex CLI, Gemini CLI, OpenClaw 등 16개 이상 에이전트와 연동

## 문제: 에이전트는 왜 매번 처음부터 시작하는가

AI 코딩 에이전트는 세션이 끝나면 모든 것을 잊는다. CLAUDE.md, .cursorrules 같은 내장 메모리 파일은 200줄 한계에 부딪히고 금방 낡아버린다. 결과적으로 매 세션마다 개발자는 같은 설명을 반복해야 한다.

```
세션 1: "API에 JWT 인증을 추가해줘"
  → 에이전트: 코드 작성, 테스트, 버그 수정 완료
  → agentmemory: 모든 도구 사용을 캡처 후 구조화 메모리로 압축

세션 2: "이번엔 레이트 리밋을 추가해줘"
  → 에이전트: (agentmemory가 자동 주입)
  → 이미 알고 있음: JWT는 src/middleware/auth.ts,
    jose 라이브러리 선택, Edge 호환성 이유,
    테스트는 test/auth.test.ts 커버
```

agentmemory는 이 사이클을 끊는다. 후킹 시스템이 세션 중 모든 도구 사용을 캡처하고, 세션 종료 시 구조화된 메모리로 압축한 뒤, 다음 세션 시작 시 관련 컨텍스트를 자동 주입한다. 사용자가 별도로 기록할 필요가 없다.

## 작동 구조: 4-Tier 메모리 파이프라인

agentmemory의 핵심은 인간 뇌의 기억 공고화(수면 중 기억 정리)를 모방한 4단계 파이프라인이다.

| 티어 | 내용 | 비유 |
|------|------|------|
| **Working** | 도구 사용에서 나온 원시 관찰 데이터 | 단기 기억 |
| **Episodic** | 세션 요약본 | "무슨 일이 있었나" |
| **Semantic** | 추출된 사실과 패턴 | "내가 아는 것" |
| **Procedural** | 워크플로우와 결정 패턴 | "어떻게 하는가" |

기억은 에빙하우스 망각 곡선에 따라 자동 소멸되고, 자주 접근하는 기억은 강화된다. 모순되는 기억은 자동 감지·해소된다. 오래된 기억은 TTL 만료 후 자동 제거되어 컨텍스트가 항상 최신 상태를 유지한다.

### 12개 자동 훅이 기억을 만드는 방법

Claude Code 기준으로 SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PreCompact, SubagentStart, SubagentStop, Stop, SessionEnd 등 12개 훅이 자동 등록된다. 개발자가 직접 기록하거나 태깅할 필요가 없다.

```
PostToolUse 훅 실행
  → SHA-256 중복 제거 (5분 윈도우)
  → 프라이버시 필터 (API 키, 비밀값 자동 제거)
  → 원시 관찰 저장
  → LLM 압축 → 구조화된 사실 + 개념 + 서사
  → 벡터 임베딩 (6개 제공자 + 로컬 무료 옵션)
  → BM25 + 벡터 인덱스 등록
```

### 트리플 스트림 하이브리드 검색

세 가지 검색 스트림을 RRF(Reciprocal Rank Fusion, k=60)로 융합하여 최종 결과를 도출한다.

| 스트림 | 역할 | 활성 조건 |
|------|------|------|
| **BM25** | 동의어 확장 키워드 매칭 | 항상 |
| **벡터** | 밀집 임베딩 코사인 유사도 | 임베딩 프로바이더 설정 시 |
| **그래프** | 지식 그래프 엔티티 탐색 | 쿼리에서 엔티티 감지 시 |

실제 성능: "database performance optimization"으로 검색하면 "N+1 query fix"를 정확히 찾아낸다 — 키워드 매칭만으로는 불가능한 수준이다. ICLR 2025 LongMemEval-S 벤치마크(500 문제)에서 R@5 **95.2%**, R@10 **98.6%**, MRR **88.2%**를 기록했다.

## 경쟁 도구 비교

CLAUDE.md가 "포스트잇"이라면, agentmemory는 "그 포스트잇 뒤의 검색 가능한 데이터베이스"다. 주요 경쟁 도구와의 차이는 명확하다.

| 항목 | agentmemory | mem0 (53K⭐) | Letta/MemGPT | CLAUDE.md |
|------|-------------|------------|-------------|-----------|
| 검색 정확도 R@5 | **95.2%** | 68.5% | 83.2% | N/A |
| 자동 캡처 | 12개 훅 (제로 수동) | 수동 add() 호출 | 에이전트 자체 편집 | 수동 편집 |
| 외부 DB | **없음** | Qdrant 필요 | Postgres+벡터DB | 없음 |
| 토큰 비용 | ~1,900/세션 ($10/년) | 가변 | 코어 메모리 상시 포함 | 22K+ (240개 기준) |
| 멀티 에이전트 | MCP + REST + 리스 | API (조율 없음) | Letta 런타임 내부만 | 불가 |
| 프레임워크 종속 | **없음** | 없음 | 높음 | 에이전트별 |
| 실시간 뷰어 | **있음** (포트 3113) | 클라우드 대시보드 | 클라우드 대시보드 | 없음 |

특히 외부 DB가 전혀 없다는 점이 주목할 만하다. SQLite + iii-engine만으로 벡터 인덱스, BM25, 지식 그래프까지 모두 처리한다.

## 빠른 시작

```bash
# 전역 설치
npm install -g @agentmemory/agentmemory

# 메모리 서버 시작 (포트 3111)
agentmemory

# 에이전트 연결
agentmemory connect claude-code

# 실시간 메모리 뷰어 확인
open http://localhost:3113

# 진단 및 문제 해결
agentmemory doctor
```

### Claude Code 플러그인 (권장)

Claude Code에서는 플러그인 두 줄로 12개 훅 + 51개 MCP 도구가 자동 등록된다:

```
/plugin marketplace add rohitg00/agentmemory
/plugin install agentmemory
```

### 다른 에이전트 MCP 공통 설정

Cursor, Claude Desktop, Cline, Windsurf, Gemini CLI 등 `mcpServers` 형식을 쓰는 모든 에이전트는 동일한 블록으로 연결된다:

```json
{
  "mcpServers": {
    "agentmemory": {
      "command": "npx",
      "args": ["-y", "@agentmemory/mcp"],
      "env": { "AGENTMEMORY_URL": "http://localhost:3111" }
    }
  }
}
```

### 기존 세션 기록 가져오기

기존 Claude Code JSONL 세션 기록도 일괄 import할 수 있어, 새로 시작해도 과거 컨텍스트를 바로 활용할 수 있다:

```bash
# ~/.claude/projects 아래 전체 import
npx @agentmemory/agentmemory import-jsonl

# 특정 파일만
npx @agentmemory/agentmemory import-jsonl ~/.claude/projects/-my-project/abc123.jsonl
```

## 실무자가 볼 핵심 포인트

1. **기본값은 보수적**: 자동 압축(`AGENTMEMORY_AUTO_COMPRESS`)과 컨텍스트 주입(`AGENTMEMORY_INJECT_CONTEXT`)은 기본 OFF다. 활성화 시 PostToolUse마다 LLM 호출이 발생해 비용이 급증할 수 있으므로, 필요성을 확인한 뒤 의도적으로 켜야 한다.
2. **로컬 임베딩이 최선**: `npm install @xenova/transformers` 한 줄로 `all-MiniLM-L6-v2` 로컬 임베딩 활성화. API 비용 없이 BM25 대비 +8pp 리콜 향상을 무료로 얻는다.
3. **iii-engine 버전 고정 주의**: 현재 `v0.11.2`에 고정. `v0.11.6+`의 새 샌드박스 모델과 아직 호환되지 않는다. `npm start`로 실행 시 자동 처리되나, 소스 빌드 시에는 수동으로 버전을 확인해야 한다.
4. **멀티 에이전트 조율 실용적**: 리스(lease), 시그널, 루틴 기능으로 여러 에이전트가 같은 메모리를 충돌 없이 공유할 수 있어, 대규모 agentic 워크플로우에서 실용적인 선택이다.
5. **프라이버시 기본 보호**: API 키, 비밀값, `<private>` 태그는 저장 전 자동 필터링된다. 민감한 코드베이스에서도 별도 설정 없이 안전하게 사용 가능하다.

*원문: [rohitg00/agentmemory — GitHub](https://github.com/rohitg00/agentmemory)*
