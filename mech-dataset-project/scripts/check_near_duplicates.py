"""近似重复检查: 基于 difflib 的文本相似度(标准库,零依赖)。

对 instruction + input + output 两两计算相似度,超过阈值则告警。
只比较 input 会把同一案例的原因/控制/检验任务误判为完全重复。
"""
from __future__ import annotations
import os, sys, argparse, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S


def run(path: str, threshold: float = 0.9) -> bool:
    recs = S.load_jsonl(path)
    # ponytail: O(n^2) 适合阶段A/阶段B；到5000条时改用分桶或MinHash。
    texts = ["\n".join(str(r.get(k, "")) for k in ("instruction", "input", "output")) for r in recs]
    ids = [r.get("id", "") for r in recs]
    near = []
    n = len(texts)
    for i in range(n):
        for j in range(i + 1, n):
            r = difflib.SequenceMatcher(None, texts[i], texts[j]).ratio()
            if r >= threshold:
                near.append((ids[i], ids[j], round(r, 3)))
    print(f"[near_dup] {path}: {n} 条, 近似对(>= {threshold}) {len(near)}")
    for a, b, r in near[:10]:
        print(f"  {a} ~ {b} : {r}")
    return len(near) == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="近似重复检查")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-t", "--threshold", type=float, default=0.9)
    a = ap.parse_args()
    ok = all(run(p, a.threshold) for p in a.inputs)
    sys.exit(0 if ok else 1)
