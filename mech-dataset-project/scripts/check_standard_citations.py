"""标准编号格式检查 + 与标准核验台账关联(V3 第9节)。

检测 output 中出现的标准编号(GB/T、ISO、ASTM、DIN 等)格式是否规范(含年份/名称),
并报告每条引用的标准号(供人工核验台账)。无来源/版本/适用范围时引用标准是风险。
"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

# 标准编号模式(粗粒度)
STD_RE = re.compile(r"(GB[/／]T ?\d{3,6}(?:[.\-]\d+)?(?:-\d{4})?|ISO ?\d+(?:-\d+)?(?::\d{4})?|ASTM [A-Z]+\d+(?:-\d+)?|DIN \d+|JIS [A-Z]+\d+)")


def run(path: str) -> bool:
    recs = S.load_jsonl(path)
    citations = []
    bare = []  # 缺年份的标准号(风险)
    for r in recs:
        out = str(r.get("output", ""))
        for m in STD_RE.finditer(out):
            std = m.group(1)
            citations.append((r.get("id"), std))
            if not re.search(r"(19|20)\d{2}", std):  # 无年份
                bare.append((r.get("id"), std))
    print(f"[std_cite] {path}: {len(recs)} 条, 标准引用 {len(citations)} 处, 缺年份 {len(bare)} 处")
    for rid, std in citations[:12]:
        print(f"  {rid}: {std}")
    if bare:
        print(f"  缺年份(风险): {[s for _, s in bare[:6]]}")
    # 仅打印报告, 不因引用而 fail(标准引用本身合法); 缺年份为风险提示
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="标准编号检查")
    ap.add_argument("inputs", nargs="+")
    a = ap.parse_args()
    for p in a.inputs:
        run(p)
    sys.exit(0)
