"""MathGraph / Metalogic Labs — E0005 frozen Hard candidate.

Explicit mutable workspace state anchored to immutable context.
Train: one cheap workspace update.
Eval: four tied workspace updates.
The token stream is encoded once; mutable workspace is a separate latent state.
"""
from __future__ import annotations
import torch
import torch.nn.functional as F
from torch import Tensor, nn
from benchmark import ModelSpec, OptimizerBundle, OptimizerSpec, Submission, assert_model_state

D_MODEL = 128
NUM_HEADS = 4
EVAL_WORKSPACE_STEPS = 4

class Config:
    def __init__(self, vocab_size: int, max_seq_len: int) -> None:
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len

class RMSNorm(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
    def forward(self, x: Tensor) -> Tensor:
        return F.rms_norm(x, (x.shape[-1],), self.weight)

class Block(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.attention_norm = RMSNorm(D_MODEL)
        self.qkv = nn.Linear(D_MODEL, 3 * D_MODEL)
        self.out = nn.Linear(D_MODEL, D_MODEL)
        self.mixer_norm = RMSNorm(D_MODEL)
        self.up = nn.Linear(D_MODEL, 4 * D_MODEL)
        self.down = nn.Linear(4 * D_MODEL, D_MODEL)

    def _self_mask(self, attention_mask: Tensor | None, batch: int, length: int, device: torch.device) -> Tensor | None:
        if attention_mask is None:
            return None
        if attention_mask.shape == (batch, length):
            mask = attention_mask[:, None, None, :]
        elif attention_mask.shape == (batch, length, length):
            mask = attention_mask[:, None, :, :]
        else:
            raise ValueError("invalid attention_mask shape")
        return mask.to(device=device, dtype=torch.bool)

    def _key_mask(self, attention_mask: Tensor | None, batch: int, length: int, device: torch.device) -> Tensor | None:
        if attention_mask is None:
            return None
        if attention_mask.shape == (batch, length):
            key_valid = attention_mask
        elif attention_mask.shape == (batch, length, length):
            key_valid = attention_mask.to(dtype=torch.bool).any(dim=1)
        else:
            raise ValueError("invalid attention_mask shape")
        return key_valid[:, None, None, :].to(device=device, dtype=torch.bool)

    def forward(self, x: Tensor, attention_mask: Tensor | None) -> Tensor:
        residual = x
        x = self.attention_norm(x)
        batch, length, _ = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q = q.view(batch, length, NUM_HEADS, -1).transpose(1, 2)
        k = k.view(batch, length, NUM_HEADS, -1).transpose(1, 2)
        v = v.view(batch, length, NUM_HEADS, -1).transpose(1, 2)
        x = F.scaled_dot_product_attention(q, k, v, attn_mask=self._self_mask(attention_mask, batch, length, x.device))
        x = x.transpose(1, 2).contiguous().view(batch, length, D_MODEL)
        x = residual + self.out(x)
        return x + self.down(F.gelu(self.up(self.mixer_norm(x))))

    def workspace_step(self, workspace: Tensor, context: Tensor, attention_mask: Tensor | None) -> Tensor:
        """Update one mutable latent workspace token against immutable prompt context."""
        residual = workspace
        ws_n = self.attention_norm(workspace)
        ctx_n = self.attention_norm(context)
        batch, length, _ = context.shape
        q = self.qkv(ws_n).chunk(3, dim=-1)[0]
        _, k, v = self.qkv(ctx_n).chunk(3, dim=-1)
        q = q.view(batch, 1, NUM_HEADS, -1).transpose(1, 2)
        k = k.view(batch, length, NUM_HEADS, -1).transpose(1, 2)
        v = v.view(batch, length, NUM_HEADS, -1).transpose(1, 2)
        x = F.scaled_dot_product_attention(q, k, v, attn_mask=self._key_mask(attention_mask, batch, length, context.device))
        x = x.transpose(1, 2).contiguous().view(batch, 1, D_MODEL)
        x = residual + self.out(x)
        return x + self.down(F.gelu(self.up(self.mixer_norm(x))))

class Model(nn.Module):
    def __init__(self, spec: ModelSpec) -> None:
        super().__init__()
        self.config = Config(spec.vocab_size, spec.max_seq_len)
        self.token_embedding = nn.Embedding(spec.vocab_size, D_MODEL)
        self.position_embedding = nn.Embedding(spec.max_seq_len, D_MODEL)
        self.block = Block()
        self.final_norm = RMSNorm(D_MODEL)
        self.head = nn.Linear(D_MODEL, spec.vocab_size, bias=False)
        self.head.weight = self.token_embedding.weight

    def forward(self, input_ids: Tensor, attention_mask: Tensor | None = None) -> tuple[Tensor, None]:
        positions = torch.arange(input_ids.shape[1], device=input_ids.device)
        context = self.token_embedding(input_ids) + self.position_embedding(positions)
        token_state = self.block(context, attention_mask)

        # Explicit state/context split. The mutable state is a single latent workspace
        # initialized from the encoded problem, not the full token stream itself.
        if attention_mask is not None and attention_mask.ndim == 2:
            weights = attention_mask.to(dtype=context.dtype).unsqueeze(-1)
            workspace = (context * weights).sum(dim=1, keepdim=True) / weights.sum(dim=1, keepdim=True).clamp_min(1.0)
        else:
            workspace = context.mean(dim=1, keepdim=True)

        steps = 1 if self.training else EVAL_WORKSPACE_STEPS
        for _ in range(steps):
            workspace = self.block.workspace_step(workspace, context, attention_mask)

        # Let the learned global state condition each output position while preserving
        # the baseline token-local representation and unbroken gradient path.
        token_state = token_state + workspace
        return self.head(self.final_norm(token_state)), None

def build_model(spec: ModelSpec) -> Model:
    model = Model(spec)
    assert_model_state(model, spec)
    return model

def build_optimizer(model: nn.Module, spec: OptimizerSpec) -> OptimizerBundle:
    return OptimizerBundle(torch.optim.AdamW(model.parameters(), lr=1e-3, betas=(0.9, 0.95), weight_decay=0.1, capturable=spec.device_type == "cuda"))

SUBMISSION = Submission(build_model=build_model, build_optimizer=build_optimizer)
