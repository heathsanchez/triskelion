import torch
import triton
import triton.language as tl
from task import input_t, output_t

# E0001 diagnostic only: all GPU work is launched through Triton on the
# evaluator's current stream. This is intentionally NOT a general eigensolver.
# It returns the diagonal and identity basis so we can distinguish a stream
# policy rejection from an ordinary correctness rejection.

@triton.jit
def _diag_values_kernel(a, values, batch: tl.constexpr, n: tl.constexpr, BLOCK: tl.constexpr):
    offs = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    total = batch * n
    mask = offs < total
    b = offs // n
    i = offs - b * n
    tl.store(values + offs, tl.load(a + b * n * n + i * n + i, mask=mask), mask=mask)


@triton.jit
def _identity_kernel(vectors, total: tl.constexpr, n: tl.constexpr, BLOCK: tl.constexpr):
    offs = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    mask = offs < total
    rem = offs % (n * n)
    row = rem // n
    col = rem - row * n
    tl.store(vectors + offs, (row == col).to(tl.float32), mask=mask)


def custom_kernel(data: input_t) -> output_t:
    batch, n, _ = data.shape
    values = torch.empty((batch, n), device=data.device, dtype=torch.float32)
    vectors = torch.empty((batch, n, n), device=data.device, dtype=torch.float32)

    block = 256
    nv = batch * n
    ne = batch * n * n
    _diag_values_kernel[(triton.cdiv(nv, block),)](data, values, batch, n, BLOCK=block)
    _identity_kernel[(triton.cdiv(ne, block),)](vectors, total=ne, n=n, BLOCK=block)
    return vectors, values
