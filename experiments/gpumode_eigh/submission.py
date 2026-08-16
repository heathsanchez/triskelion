import torch
from task import input_t, output_t

# Frozen upstream baseline from gpu-mode/reference-kernels
# problems/linalg/eigh_py/submission.py
# Do not modify without an experiment ID and prospective hypothesis.
def custom_kernel(data: input_t) -> output_t:
    values, vectors = torch.linalg.eigh(data)
    return vectors, values
