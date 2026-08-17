import torch
import triton
import triton.language as tl
from task import input_t, output_t

@triton.jit
def _mm(a, b, c, M: tl.constexpr, N: tl.constexpr, K: tl.constexpr,
        BM: tl.constexpr, BN: tl.constexpr, BK: tl.constexpr):
    pid = tl.program_id(0)
    pm = pid // tl.cdiv(N, BN)
    pn = pid % tl.cdiv(N, BN)
    rm = pm * BM + tl.arange(0, BM)
    rn = pn * BN + tl.arange(0, BN)
    rk = tl.arange(0, BK)
    ap = a + rm[:, None] * K + rk[None, :]
    bp = b + rk[:, None] * N + rn[None, :]
    acc = tl.zeros((BM, BN), tl.float32)
    for k0 in range(0, K, BK):
        av = tl.load(ap, mask=(rm[:, None] < M) & (rk[None, :] + k0 < K), other=0.0)
        bv = tl.load(bp, mask=(rk[:, None] + k0 < K) & (rn[None, :] < N), other=0.0)
        acc += tl.dot(av, bv)
        ap += BK
        bp += BK * N
    tl.store(c + rm[:, None] * N + rn[None, :], acc.to(tl.float16), mask=(rm[:, None] < M) & (rn[None, :] < N))

def custom_kernel(data: input_t) -> output_t:
    a, b, c = data
    m, k = a.shape
    _, n = b.shape
    BM = 128
    BN = 128
    BK = 32
    grid = (triton.cdiv(m, BM) * triton.cdiv(n, BN),)
    _mm[grid](a, b, c, M=m, N=n, K=k, BM=BM, BN=BN, BK=BK, num_warps=4, num_stages=3)
    return c
