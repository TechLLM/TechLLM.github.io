---
title: "nn.Linear에서 Fused MLP까지 — PyTorch 프로파일링으로 본 커널 융합의 단계"
date: 2026-06-11T20:14:00+09:00
draft: false
description: "Hugging Face가 공개한 PyTorch 프로파일링 2부. nn.Linear의 bias가 GEMM 에필로그로 접히는 과정부터 torch.compile의 Triton 융합, Liger 수제 커널까지. 같은 MLP가 5개 커널에서 1개 커널로 줄어드는 단계를 트레이스로 들여다본다."
tags: ["PyTorch", "GPU프로파일링", "커널융합", "torch.compile", "Triton"]
cover:
  image: /images/torch-mlp-fusion-pytorch-profiling-part2/torch-mlp-fusion-pytorch-profiling-part2-cover.png
  alt: "From nn.Linear to a fused MLP — profiling visualization"
---

## 개요

같은 MLP 한 덩어리를 세 가지 방식으로 돌려봅니다. eager 모드, `torch.compile`, 그리고 Hugging Face Hub에서 받아온 Liger 수제 커널. 코드로 보면 똑같이 한 줄짜리 forward인데, 트레이스를 열어 보면 GPU가 하는 일이 전혀 다릅니다. Hugging Face가 6월 11일 공개한 "Profiling in PyTorch (Part 2)"는 이 차이를 단계별 트레이스로 짚어 줍니다.

핵심은 한 가지입니다 — **언제, 어디서, 어떻게 융합(fusion)이 일어나는가**. bias addition은 이미 `nn.Linear` 안에서 GEMM의 에필로그로 접혀 있고, GeLU·곱셈·reshape는 컴파일러가 한 커널로 합쳐 주고, 수제 커널은 같은 융합을 미리 컴파일된 바이너리로 가져옵니다. 같은 결과를 만드는 길이 세 갈래라는 얘기입니다.

![source 트레이스 요약 표](/images/torch-mlp-fusion-pytorch-profiling-part2/figure-mlp-table.png)

## 핵심 요약

- `nn.Linear`의 bias는 별도 커널이 아닙니다. cuBLAS GEMM 안에 **에필로그로 접혀** 메모리 트래픽을 덜어냅니다.
- eager 모드 MLP는 GeGLU 한 번에 **GPU 커널 5개**가 뜹니다. GeLU 결과(50MB짜리 중간 텐서)가 HBM에 한 번 쓰였다가 다시 읽힙니다.
- `torch.compile`은 GeLU + 곱셈 + reshape를 **하나의 Triton 융합 커널**로 묶습니다. 중간 텐서가 레지스터에 머무릅니다. 89.4 µs.
- Liger 수제 커널은 같은 융합을 **사전 컴파일된 바이너리**로 가져옵니다. 92.8 µs. Dynamo 가드도, 모양 바뀔 때마다의 재컴파일도 없습니다.
- 셋 다 **세 개의 GEMM 자체는 동일한 cuBLAS 커널**을 그대로 씁니다. 줄어드는 건 그 사이의 pointwise 연산입니다.

## 본문

### bias는 이미 융합돼 있다

`linear_layer(x)`는 수식으로 `y = x @ w.T + b`입니다. 처음 트레이스를 열어 보면 사람들이 가장 자주 놀라는 지점이 여기입니다. `aten::add`가 어디에도 안 보입니다.

bias 덧셈은 cuBLAS GEMM 커널 안에 **에필로그**로 합쳐져 있습니다. matmul 결과가 메모리에 한 번 더 나갔다 들어오는 일을 막기 위한 기본 최적화입니다. PyTorch는 따로 한 일이 없고, 그냥 cuBLAS가 처음부터 그렇게 만들어져 있습니다.

그 와중에 `aten::t`(전치)는 CUDA 시간이 `0.000µs`로 찍힙니다. 데이터를 복사하지 않고 **stride만 바꿉니다**.

```python
>>> M = torch.tensor([[0, 1], [2, 3], [4, 5]])
>>> M.shape, M.stride()
(torch.Size([3, 2]), (2, 1))
>>> T = M.t()
>>> T.shape, T.stride()
(torch.Size([2, 3]), (1, 2))   # stride만 뒤집힌다, 데이터는 그대로
```

reshape, view, transpose 같은 메타데이터 연산들이 트레이스에서 모두 0초로 찍히는 이유도 같습니다. **연산이 아니라 텐서의 헤더 수정**입니다.

커널 이름도 정보를 담고 있습니다. `cutlass_80_wmma_tensorop_bf16_s161616gemm_bf16_32x32_32x1_tn_align8` 같은 이름의 끝에 붙는 `tn`, `nn`, `tt`는 입력·가중치의 전치 여부를 알려 줍니다. **같은 이름이면 같은 GPU 작업**이라는 점이, 뒤에서 변화를 비교할 때 유용한 신호가 됩니다.

### eager MLP — 커널 5개와 50MB짜리 왕복

이번에는 GeGLU MLP입니다. Llama 계열에서 흔히 쓰는 그 구조입니다.

```python
class SimpleGeGLUMLP(nn.Module):
    def __init__(self, dim, hidden):
        super().__init__()
        self.gate_proj = nn.Linear(dim, hidden, bias=False)
        self.up_proj   = nn.Linear(dim, hidden, bias=False)
        self.down_proj = nn.Linear(hidden, dim, bias=False)

    def forward(self, x):
        g = self.gate_proj(x)
        u = self.up_proj(x)
        h = F.gelu(g, approximate="tanh")
        m = h * u
        y = self.down_proj(m)
        return y
```

`batch=64, seq=128, dim=768, hidden=3072`로 돌려 보면 GPU 커널이 다섯 번 뜹니다.

1. `gate_proj` GEMM — `128x128` 타일
2. `up_proj` GEMM — 같은 `128x128` 타일
3. GeLU pointwise 커널
4. 곱셈 pointwise 커널
5. `down_proj` GEMM — 모양이 달라 `128x256` 타일

여기서 비용을 갉아먹는 게 3·4번입니다. GeLU가 만든 `[8192, 3072]` 모양의 중간 텐서(약 **50MB**)가 HBM에 한 번 통째로 쓰였다가, 곱셈 커널이 다시 통째로 읽어 옵니다. 계산은 가벼운데 메모리 왕복이 무겁습니다.

### torch.compile — Triton 한 덩어리

같은 코드 그대로 `--compile`을 켜 봅니다.

```bash
uv run 03_simple_mlp.py --batch 64 --seq 128 --dim 768 --hidden 3072 --compile
```

GeLU + 곱셈 + reshape가 **하나의 Triton 커널**로 합쳐집니다. 이름이 `triton_poi_fused__unsafe_view_gelu_mul_0`처럼 길게 찍히는데, 풀어 보면 `view`, `gelu`, `mul`이 하나에 들어 있다는 뜻입니다. 중간 텐서는 더 이상 HBM으로 안 나갑니다. **레지스터(온칩 메모리)에 머무르다가 곧바로 곱해집니다.**

GEMM 세 개는 그대로입니다. 같은 cuBLAS 커널, 같은 이름. 컴파일러가 손대지 않는 영역입니다.

![torch.compile 융합 후 트레이스](/images/torch-mlp-fusion-pytorch-profiling-part2/figure-fused-trace.png)

한 가지 단서가 있습니다. `torch.compile`은 입력 모양에 특수화돼서 컴파일됩니다. 배치 크기나 시퀀스 길이가 바뀌면 Dynamo가 다시 컴파일을 합니다. 추론 시점에 모양이 자주 흔들리는 상황에서는 그 비용이 그대로 표면으로 올라옵니다.

### Liger 수제 커널 — 미리 만들어 둔 같은 융합

세 번째 길은 사람이 손으로 다듬어 둔 융합을 그대로 가져오는 겁니다.

```python
from kernels import get_kernel

kernels_layers = get_kernel("kernels-community/liger-kernels", version=1).layers
kernels_geglu_mlp = kernels_layers.LigerGEGLUMLP(Config()).to(
    device, dtype=torch.bfloat16
).eval()
```

`nn.Module`처럼 그대로 꽂아 쓰면 됩니다. Hugging Face Hub에서 받아오는 순간, 융합된 GeGLU 커널이 사전 컴파일된 바이너리로 같이 들어옵니다. Dynamo도, 추적도, 컴파일 단계도 없습니다.

![Liger 커널 트레이스](/images/torch-mlp-fusion-pytorch-profiling-part2/figure-liger-trace.png)

수치는 정직합니다. **컴파일된 Triton 89.4 µs, Liger 92.8 µs.** 마지막 몇 µs는 입력 모양에 맞춰 컴파일러가 짜낸 특수화의 보상입니다. 대신 Liger는 모양이 흔들려도 같은 속도를 냅니다. 가드도, 재컴파일도, "내 머신에서는 되는데" 문제도 없습니다.

### 무엇이 바뀌고, 무엇이 그대로인가

| 단계 | 바뀐 것 | 그대로인 것 |
| --- | --- | --- |
| eager `nn.Linear` | bias가 GEMM 에필로그로 접힘 | — |
| compiled `nn.Linear` | CPU dispatch op이 사라짐 | cuBLAS 커널 동일 |
| eager MLP | 커널 5개, 중간 텐서 HBM 왕복 | GEMM 세 개 동일 |
| compiled MLP | GeLU+mul+reshape → 1개 Triton 커널 | GEMM 세 개 동일 |
| Liger MLP | 같은 융합 + Dynamo 비용 0 | GEMM 세 개 동일 |

융합으로 줄어드는 영역은 결국 **pointwise 연산과 그 사이의 메모리 왕복**입니다. GEMM 자체는 셋 다 동일한 cuBLAS 커널을 그대로 호출합니다.

## 실무자가 볼 핵심 포인트

- **bias는 이미 융합돼 있다.** Linear 앞단에서 추가 add 커널을 찾으려고 하지 말 것. 트레이스에 안 보이는 게 정상.
- **트레이스를 열기 전에 먼저 추측을 적어 두자.** 예상과 실제의 어긋남이 곧 학습 신호. 무작정 트레이스부터 열면 노이즈만 보인다.
- **커널 이름이 바뀌면 GPU 작업이 바뀐 거다.** `tn`, `nn`, 타일 크기, 데이터 타입 — 이름의 해시에 그대로 박혀 있다. 이름이 같으면 같은 일을 한다.
- **메타데이터 연산은 비용이 없다.** `aten::t`, `aten::view`, `aten::reshape`가 0µs로 찍히는 건 정상이다. stride만 다시 쓴다.
- **`torch.compile` vs 수제 커널 선택 기준** — 입력 모양이 안정적이면 컴파일이 마지막 µs까지 가져간다. 모양이 자주 흔들리면 Dynamo 가드와 재컴파일 비용이 표면으로 올라오니, 수제 커널 쪽이 운영상 안전하다.
- **추론 핫패스에서 50MB짜리 중간 텐서가 HBM을 왕복하고 있지 않은지 확인하자.** GeLU+mul처럼 가볍게 보이는 pointwise 쌍이 실제로는 메모리 대역폭을 갉는 주범인 경우가 흔하다.

다음 편은 attention 블록과 트랜스포머 전체로 넘어간다고 합니다. 이 시리즈가 좋은 이유는, 평소 "그냥 잘 돌아가는 것"으로 흘려보내던 `nn.Linear` 한 줄을 다시 들여다보게 만든다는 점입니다.

## 원문 출처

- Hugging Face 블로그 — [Profiling in PyTorch (Part 2): From nn.Linear to a Fused MLP](https://huggingface.co/blog/torch-mlp-fusion)
- 저자: Aritra Roy Gosthipaty, Rémi Ouazan Reboul, Sergio Paniego, Pedro Cuenca, Sayak Paul
- 발행일: 2026-06-11
- 예제 코드: [ariG23498/profiling-pytorch](https://huggingface.co/datasets/ariG23498/profiling-pytorch)
