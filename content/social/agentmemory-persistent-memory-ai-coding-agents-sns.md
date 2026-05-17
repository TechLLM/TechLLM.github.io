# SNS Content — agentmemory

## Threads

**버전 A (인사이트형)**
> AI 코딩 에이전트는 왜 매번 처음부터 시작할까?
>
> 세션이 끝나면 JWT 인증 경로도, 버그 히스토리도, 코드 컨벤션도 전부 잊어버린다.
>
> agentmemory가解决这个问题.
> 4-Tier 메모리 파이프라인으로 에이전트가 세션 간 기억을 유지한다.
> BM25 + 벡터 + 지식 그래프 RRF 융합.
> 검색 정확도 R@5: 95.2%.
> 토큰 비용 92% 절감.
>
> 코드 구조를 다시 설명하느라浪费时间한 적 있다면 확인해볼 만하다.
>
> 🔗 techllm.dev/posts/agentmemory...
>
> #AI #Coding #AgentMemory #ClaudeCode #Cursor

---

**버전 B (후킹형)**
> "이 파일 어디서 만졌지?" → " sessions 전에 확인했었는데..."
>
> 매 세션마다 같은 아키텍처를 재설명하고, 같은 버그를 다시 발견하는 데浪费时间한 적 있다면,
> 당신만 그런 게 아니다.
>
> agentmemory (GitHub 10K★)가 에이전트에 영구 기억을 붙여준다.
> 12개 자동 훅이 도구 사용을 전부 캡처 → 구조화 → 자동 주입.
> 개발자 별도 기록 불필요.
>
> Postgres도 Redis도 Qdrant도 필요 없음. SQLite 하나로.
>
> 🔗 techllm.dev/posts/agentmemory...
>
> #AIAgent #코딩 #프롬프트엔지니어링 #LLM

---

**버전 C (리스트형)**
> agentmemory가 해결하는 4가지 문제:
>
> ❌ 매 세션 코드 구조 재설명
> ❌ 같은 버그 다시 발견
> ❌ 코딩 컨벤션 재학습
> ❌ 전체 컨텍스트 붙여넣기 → 비용 폭발
>
> ↓
>
> ✅ 4-Tier 메모리 파이프라인
> ✅ RRF 하이브리드 검색 (R@5 95.2%)
> ✅ 토큰 92% 절감 (연~$10)
> ✅ 16개+ 에이전트 지원
>
> techllm.dev/posts/agentmemory...
>
> #AI #코딩에이전트 #LLM #AgentMemory

---

## Instagram Caption

**버전 A (감성형)**
```
AI가 내 코드를 잊어버리는 순간.

세션이 끝나면 JWT 경로도,
이전에 고쳤던 버그도,
내가 왜 그 라이브러리를 선택했는지도
전부 사라진다.

그래서 매번 처음부터 시작한다.

agentmemory (GitHub 10K★)는
에이전트에 영구 기억을 붙여주는 오픈소스다.

• 4-Tier 메모리 파이프라인
• 검색 정확도 95.2%
• 연 $10면 충분
• Postgres·Redis·Qdrant 불필요

내일은 이 문제를 다시 풀지 않아도 된다.
기술이 기억하니까.

🔗 링크를 확인해보세요.
```

**버전 B (전문가형)**
```
agentmemory 핵심 정리.

코딩 에이전트의 세션 간 기억 문제를
영구 메모리 시스템으로 해결하는 오픈소스.

핵심 수치:
• R@5 검색 정확도: 95.2%
• 토큰 비용 절감: 92%
• 연 비용: ~$10
• 지원 에이전트: 16개+

Arquitectura:
4-Tier 메모리 (Working→Episodic→Semantic→Procedural)
+ BM25/벡터/지식 그래프 RRF 융합
+ 12개 자동 훅

특징:
• 외부 DB 없음 (SQLite + iii-engine)
• 16개+ 에이전트 지원
• API 키 자동 필터링

Claude Codeユーザーは 플러그인 두 줄로 적용 가능.

자세한 분석과 경쟁 도구 비교는 블로그에서.
🔗 techllm.dev/posts/agentmemory
```

---

## Hashtags

**주제 태그**
#AI #코딩에이전트 #AIAgent #LLM #ClaudeCode #Cursor #AgentMemory #MCP #영구메모리 #코딩생산성

**타깃 태그**
#프롬프트엔지니어링 #코딩팁 #AI코딩 #개발생산성 #SoftwareEngineering #TechTips

**확산 태그**
#AITools #FutureOfCoding #CodingLife #TechNews #OpenSource #DeveloperTools #AIAssistant

---

## 블로그 카드뉴스
`content/social/cards/agentmemory-persistent-memory-ai-coding-agents/card-01~06.png`
