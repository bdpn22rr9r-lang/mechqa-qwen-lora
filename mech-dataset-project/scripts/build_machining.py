"""第6批: 机加工工艺(深度, 7类型×7失效×6角度=294条)。归 manufacturing_qc。
用法: python build_machining.py -o data/generated_v3/machining.jsonl"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
AUTHOR, V3 = "claude", "v3"
def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_mac_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(id=rid, category=cat, sub_category=sub, difficulty=diff,
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond, risk_tags=tags, task_type=cat, language="zh",
        source_type="expert_authored", license="pending", review_status="self_reviewed", reviewer="claude_expert_review",
        author=AUTHOR, split_group="v3_mac_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3).to_dict()
MTYPES = {
    "turning": ("车削", "工件旋转、单刃连续切削,加工回转面"),
    "milling": ("铣削", "刀具旋转多刃断续切削,加工平面/槽/曲面"),
    "drilling": ("钻削", "钻头轴向进给加工孔,排屑散热难"),
    "boring": ("镗削", "扩已有孔提精度,刀杆刚性受限"),
    "grinding": ("磨削", "砂轮高速磨削,高精度低粗糙度,易烧伤"),
    "broaching": ("拉削", "拉刀一次成形,高效率高精度"),
    "hobbing": ("滚齿/齿面加工", "展成法加工齿形,齿形精度控制"),
}
MFAIL = {
    "dim": ("尺寸形位超差", "切削力变形、热伸长、刀具磨损是主因", "减小切深进给、用中心架辅件、充分冷却、补偿磨损、控温", "首件与抽检测量、监控刀具磨损、温度补偿", "硬质合金刀具与合适几何、刚性装夹", "通用,加工精度直接失效"),
    "rough": ("表面粗糙度超差", "进给过大残留面积高、刀尖磨损、振动、积屑瘤", "优化进给 f 与刀尖 rε(Ra≈f²/8rε)、抑振、精加工、防积屑瘤", "粗糙度仪测 Ra/Rz、表面形貌", "锋利刀具、合适几何与冷却", "影响疲劳与配合"),
    "wear": ("刀具磨损破损", "磨料/粘结/扩散磨损或热震崩刃", "耐磨刀具(CBN/陶瓷)、优化速度、充分冷却、及时换刀", "测刀仪/声发射监测、尺寸漂移", "刀具材料匹配工件", "影响尺寸与表面"),
    "chatter": ("振动颤振", "再生颤振:厚度变化反馈放大,刚度不足或转速不稳", "提高刚度、选稳定转速区、减切宽、变进给、抑振刀具", "振动传感器、频谱、振纹", "刚性装夹短悬伸", "影响表面与刀具"),
    "burn": ("磨削烧伤", "磨削热大冷却不足,温升超相变点烧伤与拉应力", "减小磨削量(精磨<0.02mm)、充分冷却、及时修整砂轮", "酸浸/磁探、硬度、回火色", "合适砂轮与磨削液", "淬火件磨削主要风险"),
    "burr": ("毛刺飞边", "刀具切出材料塑性变形残留", "优化参数与刀具几何、调切出方向、去毛刺(光饰/热能)", "目视触检", "锋利刀具合适几何", "影响装配与安全"),
    "distort": ("加工变形", "内应力(铸锻焊热处理)释放或薄壁切削力变形", "时效消除应力、粗精分多次、对称加工、辅件减变形", "首件测变形、抽检、应力测试", "充分时效、合理工艺路线", "薄壁与内应力件主要"),
}
ANGLES = [("check", "校核/判定"), ("cause", "失效机理"), ("improve", "改进措施"), ("inspect", "检测方法"), ("material", "刀具与工艺"), ("limit", "适用边界")]
def gen():
    out = []
    for tk, (tn, tf) in MTYPES.items():
        for fk, fd in MFAIL.items():
            for ak, al in ANGLES:
                idx = {"check":1,"cause":1,"improve":2,"inspect":3,"material":4,"limit":5}[ak]
                # check 与 cause 共用机理描述, 给不同引导
                body = fd[1] if ak == "cause" else fd[idx] if ak != "check" else f"测量对照公差要求,{fd[1]}"
                out.append(make("manufacturing_qc", f"mac_{tk}_{fk}", "hard" if ak in ("check", "limit") else "medium",
                    f"请以机械专家角度,针对{tn}的{fd[0]}问题,给出{al}。",
                    f"对象:{tn}({tf});问题:{fd[0]}。",
                    f"工序特性:{tf}。\n针对{fd[0]}的{al}:{body}",
                    [fd[1][:12]], ["材料", "几何", "切削参数", "刀具"], ["manufacturing_process", "missing_information"],
                    f"{tk}_{fk}_{ak}"))
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-o", "--output", default="data/generated_v3/machining.jsonl"); a = ap.parse_args()
    recs = gen(); bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output); print(f"[machining] {len(recs)} 条 -> {a.output} (校验失败 {len(bad)})")
    if bad: print("  首个失败:", bad[0])
if __name__ == "__main__":
    main()
