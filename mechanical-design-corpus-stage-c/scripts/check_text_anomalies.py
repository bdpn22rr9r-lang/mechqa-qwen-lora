"""中文乱码、异常控制字符、超长样本检查(V3 第9节)。"""
from __future__ import annotations
import os, sys, argparse, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

MAX_LEN = 4000  # 单字段超此视为超长


def has_control(text: str) -> bool:
    return any(unicodedata.category(ch) == "Cc" and ch not in "\n\t" for ch in text)


def looks_garbled(text: str) -> bool:
    # 中文常见乱码特征: 替换符、半角乱码聚集、形如 '璇峰' 的 GBK 被误读 UTF-8
    if "�" in text:
        return True
    return False


def run(path: str) -> bool:
    recs = S.load_jsonl(path)
    long_recs, ctrl, garbled = [], [], []
    for r in recs:
        for f in ("instruction", "input", "output"):
            v = str(r.get(f, ""))
            if len(v) > MAX_LEN:
                long_recs.append((r.get("id"), f, len(v)))
            if has_control(v):
                ctrl.append((r.get("id"), f))
            if looks_garbled(v):
                garbled.append((r.get("id"), f))
    print(f"[anomalies] {path}: {len(recs)} 条, 超长 {len(long_recs)}, 控制字符 {len(ctrl)}, 疑似乱码 {len(garbled)}")
    for x in long_recs[:5]:
        print("  超长:", x)
    for x in ctrl[:5]:
        print("  控制字符:", x)
    for x in garbled[:5]:
        print("  疑似乱码:", x)
    return not (long_recs or ctrl or garbled)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="文本异常检查")
    ap.add_argument("inputs", nargs="+")
    a = ap.parse_args()
    ok = all(run(p) for p in a.inputs)
    sys.exit(0 if ok else 1)
