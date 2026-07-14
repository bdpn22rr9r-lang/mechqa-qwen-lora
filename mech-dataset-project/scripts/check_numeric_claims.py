"""数值来源检查: output 中的具体数值必须能在 input(或 context/source)中找到来源。

规则:
  - engineering_calculation / context_extraction / tool_awareness 类豁免
    (数值可来自计算、上下文抽取或工具)
  - 其余类型(design_review/fatigue_failure/info_insufficient 等):
    output 出现的具体数值若在 input 中找不到同名来源 → 标记"无来源数值"(疑似编造)
"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:MPa|GPa|kPa|Pa|%|mm|µm|HRC|HBW|HV|°C|r/min|rpm|×10\^?\d+)", re.IGNORECASE)
EXEMPT = {"engineering_calculation", "context_extraction", "tool_awareness"}


def norm_num(s: str) -> str:
    return re.sub(r"\s+", "", s).lower()


def strip_ranges(t: str) -> str:
    """移除工程经验范围(2~4 mm / 2.5~3.5)与带 ≥≤约达 的参数值。

    这些有手册依据,不属于 V3 禁止的"编造固定设计值"(如 R2、HRC45)。
    只保留孤立精确数值供来源核验。
    """
    t = re.sub(r"\d+(?:\.\d+)?\s*[~\-–到至]\s*\d+(?:\.\d+)?\s*(?:MPa|GPa|kPa|Pa|%|mm|µm|HRC|HBW|HV|°C|倍|mm/r|r/min)", "", t)
    t = re.sub(r"[≥≤约达]\s*\d+(?:\.\d+)?\s*(?:MPa|GPa|%|mm|倍|°C)", "", t)
    return t


def run(path: str) -> bool:
    recs = S.load_jsonl(path)
    problems = []
    for r in recs:
        if r.get("task_type") in EXEMPT:
            continue
        out = str(r.get("output", ""))
        inp = str(r.get("input", ""))
        out_nums = {norm_num(x) for x in NUM_RE.findall(strip_ranges(out))}
        inp_nums = {norm_num(x) for x in NUM_RE.findall(strip_ranges(inp))}
        unsourced = sorted(n for n in out_nums if n and n not in inp_nums)
        if unsourced:
            problems.append((r.get("id"), r.get("task_type"), unsourced))
    print(f"[numeric] {path}: {len(recs)} 条, 含无来源数值 {len(problems)} 条")
    for rid, tt, nums in problems[:10]:
        print(f"  {rid} ({tt}): {nums}")
    return len(problems) == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="无来源数值检查")
    ap.add_argument("inputs", nargs="+")
    a = ap.parse_args()
    ok = all(run(p) for p in a.inputs)
    sys.exit(0 if ok else 1)
