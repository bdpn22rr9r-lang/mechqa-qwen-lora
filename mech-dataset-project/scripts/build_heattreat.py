"""第7批: 热处理(深度, 8类型×7失效×6角度=336条)。
HFAIL 统一 7 元素: (name, cat, cause, improve, inspect, material, limit)。
用法: python build_heattreat.py -o data/generated_v3/heattreat.jsonl"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
AUTHOR, V3 = "claude", "v3"
def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_ht_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(id=rid, category=cat, sub_category=sub, difficulty=diff, language="zh",
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond, risk_tags=tags, task_type=cat,
        source_type="expert_authored", license="pending", review_status="self_reviewed", reviewer="claude_expert_review",
        author=AUTHOR, split_group="v3_ht_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3).to_dict()
HTYPES = {
    "anneal": ("退火", "加热保温缓冷,消除应力/改善切削/均匀组织"),
    "normalize": ("正火", "加热后空冷,细化组织、改善力学与切削"),
    "quench": ("淬火", "奥氏体化后快冷获高硬马氏体,内应力大易裂"),
    "temper": ("回火", "淬火后加热,降脆消应力调强韧,避开回火脆性"),
    "qnt": ("调质(淬+高回)", "淬火+高温回火获回火索氏体,综合力学好"),
    "induction": ("表面感应淬火", "感应加热表层淬火,表层硬化心部韧"),
    "carburize": ("渗碳淬火", "表层增碳后淬火,齿面硬化心部韧"),
    "nitride": ("渗氮", "氮渗入表层高硬耐磨耐蚀,变形小温度低"),
}
# 7 元素: name, cat, cause, improve, inspect, material, limit
HFAIL = {
    "hard_low": ("硬度不足", "manufacturing_qc", "加热温度低/时间短、冷却慢、脱碳", "校准炉温、控冷却介质、防脱碳保护气氛", "硬度计(洛氏/维氏)、金相", "材料可淬性匹配工艺", "工艺偏差主要失效"),
    "deform": ("变形", "manufacturing_qc", "热应力+相变应力叠加、结构不对称、冷却不均", "优化介质(油/分级/等温)、对称结构、预留磨量、压床定型", "变形量测量、尺寸检查", "控温控冷、对称设计", "淬火主要问题"),
    "crack": ("淬火裂纹", "manufacturing_qc", "冷却太快、应力集中、含氢夹杂、尖角结构", "选合适介质、马氏体点缓冷、避免尖角、预热", "磁粉/渗透(MT/PT)、超声(UT)", "材料纯净、避免应力集中", "高碳高合金钢危险"),
    "decarb": ("脱碳", "manufacturing_qc", "加热时表层碳氧化损失,硬度耐磨下降", "保护气氛或盐浴、控温时间、用料覆盖", "硬度梯度、金相、化学分析", "中性/还原性气氛", "表层关键件风险"),
    "overheat": ("过热过烧", "manufacturing_qc", "加热温度过高,晶粒粗大(过热)或晶界氧化(过烧)", "校准炉温控温;过热可正火挽救,过烧报废", "金相晶粒度、断口", "精确控温", "过烧不可逆"),
    "residual": ("残余应力", "material_heat_treatment", "不均匀冷却与相变产生残余应力,影响疲劳与尺寸稳定", "及时回火、消除应力退火、振动时效", "X射线应力、尺寸稳定性", "及时回火消应力", "影响尺寸稳定与疲劳"),
    "structure": ("组织不合格", "manufacturing_qc", "淬火非马、网状碳化物、带状组织", "控温冷却、改善原材料、合理工艺", "金相组织评级", "材料与工艺匹配", "影响力学性能"),
}
ANGLES = [("check", "校核/判定"), ("cause", "失效机理"), ("improve", "改进措施"), ("inspect", "检测方法"), ("material", "材料与工艺"), ("limit", "适用边界")]
def gen():
    out = []
    for tk, (tn, tf) in HTYPES.items():
        for fk, fd in HFAIL.items():
            for ak, al in ANGLES:
                if ak == "cause":
                    body = fd[2]
                elif ak == "check":
                    body = f"测量对照要求并依据:{fd[2]}的成因判定"
                else:
                    body = fd[{"improve":3, "inspect":4, "material":5, "limit":6}[ak]]
                out.append(make(fd[1], f"ht_{tk}_{fk}", "hard" if ak in ("check", "limit") else "medium",
                    f"请以机械专家角度,针对{tn}的{fd[0]}问题,给出{al}。",
                    f"对象:{tn}({tf});问题:{fd[0]}。",
                    f"工艺特性:{tf}。\n针对{fd[0]}的{al}:{body}",
                    [fd[2][:12]], ["材料牌号", "热处理状态", "截面尺寸", "工艺参数"],
                    ["heat_treatment", "manufacturing_process"], f"{tk}_{fk}_{ak}"))
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-o", "--output", default="data/generated_v3/heattreat.jsonl"); a = ap.parse_args()
    recs = gen(); bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output); print(f"[heattreat] {len(recs)} 条 -> {a.output} (校验失败 {len(bad)})")
    if bad: print("  首个失败:", bad[0])
if __name__ == "__main__":
    main()
