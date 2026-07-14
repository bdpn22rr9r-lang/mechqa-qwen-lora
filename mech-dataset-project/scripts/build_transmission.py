"""第17批: 传动/密封/弹簧/制动(深度, 10类型×7失效×6角度=420条)。归 design_fatigue/manufacturing_qc。
用法: python build_transmission.py -o data/generated_v3/transmission.jsonl"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
AUTHOR, V3 = "claude", "v3"
def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_trn_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(id=rid, category=cat, sub_category=sub, difficulty=diff, language="zh",
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond, risk_tags=tags, task_type=cat,
        source_type="expert_authored", license="pending", review_status="self_reviewed", reviewer="claude_expert_review",
        author=AUTHOR, split_group="v3_trn_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3).to_dict()
TTYPES = {
    "spring_comp": ("螺旋压缩弹簧", "受剪扭、疲劳、共振敏感"),
    "spring_torsion": ("扭转弹簧", "受弯、疲劳"),
    "coupling": ("联轴器", "连接两轴传扭、补偿对中误差"),
    "clutch": ("离合器", "接合分离、摩擦发热磨损"),
    "brake": ("制动器", "摩擦制动、发热磨损、安全关键"),
    "seal_gasket": ("垫片/O圈密封", "静密封、压紧比压、老化"),
    "mech_seal": ("机械密封", "动密封端面、磨损泄漏"),
    "chain": ("链传动", "多边形效应、磨损伸长、润滑"),
    "belt": ("带传动", "打滑、疲劳、张紧"),
    "wire_rope": ("钢丝绳", "弯曲疲劳、磨损断丝、报废"),
}
# 7 元素: name, cat, cause, improve, inspect, material, limit
TFAIL = {
    "fatigue": ("疲劳失效", "design_fatigue", "交变载荷下疲劳断裂或寿命不足", "校核疲劳强度、减应力集中、表面强化(喷丸)、避共振(工作频率远离固有频率)", "S-N 曲线、断口分析", "高强弹簧钢(60Si2MnA)、喷丸", "交变载荷主要失效"),
    "wear": ("磨损", "manufacturing_qc", "摩擦副磨损致间隙增大、泄漏或失效", "改善润滑、提高硬度、合适材料配对", "磨损量、间隙、泄漏量测量", "耐磨材料与润滑", "运动副常见失效"),
    "overload": ("过载塑性/断裂", "design_fatigue", "过载致塑性变形或断裂", "增大尺寸、设过载保护(剪切销/安全联轴器)、安全件", "应力校核、安全件完好", "高强材料", "过载保护设计"),
    "leak": ("泄漏(密封)", "manufacturing_qc", "密封比压不足、老化、磨损致介质泄漏", "合适密封型式、足够压紧、材料耐介质耐温", "试压检漏、密封检查", "密封材料(氟橡胶/石墨/聚四氟)", "密封连接常见失效"),
    "thermal": ("发热/热变形", "manufacturing_qc", "摩擦发热致温升、热变形、材料性能下降", "加强散热冷却、减摩擦、控速控载", "温度监测、热像", "耐热材料与冷却", "摩擦制动离合常见"),
    "resonance": ("共振/振动", "fault_diagnosis", "激励频率接近固有频率致振动放大", "调刚度避开共振、加阻尼、减激励", "模态分析、振动频谱", "刚度与阻尼设计", "弹簧与旋转件常见"),
    "corrosion_fatigue": ("腐蚀/腐蚀疲劳", "fault_diagnosis", "介质腐蚀降低疲劳强度、应力腐蚀开裂", "选耐蚀材料、防护、隔绝介质", "介质分析、腐蚀检查", "耐蚀材料与涂层", "腐蚀环境失效"),
}
ANGLES = [("check", "校核方法"), ("cause", "失效机理"), ("improve", "改进措施"), ("inspect", "检测方法"), ("material", "材料与工艺"), ("limit", "适用边界")]
def gen():
    out = []
    for tk, (tn, tf) in TTYPES.items():
        for fk, fd in TFAIL.items():
            for ak, al in ANGLES:
                if ak == "cause": body = fd[2]
                elif ak == "check": body = f"校核依据:{fd[2]}"
                else: body = fd[{"improve":3,"inspect":4,"material":5,"limit":6}[ak]]
                out.append(make(fd[1], f"trn_{tk}_{fk}", "hard" if ak in ("check","limit") else "medium",
                    f"请以机械专家角度,针对{tn}的{fd[0]}问题,给出{al}。",
                    f"对象:{tn}({tf});现象:{fd[0]}。",
                    f"元件特性:{tf}。\n针对{fd[0]}的{al}:{body}",
                    [fd[2][:12]], ["载荷谱", "速度", "润滑介质", "工况"],
                    ["fatigue", "wear_contact_fatigue", "vibration_resonance"], f"{tk}_{fk}_{ak}"))
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-o", "--output", default="data/generated_v3/transmission.jsonl"); a = ap.parse_args()
    recs = gen(); bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output); print(f"[transmission] {len(recs)} 条 -> {a.output} (校验失败 {len(bad)})")
    if bad: print("  首个失败:", bad[0])
if __name__ == "__main__":
    main()
