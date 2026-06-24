---
title: "엔비디아 Canary-1B-v2로 음성 인식·번역·SRT 자막을 한 번에 — 파이썬 구현 가이드"
date: 2026-06-24T13:10:00+09:00
draft: false
description: "엔비디아 Canary-1B-v2와 NeMo 툴킷으로 영어 음성을 받아 25개 언어로 번역하고, 단어·구간 타임스탬프까지 뽑아 SRT 자막 파일로 떨어뜨리는 전체 파이프라인을 파이썬 코드로 정리한다."
cover:
  image: "/images/nvidia-canary-1b-v2-asr-translation-srt-python/nvidia-canary-1b-v2-asr-translation-srt-python-cover.png"
  alt: "엔비디아 Canary-1B-v2 음성 인식 모델 표지 이미지"
  caption: "Source: MarkTechPost"
tags:
  - NVIDIA
  - Canary
  - ASR
  - SpeechTranslation
  - NeMo
  - SRT
  - Python
---

## 개요

엔비디아가 공개한 Canary-1B-v2는 1B 파라미터급 음성 모델인데, 영어 음성 인식 한 가지만 하지 않습니다. 영어로 받아 영어로 적기, 영어로 받아 25개 유럽 권역 언어로 옮기기, 단어 단위와 구간 단위 타임스탬프를 동시에 뽑기, 그 타임스탬프 그대로 SRT 자막 파일로 떨궈주기까지 한 모델 안에 다 들어 있습니다. 무거운 ffmpeg 파이프라인이나 별도 번역 API를 끼우지 않고도, NeMo 툴킷 한 줄로 호출이 끝납니다.

MarkTechPost가 6월 23일 공개한 튜토리얼은 이걸 콜랩 GPU 환경에서 처음부터 끝까지 돌리는 흐름을 보여줍니다. 코드를 그대로 따라가면 30분 안에 영상 자동 자막 시제품이 손에 떨어집니다. 이번 글은 그 코드를 한국어 작업 환경에서 다시 읽으면서, 각 구간이 실제 어떤 일을 하는지와 실무 적용 포인트를 같이 정리합니다.

## 핵심 요약

- **모델**: `nvidia/canary-1b-v2`, 1B 파라미터, 16 kHz 모노 입력 기준.
- **지원 언어**: 영어 포함 25개. 불가리아어·체코어·독일어·프랑스어·이탈리아어·폴란드어·러시아어·우크라이나어 등 유럽 권역.
- **기능**: ASR(음성→텍스트), 번역(영어 음성→다른 언어 텍스트), 단어/구간 타임스탬프, SRT 내보내기.
- **인터페이스**: NeMo `ASRModel.from_pretrained()` 한 줄로 로드. `transcribe()` 호출 시 `source_lang`, `target_lang`, `timestamps`, `batch_size` 인자만 조정.
- **속도 지표**: 실시간 배속(RTFx)으로 측정. GPU가 있으면 입력 길이 대비 수 배~수십 배 빠르게 처리됩니다.

## 본문

### 1. 환경 준비 — 의존성 한 번에

튜토리얼은 콜랩 기준이라 `apt-get`으로 `libsndfile1`, `ffmpeg`를 깔고, `nemo_toolkit[asr]`, `librosa`, `soundfile`, `pydub`을 PIP로 받습니다. NumPy는 2.2 이상 2.4 미만, SciPy는 1.15 이상으로 강제합니다. 이 버전 핀이 중요한데, NeMo 최신 빌드가 NumPy 2.x ABI에 맞춰져 있어 1.x가 깔린 환경에서는 import 단계부터 깨집니다.

```python
sh("apt-get -qq install -y libsndfile1 ffmpeg > /dev/null")
sh('pip install -q "nemo_toolkit[asr]"')
sh("pip install -q librosa soundfile pydub")
sh('pip install -q --force-reinstall --no-cache-dir "numpy>=2.2,<2.4" "scipy>=1.15"')
```

설치가 끝나면 콜랩 런타임을 강제로 재시작합니다(`os.kill(os.getpid(), 9)`). 같은 셀을 한 번 더 실행해야 본격 코드가 돕니다. 로컬 머신이라면 `python -c "import nemo.collections.asr"`가 깔끔하게 통과하는지부터 확인하는 게 안전합니다.

### 2. 모델 로딩과 지원 언어 확인

GPU 가용성을 먼저 확인하고, 25개 지원 언어 코드를 dict로 박아 둡니다. 이 코드 표는 나중에 `target_lang` 인자에 그대로 넘기는 키이기 때문에 한 번 정리해 두면 편합니다.

```python
LANGS = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "uk": "Ukrainian",
    # ... 총 25개
}
from nemo.collections.asr.models import ASRModel
asr_model = ASRModel.from_pretrained(model_name="nvidia/canary-1b-v2").to(DEVICE).eval()
```

CPU에서도 돌긴 하지만 1B 모델이라 체감 속도가 많이 떨어집니다. T4급 GPU만 있어도 짧은 클립은 1초 이내로 끝납니다.

### 3. 16 kHz 모노 정규화 — 안 맞추면 정확도가 흔들립니다

Canary는 16 kHz 모노 PCM 입력을 가정합니다. `librosa.load(path, sr=16000, mono=True)`로 다운샘플·모노화한 뒤 `soundfile`로 다시 쓰는 보일러플레이트가 필요합니다. URL로 받은 mp3나 채널이 둘인 wav를 그대로 넣으면 결과가 묘하게 어그러집니다.

```python
def prepare_audio(path_or_url, out_path=None):
    if str(path_or_url).startswith(("http://", "https://")):
        local = "/content/_dl_" + os.path.basename(path_or_url.split("?")[0])
        urllib.request.urlretrieve(path_or_url, local)
        path_or_url = local
    audio, _ = librosa.load(path_or_url, sr=16000, mono=True)
    if out_path is None:
        base = os.path.splitext(os.path.basename(path_or_url))[0]
        out_path = f"/content/{base}_16k_mono.wav"
    sf.write(out_path, audio, 16000, subtype="PCM_16")
    return out_path, len(audio) / 16000
```

이 단계가 실무에선 가장 자주 사고가 납니다. 유튜브에서 받은 영상의 오디오 트랙은 보통 44.1 kHz 스테레오 AAC라, ffmpeg로 한 번 풀고 다시 받아야 합니다.

### 4. ASR과 번역 — 같은 호출, 인자만 다르게

영어 음성을 영어 텍스트로 받는 기본 ASR과, 영어 음성을 프랑스어·독일어·스페인어·이탈리아어로 옮기는 번역이 같은 `transcribe()` 호출로 끝납니다. `target_lang`만 바꿔주면 됩니다.

```python
res = asr_model.transcribe(sample_wav, source_lang="en", target_lang="en")
print("Transcript:", res[0].text)

for tgt in ["fr", "de", "es", "it"]:
    out = asr_model.transcribe(sample_wav, source_lang="en", target_lang=tgt)
    print(f"EN -> {LANGS[tgt]} ({tgt}): {out[0].text}")
```

별도 번역 API를 거치지 않으니 지연이 줄고, ASR 결과를 한 번 더 번역기에 넣을 때 생기는 누락·왜곡도 줄어듭니다. 다만 한국어·일본어·중국어는 지원 목록에 없습니다. 동아시아 언어가 필요하면 NeMo의 다른 다국어 ASR 라인업이나 위스퍼 계열을 같이 두고 골라야 합니다.

### 5. 타임스탬프와 SRT 자막 — 자동 자막 파이프라인의 핵심

`timestamps=True`로 호출하면 단어 단위와 구간 단위 타임스탬프가 같이 나옵니다. 구간 타임스탬프는 그대로 SRT 포맷으로 풀어주면 됩니다.

```python
def _srt_time(t):
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def segments_to_srt(segments, out_path="/content/output.srt"):
    lines = []
    for i, seg in enumerate(segments, 1):
        lines += [
            str(i),
            f"{_srt_time(seg['start'])} --> {_srt_time(seg['end'])}",
            seg["segment"].strip(),
            "",
        ]
    open(out_path, "w", encoding="utf-8").write("\n".join(lines))
    return out_path

fr_ts = asr_model.transcribe(sample_wav, source_lang="en", target_lang="fr", timestamps=True)
segments_to_srt(fr_ts[0].timestamp["segment"], "/content/subtitles_fr.srt")
```

번역과 타임스탬프가 같이 떨어진다는 점이 특히 쓸 만합니다. 영어 강연을 받아 프랑스어 자막을 자동으로 만들고 싶다면 위 한 줄로 끝납니다. 단어 단위 타임스탬프도 같이 잡히므로, 자막 한 줄 안에서 한 단어만 강조하는 가라오케 스타일도 어렵지 않게 구현할 수 있습니다.

### 6. 긴 오디오·배치·속도 측정

긴 클립은 그대로 `transcribe()`에 넘기면 됩니다. 튜토리얼은 같은 샘플을 6번 이어 붙여(`np.tile`) 긴 클립을 만들고, 처음 300자를 찍어 정상 동작을 확인합니다. 배치는 파일 리스트와 `batch_size`만 넘기면 됩니다.

```python
long_audio = np.tile(librosa.load(sample_wav, sr=16000, mono=True)[0], 6)
sf.write("/content/long.wav", long_audio, 16000, subtype="PCM_16")
long_out = asr_model.transcribe("/content/long.wav", source_lang="en", target_lang="en", batch_size=1)

batch = asr_model.transcribe(["/content/clip_a.wav", "/content/clip_b.wav"],
                             source_lang="en", target_lang="en", batch_size=2)
```

속도는 실시간 배속(RTFx)으로 잽니다. 입력 오디오 길이를 처리 시간으로 나눈 값입니다. 10초 클립을 1초 만에 끝내면 RTFx ≈ 10. T4에서 짧은 영어 클립은 보통 두 자릿수 RTFx가 나옵니다. 즉 1시간짜리 강연이라면 몇 분 안에 자막이 떨어진다는 뜻입니다.

## 실무자가 볼 핵심 포인트

- **단일 모델, 단일 API**: ASR·번역·타임스탬프가 한 호출 안에 끝납니다. 외부 번역 서비스를 거치지 않으니 비용·지연·프라이버시 모두 유리합니다.
- **언어 한정**: 25개 유럽 권역 언어가 전부입니다. 한·중·일이 필요하면 별도 ASR 라인을 추가해야 합니다.
- **입력 표준화 의무**: 16 kHz 모노 PCM이 아니면 정확도가 흔들립니다. `librosa.load(..., sr=16000, mono=True)`를 파이프라인 맨 앞에 박아 두세요.
- **버전 핀 주의**: NumPy 2.2~2.3, SciPy 1.15 이상이 아니면 import에서 깨집니다. requirements.txt에 명시 고정 권장.
- **자막 자동화 적합**: 영어 강연 → 프랑스어/독일어/스페인어 자막 자동 생성 같은 시나리오에 바로 투입 가능. 단, 고유명사·전문 용어는 사후 교정 단계가 여전히 필요합니다.
- **GPU 권장**: 1B 모델이라 CPU에서는 체감 속도가 떨어집니다. T4급 한 장이면 충분하고, 더 큰 워크로드라면 A10/L4 정도부터 의미가 있습니다.

## 원문 출처

[원문 보기](https://www.marktechpost.com/2026/06/23/how-to-use-nvidia-canary-1b-v2-for-asr-translation-and-automatic-srt-subtitle-export-in-python/)
