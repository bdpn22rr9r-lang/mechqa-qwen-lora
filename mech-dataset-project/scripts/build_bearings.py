"""第3批: 轴承与润滑(深度, 7类型×7失效×6角度 ≈ 294 条)。

疲劳点蚀/寿命校核归 design_fatigue;故障诊断归 fault_diagnosis。
review_status=self_reviewed。
用法: python build_bearings.py -o data/generated_v3/bearings.jsonl
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

AUTHOR, V3 = "claude", "v3"


def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_brg_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(
        id=rid, category=cat, sub_category=sub, difficulty=diff, language="zh",
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond,
        risk_tags=tags, task_type=cat, source_type="expert_authored", license="pending",
        review_status="self_reviewed", reviewer="claude_expert_review", author=AUTHOR,
        split_group="v3_brg_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3,
    ).to_dict()


BTYPES = {
    "deep_groove": ("深沟球轴承", "主要承受径向、可受小轴向、高速、应用最广"),
    "cylindrical": ("圆柱滚子轴承", "径向承载大、刚性好、一般不能受轴向、适于重载"),
    "angular_contact": ("角接触球轴承", "能受联合载荷、常成对使用、可调游隙、适于高速联合载荷"),
    "tapered": ("圆锥滚子轴承", "联合载荷承载大、可调游隙、适于中低速重载联合载荷"),
    "spherical": ("调心滚子轴承", "能自动调心、抗冲击、适于轴挠曲与不对中工况"),
    "thrust": ("推力轴承", "主要承受轴向载荷、转速受限、须防滑动"),
    "journal": ("滑动轴承(轴瓦)", "液体动压/静压润滑、适高速重载平稳运转、需稳定供油"),
}

BFAIL = {
    "fatigue_pitting": {
        "name": "疲劳点蚀剥落",
        "cat": "design_fatigue",
        "check": "基本额定寿命 L10=(C/P)^ε ≤ 要求寿命 Lh(ε=3 球、10/3 滚子;GB/T 6391-2010);P=当量动载荷,须实际载荷谱换算",
        "cause": "滚道或滚动体次表层剪切应力反复作用,萌生裂纹扩展至表面,材料剥落形成点蚀;当量动载荷过大或寿命不足时加速",
        "improve": "选更大额定动载荷 C 的型号、改善载荷分布(避免偏载)、保证良好润滑形成弹流油膜、提高清洁度",
        "inspect": "振动包络解调找 BPFO/BPFI/BSF 缺陷特征频率、油液铁谱磨粒、温升监测",
        "material": "高纯度轴承钢 GCr15 淬火 60~65 HRC、滚道精磨抛光",
        "limit": "闭式润滑良好轴承的主要失效;L10 为 90% 可靠度统计值,高可靠度用 a1 修正"},
    "wear": {
        "name": "磨粒/粘着磨损",
        "cat": "fault_diagnosis",
        "check": "监测游隙增大与振动;润滑不良或污染致磨粒磨损,低速重载油膜破裂致粘着磨损",
        "cause": "润滑油污染(硬质颗粒)造成磨粒磨损;低速重载或油膜破裂造成金属直接接触粘着磨损,游隙逐渐增大",
        "improve": "保证润滑清洁(NAS 等级)、合适粘度、改善密封防污染、避免低速重载边界润滑",
        "inspect": "游隙测量、油液清洁度与磨粒分析、振动宽频噪声",
        "material": "提高滚道与滚动体硬度、耐磨",
        "limit": "污染环境与润滑不良工况主要失效"},
    "plastic_indent": {
        "name": "塑性压痕(过载压痕)",
        "cat": "fault_diagnosis",
        "check": "校核静强度 C0/P0 ≤ 许用(C0 额定静载荷),过载或冲击压痕",
        "cause": "过载冲击或装配不当(锤击)使滚道产生塑性压痕,运转时产生振动噪声",
        "improve": "核算冲击载荷、正确装配(禁止直接锤击滚子)、选更大 C0 型号",
        "inspect": "滚道压痕目视/内窥镜、振动冲击特征",
        "material": "提高滚道硬度与抗压能力",
        "limit": "过载或装配不当失效;非疲劳"},
    "corrosion": {
        "name": "腐蚀",
        "cat": "fault_diagnosis",
        "check": "工况介质分析;潮湿/腐蚀环境致滚道锈蚀、腐蚀磨损",
        "cause": "水分或腐蚀介质侵入润滑剂,滚道与滚动体表面锈蚀,形成腐蚀磨损与点蚀源",
        "improve": "改善密封防潮、选防腐轴承或镀层、定期换油、控制环境",
        "inspect": "滚道与滚动体锈蚀目视、油液水分与酸值检测",
        "material": "不锈钢轴承或表面防腐处理",
        "limit": "潮湿腐蚀环境失效;停机期也可能发生(微动腐蚀)"},
    "electric_erosion": {
        "name": "电蚀",
        "cat": "fault_diagnosis",
        "check": "检查轴电流路径;变频电机轴电流通过轴承放电致熔蚀",
        "cause": "变频电机轴电流通过轴承,在滚道与滚动体间放电,形成熔坑与搓衣板纹,加速失效",
        "improve": "绝缘轴承、轴接地碳刷、电缆布线抑制共模电流",
        "inspect": "滚道搓衣板纹与熔坑目视、电流检测",
        "material": "绝缘涂层轴承(外圈陶瓷或涂层)",
        "limit": "变频电机轴电流工况特有失效"},
    "cage_damage": {
        "name": "保持架破损",
        "cat": "fault_diagnosis",
        "check": "振动 FTF(保持架缺陷频率);润滑不良、冲击或偏载致保持架断裂",
        "cause": "润滑不足、转速过高、冲击偏载或安装不当,保持架受额外力致磨损断裂",
        "improve": "保证润滑、控制转速与偏载、正确安装、必要时选加强保持架",
        "inspect": "振动 FTF 特征频率与边带、噪声、拆检",
        "material": "选钢/黄铜保持架(高速冲击)替代冲压钢/尼龙",
        "limit": "保持架失效常继发滚动体/滚道破坏"},
    "burn_seize": {
        "name": "烧伤卡死",
        "cat": "fault_diagnosis",
        "check": "温升急剧;润滑失效或游隙过小致发热烧伤卡死",
        "cause": "润滑中断、游隙过小、预紧过大或转速过高,发热使滚道/滚动体退火变色甚至卡死",
        "improve": "保证供油与冷却、选合适游隙(C3/C4 考虑温升)、控制预紧与转速",
        "inspect": "温升监测(报警)、振动突增、拆检滚道变色",
        "material": "耐高温材料与润滑脂(高温工况)",
        "limit": "润滑失效或装配不当的快速失效"},
}

ANGLES = [("check", "校核方法"), ("cause", "原因机理"), ("improve", "改进措施"),
          ("inspect", "检测方法"), ("material", "材料与润滑"), ("limit", "适用边界")]


def gen_bearings():
    out = []
    for tk, (tname, tfeat) in BTYPES.items():
        for fk, fd in BFAIL.items():
            for ak, alabel in ANGLES:
                body = fd[ak]
                sg = f"{tk}_{fk}_{ak}"
                out.append(make(fd["cat"], f"bearing_{tk}_{fk}", "hard" if ak in ("check", "limit") else "medium",
                    f"请以机械专家角度,针对该轴承的{fd['name']}问题,给出{alabel}。",
                    f"对象:{tname}({tfeat});现象:{fd['name']}。",
                    f"轴承特性:{tfeat}。\n针对{fd['name']}的{alabel}:{body}",
                    [body[:14]], ["载荷谱", "转速", "润滑", "配合游隙"],
                    ["wear_contact_fatigue", "fatigue", "inspection_ndt"],
                    sg))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="data/generated_v3/bearings.jsonl")
    a = ap.parse_args()
    recs = gen_bearings()
    bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output)
    print(f"[bearings] {len(recs)} 条 -> {a.output}  (校验失败 {len(bad)})")
    print(f"  类型×失效×角度: {len(BTYPES)}×{len(BFAIL)}×{len(ANGLES)}; 类别: {dict(Counter(r['category'] for r in recs))}")
    if bad:
        print("  首个失败:", bad[0])


if __name__ == "__main__":
    main()
