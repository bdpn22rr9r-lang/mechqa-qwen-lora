"""Fail when any LoRA tensor contains NaN or Inf."""
import argparse
import torch
from safetensors.torch import load_file

p = argparse.ArgumentParser()
p.add_argument("adapter")
a = p.parse_args()
state = load_file(a.adapter)
bad = [(name, int(torch.isnan(t).sum()), int(torch.isinf(t).sum())) for name, t in state.items() if not torch.isfinite(t).all()]
print("tensor_count=", len(state))
print("bad_tensor_count=", len(bad))
print("bad_examples=", bad[:10])
raise SystemExit(bool(bad))
