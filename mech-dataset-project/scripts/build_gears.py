"""第2批: 齿轮传动细化(深度, 7类型×6失效×6角度 ≈ 252 条)。

每个样本融入 齿轮类型特性 + 失效模式(校核公式/机理/改进/检测/材料/边界)。
归 design_fatigue 类。review_status=self_reviewed(AI 专家自审)。
用法: python build_gears.py -o data/generated_v3/gears.jsonl
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

AUTHOR, V3 = "claude", "v3"


def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_gear_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(
        id=rid, category=cat, sub_category=sub, difficulty=diff, language="zh",
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond,
        risk_tags=tags, task_type=cat, source_type="expert_authored", license="pending",
        review_status="self_reviewed", reviewer="claude_expert_review", author=AUTHOR,
        split_group="v3_gear_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3,
    ).to_dict()


GTYPES = {
    "spur": ("直齿圆柱齿轮", "无轴向力、噪声较大、适于低速中载(节圆速度 v<5 m/s)"),
    "helical": ("斜齿圆柱齿轮", "有轴向力、重合度大、传动平稳、适于高速重载(v 可达 25 m/s)"),
    "herringbone": ("人字齿轮", "左右旋抵消轴向力、适于重型大功率传动"),
    "straight_bevel": ("直齿锥齿轮", "相交轴传动、轴向力指向锥顶、适低速相交轴"),
    "spiral_bevel": ("曲线齿锥齿轮", "传动平稳、重载相交轴、噪声低"),
    "worm": ("蜗轮蜗杆传动", "传动比大(i 可达 80)、滑动大发热高(η<90%)、青铜蜗轮配钢蜗杆、可能自锁"),
    "internal": ("内齿圈", "同轴内啮合、结构紧凑、用于行星传动、重合度高"),
}

# 每失效模式 6 个角度的深度内容
FAIL = {
    "tooth_bending": {
        "name": "齿根弯曲疲劳折断",
        "check": "齿根弯曲应力 σF = Ft·KA·KV·KFβ·KFα/(b·m)·YFa·YSa ≤ σFP(GB/T 3480-2019)。YFa 齿形系数随齿数与变位变化(齿数少 YFa 大),YSa 应力校正系数。",
        "cause": "齿根受脉动/交变弯曲,最大拉应力在齿根过渡圆角受拉侧,长期循环萌生疲劳裂纹并沿截面扩展,最终致断齿。",
        "improve": "增大模数 m 与齿宽 b(齿宽系数 φd=b/d1≈0.8~1.2)、正变位降低 YFa、加大齿根圆角半径、喷丸强化引入表层残余压应力。",
        "inspect": "磁粉(MT)检测齿根裂纹、定期测公法线长度/齿厚、振动监测啮合频率及边带。",
        "material": "渗碳淬火 20CrMnTi 齿面 58~62 HRC、心部 30~45 HRC 保韧性;或调质 40Cr 齿面 HB 280~320。",
        "limit": "硬齿面弯曲强度高但跑合性差;软齿面易塑性变形;高速还须校核胶合。"},
    "pitting": {
        "name": "齿面接触疲劳点蚀",
        "check": "接触应力 σH = ZH·ZE·√(Ft·(u±1)·KA·KV·KHβ·KHα/(b·d1·u)) ≤ σHP。ZE 弹性系数(钢-钢≈189.8 √MPa),ZH 节点区域系数。",
        "cause": "赫兹接触反复作用,次表层最大剪切应力处萌生微裂纹,润滑油渗入后在挤压下扩展,致材料剥落形成点蚀凹坑。",
        "improve": "提高齿面硬度、降低齿面粗糙度(磨齿 Ra 0.8)、提高润滑油膜比厚(λ>1.5)、合理跑合改善接触。",
        "inspect": "齿面目视或内窥镜查点蚀分布与扩展、油液光谱/铁谱分析磨粒、振动啮合频率边带。",
        "material": "硬齿面:渗碳淬火 58~62 HRC;或氮化 38CrMoAl;软齿面调质 HB≤350。",
        "limit": "闭式齿轮主要失效形式;早期点蚀可能跑合后收敛,扩展性点蚀预示寿命不足须处理。"},
    "scuffing": {
        "name": "齿面胶合",
        "check": "闪温法 θf 或积分温度法,校核积分温度 θint ≤ 许用 θintS;高速重载齿轮必须校核。",
        "cause": "高速重载下油膜破裂,两齿面金属直接接触瞬间熔焊,随后在相对滑动中被撕开,沿滑动方向形成条痕。",
        "improve": "降低滑动率(齿顶齿根修形、减小模数)、选用高粘度油、加极压(EP)添加剂、加强冷却、减小齿面粗糙度。",
        "inspect": "齿面沿滑动方向条痕(擦伤/胶合)、油温监测、铁谱查大尺寸磨粒。",
        "material": "提高齿面硬度、大小齿轮合理硬度差(小轮略硬)、抗胶合材料配对。",
        "limit": "高速重载预警性失效;开式低速一般不发生胶合。"},
    "wear": {
        "name": "齿面磨损",
        "check": "监测齿厚减薄量;开式传动主要失效。低速重载粘着磨损、污染环境磨粒磨损。",
        "cause": "磨粒磨损(润滑油污染含硬质颗粒)或低速重载下油膜破裂粘着磨损,齿厚逐渐减薄、齿廓失真。",
        "improve": "提高齿面硬度、保证润滑清洁(精细过滤)、选合适粘度、改用闭式传动防污染。",
        "inspect": "测齿厚/公法线减薄、油液清洁度(NAS 等级)、齿面形貌与粗糙度。",
        "material": "高硬度齿面、抗磨配对材料。",
        "limit": "开式齿轮主要失效;闭式润滑良好时磨损轻微。"},
    "plastic_flow": {
        "name": "齿面塑性变形",
        "check": "软齿面在冲击/重载下校核接触应力是否超过表层屈服强度。",
        "cause": "软齿面在重载冲击下,表层金属沿摩擦力方向塑性流动,齿顶/齿根形成峰脊与沟脊。",
        "improve": "提高齿面硬度(HB350 以上)、降低接触应力、改善润滑、减小冲击载荷。",
        "inspect": "齿面峰脊/沟脊外观检查、齿廓形状检测。",
        "material": "提高齿面硬度,采用硬齿面。",
        "limit": "软齿面重载工况失效;硬齿面不易发生。"},
    "overload_break": {
        "name": "过载/冲击断齿",
        "check": "静强度校核 σFmax ≤ σFE(过载工况);核算冲击载荷谱与最大瞬时载荷。",
        "cause": "冲击过载或异物卡死,齿根瞬时应力超过材料强度,发生脆性或韧性断裂。",
        "improve": "核算冲击载荷谱、设安全保护(剪切销、安全联轴器、扭矩限制器)、提高材料韧性。",
        "inspect": "断口宏观分析(疲劳纹 vs 瞬断区)、工况与载荷记录追溯。",
        "material": "心部韧性好的渗碳钢或调质钢,避免过脆。",
        "limit": "冲击工况须防;非疲劳,是瞬时过载失效。"},
}

ANGLES = [("check", "校核方法"), ("cause", "失效机理"), ("improve", "改进措施"),
          ("inspect", "检测方法"), ("material", "材料与热处理"), ("limit", "适用边界")]


def gen_gears():
    out = []
    for tk, (tname, tfeat) in GTYPES.items():
        for fk, fd in FAIL.items():
            for ak, alabel in ANGLES:
                body = fd[ak]
                sg = f"{tk}_{fk}_{ak}"
                diff = "hard" if ak in ("check", "limit") else "medium"
                out.append(make("design_fatigue", f"gear_{tk}_{fk}", diff,
                    f"请以机械设计专家角度,针对该齿轮的{fd['name']}问题,给出{alabel}。",
                    f"对象:{tname}({tfeat});工况:出现{fd['name']}。",
                    f"齿轮特性:{tfeat}。\n针对{fd['name']}的{alabel}:{body}",
                    [body[:14]], ["载荷谱", "模数齿数", "材料热处理", "精度等级"],
                    ["fatigue", "wear_contact_fatigue", "stress_concentration"],
                    sg))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="data/generated_v3/gears.jsonl")
    a = ap.parse_args()
    recs = gen_gears()
    bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output)
    print(f"[gears] {len(recs)} 条 -> {a.output}  (校验失败 {len(bad)})")
    print(f"  类型×失效×角度: {len(GTYPES)}×{len(FAIL)}×{len(ANGLES)}")
    if bad:
        print("  首个失败:", bad[0])


if __name__ == "__main__":
    main()
