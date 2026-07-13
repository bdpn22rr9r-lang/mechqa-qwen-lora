"""检测重复前缀/后缀/跨样本高频 n-gram。

针对 V2 失败主因"边界模板复制": 若很多 output 共享相同的 6+ 字片段,
说明存在复制模板(应因题而异)。报告跨样本高频片段。

用法: python check_repeated_templates.py <jsonl> [-n 6] [--threshold 3]
"""
from __future__ import annotations
import os, sys, argparse
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S


def run(path: str, n: int = 6, threshold: int = 3, top: int = 12) -> bool:
    recs = S.load_jsonl(path)
    ng_count = Counter()
    for r in recs:
        out = str(r.get("output", "")).replace("\n", "")
        grams = {out[i:i + n] for i in range(len(out) - n + 1)}  # 每条每片段只计一次
        for g in grams:
            ng_count[g] += 1
    repeated = [(g, c) for g, c in ng_count.most_common(80) if c >= threshold]
    print(f"[templates] {path}: {len(recs)} 条, 跨样本高频 {n}-gram(>= {threshold} 条出现): {len(repeated)} 个")
    for g, c in repeated[:top]:
        print(f"  {c} 条: {g!r}")
    return len(repeated) == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="重复模板/n-gram 检测")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-n", type=int, default=6)
    ap.add_argument("--threshold", type=int, default=3)
    a = ap.parse_args()
    ok = all(run(p, a.n, a.threshold) for p in a.inputs)
    sys.exit(0 if ok else 1)
