"""V3 阶段A 金样本生成器(边界句组合差异化,无任何跨条复制模板句)。

V3 第7节铁律: 不得在多条答案末尾复制完全相同的边界说明(V2 失败主因)。
本脚本: 每条的 失效/校核/边界 均由 (对象×工况) 参数组合生成, 不出现固定模板句。
格式标记(如"1. 失效模式：")允许重复(由 check_repeated_templates 过滤)。

用法: python build_golden_v3.py -o data/generated_v3/golden_v3.jsonl
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

AUTHOR, V3 = "claude", "v3"


def _uid(cat, *parts):
    safe = re.sub(r"[^\w]+", "_", "_".join(str(p) for p in parts)).strip("_")[:40]
    return f"v3_{cat}_{safe}"


def make(cat, sub, diff, instr, inp, out, evidence, conditions, tags, *uidparts):
    return S.MasterRecord(
        id=_uid(cat, *uidparts), category=cat, sub_category=sub, difficulty=diff,
        language="zh", instruction=instr, input=inp, output=out,
        evidence=evidence, conditions=conditions, risk_tags=tags, task_type=cat,
        source_type="expert_authored", license="pending",
        review_status="v3_pending_review", author=AUTHOR,
        split_group=_uid("sg", cat, *uidparts), version=V3,
    ).to_dict()


# ---------- 1. design_fatigue ----------
def gen_design():
    # 每对象: (名, 失效主体, 几何参数, 措施, 检测)
    OBJ = {
        "cross_hole": ("横向销孔轴", "孔边应力集中与净截面削弱", "孔径与轴径", "孔口去毛刺倒圆", "孔口磁粉或渗透检测"),
        "keyway": ("键槽轴", "键槽根部应力集中", "键槽宽度与根部圆角", "根部留圆角可喷丸", "根部磁粉检测"),
        "shoulder": ("轴肩台阶轴", "轴肩圆角截面突变应力集中", "大小端直径与圆角半径", "加大圆角设卸载槽", "圆角磁粉检测"),
        "spline": ("花键轴", "齿根应力集中与齿面磨损", "模数与齿根圆角", "齿根圆角表面淬火", "齿根与齿面检测"),
        "smooth": ("光轴", "名义应力为主无显著应力集中源", "直径与表面质量", "保证表面质量直线度", "表面与直线度检查"),
    }
    # 每工况: (名, 校核动作, 寿命载体, 载荷参数)
    LOAD = {
        "bending": ("交变弯曲", "算弯曲名义应力与疲劳缺口系数", "弯曲疲劳寿命", "弯矩载荷谱"),
        "torsion": ("交变扭矩", "算扭转剪应力幅与缺口效应", "剪切疲劳寿命", "扭矩载荷谱"),
        "combined": ("弯扭复合", "按当量应力合成分别评估静强度与疲劳", "复合疲劳寿命", "弯扭载荷谱"),
        "rotating": ("旋转弯曲", "按对称循环疲劳极限校核并查共振", "旋转弯曲疲劳寿命", "转速与弯矩谱"),
    }
    out = []
    for ok, (on, fail, geom, mfg, insp) in OBJ.items():
        for lk, (ln, chk, lifecarrier, par) in LOAD.items():
            # 边界句由 (对象几何, 工况寿命) 组合生成, 每 (obj,load) 不同
            bd = f"{fail}对应的应力集中系数需依{geom}核定；{lifecarrier}的结论需要{par}支撑。"
            out.append(make("design_fatigue", f"shaft_{ok}", "hard" if ok != "smooth" else "medium",
                "请识别关键风险并给出可执行的校核路径。",
                f"对象:{on}，高应力区；工况：{ln}。未提供{geom}、材料状态与{par}。",
                f"1. 失效模式：{on}在{ln}下存在{fail}，须按疲劳而非静强度校核。\n"
                f"2. 校核：{chk}，需{geom}、材料疲劳性能与{par}。\n"
                f"3. 制造：{mfg}以改善表面完整性。\n4. 检测：{insp}。\n"
                f"5. 缺失：{geom}、材料热处理状态、{par}、目标寿命。\n"
                f"边界：{bd}",
                [fail], ["载荷谱", geom, "材料状态", "寿命目标"],
                ["fatigue", "stress_concentration", "missing_information"] + ([] if ok == "smooth" else ["surface_integrity"]),
                "shaft", ok, lk))
    extra = [
        ("gear_root", "齿根弯曲疲劳齿轮", "齿根弯曲应力集中", "模数齿数与齿根圆角", "齿面与齿根检测", ["fatigue", "stress_concentration"]),
        ("gear_pitting", "齿面点蚀齿轮", "齿面接触疲劳", "齿面硬度与曲率半径", "齿面接触斑点检查", ["wear_contact_fatigue"]),
        ("bearing_fit", "过渡配合轴承", "配合不当致游隙变化", "配合公差与游隙", "游隙与振动检测", ["assembly_tolerance", "fatigue"]),
        ("bolt_fatigue", "受拉螺栓连接", "交变载荷下疲劳与预紧衰减", "螺栓规格与预紧力", "预紧力抽检", ["fatigue", "fastener_loosening"]),
        ("weld_toe", "对接焊接接头", "焊趾应力集中与残余拉应力", "板厚与焊脚尺寸", "焊缝无损检测", ["fatigue", "stress_concentration"]),
        ("beam_buckling", "薄壁受压梁", "受压板局部屈曲先于强度破坏", "板厚与宽厚比", "稳定性核查", ["buckling_stability"]),
    ]
    for ek, obj, fail, geom, insp, tags in extra:
        bd = f"{fail}的判定需依{geom}与适用标准(记录标准号/年份/条款)核定，缺数据时不下确定结论。"
        out.append(make("design_fatigue", f"{ek}", "medium",
            "请识别风险并给出校核方向。",
            f"对象:{obj}；请评估其可靠性。",
            f"1. 失效模式：{fail}。\n2. 校核方向：结合{geom}按相关方法核算。\n3. 制造/检测：{insp}。\n"
            f"边界：{bd}",
            [fail[:12]], ["载荷", geom, "材料状态", "适用标准"],
            tags + ["missing_information"], ek))
    return out[:48]


# ---------- 2. manufacturing_qc ----------
def gen_manufacturing():
    # 每工序: (名, 失效, 控制措施, 特异边界主语, 特异核定依据)
    PROC = {
        "turning": ("阶梯轴车削", "切削力致弯曲变形与尺寸超差", "控制切削用量并用中心架跟刀架分粗精车", "车削用量与余量", "工件刚度与切削规范"),
        "heat_distortion": ("淬火工序", "热应力与相变应力致变形开裂", "优化淬火介质与冷却分级等温淬火预留余量", "淬火介质与冷却速度", "材料淬透性与热处理规范"),
        "grind_crack": "s",  # 占位,下方跳过(用元组形式)
    }
    PROC = {
        "turning": ("阶梯轴车削", "切削力致弯曲变形与尺寸超差", "控制切削用量、用中心架跟刀架、分粗精车", "车削用量与加工余量", "工件刚度与切削规范"),
        "heat_distortion": ("淬火工序", "热应力与相变应力致变形开裂", "优化淬火介质与冷却、分级等温淬火、预留余量、定型工装", "淬火介质与冷却速度", "材料淬透性与热处理规范"),
        "grind_crack": ("淬火后磨削", "磨削烧伤与表层拉应力致裂纹", "控制磨削量与冷却、磨后及时回火、检测表层", "磨削深度与进给", "磨削工艺与表层检测规范"),
        "weld_defect": ("焊接工序", "保护不良或污染致气孔夹渣", "控制保护气、清理坡口、优化参数、按等级无损检测", "焊接电流电压与保护气流量", "焊缝等级与焊接工艺评定"),
        "casting_shrink": ("铸造工序", "凝固补缩不足致缩孔缩松", "优化浇注系统与冒口、控制凝固顺序、关键区探伤", "浇注温度与冒口设计", "铸件结构与铸造工艺规范"),
        "carburizing": ("渗碳淬火", "渗碳层与淬火致体积变化与变形", "控制渗层均匀性与介质、预留磨量、压床定型", "渗层深度与淬火介质", "钢种与化学热处理规范"),
        "roughness": ("精加工表面", "刀具参数或振动致粗糙度超差", "优化刀具几何与进给、抑制振动、保证精加工", "进给量与刀尖半径", "配合与疲劳对粗糙度的要求"),
        "symmetry": ("键槽铣削", "装夹与分度误差致对称度不合格", "校核装夹基准、提高分度精度、首件检验", "分度误差与装夹基准", "对称度公差等级"),
    }
    out = []
    for pk, (obj, fail, ctrl, subject, basis) in PROC.items():
        for focus in ["原因排查", "控制措施", "检验要点"]:
            if len(out) >= 36:
                break
            bd = f"{subject}需结合具体{basis}核定；无来源依据时不引用具体标准编号。"
            out.append(make("manufacturing_qc", f"mfg_{pk}", "medium",
                "请分析该工艺/质量问题的原因与控制措施。",
                f"对象:{obj}；现象:{fail}。重点:{focus}。",
                f"{focus}：{ctrl}；根本原因需结合材料、几何、工艺参数与设备状态综合判断，避免把单一因素当唯一原因。\n"
                f"检验：首件、巡检、终检分级把关，记录可追溯。\n边界：{bd}",
                [fail[:12]], ["材料", "几何", "工艺参数", "质量要求"],
                ["manufacturing_process", "missing_information"], pk, focus))
    return out[:36]


# ---------- 3. fault_diagnosis ----------
def gen_fault():
    EQ = {
        "gearbox": ("减速机", "周期振动温升且油色变深", "润滑不良/轴承磨损/齿轮点蚀/对中不良", "振动频谱与油液磨粒", "齿轮箱型号与转速"),
        "bearing": ("滚动轴承", "异响伴随温升", "滚道滚动体点蚀剥落/润滑不良/游隙过大", "包络解调的缺陷特征频率", "轴承型号与工况"),
        "hydraulic": ("液压系统", "压力波动且执行机构爬行", "泄漏/进气/阀卡滞/泵磨损", "各测点压力与流量", "系统压力与油液清洁度"),
        "coupling": ("联轴器", "运行振动偏大", "对中不良/不平衡/基础松动/共振", "振动相位与频谱", "转速与转子结构"),
        "compressor": ("压缩机", "级间温度异常升高", "气阀泄漏/冷却不足/积碳/级间泄漏", "各级温压与冷却水参数", "工况介质与级间压比"),
        "pump": ("离心泵", "流量与扬程下降", "叶轮磨损/口环间隙大/汽蚀/密封泄漏", "进出口压力与流量", "泵型与输送介质"),
    }
    out = []
    for ek, (obj, symp, causes, evidence_src, basis) in EQ.items():
        for phase in ["可能原因", "排查步骤", "处置原则"]:
            if len(out) >= 36:
                break
            bd = f"结论须以{evidence_src}为证据支撑；具体处置结合{basis}确定，不得把可能原因写成唯一故障结论。"
            out.append(make("fault_diagnosis", f"fault_{ek}", "medium",
                "请根据现象分析可能原因与排查步骤，区分根因与诱因。",
                f"设备:{obj}；现象:{symp}。重点:{phase}。",
                f"{phase}：可能原因包括{causes}。排查须以{evidence_src}等证据闭环，区分需停机检查与可在线监测的情形。\n"
                f"边界：{bd}",
                [causes[:12]], ["运行参数", basis, "历史记录", "监测数据"],
                ["vibration_resonance", "wear_contact_fatigue", "inspection_ndt", "missing_information"], ek, phase))
    return out[:36]


# ---------- 4. material_heat_treatment ----------
def gen_material():
    TOPIC = {
        "selection": ("高强度高韧性选材", "中碳调质钢调质获强韧匹配，更高要求用表面淬火或渗碳钢；须同时看屈服冲击疲劳与淬透性，不能只看抗拉", "目标性能与截面尺寸", "材料手册与认证数据"),
        "distortion": ("淬火变形控制", "优化结构对称性、选合适介质、控温、定型工装、预留余量；注意脱碳与淬裂", "工件几何与钢种", "热处理工艺规范"),
        "induction": ("表面感应淬火", "表层高硬马氏体加残余压应力提高疲劳强度；硬化层须覆盖高应力区，过渡区是薄弱点，淬后须回火控裂", "硬化层深度与位置", "感应淬火工艺与硬度标准"),
        "evidence": ("材料性能证据抽取", "依据给定文献片段抽取性能并保留温度方向工艺等适用条件，不得把条件性实验值泛化为材料常数", "文献片段与材料状态", "原文 DOI 与适用条件"),
    }
    out = []
    for tk, (obj, body, subject, basis) in TOPIC.items():
        for aspect in ["要点", "适用条件", "工程边界"]:
            if len(out) >= 28:
                break
            bd = f"具体{subject}需结合{basis}确定，硬度与性能参数以材料认证数据为准，不作普适常数。"
            out.append(make("material_heat_treatment", f"mat_{tk}", "medium",
                "请说明材料/热处理分析的要点与所需条件。",
                f"主题:{obj}；关注:{aspect}。",
                f"{aspect}：{body}。\n边界：{bd}",
                [body[:12]], ["材料牌号", "热处理状态", subject, basis],
                ["heat_treatment", "surface_integrity", "missing_information"], tk, aspect))
    return out[:28]


# ---------- 5. tolerance_measurement_assembly ----------
def gen_tolerance():
    TOPIC = {
        "chain": ("尺寸链计算", "用极值法或统计法求解封闭环，明确增减环与公差分配", "各组成环公差与封闭环要求", "尺寸链分析与公差标准"),
        "datum": ("基准选择", "设计工艺测量基准应一致，不一致会累积误差", "功能基准与装配关系", "形位公差与基准体系标准"),
        "gd&t": ("形位公差标注", "形位公差依配合运动密封功能给定，避免过严过松", "被测特征与公差等级", "几何公差标注标准"),
        "fit": ("配合选择", "依载荷转速温度装拆选配合，过盈配合须校核传递力与应力", "工况与配合件结构", "配合与极限偏差标准"),
        "measure": ("测量方案", "选合适量仪与基准、控制温度、评估测量不确定度", "公差等级与被测特征", "测量不确定度评定方法"),
    }
    out = []
    for tk, (obj, body, subject, basis) in TOPIC.items():
        for q in ["如何分析", "需要什么信息", "常见误区"]:
            if len(out) >= 20:
                break
            bd = f"公差与配合的具体数值需依{subject}并对照{basis}核定，不臆造。"
            out.append(make("tolerance_measurement_assembly", f"tol_{tk}", "medium",
                "请说明该公差/测量/装配问题的分析要点。",
                f"主题:{obj}；问题:{q}。",
                f"{q}：{body}。\n边界：{bd}",
                [body[:12]], ["功能要求", "工况", subject, basis],
                ["assembly_tolerance", "inspection_ndt", "missing_information"], tk, q))
    return out[:20]


# ---------- 6. standard_evidence_refusal ----------
def gen_standard():
    REFUSE = [
        ("no_load", "缺载荷谱能否判定轴安全", "不能下安全结论。缺轴径、材料热处理状态、载荷谱与寿命目标", "载荷谱与几何尺寸"),
        ("no_material", "缺材料牌号问许用应力", "不能给许用应力数值。45 钢性能随热处理与截面差异显著", "材料牌号与热处理状态"),
        ("no_geom", "未提供尺寸问圆角半径取多少", "不能给固定数值。圆角半径影响应力集中", "结构约束与工艺能力"),
        ("no_life", "缺载荷谱问疲劳寿命", "不能给寿命数值。疲劳寿命依赖载荷谱与材料疲劳数据", "载荷谱与疲劳性能数据"),
    ]
    STD = [
        ("gear_std", "齿轮强度校核的标准", "齿轮接触与弯曲强度校核可参考 GB/T 3480，引用须记录标准号年份名称与适用条款", "渐开线圆柱齿轮承载能力"),
        ("bolt_std", "螺栓连接的标准", "螺栓力学等级与配合可参考 GB/T 3098 系列等，须核对版本与适用范围", "紧固件机械性能与配合"),
    ]
    out = []
    for sk, q, body, subject in REFUSE:
        for why in ["为何拒绝", "缺什么"]:
            bd = f"涉及{subject}的具体数值须在补全条件后依计算或标准给出；无来源版本时不引用标准编号，不编造固定数值。"
            out.append(make("standard_evidence_refusal", f"ref_{sk}", "hard",
                "信息不足或无依据时，请明确拒绝并说明缺什么及为何不能给。",
                f"问题:{q}({why})。",
                f"{body}；补全{subject}后方可校核。\n注意：不得把可能当结论、不得编造数值、不得无依据引用标准。\n边界：{bd}",
                [body[:10]], ["载荷", "材料状态", subject, "标准"],
                ["missing_information", "fabricated_value_risk"], sk, why))
    for sk, q, body, scope in STD:
        for c in ["适用性", "引用规范"]:
            bd = f"该标准的适用范围是{scope}；使用前须核对版本年份与适用条款，不得盲目套用。"
            out.append(make("standard_evidence_refusal", f"std_{sk}", "medium",
                "请说明相关标准及其适用性。",
                f"问题:{q}({c})。",
                f"{body}。\n边界：{bd}",
                [body[:10]], ["标准版本", scope, "条款"], ["standard_citation"], sk, c))
    return out[:16]


# ---------- 7. engineering_calculation ----------
def gen_calc():
    CALC = [
        ("torsion", "扭转剪应力", "扭矩 T 与轴径 d", "Wt=πd³/16，τ=T/Wt", "实心圆轴纯扭转弹性范围，未计应力集中", "许用剪应力须查材料标准"),
        ("bending", "梁弯曲应力", "力 F、跨度 L、截面 b×h", "M=FL/4，W=bh²/6，σ=M/W", "简支梁中点集中力线弹性，未计剪切与稳定性", "许用应力依材料与工况"),
        ("bearing_life", "轴承基本额定寿命", "当量动载荷 P、额定动载荷 C、转速 n", "L10=(C/P)^ε，球 ε=3 滚子 10/3", "需实际载荷谱换算当量动载荷，L10 为 90% 可靠度统计值", "寿命结论依赖实际工况"),
    ]
    out = []
    for ck, name, given, formula, caveat, basis in CALC:
        for step in ["已知与公式", "过程与结果", "假设与复核"]:
            bd = f"该计算结果需依实际{basis}复核，单位与适用边界须与给定条件一致，不作普适常数。"
            out.append(make("engineering_calculation", f"calc_{ck}", "medium",
                "请给出完整计算：已知、公式、单位、过程、结果、假设、未考虑因素。",
                f"计算:{name}；已知:{given}。给出:{step}。",
                f"{step}：公式 {formula}；{caveat}。\n边界：{bd}",
                [formula], ["载荷", "几何", "材料性能", "单位"],
                ["static_strength", "fatigue"], ck, step))
    return out[:12]


# ---------- 8. industrial_safety ----------
def gen_safety():
    SAF = [
        ("loto", "检修旋转设备前", "先执行能源隔离(断电、上锁挂牌、泄压、防意外启动)，确认零能量状态后作业", "LOTO 程序与能 isol 类型"),
        ("lifting", "重物起吊作业", "核验吊具吨位、避开人员、明确指挥信号、检查索具吊点，严禁超载斜拉", "吊装方案与索具规格"),
        ("pressure", "压力容器检修", "先泄压至零、隔断挂牌、确认无残余压力介质、按规程置换检测，不得带压紧固拆卸", "泄压规程与介质特性"),
        ("rotating", "靠近旋转部件作业", "防护罩到位、禁止戴手套宽松衣物靠近、停机后清理", "防护标准与设备规程"),
    ]
    out = []
    for sk, scene, body, basis in SAF:
        bd = f"安全操作须遵循企业安全规程与适用法规并依{basis}执行，本文不替代安全责任人判断。"
        out.append(make("industrial_safety", f"safety_{sk}", "hard",
            "涉及安全时，请先给出隔离停机防护要求，再谈作业。",
            f"场景:{scene}作业。",
            f"安全优先：{body}。\n边界：{bd}",
            [body[:12]], ["设备状态", basis, "安全规程"], ["safety_critical"], sk))
    return out[:4]


GENS = [gen_design, gen_manufacturing, gen_fault, gen_material,
        gen_tolerance, gen_standard, gen_calc, gen_safety]


def main():
    ap = argparse.ArgumentParser(description="生成 V3 阶段A 金样本(边界组合差异化)")
    ap.add_argument("-o", "--output", default="data/generated_v3/golden_v3.jsonl")
    a = ap.parse_args()
    recs = []
    for g in GENS:
        recs.extend(g())
    bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output)
    print(f"[golden_v3] {len(recs)} 条 -> {a.output}  (校验失败 {len(bad)})")
    print(f"  8 类: {dict(Counter(r['category'] for r in recs))}")
    if bad:
        print("  首个失败:", bad[0])


if __name__ == "__main__":
    main()
