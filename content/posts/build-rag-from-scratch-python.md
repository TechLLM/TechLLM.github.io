---
title: "외부 라이브러리 없이 RAG를 직접 만들어보자 — Python + ollama로 처음부터 구현하기"
date: 2026-05-12T07:01:00+09:00
draft: false
description: "벡터 DB, 임베딩, 코사인 유사도까지 — RAG의 핵심 구성 요소를 외부 프레임워크 없이 Python으로 직접 구현하는 방법을 단계별로 살펴본다."
tags: ["RAG", "LLM", "Python", "임베딩", "벡터데이터베이스", "ollama", "Llama-3.2"]
categories: ["AI 개발"]
cover:
  image: "/images/build-rag-from-scratch-cover.png"
  alt: "RAG 시스템 구조 — 검색과 생성의 연결"
  caption: "벡터 DB, 임베딩, LLM — RAG의 세 축을 직접 손으로 짜보면 구조가 보인다"
---

LangChain이나 LlamaIndex 없이, RAG를 밑바닥부터 만들 수 있을까?

## 개요

Retrieval-Augmented Generation(RAG)은 LLM이 학습 데이터에 없는 외부 지식을 참조해 답변을 생성하게 만드는 구조다. 요즘은 프레임워크가 많아서 몇 줄이면 RAG를 붙일 수 있지만, 내부에서 무슨 일이 일어나는지 이해하지 못한 채 쓰면 디버깅도, 튜닝도 막막해진다.

Hugging Face의 Xuan-Son Nguyen이 쓴 이 글은 RAG를 아무 추상 레이어 없이 Python으로 직접 구현한다. 벡터 DB도 메모리 위에서 직접 만들고, 코사인 유사도도 수식부터 손으로 짠다. 구현이 목적이 아니라 **이해가 목적**인 튜토리얼이다.

## 핵심 요약

- RAG는 **검색(Retrieval)**과 **생성(Generation)** 두 단계로 구성되며, 둘을 이어주는 게 임베딩 벡터다
- 전체 파이프라인은 **인덱싱 → 검색 → 생성** 세 단계로 나뉜다
- 벡터 DB는 `(청크, 임베딩 벡터)` 튜플 리스트로 충분히 구현 가능하다
- 유사도 계산은 **코사인 유사도**로 처리하며, 외부 라이브러리 없이 Python 기본 연산만으로 작성한다
- 모델 실행은 로컬 CLI 도구 **ollama**를 사용해 서버 없이 맥/리눅스에서 돌릴 수 있다

## RAG가 필요한 이유

ChatGPT에게 "우리 엄마 이름이 뭐야?"라고 물으면 대답을 못 한다. 학습 데이터에 없는 정보이기 때문이다. RAG는 이 문제를 "모델 외부에 있는 지식을 쿼리 시점에 주입"해서 해결한다.

구조는 단순하다. 검색 모델이 외부 지식 소스에서 관련 정보를 뽑아오고, 언어 모델이 그 정보를 바탕으로 응답을 생성한다. 이 글에서는 고양이 사실 데이터셋을 지식 소스로 쓰고, ollama로 로컬에서 두 모델을 구동한다.

## 세 단계로 이루어진 RAG 구조

### 1단계 — 인덱싱(Indexing)

지식 소스를 **청크(chunk)** 단위로 잘라 각각을 임베딩 벡터로 변환한 뒤 DB에 저장하는 단계다.

```python
import ollama

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
VECTOR_DB = []  # (청크, 임베딩 벡터) 튜플 리스트

def add_chunk_to_database(chunk):
    embedding = ollama.embed(model=EMBEDDING_MODEL, input=chunk)['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))
```

데이터셋의 각 줄을 하나의 청크로 취급하면 된다. 실제 서비스에서는 청크 크기 전략이 중요하지만, 개념 이해 단계에서는 한 줄 = 한 청크로 충분하다.

### 2단계 — 검색(Retrieval)

사용자의 질문을 임베딩 벡터로 변환하고, DB에 저장된 벡터들과 **코사인 유사도**를 계산해 가장 관련 있는 청크 N개를 반환한다.

```python
def cosine_similarity(a, b):
    dot_product = sum([x * y for x, y in zip(a, b)])
    norm_a = sum([x ** 2 for x in a]) ** 0.5
    norm_b = sum([x ** 2 for x in b]) ** 0.5
    return dot_product / (norm_a * norm_b)

def retrieve(query, top_n=3):
    query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=query)['embeddings'][0]
    similarities = []
    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((chunk, similarity))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]
```

코사인 유사도가 높을수록 의미적으로 가까운 청크다. `numpy` 없이 리스트 컴프리헨션만으로 구현했다는 점이 이 코드의 핵심이다.

### 3단계 — 생성(Generation)

검색된 청크들을 프롬프트에 주입하고, LLM이 해당 맥락만으로 답변을 생성하게 한다.

```python
instruction_prompt = f'''You are a helpful chatbot.
Use only the following pieces of context to answer the question. Don't make up any new information:
{chr(10).join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}
'''

stream = ollama.chat(
    model=LANGUAGE_MODEL,
    messages=[
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': input_query},
    ],
    stream=True,
)
```

"맥락 밖의 정보는 만들어내지 말라"는 지시가 핵심이다. 이게 없으면 LLM은 검색 결과를 무시하고 hallucination을 일으킨다.

## 사용 모델과 도구

- **임베딩 모델**: `CompendiumLabs/bge-base-en-v1.5-gguf` — 텍스트를 벡터로 변환
- **언어 모델**: `bartowski/Llama-3.2-1B-Instruct-GGUF` — 응답 생성
- **실행 환경**: [ollama](https://ollama.com) — 서버 없이 로컬에서 모델 구동

ollama 설치 후 두 모델을 pull하면 인터넷 연결 없이 전체 파이프라인이 돌아간다.

## 실무자가 볼 핵심 포인트

1. **프레임워크 없이 구현해보는 게 실력이 된다.** LangChain이 내부에서 하는 일을 이 코드로 이해하면, RAG가 안 풀릴 때 어디를 들여다봐야 하는지 보인다.

2. **청크 크기 전략은 이 튜토리얼이 다루지 않는 핵심 변수다.** 실제 서비스에서는 한 줄 = 한 청크가 아니라, 의미 단위(문단, 슬라이딩 윈도우 등)로 자르는 방식이 검색 품질을 결정한다.

3. **코사인 유사도는 단순하지만 효과적이다.** 더 정교한 검색이 필요하다면 Hybrid RAG(키워드 검색 + 벡터 검색 혼합)나 reranker 레이어를 추가하는 방향으로 발전시킬 수 있다.

4. **"맥락만 써라"는 프롬프트 지시가 RAG 품질의 안전핀이다.** 이 지시가 없으면 LLM은 검색 결과와 무관하게 hallucination을 섞는다.

5. **ollama로 RAG 전체를 로컬에서 돌릴 수 있다.** API 키, 클라우드 비용 없이 개발·테스트 환경을 완전히 통제할 수 있다는 점은 프로덕션 투입 전 프로토타이핑에 큰 장점이다.

---

*원문: Xuan-Son Nguyen, "Code a simple RAG from scratch", Hugging Face Blog, 2024년 10월 29일 — https://huggingface.co/blog/ngxson/make-your-own-rag*
