"""V3 深度版金样本生成器(机械工程师级,非提纲式)。

每条 output 含: 具体方法/公式名、数值范围、可执行步骤、检验频率、处置逻辑。
修 bug: design 轴类 failure 去工况前缀(避免"交变弯曲下，交变弯曲下")、
safety 场景去"作业"重复、material 常温误导改为针对性表述。
review_status=self_reviewed(AI 专家自审,非真人终审)。

用法: python build_golden_v3.py -o data/generated_v3/golden_v3.jsonl
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

AUTHOR, V3 = "claude", "v3"


def _uid(cat, *parts):
    return "v3_" + cat + "_" + re.sub(r"[^\w]+", "_", "_".join(map(str, parts))).strip("_")[:36]


def make(cat, sub, diff, instr, inp, out, ev, cond, tags, *uidparts):
    return S.MasterRecord(
        id=_uid(cat, *uidparts), category=cat, sub_category=sub, difficulty=diff,
        language="zh", instruction=instr, input=inp, output=out,
        evidence=ev, conditions=cond, risk_tags=tags, task_type=cat,
        source_type="expert_authored", license="pending",
        review_status="self_reviewed", reviewer="claude_expert_review", author=AUTHOR,
        split_group=_uid("sg", cat, *uidparts), version=V3,
    ).to_dict()


# ============ 1. design_fatigue(深度) ============
# fail 已去工况前缀; 加 Kt 量级与方法
SHAFT = {
    "cross_hole": {"name": "横向销孔轴", "geom": "孔径与轴径", "kt": "理论应力集中系数 Kt 随 d/D 变化可达约 2.5~3.5", "mfg": "孔口去毛刺、倒圆 R 控制在工艺允许上限", "insp": "孔口与孔轴线交界面磁粉(MT)或渗透(PT)检测",
                   "fail": {"bending": "孔边受拉侧弯曲应力峰值显著", "torsion": "孔周剪应力集中,主应力方向反复", "combined": "孔边正应力与剪应力集中叠加", "rotating": "孔口每转承受一次交变应力峰值"}},
    "keyway": {"name": "键槽轴", "geom": "键槽宽与根部圆角", "kt": "键槽根部 Kt 约 2~3,长键槽端部更高", "mfg": "根部留圆角 R≥0.3~0.5 mm,可喷丸强化", "insp": "键槽根部磁粉检测",
               "fail": {"bending": "键槽根部拉应力集中", "torsion": "键槽根部剪应力集中,为扭转传力薄弱区", "combined": "根部弯扭合成应力集中", "rotating": "根部每转应力交变"}},
    "shoulder": {"name": "轴肩台阶轴", "geom": "大小端直径 D/d 与圆角 r", "kt": "随 D/d 与 r/r0 变化,r 越小 Kt 越高(可达 3 以上)", "mfg": "在轴承定位允许内加大圆角 r,必要时设卸载槽", "insp": "圆角磁粉检测",
                 "fail": {"bending": "轴肩圆角拉应力集中", "torsion": "圆角处扭转仍有应力集中", "combined": "圆角弯扭合成应力集中", "rotating": "圆角每转应力交变"}},
    "spline": {"name": "花键轴", "geom": "模数 m 与齿根圆角", "kt": "齿根 Kt 约 1.5~2.5", "mfg": "齿根圆角、感应淬火硬化层覆盖齿根", "insp": "齿根磁粉、齿面接触斑点检查",
               "fail": {"bending": "齿根拉应力集中", "torsion": "齿根剪应力集中伴齿面磨损", "combined": "齿根弯扭合成应力集中", "rotating": "齿根每转应力交变"}},
    "smooth": {"name": "光轴(对照)", "geom": "直径与表面质量", "kt": "无几何集中,疲劳受表面系数 bσ 与尺寸 ε 控制", "mfg": "保证表面粗糙度 Ra 与直线度", "insp": "表面与直线度检查",
               "fail": {"bending": "表面弯曲应力无几何集中源", "torsion": "扭转剪应力无几何集中源", "combined": "弯扭合成无几何集中", "rotating": "旋转弯曲疲劳受表面与尺寸控制"}},
}
LOAD = {"bending": ("交变弯曲", "名义应力法:算弯曲名义应力 σa,查 Kt、疲劳缺口系数 Kf=1+q(Kt-1)", "弯曲疲劳寿命", "弯矩载荷谱"),
        "torsion": ("交变扭矩", "算扭转剪应力幅 τa 与 Kf,按剪切疲劳强度校核", "剪切疲劳寿命", "扭矩载荷谱"),
        "combined": ("弯扭复合", "按当量应力(如 σeq=√(σ²+3τ²))分别评估静强度与疲劳", "复合疲劳寿命", "弯扭载荷谱"),
        "rotating": ("旋转弯曲", "按对称循环(r=-1)疲劳极限校核,并核查工作转速避开临界转速", "旋转弯曲疲劳寿命", "转速与弯矩谱")}
def gen_design():
    out = []
    for ok, o in SHAFT.items():
        for lk, (ln, chk, life, par) in LOAD.items():
            bd = f"{o['fail'][lk]};{o['kt']}。应力集中系数与 {life} 需依 {o['geom']} 与材料疲劳数据核定,需 {par} 支撑,缺数据不下确定结论。"
            out.append(make("design_fatigue", f"shaft_{ok}", "hard" if ok != "smooth" else "medium",
                "请以机械设计审查角度,识别关键风险并给出可执行的校核路径。",
                f"对象:{o['name']},高应力区;工况:{ln}。未提供{o['geom']}、材料状态与{par}。",
                f"1. 失效模式:{o['name']}在{ln}下,{o['fail'][lk]},须按疲劳(非静强度)校核。\n"
                f"2. 应力集中:{o['kt']}。\n"
                f"3. 校核方法:{chk};需{o['geom']}、材料疲劳性能(S-N 或 ε-N 曲线)与{par}。\n"
                f"4. 制造:{o['mfg']}以改善表面完整性(表层残余压应力可显著提高疲劳强度)。\n"
                f"5. 检测:{o['insp']}。\n"
                f"6. 缺失:{o['geom']}、材料状态、{par}、目标寿命与可靠度。\n边界:{bd}",
                [o['fail'][lk][:12], o['kt'][:12]], ["载荷谱", o['geom'], "材料状态", "寿命目标", "可靠度"],
                ["fatigue", "stress_concentration", "missing_information"] + ([] if ok == "smooth" else ["surface_integrity"]),
                "shaft", ok, lk))
    EXTRA = [
        ("gear_root", "齿根弯曲疲劳", "齿根弯曲应力致断齿", "按 GB/T 3480-2019 齿根弯曲应力公式,算 σF 对照许用 σFP(含寿命、可靠度、应力修正系数)", ["fatigue", "stress_concentration"]),
        ("gear_pitting", "齿面接触疲劳点蚀", "赫兹接触应力反复作用致点蚀", "按 GB/T 3480-2019 接触应力 σH 对照许用 σHP;提高齿面硬度与降低粗糙度", ["wear_contact_fatigue"]),
        ("gear_scuffing", "齿面胶合", "高速重载油膜破裂金属直接接触熔焊", "按 Blok 闪温法或积分温度法校核胶合温度", ["wear_contact_fatigue", "thermal_deformation"]),
        ("bearing_loose", "游隙过大轴承", "游隙过大致振动与打滑点蚀", "校核配合后工作游隙,按 GB/T 6391 算 L10 并修正", ["assembly_tolerance", "fatigue"]),
        ("bolt_fatigue", "受拉交变螺栓", "应力幅致疲劳断裂", "校核应力幅 σa=(F0-Fi)/(2·As) 对照螺栓疲劳极限;保证残余预紧力", ["fatigue", "fastener_loosening"]),
        ("weld_toe", "焊趾疲劳", "焊趾应力集中+残余拉应力", "按 IIW 推荐的名义应力法或热点应力法,选 FAT 级别", ["fatigue", "stress_concentration"]),
        ("beam_buckling", "薄壁受压梁屈曲", "受压板局部屈曲先于强度", "校核宽厚比 b/t 与加劲肋间距", ["buckling_stability"]),
    ]
    for ek, obj, fail, chk, tags in EXTRA:
        bd = f"{fail}的判定须依相关几何、载荷与适用标准(记录标准号/年份/条款),缺数据不下确定结论。"
        out.append(make("design_fatigue", f"{ek}", "medium",
            "请识别风险并给出校核方向。",
            f"对象:{obj}的零件;请评估可靠性。",
            f"1. 失效模式:{fail}。\n2. 校核方向:{chk}。\n3. 制造/检测:关注质量控制与无损检测。\n边界:{bd}",
            [fail[:12]], ["载荷", "几何", "材料状态", "适用标准"],
            tags + ["missing_information"], ek))
    return out[:48]


# ============ 2. manufacturing_qc(深度,加数值/步骤) ============
PROC = {
    "turning": ("阶梯轴车削变形", "切削径向力致弯曲让刀、热伸长、装夹偏载", "粗车切深 2~4 mm、进给 0.3~0.5 mm/r,精车余量 0.5~1 mm 分多次走刀;长径比>5 用中心架/跟刀架支承近切削区;尾座顶尖适度预紧并校正;充分切削液控热", "首件测各段跳动与直径,每 10~20 件抽检,终检形位"),
    "heat_distortion": ("淬火变形开裂", "热应力与相变应力叠加、结构不对称、冷却不均", "选合适介质(油/分级/等温淬火)、控温、马氏体区缓冷;结构尽量对称、避免尖角;预留磨量、用压床定型", "变形量测量、磁粉查裂纹、硬度与金相抽检"),
    "grind_crack": ("磨削裂纹烧伤", "磨削深度大、冷却不足、表层残余应力", "减小磨削量(精磨切深<0.02 mm)、充分冷却、及时回火去应力、控制进给", "酸浸或磁探查裂纹、表面硬度与烧伤(回火色)检查"),
    "weld_defect": ("焊缝气孔夹渣", "保护不良、坡口污染、参数不当、焊剂受潮", "清理坡口露金属光泽、烘干焊剂(250℃×1h)、优化电流电压与保护气流量、控制焊速", "按焊缝等级做射线(RT)/超声(UT)/渗透(PT)检测"),
    "casting_shrink": ("铸件缩孔缩松", "凝固顺序不当、补缩不足", "优化浇注系统与冒口(补缩)、加冷铁控制顺序凝固、控制浇注温度", "关键区 RT 或工业 CT、尺寸与外观检查"),
    "carburizing": ("渗碳淬火变形", "渗碳层体积变化、淬火冷却不均", "控制渗层深度均匀(通常 0.8~1.2 mm)、预留磨量、压床定型、选合适淬火介质", "渗层深度与硬度梯度、变形量、磁粉探伤"),
    "roughness": ("表面粗糙度超差", "刀具磨损、进给过大、工艺系统振动", "优化刀尖半径 rε 与进给 f(Ra≈f²/(8rε))、抑振、精加工保证、建立换刀管理", "粗糙度仪测 Ra/Rz 对照要求等级"),
    "symmetry": ("键槽对称度超差", "装夹基准误差、分度误差、刀具偏让", "校核装夹基准、提高分度精度、首件验证、刚性装夹减少让刀", "三坐标测对称度、首件与抽检"),
}
def gen_manufacturing():
    out = []
    for pk, (obj, cause, ctrl, insp) in PROC.items():
        subs = [("cause", "请分析主要原因。", f"主要原因:{cause}。注意:多因素耦合,需结合材料、几何、工艺参数与设备状态,避免单一归因。"),
                ("control", "请给出可执行的控制措施。", f"控制措施:{ctrl}"),
                ("inspect", "请说明检验要点。", f"检验:{insp}")]
        for sk, q, body in subs:
            if len(out) >= 36:
                break
            bd = f"{obj}的具体参数与判定须结合工艺规范与质量等级核定,无来源依据不引用标准编号。"
            out.append(make("manufacturing_qc", f"mfg_{pk}", "medium", q, f"对象:{obj}工序。",
                f"{body}\n边界:{bd}",
                [cause[:12]], ["材料", "几何", "工艺参数", "质量要求"],
                ["manufacturing_process", "missing_information"], pk, sk))
    return out[:36]


# ============ 3. fault_diagnosis(深度,加频谱/概率) ============
EQ = {
    "gearbox": ("减速机振动温升油变质", "润滑不良、轴承磨损、齿轮点蚀、对中不良",
                "油液光谱/铁谱分析磨粒;振动频谱:轴承看 BPFO/BPFI 等特征频率,齿轮看啮合频率 gm 及其边带;查对中与地脚",
                "换油、校中、换轴承或修齿轮;齿轮点蚀扩展或轴承剥落须停机"),
    "bearing": ("滚动轴承异响温升", "滚道/滚动体点蚀剥落、润滑不良、游隙过大",
                "包络解调找外圈 BPFO/内圈 BPFI/滚动体 BSF 缺陷频率;查润滑与游隙",
                "早期点蚀可监测运行,剥落快速扩展或温升持续须更换"),
    "hydraulic": ("液压压力波动执行件爬行", "泄漏、进气、阀卡滞、泵磨损",
                  "测各测点压力与流量、排气、查阀芯与泵容积效率",
                  "堵漏换密封、换阀或泵、严格控制油液清洁度(NAS 等级)"),
    "coupling": ("联轴器端振动大", "对中不良、不平衡、基础松动、共振",
                 "测振动相位与频谱(1× 不平衡/2× 不对中)、查对中(激光对中仪)与地脚、动平衡",
                 "校中、紧固、动平衡、调整转速避开共振"),
    "compressor": ("压缩机级间温度升高", "气阀泄漏、冷却不足、积碳、级间泄漏",
                   "查冷却水温水量、气阀密封、级间压比与温度分布",
                   "换阀片、清积碳、修冷却器;严重须解体"),
    "pump": ("离心泵流量扬程下降", "叶轮磨损、口环间隙大、汽蚀、密封泄漏",
             "测进出口压力流量、核算 NPSHA>NPSHR 防汽蚀、测口环间隙",
             "换叶轮口环、治漏、改善吸入条件"),
}
def gen_fault():
    out = []
    for ek, (symp, cause, probe, handle) in EQ.items():
        subs = [("cause", "请按概率排序分析可能原因。", f"可能原因(按概率):{cause}。"),
                ("probe", "请给出可执行的排查步骤。", f"排查:{probe}"),
                ("handle", "请说明处置原则。", f"处置:{handle}")]
        for sk, q, body in subs:
            if len(out) >= 36:
                break
            bd = "结论须以监测数据(振动/油液/温度/压力)为证据;不得把可能原因写成唯一故障结论;区分需停机检查与可在线监测。"
            out.append(make("fault_diagnosis", f"fault_{ek}", "medium", q, f"设备现象:{symp}。",
                f"{body}\n注意:区分根因与诱因,证据闭环。\n边界:{bd}",
                [symp[:10]], ["运行参数", "型号", "历史记录", "监测数据"],
                ["vibration_resonance", "wear_contact_fatigue", "inspection_ndt", "missing_information"], ek, sk))
    return out[:36]


# ============ 4. material_heat_treatment(深度,修常温误导) ============
MAT = {
    "selection": ("高强度高韧性选材", "中碳调质钢(40Cr、42CrMo)调质获强韧匹配;更高表面要求用表面淬火或渗碳钢(20CrMnTi)。须同时看屈服、冲击韧性、疲劳与淬透性,不只看抗拉。截面越大越需选淬透性高的钢种。", ["heat_treatment", "static_strength"]),
    "distortion": ("淬火变形控制", "热应力(冷却温差)与相变应力(奥氏体→马氏体体积膨胀~4%)叠加致变形。控制:结构对称、避免尖角截面突变;选合适介质(油/分级/等温);马氏体区缓冷;预留磨量;用压床定型。", ["heat_treatment", "thermal_deformation"]),
    "induction": ("表面感应淬火提疲劳", "表层获高硬马氏体+残余压应力(可达数百 MPa),显著提高疲劳强度。硬化层须覆盖高应力区(通常 1~3 mm);过渡区是薄弱点;淬后须低温回火(约 150~200℃)控裂。", ["surface_integrity", "fatigue"]),
    "tempering": ("回火工艺与权衡", "回火温度决定强度-韧性权衡。低温回火(150~250℃)保硬度(刀具/轴承),中温(350~500℃)注意回火脆性,高温(500~650℃)调质获强韧匹配(40Cr 调质约 850℃淬+520℃回)。须避开第一/二类回火脆性区。", ["heat_treatment"]),
    "evidence": ("材料性能证据抽取", "依据给定文献片段抽取性能,须保留温度、方向、工艺等适用条件。不得把条件性实验值泛化为材料常数。须核对数值对应的材料实体(避免相邻实体错配)。", ["missing_information"]),
    "anisotropy": ("材料各向异性", "轧制/锻造材料纵横向性能不同:横向疲劳与断裂韧度显著低于纵向。设计须注意受力方向与流线,关键件取样方向与主应力方向一致。", ["fatigue", "static_strength"]),
    "corrosion": ("腐蚀环境与腐蚀疲劳", "腐蚀介质降低疲劳强度(腐蚀疲劳),无明确疲劳极限;特定材料-介质组合(如奥氏体不锈钢-氯离子)有应力腐蚀开裂风险。须评估工况介质并选耐蚀材料或防护。", ["corrosion", "fatigue"]),
}
def gen_material():
    out = []
    # 按工况给针对性表述(不再用"常温可能不同"套话)
    cond_note = {"常温工况": "常温下以强度、韧性与疲劳为主,关注材料标准性能即可",
                 "高温工况": "高温须考虑蠕变与持久强度(材料高温数据),强度随温度下降",
                 "腐蚀工况": "腐蚀环境须考虑腐蚀疲劳与应力腐蚀,选耐蚀材料或防护",
                 "交变载荷": "交变载荷以疲劳为主,关注疲劳强度与应力集中敏感度"}
    for mk, (obj, body, tags) in MAT.items():
        for cond in ["常温工况", "高温工况", "腐蚀工况", "交变载荷"]:
            if len(out) >= 28:
                break
            bd = f"{obj}的具体性能与工艺参数须依材料牌号、热处理状态与标准确定,硬度以材料认证数据为准,不作普适常数。"
            out.append(make("material_heat_treatment", f"mat_{mk}", "medium",
                "请说明该材料/热处理问题的要点与在该工况下的注意点。",
                f"主题:{obj};工况:{cond}。",
                f"要点:{body}\n该工况注意:{cond_note[cond]}。\n边界:{bd}",
                [body[:14]], ["材料牌号", "热处理状态", "截面尺寸", cond],
                tags + ["missing_information"], mk, cond))
    return out[:28]


# ============ 5. tolerance_measurement_assembly(深度) ============
TOL = {
    "chain": ("尺寸链计算", "极值法(全部增环最大+减环最小)保守、经济性差;统计法(平方和)经济但需公差分布假设(通常正态)。须先正确识别封闭环(装配要求)与增减环。", ["assembly_tolerance"]),
    "datum": ("基准统一原则", "设计、工艺、测量三基准应统一。基准不一致累积误差;通常选功能配合面或装配定位面为主要基准。", ["assembly_tolerance"]),
    "gd&t": ("形位公差给定", "依功能给定:配合面用尺寸公差,运动/同心用位置度/同轴度,密封用平面度。过严增成本,过松失功能。须与尺寸链协调。", ["assembly_tolerance", "inspection_ndt"]),
    "fit_clearance": ("间隙配合", "H/g、H/f 等保证相对运动与润滑;最小间隙须大于热膨胀量与油膜厚度,按工况选配合。", ["assembly_tolerance", "thermal_deformation"]),
    "fit_interference": ("过盈配合", "H/u、H/s 等靠弹性过盈传递力;须校核传递扭矩与配合应力(不超过材料许用),厚壁圆筒公式。", ["assembly_tolerance", "static_strength"]),
    "measure_uncertainty": ("测量不确定度", "测量结果含不确定度 U。选合适量仪(分辨力≤公差 1/10)、控制温度(20℃基准)、评估 U 是否小于公差(通常 U≤T/4)。", ["inspection_ndt"]),
    "assembly_seq": ("装配顺序", "复杂装配顺序影响累积误差与内应力。须规划顺序,关键配合用选配(分组)或修配,记录选配数据。", ["assembly_tolerance", "manufacturing_process"]),
}
def gen_tolerance():
    out = []
    for tk, (obj, body, tags) in TOL.items():
        for focus in ["如何确定", "需要什么信息", "常见错误"]:
            if len(out) >= 20:
                break
            bd = f"{obj}的具体数值须依功能要求、工况与相关公差配合标准(GB/T 1800 系列)核定。"
            out.append(make("tolerance_measurement_assembly", f"tol_{tk}", "medium",
                f"请说明{obj}的{focus}。",
                f"主题:{obj};问题:{focus}。",
                f"{body}\n关于{focus}:须结合具体功能与工况。\n边界:{bd}",
                [body[:14]], ["功能要求", "工况", "公差等级", "相关标准"],
                tags + ["missing_information"], tk, focus))
    return out[:20]


# ============ 6. standard_evidence_refusal(深度) ============
def gen_standard():
    REFUSE = [
        ("no_load", "缺载荷谱判定轴安全", "不能下安全结论", "轴径、材料热处理状态、载荷谱、寿命目标"),
        ("no_material", "缺材料牌号问许用应力", "不能给数值", "材料牌号、热处理状态、载荷性质、适用标准"),
        ("no_geom", "未给尺寸问圆角半径", "不能给固定数值", "结构约束、应力集中要求、工艺能力、设计规范"),
        ("no_life", "缺载荷谱问疲劳寿命", "不能给寿命数值", "载荷谱、几何应力集中、材料疲劳数据"),
        ("no_heat", "不知热处理问硬度", "不能给硬度数值", "材料牌号、热处理状态、工况、硬度标准"),
        ("no_weld", "无焊缝等级问是否合格", "不能判定合格", "设计焊缝等级、检测标准、检测结果"),
    ]
    STD = [("gear", "齿轮强度校核", "GB/T 3480-2019《渐开线圆柱齿轮承载能力计算方法》", "渐开线圆柱齿轮接触与弯曲强度"),
           ("bolt", "螺栓力学性能", "GB/T 3098.1-2010《紧固件机械性能 螺栓、螺钉和螺柱》", "螺栓螺钉力学性能等级"),
           ("weld", "焊缝超声检测", "GB/T 11345-2013《焊缝无损检测 超声检测技术、检测等级和评定》", "焊缝超声检测等级与验收"),
           ("bearing", "轴承额定寿命", "GB/T 6391-2010《滚动轴承 额定动载荷和额定寿命》", "滚动轴承基本额定动载荷与寿命")]
    out = []
    for sk, q, refuse, missing in REFUSE:
        bd = f"涉及{missing}的具体结论须补全后依计算或标准给出;无来源版本不引用标准编号,不编造固定数值。"
        out.append(make("standard_evidence_refusal", f"ref_{sk}", "hard",
            "信息不足或无依据时,请明确拒绝并说明缺什么。",
            f"问题:{q}。",
            f"{refuse}。缺失:{missing}。补全后:静载按强度校核,交变按疲劳校核。\n注意:不得把可能当结论、不编造数值、不无依据引用标准。\n边界:{bd}",
            [refuse], ["载荷", "材料状态", "几何", "标准"], ["missing_information", "fabricated_value_risk"], sk))
    for sk, topic, std, scope in STD:
        bd = f"使用{std}前须核对版本、年份与适用范围({scope}),引用须记录标准号/年份/名称/条款。"
        out.append(make("standard_evidence_refusal", f"std_{sk}", "medium",
            f"请说明{topic}应参考的标准及适用性。",
            f"问题:{topic}参考什么标准。",
            f"{topic}参考{std};适用于{scope}。\n边界:{bd}",
            [topic[:10]], ["标准版本", scope, "适用条款"], ["standard_citation"], sk))
    extra = [("no_all", "几乎无信息问全面结论", "不能下任何确定结论", "载荷、材料、几何、寿命、标准全缺"),
             ("vague", "描述模糊问是否可行", "不能判断,描述不足以建模", "明确载荷、几何、材料、功能要求")]
    for sk, q, refuse, missing in extra:
        out.append(make("standard_evidence_refusal", f"ref_{sk}", "hard", "信息不足时请拒绝。",
            f"问题:{q}。", f"{refuse}。缺失:{missing}。\n边界:补全信息后才能工程判断。",
            [refuse], ["载荷", "材料", "几何", "标准"], ["missing_information"], sk))
    for sk in ["fatigue_method"]:
        for c in ["方法选择", "数据来源"]:
            out.append(make("standard_evidence_refusal", f"std_{sk}", "medium",
                f"请说明疲劳校核的{c}。",
                f"问题:疲劳校核的{c}。",
                f"{c}:名义应力法/局部应变法;数据须有出处(材料疲劳手册或试验),不臆造。\n边界:方法与数据须可追溯。",
                ["疲劳校核"], ["方法来源", "数据来源"], ["standard_citation"], sk, c))
    return out[:16]


# ============ 7. engineering_calculation(深度,加单位/陷阱) ============
CALC = [
    ("torsion", "实心圆轴扭转剪应力", "扭矩 T=5e6 N·mm, 轴径 d=50 mm", "Wt=πd³/16=π×125000/16≈24544 mm³；τ=T/Wt=5e6/24544≈203.7 MPa", "实心圆轴、纯扭转、弹性范围;未计键槽应力集中。注意 d 用 mm、T 用 N·mm,结果即 MPa(N/mm²)", "许用剪应力查材料标准(如 45 钢调质 [τ]≈60~80 MPa,需核实)"),
    ("bending", "简支梁跨中弯曲应力", "F=2 kN, L=200 mm, 截面 b×h=20×50 mm", "M=FL/4=2000×200/4=1.0e5 N·mm；W=bh²/6=20×2500/6≈8333 mm³；σ=M/W≈12.0 MPa", "线弹性、忽略自重与剪切;中点集中力", "对照材料许用弯曲应力"),
    ("bearing_life", "球轴承基本额定寿命", "当量动载荷 P=5 kN, 额定动载荷 C=20 kN", "L10=(C/P)³=(20/5)³=64 百万转;按转速 n 换算小时 Lh=106·L10/(60n)", "须实际载荷谱换算 P(当量动载荷);L10 为 90% 可靠度统计值", "高可靠度用 a1 系数修正"),
    ("tensile", "杆件拉伸应力", "F=10 kN, A=50 mm²", "σ=F/A=10000/50=200 MPa", "均匀拉伸、弹性范围", "对照屈服强度,σ<σs/n"),
    ("thin_cylinder", "薄壁圆筒环向应力", "内压 p, 半径 r, 壁厚 t", "环向 σθ=pr/t, 轴向 σz=pr/(2t),σθ=2σz", "薄壁假设 t/r≤0.1", "厚壁须用拉美公式"),
    ("gear_ratio", "齿轮传动比与扭矩", "z1=20, z2=60, 输入扭矩 T1", "i=z2/z1=3;T2=i·T1·η(η 为效率,0.97~0.99)", "单级减速;忽略损失 η=1", "多级传动 i 总=各级乘积"),
    ("twist_angle", "圆轴单位长度扭转角", "扭矩 T, 剪切模量 G, 极惯性矩 Ip", "单位长度 θ=T/(G·Ip);全长 φ=TL/(G·Ip)", "弹性、纯扭转、圆截面", "G 钢约 80 GPa"),
    ("cantilever", "悬臂梁端挠度", "端力 F, 长 L, 弹性模量 E, 惯性矩 I", "w=FL³/(3EI)", "线弹性、小变形、忽略剪切", "钢 E≈206 GPa"),
    ("euler", "压杆欧拉临界载荷", "E, 最小惯性矩 Imin, 长 L(两端铰支 μ=1)", "Pcr=π²EImin/L²", "弹性屈曲、细长杆(λ≥λp)、理想边界", "中长杆用直线/Johnson 公式"),
    ("hertz", "圆柱平行接触最大应力", "法向力 F, 接触长 Lc, 当量半径 R, 当量弹模 Ee", "接触半宽 a=√(4F·R/(π·Lc·Ee));最大接触应力 σHmax 在表面下浅层", "弹性、干接触、忽略润滑与粗糙度", "接触疲劳校核 σHmax"),
    ("centrifugal", "旋转薄环离心应力", "密度 ρ, 角速度 ω, 半径 r", "σ≈ρ·(ω·r)²=ρ·v²", "匀质薄环近似", "实际须计轮辐与应力分布"),
    ("thermal", "全约束杆热应力", "温升 ΔT, 线膨胀系数 α, 弹性模量 E", "σ=E·α·ΔT(两端全约束)", "全约束、弹性、未计屈服与松弛", "部分约束按约束度折减"),
]
def gen_calc():
    out = []
    for ck, name, given, proc, unit_note, review in CALC:
        bd = "结果需依实际工况与材料数据复核,单位须一致,不作普适常数。"
        out.append(make("engineering_calculation", f"calc_{ck}", "medium",
            "请给出完整计算:已知、公式、过程、结果、单位、假设、未考虑因素。",
            f"计算:{name};已知:{given}。",
            f"已知:{given}。\n公式与过程:{proc}。\n单位与陷阱:{unit_note}。\n复核:{review}。\n边界:{bd}",
            [proc[:14]], ["载荷", "几何", "材料性能", "单位"],
            ["static_strength", "fatigue"], ck))
    return out[:12]


# ============ 8. industrial_safety(修"作业"重复+深度) ============
SAF = [
    ("loto", "旋转设备检修前", "安全优先:先能源隔离——断电、上锁挂牌(LOTO)、泄压、释放残余能量(弹簧/电容/液压蓄能)、防止意外启动;用万用表/试电笔确认零能量状态后方可作业。一人一锁,钥匙随身。", ["safety_critical"]),
    ("lifting", "重物起吊", "安全优先:核验吊具吨位(工况余量≥1.25 倍)、检查索具与吊点(夹角≤60°)、明确指挥信号(哨音/对讲)、避开人员区域;严禁超载与斜拉;持证指挥,无人指挥不开机。", ["safety_critical"]),
    ("pressure", "压力容器检修", "安全优先:先泄压至零(确认压力表)、隔断并挂牌、排放残余介质、按规程置换与检测(测氧/可燃)达标后方可作业;严禁带压紧固或拆卸。", ["safety_critical"]),
    ("rotating", "靠近旋转部件", "安全优先:防护罩到位并确认、禁止戴手套或宽松衣物靠近、长发盘起、停机并锁机后方可清理或测量;遵守设备安全规程,未经培训不得作业。", ["safety_critical"]),
]
def gen_safety():
    out = []
    for sk, scene, body, tags in SAF:
        bd = "安全操作须遵循企业安全规程与适用法规,本文不替代安全责任人判断。"
        out.append(make("industrial_safety", f"safety_{sk}", "hard",
            "涉及安全时,请先给出隔离/停机/防护要求,再谈作业。",
            f"场景:{scene}。",
            f"{body}\n边界:{bd}",
            [body[:12]], ["设备状态", "能源类型", "安全规程"], tags, sk))
    return out[:4]


GENS = [gen_design, gen_manufacturing, gen_fault, gen_material,
        gen_tolerance, gen_standard, gen_calc, gen_safety]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="data/generated_v3/golden_v3.jsonl")
    a = ap.parse_args()
    recs = []
    for g in GENS:
        recs.extend(g())
    bad = [(r["id"], S.dict_to_record(r).validate()) for r in recs if S.dict_to_record(r).validate()]
    S.save_jsonl(recs, a.output)
    print(f"[golden_v3 深度版] {len(recs)} 条 -> {a.output}  (校验失败 {len(bad)})")
    print(f"  8 类: {dict(Counter(r['category'] for r in recs))}")
    if bad:
        print("  首个失败:", bad[0])


if __name__ == "__main__":
    main()
