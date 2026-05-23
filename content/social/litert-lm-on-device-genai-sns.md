# SNS Content — LiteRT-LM On-device GenAI

블로그 URL: https://techllm.github.io/posts/litert-lm-on-device-genai/
대표 이미지: https://techllm.github.io/images/litert-lm-hero.png

## Threads

**P1**
> 서버 없이 76 tokens/sec.
>
> Google이 LiteRT-LM으로 보여준 건 단순한 온디바이스 데모가 아닙니다.
>
> Gemma 4를 Android, iOS, WebGPU 위에서 빠르게 돌리고, MTP·세션 복원·메모리 최적화까지 런타임 레벨에서 묶었습니다.
>
> 온디바이스 AI 경쟁이 모델 크기 싸움에서 실행 스택 싸움으로 넘어가고 있습니다.

**P2**
> 핵심은 MTP입니다.
>
> 일반 LLM 추론은 한 토큰마다 큰 가중치를 옮기느라 메모리 대역폭에 묶입니다.
>
> LiteRT-LM은 MTP drafter와 기본 Gemma 4 모델을 같은 GPU 같은 hardware IP 위에서 돌려 데이터 이동을 줄입니다.
>
> 원문 기준 최대 2.2배 decode speedup.
> Android GPU 52 tok/s, iOS 56 tok/s, WebGPU 최대 76 tok/s.

**P3**
> 더 흥미로운 건 속도만이 아닙니다.
>
> LiteRT-LM은 KV cache 세션 저장·복원, constrained decoding, Thinking Mode, function calling까지 지원합니다.
>
> 즉 “기기 안에서 돌아가는 작은 챗봇”이 아니라, 로컬 에이전트 앱의 실행 기반을 노리는 겁니다.
>
> 정리 글:
> https://techllm.github.io/posts/litert-lm-on-device-genai/
>
> #AI #LLM #LiteRT #Gemma #OnDeviceAI

## Instagram Caption

**전문가형**
```
서버 없이 76 tokens/sec.

Google이 공개한 LiteRT-LM은
Gemma 4를 Android, iOS, WebGPU 환경에서 빠르게 실행하기 위한
온디바이스 LLM 런타임입니다.

핵심은 모델 하나가 아닙니다.

• LiteRT 기반 실행
• XNNPACK / MLDrift 커널
• CPU·GPU·NPU 백엔드 최적화
• Multi-Token Prediction(MTP)
• KV cache 세션 저장·복원
• constrained decoding
• function calling

원문 기준 Gemma 4 E2B는
Android GPU 52 tok/s,
iOS Metal 56 tok/s,
WebGPU 최대 76 tok/s decode 성능을 제시했습니다.

온디바이스 AI의 경쟁은
이제 모델 압축만이 아니라
런타임, 메모리, 세션, 도구 호출까지 포함한
전체 스택 싸움으로 가고 있습니다.

자세한 해설은 TechLLM 블로그에서 확인하세요.
🔗 https://techllm.github.io/posts/litert-lm-on-device-genai/
```

## Instagram 카드뉴스 구성

1. 서버 없이 76 tokens/sec?
2. LiteRT-LM은 Gemma 4용 온디바이스 LLM 런타임
3. MTP로 최대 2.2배 decode speedup
4. 세션 저장·복원으로 긴 대화의 prefill 비용 감소
5. Thinking Mode + constrained decoding + function calling
6. 결론: 온디바이스 AI는 실행 스택 싸움이다

## Hashtags

#AI #LLM #LiteRT #LiteRTLM #Gemma #Gemma4 #OnDeviceAI #EdgeAI #WebGPU #Android #iOS #GoogleAI #AI개발 #모바일AI #TechLLM

## 카드뉴스 이미지
`content/social/cards/litert-lm-on-device-genai/card-01~06.png`
