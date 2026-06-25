---
name: <internal>-forge
description: Use this skill when creating or modifying a Claude Code/OpenClaw skill and you need <internal> regression tests with a mock workspace, verification checks, and acceptance criteria.
---

# Workspace Regression Forge

## 목적

새 스킬이나 기존 스킬 수정이 실제 파일을 망가뜨리지 않고 목표 상태를 만드는지 반복 검증하기 위한 작업공간 기반 회귀 테스트셋을 만든다. 답변 품질이 아니라 초기 파일 상태, 에이전트 작업 후 변경 상태, 검증 조건을 기준으로 평가한다.

## 사용 시점

- Claude Code/OpenClaw 스킬을 만들거나 고친 뒤 동작 회귀 테스트가 필요할 때
- 로컬 프로젝트, OpenClaw 설정 디렉터리, Obsidian vault, 샘플 문서 폴더를 안전하게 복제해 테스트하고 싶을 때
- 작업 설명을 기준으로 acceptance criteria, mock workspace, 검증 스크립트를 함께 만들고 싶을 때
- 실제 사용자 파일 대신 sandbox 안에서 에이전트 작업을 반복 실행하고 싶을 때

기존 테스트 프레임워크가 이미 명확하면 그 구조를 따른다. 없으면 이 스킬의 스크립트와 파일 레이아웃을 사용한다.

## 단계별 절차

1. 테스트 대상 정의
   - 검증할 스킬 이름, 대표 사용자 요청, 입력 워크스페이스 경로, 기대 최종 상태를 적는다.
   - 원본 워크스페이스는 절대 직접 수정하지 않는다. 항상 복제본에서 실행한다.
   - OpenClaw 설정을 다룰 때는 cron job에 payload.model 또는 payload.fallbacks가 생기지 않아야 한다는 정책처럼 시스템 고유 불변 조건을 acceptance criteria에 포함한다.

2. 샘플 워크스페이스 준비
   - 실제 프로젝트 전체 대신 실패를 재현할 수 있는 최소 파일만 포함한다.
   - 비밀키, 토큰, 개인 대화 로그, 대용량 산출물은 제외하거나 더미 값으로 바꾼다.
   - Obsidian vault는 링크, frontmatter, 첨부파일 참조가 깨지는지 확인할 수 있는 작은 노트 세트를 포함한다.

3. 테스트셋 생성
   - 가능하면 bundled script를 실행한다.
   - 기본 명령: `python3 scripts/run.py forge --task task.md --sample /path/to/sample --out regression/<internal>-forge/example --mode pytest`
   - `--mode bash`를 쓰면 pytest 없이 POSIX shell 검증 파일을 만든다.

4. 검증 조건 작성
   - 파일 존재, 파일 내용, JSON/YAML 구조, 금지된 변경, 명령 성공 여부를 각각 분리해 적는다.
   - 체크는 결정적이어야 한다. LLM 심사만으로 pass/fail을 정하지 않는다.
   - 필요하면 LLM이 생성한 기대 상태 초안을 사람이 검토한 뒤 고정한다.

5. 에이전트 실행 루프
   - `workspace/` 복제본에서 대상 스킬을 호출해 작업을 수행한다.
   - 실행 후 `pytest checks/` 또는 `bash checks/check.sh`를 돌린다.
   - 실패하면 스킬 지침, 검증 조건, fixture 중 무엇이 문제인지 분리해서 고친다.

6. 회귀 테스트 보관
   - 각 케이스는 `manifest.json`, `task.md`, `acceptance.md`, `workspace/`, `checks/`를 가진다.
   - 케이스 이름은 스킬명과 행동을 드러내는 kebab-case로 만든다.
   - 원본 파일 경로 대신 복제본 기준 상대 경로를 사용한다.

## 입출력

입력:
- 작업 설명 또는 스킬 변경 설명
- 샘플 워크스페이스 경로
- 기대 최종 상태와 금지할 변경 사항
- 선택 검증 방식: pytest 또는 bash

출력:
- `manifest.json`: 테스트 메타데이터와 실행 방법
- `task.md`: 에이전트에게 줄 재현 가능한 작업 요청
- `acceptance.md`: 사람이 읽는 합격 기준
- `workspace/`: mock workspace 복제본
- `checks/test_workspace.py` 또는 `checks/check.sh`: 결정적 검증 스크립트

## 예시

```bash
python3 scripts/run.py forge \
  --task task.md \
  --sample ~/.openclaw/skills/my-skill/example-workspace \
  --out regression/my-skill/basic-file-edit \
  --mode pytest \
  --expect-file output/result.md \
  --expect-contains output/result.md:완료 \
  --forbid-contains cron/jobs.json:payload.model
```

생성 후 실행:

```bash
cd regression/my-skill/basic-file-edit/workspace
# 여기서 대상 스킬을 호출해 작업 수행
cd ..
pytest checks
```

## OpenClaw 적용 메모

- `coder`, `codex`, `reviewer`, `supervisor` 에이전트의 실제 파일 변경 능력을 회귀 테스트로 검증하는 데 적합하다.
- `mcp-builder`, `blog-sns-publisher`, `paper-fetch`, `graphify`, `llm-wiki-ingestor`처럼 파일과 설정을 많이 바꾸는 스킬에 특히 효과가 크다.
- OpenClaw의 cron 정책, KB 경로, vault 링크 무결성 같은 운영 불변 조건을 테스트 케이스에 넣으면 새 스킬이 시스템 규칙을 깨는지 빠르게 잡을 수 있다.