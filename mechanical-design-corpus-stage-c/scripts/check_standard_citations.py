"""标准编号格式检查 + 与标准核验台账关联(V3 第9节)。

检测 output 中出现的标准编号(GB/T、ISO、ASTM、DIN 等)格式是否规范(含年份/名称),
并报告每条引用的标准号(供人工核验台账)。无来源/版本/适用范围时引用标准是风险。
"""
from __future__ import annotations
import os, sys, argparse, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

# 标准编号模式(粗粒度)
STD_RE = re.compile(r"(GB[/／]T ?\d{3,6}(?:[.\-]\d+)?(?:-\d{4})?|ISO ?\d+(?:-\d+)?(?::\d{4})?|ASTM [A-Z]+\d+(?:-\d+)?|DIN \d+|JIS [A-Z]+\d+)")


def load_registry(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    return {row["standard_no"]: row for row in rows}


def run(path: str, registry_path: str) -> bool:
    recs = S.load_jsonl(path)
    registry = load_registry(registry_path)
    citations = []
    bare = []
    unknown = []
    inactive = []
    for r in recs:
        out = str(r.get("output", ""))
        for m in STD_RE.finditer(out):
            std = m.group(1)
            citations.append((r.get("id"), std))
            if not re.search(r"(19|20)\d{2}", std):
                bare.append((r.get("id"), std))
            row = registry.get(std)
            if row is None:
                unknown.append((r.get("id"), std))
            elif row.get("status") != "current":
                inactive.append((r.get("id"), std, row.get("status")))
    print(f"[std_cite] {path}: {len(recs)} 条, 标准引用 {len(citations)} 处, 缺年份 {len(bare)} 处")
    for rid, std in citations[:12]:
        print(f"  {rid}: {std}")
    if bare:
        print(f"  缺年份(风险): {[s for _, s in bare[:6]]}")
    if unknown:
        print(f"  未登记标准(失败): {unknown[:6]}")
    if inactive:
        print(f"  非现行标准(失败): {inactive[:6]}")
    return not bare and not unknown and not inactive


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="标准编号检查")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--registry", default="reports/standard_registry.json")
    a = ap.parse_args()
    ok = all(run(p, a.registry) for p in a.inputs)
    sys.exit(0 if ok else 1)
