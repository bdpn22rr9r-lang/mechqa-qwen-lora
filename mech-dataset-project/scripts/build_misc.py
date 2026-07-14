"""第18批: 杂项机械元件(深度, 10类型×7失效×6角度=420条)。归 design_fatigue/manufacturing_qc。
凸轮/棘轮/螺纹副/键/销/铆接/粘接/万向节/丝杠/导轨。
用法: python build_misc.py -o data/generated_v3/misc.jsonl"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
AUTHOR, V3 = "claude", "v3"
def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_msc_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(id=rid, category=cat, sub_category=sub, difficulty=diff, language="zh",
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond, risk_tags=tags, task_type=cat,
        source_type="expert_authored", license="pending", review_status="self_reviewed", reviewer="claude_expert_review",
        author=AUTHOR, split_group="v3_msc_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3).to_dict()
MTYPES = {
    "cam": ("凸轮机构", "高副、接触应力、运动学设计"),
    "ratchet": ("棘轮棘爪", "单向间歇、冲击、强度"),
    "screw_pair": ("螺纹副(螺旋传动)", "传力/传运动、自锁、效率"),
    "key_joint": ("键联接(平键/楔键)", "周向固定传扭、剪切挤压"),
    "pin_joint": ("销联接", "定位/连接、安全销过载剪断"),
    "rivet": ("铆接", "永久连接、剪切、工艺性"),
    "adhesive": ("粘接", "面连接、应力均匀、耐温耐久"),
    "universal": ("万向节", "夹角传扭、不等速、双万向等速"),
    "leadscrew": ("丝杠(滚动/滑动)", "回转↔直线、精度、刚度"),
    "guide": ("导轨(滑动/滚动)", "导向精度、爬行、磨损"),
}
MFAIL = {
    "contact": ("接触疲劳/点蚀", "design_fatigue", "高副接触反复作用,表面点蚀剥落", "校核接触应力 ≤ 许用、提高硬度表面、良好润滑", "接触面点蚀、油液磨粒", "高硬表面材料", "凸轮/丝杠/导轨常见"),
    "wear": ("磨损", "manufacturing_qc", "运动副磨损致精度与间隙劣化", "改善润滑、提高硬度、合适配对", "磨损量、间隙、精度测量", "耐磨材料与润滑", "运动副常见"),
    "fatigue": ("疲劳", "design_fatigue", "交变载荷疲劳断裂", "校核疲劳强度、减应力集中、表面强化", "S-N、断口", "高强材料", "交变载荷失效"),
    "overload": ("过载剪断/压溃", "design_fatigue", "过载致剪切/挤压破坏(键/销/铆)", "校核剪切与挤压应力、增尺寸、安全销", "应力校核、失效件检查", "合适强度材料", "键销铆过载失效"),
    "loosen_backlash": ("松动/间隙", "fault_diagnosis", "磨损或预紧不足致间隙与冲击", "调预紧、补偿磨损、减间隙", "间隙测量、振动冲击", "刚度与预紧设计", "运动精度相关"),
    "corrosion_seize": ("腐蚀咬死", "fault_diagnosis", "腐蚀或微动磨损致咬合卡死", "防腐蚀、润滑、合适材料配对", "腐蚀检查、运动灵活性", "防腐与防咬", "潮湿腐蚀工况"),
    "adhesive_fail": ("粘接/连接失效", "manufacturing_qc", "粘接老化/超载/工艺不良致脱粘", "合适胶种、表面处理、固化工艺、校核强度", "超声/目视、剥离试验", "结构胶与工艺", "粘接连接特有"),
}
ANGLES = [("check", "校核方法"), ("cause", "失效机理"), ("improve", "改进措施"), ("inspect", "检测方法"), ("material", "材料与工艺"), ("limit", "适用边界")]
def gen():
    out = []
    for tk, (tn, tf) in MTYPES.items():
        for fk, fd in MFAIL.items():
            for ak, al in ANGLES:
                if ak == "cause": body = fd[2]
                elif ak == "check": body = f"校核依据:{fd[2]}"
                else: body = fd[{"improve":3,"inspect":4,"material":5,"limit":6}[ak]]
                out.append(make(fd[1], f"msc_{tk}_{fk}", "hard" if ak in ("check","limit") else "medium",
                    f"请以机械专家角度,针对{tn}的{fd[0]}问题,给出{al}。",
                    f"对象:{tn}({tf});现象:{fd[0]}。",
                    f"元件特性:{tf}。\n针对{fd[0]}的{al}:{body}",
                    [fd[2][:12]], ["载荷", "速度", "润滑", "工况"],
                    ["wear_contact_fatigue", "fatigue", "assembly_tolerance"], f"{tk}_{fk}_{ak}"))
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-o", "--output", default="data/generated_v3/misc.jsonl"); a = ap.parse_args()
    recs = gen(); bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output); print(f"[misc] {len(recs)} 条 -> {a.output} (校验失败 {len(bad)})")
    if bad: print("  首个失败:", bad[0])
if __name__ == "__main__":
    main()
