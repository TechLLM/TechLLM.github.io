---
title: "구글 클라우드 OKF 공개 — AI 에이전트에 ‘큐레이션된 컨텍스트’를 주는 벤더 중립 마크다운 표준"
date: 2026-06-17T06:26:01+09:00
draft: false
description: "구글 클라우드가 LLM-Wiki 패턴을 표준화한 Open Knowledge Format(OKF) v0.1을 공개했습니다. 마크다운과 YAML 프런트매터만으로 에이전트가 바로 읽고 쓰는 휴대성 있는 지식 번들의 구조와 의미를 풀어봅니다."
cover:
  image: "/images/google-cloud-open-knowledge-format-okf/source-hero.png"
  alt: "Open Knowledge Format 소개 이미지"
  caption: "Source: MarkTechPost (Google Cloud OKF v0.1 발표)"
tags:
  - "OKF"
  - "Open Knowledge Format"
  - "구글 클라우드"
  - "AI 에이전트"
  - "메타데이터"
  - "LLM Wiki"
  - "Markdown 표준"
categories:
  - "AI"
  - "데이터 인프라"
---

## 개요

파운데이션 모델은 점점 똑똑해지는데, 정작 회사 안에서 일을 시키려고 하면 늘 같은 벽에 부딪힙니다. **"우리 데이터에 대한 맥락이 없다."** 테이블 스키마, 지표 정의, 운영 런북, 조인 경로 같은 사내 지식이 카탈로그·위키·시니어 엔지니어의 머릿속에 흩어져 있기 때문이죠. 구글 클라우드가 6월 16일 공개한 **Open Knowledge Format(OKF) v0.1**은 바로 이 문제를 겨냥한 벤더 중립 표준입니다. 한 줄로 줄이면, "에이전트가 직접 읽고 갱신할 수 있는 마크다운 + YAML 위키"를 산업 표준으로 만들겠다는 시도입니다.

## 핵심 요약

- **OKF v0.1은 마크다운 파일 디렉터리 + YAML 프런트매터로 지식을 표현하는 개방형 명세입니다.** SDK, 런타임, 레지스트리 없이 깃허브에서 그대로 렌더링되고 타르볼로 묶이며, 어떤 파일시스템에도 마운트됩니다.
- 모든 개념(concept)이 의무적으로 가져야 하는 필드는 **`type` 단 하나**입니다. 나머지(`title`, `description`, `resource`, `tags`, `timestamp`)는 예약 필드지만 강제하지 않습니다.
- 파일 간 **표준 마크다운 링크**가 곧 지식 그래프가 됩니다. 별도의 그래프 DB, 임베딩 인덱스, 벤더 스키마가 필요 없습니다.
- 안드레이 카파시가 2026년 4월에 정리한 "LLM Wiki" 발상을 산업 명세 수준으로 끌어올린 셈입니다. Obsidian 볼트, `AGENTS.md` / `CLAUDE.md`, "메타데이터 as 코드" 같은 흐름이 한곳으로 수렴합니다.
- RAG와는 결이 다릅니다. RAG가 질의 시점에 청크를 다시 짜맞춘다면, **OKF는 사람이 큐레이션한 개념을 버전 관리하고 에이전트가 그 위에서 직접 읽고 쓰는** 구조입니다.

## 본문

### 컨텍스트 단편화 문제

대부분의 조직에서 모델이 참고할 만한 맥락은 호환되지 않는 사일로에 흩어져 있습니다. 독점 API를 쓰는 메타데이터 카탈로그, 사내 위키, 공유 드라이브, 코드 주석, 도큐멘트 문자열까지요. "이벤트 스트림에서 주간 활성 사용자(WAU)를 어떻게 계산하지?" 같은 단순한 질문에도 에이전트는 서로 따로 노는 데이터 표면을 더듬어가며 답을 짜맞춰야 합니다.

문제는 두 가지입니다. 첫째, 에이전트를 만드는 사람마다 컨텍스트 조립을 처음부터 다시 짭니다. 둘째, 카탈로그 벤더마다 비슷한 데이터 모델을 새로 발명합니다. 결과는 중복 노동의 산업화입니다. OKF는 바로 이 **상호운용 계층**만 표준화하자고 제안합니다.

![OKF 소개 이미지](/images/google-cloud-open-knowledge-format-okf/source-hero.png)

### OKF는 어떻게 동작하나

OKF v0.1의 가장 큰 매력은 단순함입니다. 번들 하나는 마크다운 파일이 담긴 디렉터리 그 자체입니다. 예를 들면 이렇게 생겼습니다.

```
sales/
├── index.md
├── datasets/
│   ├── index.md
│   └── orders_db.md
├── tables/
│   ├── index.md
│   ├── orders.md
│   └── customers.md
└── metrics/
    ├── index.md
    └── weekly_active_users.md
```

각 파일의 YAML 프런트매터는 이런 식입니다.

```yaml
---
type: BigQuery Table
title: Orders
description: One row per completed customer order.
resource: https://console.cloud.google.com/bigquery?p=acme&d=sales&t=orders
tags: [sales, revenue]
timestamp: 2026-05-28T14:30:00Z
---

# Schema

| Column        | Type   | Description                              |
|---------------|--------|------------------------------------------|
| `order_id`    | STRING | Globally unique order identifier.        |
| `customer_id` | STRING | FK to [customers](/tables/customers.md). |
```

예약 필드는 `type`, `title`, `description`, `resource`, `tags`, `timestamp` 여섯 개. 그중 **의무는 `type` 하나**입니다. 개념끼리는 평범한 마크다운 링크(`[customers](/tables/customers.md)`)로 잇고, 그 링크가 모이면 자연스럽게 지식 그래프가 됩니다. 디렉터리에는 점진적 공개를 위한 `index.md`, 변경 이력을 위한 `log.md`를 옵션으로 둘 수 있습니다.

### 세 가지 설계 원칙

OKF가 끈질기게 지키는 원칙은 세 가지입니다.

- **최소 강제(Minimally Opinionated)** — 모든 개념에 강제하는 필드는 `type` 하나뿐. 명세는 콘텐츠 모델이 아니라 상호운용 표면만 정의합니다.
- **생산자/소비자 분리** — 사람이 쓴 번들을 에이전트가 읽을 수 있고, 파이프라인이 생성한 번들을 사람이 시각화 도구로 볼 수 있습니다. 양쪽 도구가 서로 갈아 끼울 수 있는 구조입니다.
- **플랫폼이 아니라 포맷** — 특정 클라우드, DB, 모델 제공자, 에이전트 프레임워크에 묶이지 않습니다. 읽고 쓰는 데 어떤 계정도 필요 없습니다.

### 어디에 쓰면 좋을까

- **데이터 팀의 메타데이터-as-코드** — 빅쿼리 테이블·지표 정의를 번들로 내보내 SQL 옆에 같이 커밋하고, PR로 변경을 리뷰합니다.
- **온콜 에이전트의 런북** — 런북을 개념으로 저장합니다. 사고 발생 시 에이전트가 `index.md`를 읽고 크로스링크를 따라가며 해결합니다.
- **조직 간 지식 교환** — 벤더가 카탈로그 익스포트를 OKF로 배포하면, 다른 회사 에이전트는 추가 통합 작업 없이 바로 소비합니다.
- **개발팀 위키** — 낡아가는 Notion·Obsidian 공간을 버전 관리되는 마크다운으로 바꾸고, 에이전트가 최신 상태를 유지하도록 맡깁니다.

### RAG와 무엇이 다른가

표로 정리하면 차이가 한눈에 보입니다.

| 접근법 | 저장소 | 필수 스키마 | 휴대성 | SDK/레지스트리 | 에이전트 친화 |
|---|---|---|---|---|---|
| **OKF v0.1** | 마크다운 + YAML | `type` 하나 | 있음 | 없음 | 번역 없이 바로 읽기 |
| Notion | 독점 DB | 워크스페이스별 | 익스포트만 | API 필요 | API 경유 |
| Obsidian 볼트 | 마크다운 | 강제 없음 | 있음 | 없음 | 관습 의존 |
| 메타데이터 카탈로그 | 벤더 저장소 | 벤더 스키마 | 익스포트만 | 벤더 SDK | 벤더별 상이 |
| RAG 인덱스 | 벡터 스토어 | 임베딩 모델 | 없음 | 있음 | 청크 단위 |

핵심은 마지막 줄입니다. RAG가 매번 청크를 다시 줍는다면, OKF는 **사람이 정리한 개념을 깃으로 관리하고 에이전트가 그 위에서 글을 쓰는** 방식입니다. 두 접근은 경쟁이 아니라 보완 관계에 가깝습니다.

### 최소 컨슈머 구현

OKF가 표준 도구만으로 파싱 가능하다는 점이 매력입니다. 번들을 읽어 링크 그래프를 만드는 코드는 이 정도면 충분합니다.

```python
import pathlib, re, yaml

def load_bundle(root):
    concepts, links = {}, []
    for path in pathlib.Path(root).rglob("*.md"):
        text = path.read_text()
        meta = {}
        if text.startswith("---"):
            _, fm, body = text.split("---", 2)
            meta = yaml.safe_load(fm) or {}
        else:
            body = text
        concepts[str(path)] = meta
        for target in set(re.findall(r"\]\((/[^)]+\.md)\)", body)):
            links.append((str(path), target))
    return concepts, links

concepts, graph = load_bundle("sales/")
```

백엔드도, 설치 명령도 필요 없습니다. 같은 파일이 코드 옆 같은 깃 리포지토리에 그대로 살아 있습니다.

### 카파시의 LLM Wiki에서 OKF까지

카파시는 4월에 공개한 LLM Wiki 글에서 이렇게 적었습니다. *"LLM은 지치지 않고, 크로스 레퍼런스 갱신을 잊지 않으며, 한 번에 여러 파일을 편집할 수 있다."* 사람이 개인 위키에 손대다가 결국 포기하던 그 자질구레한 정리 작업이야말로 LLM이 제일 잘하는 일이라는 얘기죠.

같은 패턴은 그동안 여러 이름으로 등장했습니다. 코딩 에이전트에 연결한 Obsidian 볼트, `AGENTS.md`나 `CLAUDE.md` 같은 규약 파일, "메타데이터 as 코드" 리포지토리까지요. 모두 같은 발상을 각자 다른 방식으로 풀어낸 결과라 서로 호환되지 않았습니다. OKF는 그 상호운용 계층만 표준화해서 *무거운 일은 에이전트에게 맡기자*는 단순한 약속입니다.

### 구글이 함께 공개한 도구들

표준만 던지지 않았습니다. 구글 클라우드는 빅쿼리 강화 에이전트, 정적 HTML 시각화 도구, 그리고 세 개의 샘플 번들을 함께 공개했습니다. 명세 본문은 [Google Cloud 블로그](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)에서 확인할 수 있습니다.

## 실무자가 볼 핵심 포인트

- **메타데이터 카탈로그를 깃으로 옮길 명분이 생겼습니다.** 빅쿼리·스노우플레이크 카탈로그를 OKF로 익스포트해 SQL과 같은 레포에 두면, 변경 이력이 PR로 남고 에이전트가 그 위에서 질의를 자동화할 수 있습니다.
- **위키와 코드의 경계가 흐려집니다.** Obsidian이나 Notion에 둔 운영 지식을 OKF 번들로 옮겨두면 IDE 안의 코딩 에이전트가 바로 읽고 갱신할 수 있습니다.
- **RAG를 완전히 대체하기보다 RAG 앞단에 두는 게 현실적입니다.** 큐레이션된 OKF 개념은 정답에 가까운 컨텍스트, RAG는 보강용 롱테일로 분리하면 환각이 눈에 띄게 줄어듭니다.
- **표준 단계는 아직 v0.1입니다.** 사양은 작지만, 산업 채택은 도구·벤더 생태계 합의에 달려 있습니다. 지금은 사내 PoC로 빠르게 도입하면서 표준의 향방을 지켜볼 시점입니다.
- **운영 측면에서 가장 큰 매력은 ‘런타임 제로’입니다.** 의존성 없이 깃과 마크다운 뷰어만으로 굴러간다는 점은 보안·감사 요건이 엄격한 조직일수록 더 큰 장점이 됩니다.

## 원문 출처

[원문 보기](https://www.marktechpost.com/2026/06/16/google-cloud-introduces-open-knowledge-format-okf-a-vendor-neutral-markdown-spec-for-giving-ai-agents-curated-context/) — MarkTechPost, Asif Razzaq, 2026-06-16
