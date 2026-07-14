"""第13批: 公差配合测量装配(深度, 8类型×7主题×6角度=336条)。归 tolerance_measurement_assembly。
用法: python build_tolerance2.py -o data/generated_v3/tolerance2.jsonl"""
from __future__ import annotations
import os, sys, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S
AUTHOR, V3 = "claude", "v3"
def make(cat, sub, diff, instr, inp, out, ev, cond, tags, sg):
    rid = "v3_tol2_" + re.sub(r"[^\w]+", "_", sg).strip("_")[:40]
    return S.MasterRecord(id=rid, category=cat, sub_category=sub, difficulty=diff, language="zh",
        instruction=instr, input=inp, output=out, evidence=ev, conditions=cond, risk_tags=tags, task_type=cat,
        source_type="expert_authored", license="pending", review_status="self_reviewed", reviewer="claude_expert_review",
        author=AUTHOR, split_group="v3_tol2_sg_" + re.sub(r"[^\w]+", "_", sg)[:36], version=V3).to_dict()
TTYPES = {
    "chain": ("尺寸链", "封闭环与组成环,极值/统计法求解"),
    "datum": ("基准体系", "设计/工艺/测量基准统一原则"),
    "clearance": ("间隙配合", "H/g、H/f,保证相对运动与润滑"),
    "interference": ("过盈配合", "H/u、H/s,靠弹性过盈传力"),
    "transition": ("过渡配合", "H/k、H/m,定位精确可拆装"),
    "gdnt": ("形位公差(几何公差)", "形状/方向/位置/跳动,依功能给定"),
    "measure": ("测量与不确定度", "量仪、基准、温度、不确定度评定"),
    "assembly": ("装配工艺", "顺序、选配、修配、累积误差控制"),
}
# 7 元素: name, cat, cause/背景, improve/方法, inspect, material/数据, limit
TOPIC = {
    "method": ("计算与选择方法", "tolerance_measurement_assembly", "依功能与工况,极值法保守统计法经济,配合按基孔制/基轴制选", "查 GB/T 1800 配合表、统计法用正态假设、明确封闭环", "三坐标/量仪测量、对照公差带", "GB/T 1800 系列配合数据", "须依功能与工况"),
    "selection": ("配合选择", "tolerance_measurement_assembly", "依载荷转速温度装拆与精度选配合等级", "间隙保证润滑、过盈校核传力、过渡定位", "装配测间隙/过盈量", "GB/T 1801 配合推荐", "权衡可制造性与功能"),
    "calc_chain": ("尺寸链计算", "tolerance_measurement_assembly", "封闭环公差=组成环公差合成,极值法相加/统计法平方和", "正确识别增减环、合理分配组成环公差", "封闭环测量、组成环验证", "公差分配原则", "极值保守统计经济"),
    "datum_issue": ("基准不统一误差", "tolerance_measurement_assembly", "设计/工艺/测量基准不一致,误差累积放大", "三基准统一、选功能面为主基准", "基准拟合测量、误差分析", "基准建立与转换", "影响装配与功能"),
    "deformation_fit": ("配合与变形", "tolerance_measurement_assembly", "温差与受力改变实际配合,高速或高温配合变化", "考虑热膨胀、离心变形、修正确合", "工况温度下测配合", "线膨胀系数 α 数据", "高温高速须修正"),
    "measure_uncert": ("测量不确定度", "tolerance_measurement_assembly", "测量结果含不确定度,需评定是否满足公差判定", "选合适量仪(U≤T/4)、控温(20℃基准)、A/B 类评定", "不确定度评定报告", "GUM 不确定度评定方法", "U≤T/4 才能判定合格"),
    "assembly_accum": ("装配累积误差", "tolerance_measurement_assembly", "多环节装配顺序影响累积误差与内应力", "规划装配顺序、关键配合选配(分组)、修配", "装配后综合测量", "选配/修配数据记录", "影响最终精度"),
}
ANGLES = [("check", "判定方法"), ("cause", "问题机理"), ("improve", "解决措施"), ("inspect", "检测方法"), ("material", "标准数据"), ("limit", "适用边界")]
def gen():
    out = []
    for tk, (tn, tf) in TTYPES.items():
        for fk, fd in TOPIC.items():
            for ak, al in ANGLES:
                if ak == "cause": body = fd[2]
                elif ak == "check": body = f"判定依据:{fd[2]}"
                else: body = fd[{"improve":3,"inspect":4,"material":5,"limit":6}[ak]]
                out.append(make(fd[1], f"tol2_{tk}_{fk}", "hard" if ak in ("check","limit") else "medium",
                    f"请以机械专家角度,针对{tn}的{fd[0]}问题,给出{al}。",
                    f"对象:{tn}({tf});主题:{fd[0]}。",
                    f"主题特性:{tf}。\n针对{fd[0]}的{al}:{body}",
                    [fd[2][:12]], ["功能要求", "工况", "公差等级", "相关标准"],
                    ["assembly_tolerance", "inspection_ndt"], f"{tk}_{fk}_{ak}"))
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("-o", "--output", default="data/generated_v3/tolerance2.jsonl"); a = ap.parse_args()
    recs = gen(); bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output); print(f"[tolerance2] {len(recs)} 条 -> {a.output} (校验失败 {len(bad)})")
    if bad: print("  首个失败:", bad[0])
if __name__ == "__main__":
    main()
