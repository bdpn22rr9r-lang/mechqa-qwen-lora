"""第12批: MechQA 核验导入(深度, 限400条, V3 第5.2节)。归 material_heat_treatment。
转换 MechQA 为 V3 schema, 标 review_status=v3_pending_review(数值-实体对应待机械专家核验)。
用法: python build_mechqa_v3.py -n 400 -o data/generated_v3/mechqa_v3.jsonl"""
from __future__ import annotations
import os, sys, argparse, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
AUTHOR, V3 = "claude", "v3"
INSTR = ("请仅依据下方英文文献片段抽取材料性能,并说明适用条件。"
         "不得把带工艺、温度、方向或应变率条件的实验值泛化为无条件材料常数。")
NOISE = ("注:MechQA 为自动标注,存在数值串行、性能类型或单位错误的风险,本条数值与性能的对应须经机械工程人员核验。")
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:MPa|GPa|kPa|Pa|%|mm|°C)", re.I)

def to_record(obj, idx):
    q = obj.get("question", "").strip()
    ctx = obj.get("context", "").strip()
    doi = obj.get("DOI", "").strip()
    ans = obj.get("answers", {}).get("text", [])
    ans_txt = ans[0].strip() if ans else ""
    qtype = obj.get("qa_type", "").strip()
    sid = str(obj.get("id", idx))
    inp = f"问题:{q}\n文献片段(英文原文,作证据):{ctx}" + (f"\nDOI:{doi}" if doi else "")
    out = (f"依据文献片段,所提取的性能为:{ans_txt}。" + (f"(问答类型:{qtype})。" if qtype else "")
           + "该数值仅适用于片段所述材料状态与实验条件,不可泛化为材料常数。" + NOISE
           + (f" 来源 DOI:{doi}。" if doi else ""))
    nums = NUM_RE.findall(ctx)[:8]
    rec = S.MasterRecord(
        id=f"v3_mechqa_{sid}", category="material_heat_treatment", sub_category="mechqa_evidence",
        difficulty="medium", language="zh", instruction=INSTR, input=inp, output=out,
        evidence=[ctx[:80]], conditions=["材料状态", "实验条件", qtype or "性能类型"],
        risk_tags=["missing_information"], numeric_claims=[{"value": n.strip(), "unit": "", "source": f"mechqa:{doi or sid}"} for n in nums],
        requires_tool=False, requires_rag=True, task_type="material_heat_treatment",
        source_type="mechqa_converted", source_ref=doi or f"mechqa:{sid}", license="cc-by-4.0",
        review_status="v3_pending_review", reviewer="", author=AUTHOR,
        split_group=f"v3_mechqa_sg_{sid}", version=V3)
    return rec.to_dict()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-n", "--limit", type=int, default=400)
    ap.add_argument("-o", "--output", default="data/generated_v3/mechqa_v3.jsonl")
    ap.add_argument("--input", default="data/raw/mechqa/dataset_example/train_sample.json")
    a = ap.parse_args()
    out_recs, seen = [], set()
    with open(a.input, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line: continue
            try: obj = json.loads(line)
            except: continue
            sid = str(obj.get("id", i))
            if sid in seen: continue
            seen.add(sid)
            out_recs.append(to_record(obj, i))
            if len(out_recs) >= a.limit: break
    bad = sum(1 for r in out_recs if S.dict_to_record(r).validate())
    S.save_jsonl(out_recs, a.output)
    print(f"[mechqa_v3] {len(out_recs)} 条 -> {a.output} (校验失败 {bad}; review_status=v3_pending_review 待核验)")

if __name__ == "__main__":
    main()
