"""检测跨样本重复的长句模板。

针对 V2 失败主因"边界模板复制"。短 n-gram 会把"失效模式"等正常术语
误报为模板,因此只统计去掉编号后的完整长句。

用法: python check_repeated_templates.py <jsonl> [-n 6] [--threshold 3]
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S


def run(path: str, n: int = 12, threshold: int = 5, top: int = 12) -> bool:
    recs = S.load_jsonl(path)
    ng_count = Counter()
    for r in recs:
        out = str(r.get("output", ""))
        sentences = set()
        for text in re.split(r"[。；;！？!?\n]+", out):
            text = re.sub(r"^\s*(?:\d+[.、]|边界[:：]?|注意[:：]?|验证要求[:：]?)\s*", "", text).strip()
            if len(text) >= n:
                sentences.add(text)
        for sentence in sentences:
            ng_count[sentence] += 1
    repeated = [(g, c) for g, c in ng_count.most_common(80) if c >= threshold]
    print(f"[templates] {path}: {len(recs)} 条, 重复长句(长度>= {n}, >= {threshold} 条出现): {len(repeated)} 个")
    for g, c in repeated[:top]:
        print(f"  {c} 条: {g!r}")
    return len(repeated) == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="重复模板/n-gram 检测")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-n", type=int, default=12, help="最短句长")
    ap.add_argument("--threshold", type=int, default=5, help="最少跨样本出现次数")
    a = ap.parse_args()
    ok = all(run(p, a.n, a.threshold) for p in a.inputs)
    sys.exit(0 if ok else 1)
