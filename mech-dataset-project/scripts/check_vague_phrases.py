"""检测空泛表达频率(V3 第9节)。

"应按相关标准""需客户批准""与图纸一致""根据经验"等空泛句代替工程判断的频率报告。
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

VAGUE = [
    "应按相关标准", "按相关规范", "需客户批准", "经客户批准", "与图纸一致",
    "根据经验", "经验表明", "通常认为", "一般认为", "视情况而定",
    "综合考虑", "适当处理", "妥善处理", "符合要求", "满足要求",
]


def run(path: str) -> bool:
    recs = S.load_jsonl(path)
    hits = Counter()
    affected = 0
    for r in recs:
        out = str(r.get("output", ""))
        found = [p for p in VAGUE if p in out]
        if found:
            affected += 1
            for p in found:
                hits[p] += 1
    print(f"[vague] {path}: {len(recs)} 条, 含空泛表达 {affected} 条")
    for p, c in hits.most_common(10):
        print(f"  {p}: {c}")
    return affected == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="空泛表达检测")
    ap.add_argument("inputs", nargs="+")
    a = ap.parse_args()
    ok = all(run(p) for p in a.inputs)
    sys.exit(0 if ok else 1)
