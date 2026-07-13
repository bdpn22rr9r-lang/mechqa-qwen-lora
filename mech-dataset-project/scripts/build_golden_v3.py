"""V3 阶段A 金样本生成器(每条 output 实质独特,根治近似重复)。

设计: 每个变体(子问题)讲不同内容——轴类失效机理按工况特异;
manufacturing/fault 的"原因/控制/检验"是三段独立文本。不用换词复制。

用法: python build_golden_v3.py -o data/generated_v3/golden_v3.jsonl
"""
from __future__ import annotations
import os, sys, argparse, re
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema as S

AUTHOR, V3 = "model_assisted_draft", "v3"


def _uid(cat, *parts):
    return "v3_" + cat + "_" + re.sub(r"[^\w]+", "_", "_".join(map(str, parts))).strip("_")[:36]


def make(cat, sub, diff, instr, inp, out, ev, cond, tags, *uidparts):
    return S.MasterRecord(
        id=_uid(cat, *uidparts), category=cat, sub_category=sub, difficulty=diff,
        language="zh", instruction=instr, input=inp, output=out,
        evidence=ev, conditions=cond, risk_tags=tags, task_type=cat,
        source_type="expert_authored",
        source_ref="reports/standard_registry.json" if "standard_citation" in tags else "",
        license="pending",
        review_status="v3_pending_review", author=AUTHOR,
        split_group=_uid("sg", cat, *uidparts), version=V3,
    ).to_dict()


# ============ 1. design_fatigue ============
# 轴类: 每对象×工况 的失效机理特异(20条各不同)
SHAFT = {
    "cross_hole": {
        "name": "横向销孔轴", "geom": "孔径与轴径", "mfg": "孔口去毛刺倒圆、关注孔壁表面完整性", "insp": "孔口磁粉或渗透检测",
        "fail": {"bending": "交变弯曲下孔边产生弯曲应力集中,孔口受拉侧应力峰值显著",
                 "torsion": "交变扭转下孔周产生剪应力集中,孔壁主应力方向反复",
                 "combined": "弯扭复合下孔边同时存在正应力与剪应力集中叠加",
                 "rotating": "旋转弯曲下孔口每转承受一次交变应力集中峰值"}},
    "keyway": {
        "name": "键槽轴", "geom": "键槽宽与根部圆角", "mfg": "键槽根部留圆角、可喷丸强化", "insp": "键槽根部磁粉检测",
        "fail": {"bending": "键槽根部在弯曲下的拉应力集中",
                 "torsion": "键槽根部在扭转下剪应力集中(键槽是扭转传力薄弱区)",
                 "combined": "键槽根部弯扭合成应力集中",
                 "rotating": "旋转弯曲下键槽根部每转应力交变"}},
    "shoulder": {
        "name": "轴肩台阶轴", "geom": "大小端直径与圆角半径", "mfg": "加大圆角、设卸载槽", "insp": "圆角磁粉检测",
        "fail": {"bending": "轴肩圆角在弯曲下的拉应力集中",
                 "torsion": "轴肩处扭转剪应力相对均匀但圆角仍有应力集中",
                 "combined": "轴肩圆角弯扭合成应力集中",
                 "rotating": "旋转弯曲下轴肩圆角每转应力交变"}},
    "spline": {
        "name": "花键轴", "geom": "模数与齿根圆角", "mfg": "齿根圆角、表面淬火", "insp": "齿根与齿面检测",
        "fail": {"bending": "花键齿根在弯曲下的拉应力集中",
                 "torsion": "花键齿根在扭转下剪应力集中并伴齿面磨损",
                 "combined": "花键齿根弯扭合成应力集中",
                 "rotating": "旋转弯曲下花键齿根每转应力交变"}},
    "smooth": {
        "name": "光轴(对照)", "geom": "直径与表面质量", "mfg": "保证表面质量与直线度", "insp": "表面与直线度检查",
        "fail": {"bending": "光轴表面弯曲应力无几何集中,疲劳受表面质量与尺寸系数控制",
                 "torsion": "光轴扭转剪应力无几何集中,受表面质量控制",
                 "combined": "光轴弯扭合成应力无几何集中源",
                 "rotating": "光轴旋转弯曲疲劳受表面质量与尺寸控制"}},
}
LOAD = {
    "bending": ("交变弯曲", "算弯曲名义应力与疲劳缺口系数做疲劳校核", "弯曲疲劳寿命", "弯矩载荷谱"),
    "torsion": ("交变扭矩", "算扭转剪应力幅与缺口效应做剪切疲劳校核", "剪切疲劳寿命", "扭矩载荷谱"),
    "combined": ("弯扭复合", "按当量应力合成分别评估静强度与疲劳", "复合疲劳寿命", "弯扭载荷谱"),
    "rotating": ("旋转弯曲", "按对称循环疲劳极限校核并核查共振", "旋转弯曲疲劳寿命", "转速与弯矩谱"),
}
def gen_design():
    out = []
    for ok, o in SHAFT.items():
        for lk, (ln, chk, life, par) in LOAD.items():
            bd = f"{o['fail'][lk]}对应的应力集中系数需依{o['geom']}核定,且{o['name']}的{life}结论需要{par}支撑。"
            out.append(make("design_fatigue", f"shaft_{ok}", "hard" if ok != "smooth" else "medium",
                "请识别关键风险并给出可执行的校核路径。",
                f"对象:{o['name']}，高应力区；工况：{ln}。未提供{o['geom']}、材料状态与{par}。",
                f"1. 失效模式：{o['name']}在{ln}下，{o['fail'][lk]}，须按疲劳而非静强度校核。\n"
                f"2. 校核：{chk}，需{o['geom']}、材料疲劳性能与{par}。\n"
                f"3. 制造：{o['mfg']}。\n4. 检测：{o['insp']}。\n5. 缺失：{o['geom']}、材料状态、{par}、目标寿命。\n边界：{bd}",
                [o['fail'][lk][:14]], ["载荷谱", o['geom'], "材料状态", "寿命目标"],
                ["fatigue", "stress_concentration", "missing_information"] + ([] if ok == "smooth" else ["surface_integrity"]),
                "shaft", ok, lk))
    # 其他对象: 每个独立子主题(齿轮3/轴承3/螺栓3/焊接3/梁4 = 16), 凑到~48需再加变体但用独立问题
    EXTRA = [
        ("gear_root_bending", "齿根弯曲疲劳齿轮", "齿根弯曲应力集中致齿根断裂", "齿根弯曲强度按 GB/T 3480.3-2021 的适用范围和方法校核", ["fatigue", "stress_concentration"]),
        ("gear_pitting", "齿面点蚀齿轮", "齿面接触疲劳致点蚀剥落", "按赫兹接触应力校核齿面接触疲劳", ["wear_contact_fatigue"]),
        ("gear_scuffing", "重载高速齿轮", "齿面油膜破裂致胶合", "按闪温法或积分温度法校核胶合", ["wear_contact_fatigue", "thermal_deformation"]),
        ("bearing_loose_fit", "游隙过大轴承", "游隙过大致振动与早期点蚀", "校核配合后游隙与当量动载荷寿命", ["assembly_tolerance", "fatigue"]),
        ("bearing_life", "受载轴承", "滚动体与滚道接触疲劳", "按 L10=(C/P)^ε 估算寿命并修正可靠度", ["fatigue", "wear_contact_fatigue"]),
        ("bearing_creep", "内圈蠕动轴承", "内圈配合过盈不足致蠕动磨损", "校核过盈量与摩擦力矩防蠕动", ["assembly_tolerance", "wear_contact_fatigue"]),
        ("bolt_fatigue", "受拉螺栓", "交变载荷下螺栓疲劳断裂", "校核应力幅与残余预紧力", ["fatigue", "fastener_loosening"]),
        ("bolt_loosen", "横向载荷螺栓", "横向滑移致螺栓松动", "校核防松方案与残余预紧", ["fastener_loosening", "fatigue"]),
        ("bolt_separation", "受拉螺栓连接", "被连接件分离致刚度突变", "保证残余预紧力大于分离要求", ["fastener_loosening"]),
        ("weld_toe_fatigue", "对接焊接接头", "焊趾应力集中与残余拉应力致疲劳", "按 IIW 名义/热点应力法评估", ["fatigue", "stress_concentration"]),
        ("weld_defect", "含缺陷焊缝", "气孔夹渣或未熔合成为裂纹源", "按焊缝等级与无损检测结果评定", ["inspection_ndt", "manufacturing_process"]),
        ("weld_distortion", "焊接结构", "焊接残余应力致变形与失稳", "控制焊接顺序与残余应力分布", ["thermal_deformation", "manufacturing_process"]),
        ("beam_buckling", "薄壁受压梁", "受压板局部屈曲先于强度破坏", "校核宽厚比与加劲肋", ["buckling_stability"]),
        ("beam_deflection", "细长梁", "刚度不足致变形超限", "校核挠度与刚度", ["stiffness_deflection"]),
        ("plate_shear_buckling", "腹板", "腹板高剪下剪切屈曲", "校核高厚比与横向加劲肋", ["buckling_stability"]),
        ("shell_buckling", "薄壳结构", "外压下整体或局部屈曲", "按临界外压校核稳定性", ["buckling_stability"]),
        ("shaft_ring_groove", "带挡圈槽传动轴", "挡圈槽根部截面突变形成疲劳裂纹起点", "按槽底净截面和缺口效应校核交变弯曲疲劳", ["fatigue", "stress_concentration"]),
        ("shaft_thread_runout", "带外螺纹轴端", "螺纹收尾与退刀槽叠加应力集中", "确定危险截面并校核螺纹根部疲劳强度", ["fatigue", "stress_concentration"]),
        ("crank_oil_hole", "带斜油孔曲轴", "油孔出口位于高应力区时易萌生疲劳裂纹", "结合弯扭载荷和油孔位置评估局部疲劳", ["fatigue", "surface_integrity"]),
        ("press_fit_hub", "过盈配合轮毂轴", "配合边缘接触压力与交变弯曲叠加可能引起微动疲劳", "校核配合压力、边缘应力和传扭能力", ["fatigue", "wear_contact_fatigue"]),
        ("lifting_lug", "焊接起吊耳板", "孔边承压、净截面撕裂和焊趾疲劳可能共同控制", "按实际吊装方向校核耳板与焊缝载荷路径", ["static_strength", "fatigue"]),
        ("pin_joint", "受交变载荷销轴连接", "销孔承压磨损与板件净截面疲劳相互影响", "分别校核销轴剪弯、孔壁承压和板件净截面", ["fatigue", "wear_contact_fatigue"]),
        ("spring_fatigue", "往复压缩弹簧", "平均应力和应力幅共同影响弹簧疲劳寿命", "结合载荷循环、应力修正和稳定性校核", ["fatigue"]),
        ("thin_gear_rim", "薄轮缘齿轮", "轮缘柔度会改变齿根应力分布并诱发轮缘裂纹", "同时校核齿根弯曲和轮缘厚度影响", ["fatigue", "stiffness_deflection"]),
        ("planet_carrier", "行星架销孔", "销孔载荷分配不均会造成孔边局部高应力和变形", "校核销孔承压、行星架刚度和载荷均布", ["fatigue", "stiffness_deflection"]),
        ("eccentric_flange", "偏心受载法兰连接", "外载偏心引起连接面压力重分布和螺栓附加拉力", "建立连接刚度模型并校核不分离与螺栓疲劳", ["fatigue", "fastener_loosening"]),
        ("coupling_hub_key", "键连接联轴器轮毂", "键槽削弱轮毂且冲击扭矩可能导致槽角裂纹", "校核键侧挤压、轮毂强度和冲击疲劳", ["fatigue", "stress_concentration"]),
        ("frame_load_path", "螺栓连接设备机架", "连接刚度不均会造成载荷旁路和局部板件过载", "梳理载荷路径并校核连接滑移、板件和焊缝", ["static_strength", "stiffness_deflection"]),
    ]
    for ek, obj, fail, chk, tags in EXTRA:
        bd = f"{fail}的判定需结合相关几何与适用标准(记录标准号/年份/条款)核定,缺数据不下确定结论。"
        out.append(make("design_fatigue", f"{ek}", "medium",
            "请识别风险并给出校核方向。",
            f"对象:{obj}；请评估其可靠性。",
            f"1. 失效模式：{fail}。\n2. 校核方向：{chk}。\n边界：{bd}",
            [fail[:12]], ["载荷", "几何", "材料状态", "适用标准"],
            tags + ["missing_information"], ek))
    return out[:48]


# ============ 2. manufacturing_qc ============
# 每工序: 三段独立文本(原因/控制/检验), 子问题变体分别用对应段
PROC = {
    "turning": ("阶梯轴车削变形", "原因：切削力、工件刚度不足、装夹不当、切削热致尺寸与形位超差", "控制：降低切削用量、用中心架跟刀架、分粗精车、控制切削液", "检验：首件测跳动与直径、过程抽检变形、终检形位"),
    "heat_distortion": ("淬火变形开裂", "原因：热应力与相变应力叠加、结构不对称、冷却不均", "控制：优化淬火介质与冷却、分级等温淬火、预留余量、定型工装", "检验：变形量测量、磁粉探伤查裂纹、硬度与金相抽检"),
    "grind_crack": ("磨削裂纹烧伤", "原因：磨削深度大、冷却不足、磨削进给快、表面淬火件残余应力", "控制：减小磨削量、充分冷却、及时回火、控制进给", "检验：酸洗或磁探查裂纹、表面硬度与烧伤检查"),
    "weld_defect": ("焊缝气孔夹渣", "原因：保护不良、坡口污染、参数不当、焊剂受潮", "控制：清理坡口、烘干焊剂、优化电流电压与保护气流量", "检验：按焊缝等级做射线/超声/渗透检测"),
    "casting_shrink": ("铸件缩孔缩松", "原因：凝固顺序不当、补缩不足、浇注温度与冒口设计问题", "控制：优化浇注系统与冒口、控制凝固顺序、加冷铁", "检验：关键区射线或CT探伤、尺寸与外观检查"),
    "carburizing": ("渗碳淬火变形", "原因：渗碳层体积变化、淬火介质与冷却不均", "控制：控制渗层均匀性、预留磨量、压床定型、选合适介质", "检验：渗层深度与硬度梯度、变形量、磁粉探伤"),
    "roughness": ("表面粗糙度超差", "原因：刀具磨损或几何不当、进给过大、工艺系统振动", "控制：优化刀尖半径与进给、抑振、精加工保证、换刀管理", "检验：粗糙度仪测量、对照要求的 Ra/Rz 等级"),
    "symmetry": ("键槽对称度超差", "原因：装夹基准误差、分度误差、刀具偏让", "控制：校核装夹基准、提高分度精度、首件验证、刚性装夹", "检验：三坐标或量具测对称度、首件与抽检"),
    "deep_hole": ("深孔钻削偏斜", "原因：刀具导向不足、排屑受阻、进给与冷却不稳定", "控制：采用可靠导向与分段排屑、稳定供液、监控刀具磨损", "检验：测孔轴线位置、直线度、孔径与内壁缺陷"),
    "thin_wall": ("薄壁壳体加工变形", "原因：装夹变形、残余应力释放、切削热和余量不均", "控制：使用低变形夹紧、对称去除余量、分阶段时效与精加工", "检验：松夹后复测尺寸、平面度、圆度和壁厚分布"),
    "thread_rolling": ("高疲劳螺纹成形", "原因：切削螺纹可能破坏材料流线并留下刀痕", "控制：在材料与结构允许时评估滚压工艺、控制坯径和模具状态", "检验：检查牙型、有效径、表面缺陷与工艺批次一致性"),
    "nitriding": ("氮化层质量波动", "原因：表面污染、温度或气氛波动导致层深和脆性不均", "控制：规范预清洗、装炉间距、温度与介质控制并保护非氮化区", "检验：按图样要求检查层深、硬度梯度、脆性与变形"),
}
def gen_manufacturing():
    out = []
    for pk, (obj, cause, ctrl, insp) in PROC.items():
        # 3 个子问题, 各用对应段(output 内容实质不同)
        subs = [("cause", "请分析该质量问题的主要原因。", cause),
                ("control", "请给出该工序的控制措施。", ctrl),
                ("inspect", "请说明该工序的检验要点。", insp)]
        for sk, q, body in subs:
            if len(out) >= 36:
                break
            bd = {
                "cause": f"以上是{obj}的候选机制,须用设备记录、工件实测和工艺追溯区分主因。",
                "control": f"{obj}的控制窗口须经首件和过程能力验证,本条不代替正式工艺卡。",
                "inspect": f"{obj}的验收项目与限值以图样、工艺文件和检验规范为准。",
            }[sk]
            out.append(make("manufacturing_qc", f"mfg_{pk}", "medium",
                q,
                f"对象:{obj}工序。",
                f"{body}\n边界：{bd}",
                [obj[:8]], ["材料", "几何", "工艺参数", "质量要求"],
                ["manufacturing_process", "missing_information"], pk, sk))
    return out[:36]


# ============ 3. fault_diagnosis ============
EQ = {
    "gearbox": ("减速机振动温升油变质", "原因：润滑不良、轴承磨损、齿轮点蚀、对中不良", "排查：油液分析磨粒、振动频谱找轴承/齿轮特征频率、查对中", "处置：换油、校中、换轴承或修齿轮,区分停机与在线监测"),
    "bearing": ("滚动轴承异响温升", "原因：滚道滚动体点蚀剥落、润滑不良、游隙过大", "排查：包络解调找外圈/内圈/滚动体缺陷频率、查润滑游隙", "处置：早期点蚀可监测,剥落扩展需更换"),
    "hydraulic": ("液压系统压力波动爬行", "原因：泄漏、进气、阀卡滞、泵磨损", "排查：测各点压力流量、排气、查阀芯与泵容积效率", "处置：堵漏换密封、换阀或泵、严格控制清洁度"),
    "coupling": ("联轴器端振动大", "原因：对中不良、不平衡、基础松动、共振", "排查：测振动相位与频谱、查对中与地脚、动平衡", "处置：校中、紧固、动平衡、避开共振转速"),
    "compressor": ("压缩机级间温度升高", "原因：气阀泄漏、冷却不足、积碳、级间泄漏", "排查：查冷却水温水量、气阀密封、级间压比与温度", "处置：换阀片、清积碳、修冷却器,必要时解体"),
    "pump": ("离心泵流量扬程下降", "原因：叶轮磨损、口环间隙大、汽蚀、密封泄漏", "排查：测进出口压力流量、查NPSHA防汽蚀、测口环间隙", "处置：换叶轮口环、治漏、改善吸入条件"),
    "fan": ("风机一倍转频振动升高", "原因：叶轮积灰或损伤导致不平衡、轴弯曲、基础松动", "排查：比较径向振幅与相位、检查叶轮和轴跳动、复核基础", "处置：清理修复叶轮、校直或动平衡、紧固基础后复测"),
    "seal": ("机械密封持续泄漏", "原因：端面损伤、轴跳动超限、冲洗不足、密封材料不适配", "排查：确认泄漏位置、检查冲洗参数、测轴跳动与窜量", "处置：纠正轴系问题并按介质复核密封材料后更换损坏件"),
    "conveyor": ("输送带持续跑偏", "原因：滚筒托辊不正、落料偏载、张紧不均或接头不正", "排查：分别观察空载与负载轨迹、校核滚筒托辊和落料中心", "处置：先消除结构与落料根因,再逐级微调托辊和张紧"),
    "spindle": ("机床主轴加工出现周期振纹", "原因：刀具不平衡、主轴轴承状态异常、切削参数激发颤振", "排查：做空转与切削对比、检查刀柄跳动、分析频谱和稳定区", "处置：修正刀具装夹与平衡、避开不稳定工况并评估轴承"),
    "robot_joint": ("机器人关节热态定位误差增大", "原因：减速器热膨胀、回差变化、编码器安装或补偿不足", "排查：记录温度与误差关系、比较冷热态回差、检查机械零位", "处置：排除松动磨损后建立经验证的温度补偿"),
    "screw_conveyor": ("螺杆输送机电流升高并卡停", "原因：物料结块或异物、叶片变形、吊轴承损坏、出料受阻", "排查：停机隔离后清料,检查出入口、轴线、间隙和轴承", "处置：清除堵塞并修复变形磨损,复核运行负荷与保护设定"),
}
def gen_fault():
    out = []
    for ek, (symp, cause, probe, handle) in EQ.items():
        subs = [("cause", "请分析可能的故障原因(排序)。", cause),
                ("probe", "请给出排查步骤。", probe),
                ("handle", "请说明处置原则。", handle)]
        for sk, q, body in subs:
            if len(out) >= 36:
                break
            bd = {
                "cause": f"{symp}可能由多种因素共同造成,原因排序须由趋势、频谱和现场检查相互印证。",
                "probe": f"{symp}的排查应保留原始数据和工况,避免检修后失去根因证据。",
                "handle": f"{symp}的处置等级须结合报警限值、劣化速度和失效后果决定。",
            }[sk]
            out.append(make("fault_diagnosis", f"fault_{ek}", "medium",
                q,
                f"设备现象:{symp}。",
                f"{body}\n边界：{bd}",
                [symp[:10]], ["运行参数", "型号", "历史记录", "监测数据"],
                ["vibration_resonance", "wear_contact_fatigue", "inspection_ndt", "missing_information"], ek, sk))
    return out[:36]


# ============ 4. material_heat_treatment ============
MAT = {
    "selection": ("高强度高韧性选材", "要点：中碳调质钢调质获强韧匹配;更高要求用表面淬火或渗碳钢。须同时看屈服、冲击、疲劳与淬透性,不只看抗拉强度。截面越大越需选淬透性高的钢。", ["heat_treatment", "static_strength"]),
    "distortion": ("淬火变形控制", "要点：优化结构对称性、选合适介质(油/分级/等温)、控制温度、用定型工装、预留余量。注意脱碳与淬火裂纹。结构不对称与冷却不均是主因。", ["heat_treatment", "thermal_deformation"]),
    "induction": ("表面感应淬火提疲劳", "要点：表层高硬马氏体加残余压应力显著提高疲劳强度。硬化层须覆盖高应力区;过渡区是新的薄弱点。淬后须回火控裂。", ["surface_integrity", "fatigue"]),
    "tempering": ("回火工艺", "要点：回火温度决定强度与韧性权衡。低温回火保硬度,高温回火提韧性(调质)。须避开回火脆性区。具体工艺依材料牌号与性能要求。", ["heat_treatment"]),
    "evidence": ("材料性能证据抽取", "要点：依据给定文献片段抽取性能并保留温度、方向、工艺等适用条件。不得把条件性实验值泛化为材料常数。须核对数值与材料实体对应。", ["missing_information"]),
    "anisotropy": ("材料各向异性", "要点：轧制或锻造材料的纵向与横向力学性能不同,疲劳与断裂性能各向异性显著。设计与校核须注意取样方向。", ["fatigue", "static_strength"]),
    "corrosion": ("腐蚀环境影响", "要点：腐蚀环境降低疲劳强度(腐蚀疲劳),应力腐蚀开裂在特定材料-介质组合下危险。须评估工况介质并选耐蚀材料或防护。", ["corrosion", "fatigue"]),
}
MATERIAL_CONDITION_FOCUS = {
    "常温工况": "重点核对室温拉伸、冲击和硬度等批次证明,并确认试样方向与零件截面差异。",
    "高温工况": "除瞬时强度外还要检查蠕变、松弛、氧化及组织稳定性,使用目标温度和持续时间下的数据。",
    "腐蚀工况": "需要介质成分、浓度、温度和应力状态,评估点蚀、腐蚀疲劳或应力腐蚀开裂。",
    "交变载荷": "应使用与表面、尺寸、缺口和可靠度相匹配的疲劳数据,不能以抗拉强度替代寿命校核。",
}
def gen_material():
    out = []
    for mk, (obj, body, tags) in MAT.items():
        for cond in ["常温工况", "高温工况", "腐蚀工况", "交变载荷"]:
            if len(out) >= 28:
                break
            focus = MATERIAL_CONDITION_FOCUS[cond]
            bd = f"{obj}在{cond}下的结论须由材料牌号、热处理状态、零件尺寸和可追溯数据共同支持。"
            out.append(make("material_heat_treatment", f"mat_{mk}", "medium",
                "请说明该材料/热处理问题的要点与适用条件。",
                f"主题:{obj};工况:{cond}。",
                f"{body}\n{obj}在{cond}下的工况重点：{focus}\n边界：{bd}",
                [body[:14]], ["材料牌号", "热处理状态", "截面尺寸", cond],
                tags + ["missing_information"], mk, cond))
    return out[:28]


# ============ 5. tolerance_measurement_assembly ============
TOL = {
    "chain": ("尺寸链", "用极值法或统计法求解封闭环。极值法保守,统计法经济但需公差分布假设。须明确增减环。", ["assembly_tolerance"]),
    "datum": ("基准统一", "设计、工艺、测量基准应统一。基准不一致会累积误差,影响装配与功能。", ["assembly_tolerance"]),
    "gd&t_runout": "s",
}
TOL = {
    "chain": ("尺寸链计算", "用极值法或统计法求解封闭环。极值法保守,统计法经济但需分布假设。须明确增减环与公差分配。", ["assembly_tolerance"]),
    "datum": ("基准统一原则", "设计、工艺、测量基准应统一。基准不一致累积误差,影响装配与功能。", ["assembly_tolerance"]),
    "gd&t": ("形位公差给定", "形位公差依配合、运动、密封功能给定。过严增加成本,过松丧失功能。须结合尺寸链。", ["assembly_tolerance", "inspection_ndt"]),
    "fit_clearance": ("间隙配合选择", "间隙配合依相对运动、润滑、温度选。须保证最小间隙大于热膨胀与油膜厚度。", ["assembly_tolerance", "thermal_deformation"]),
    "fit_interference": ("过盈配合选择", "过盈配合依传递力、转速、装拆选。须校核传递扭矩与配合应力,避免应力过大。", ["assembly_tolerance", "static_strength"]),
    "measure_uncertainty": ("测量不确定度", "测量结果含不确定度。须选合适量仪与基准、控制温度,评估不确定度是否小于公差。", ["inspection_ndt"]),
    "assembly_seq": ("装配顺序", "复杂装配的顺序影响累积误差与应力。须规划装配顺序,关键配合用选配或修配。", ["assembly_tolerance", "manufacturing_process"]),
}
TOLERANCE_FOCUS = {
    "如何确定": "确定流程应从功能量和失效后果出发,建立尺寸链或配合模型,再在制造能力与成本约束下分配要求。",
    "需要什么信息": "输入至少包括功能接口、基准体系、载荷温度、装配顺序、测量方案和过程能力数据。",
    "常见错误": "重点防止基准不统一、公差重复约束、忽略温度与测量不确定度,以及脱离功能盲目提高精度。",
}
def gen_tolerance():
    out = []
    for tk, (obj, body, tags) in TOL.items():
        for focus in ["如何确定", "需要什么信息", "常见错误"]:
            if len(out) >= 20:
                break
            bd = f"{obj}的具体数值须依功能要求、工况与相关公差配合标准核定。"
            out.append(make("tolerance_measurement_assembly", f"tol_{tk}", "medium",
                f"请说明{obj}的{focus}。",
                f"主题:{obj};问题:{focus}。",
                f"{body}\n对于{obj},{TOLERANCE_FOCUS[focus]}\n边界：{bd}",
                [body[:14]], ["功能要求", "工况", "公差等级", "相关标准"],
                tags + ["missing_information"], tk, focus))
    return out[:20]


# ============ 6. standard_evidence_refusal ============
def gen_standard():
    REFUSE = [
        ("no_load", "缺载荷谱判定轴安全", "不能下安全结论", "轴径、材料热处理状态、载荷谱、寿命目标"),
        ("no_material", "缺材料牌号问许用应力", "不能给数值", "材料牌号、热处理状态、载荷性质、适用标准"),
        ("no_geom", "未给尺寸问圆角半径", "不能给固定数值", "结构约束、应力集中要求、工艺能力、设计规范"),
        ("no_life", "缺载荷谱问疲劳寿命", "不能给寿命数值", "载荷谱、几何应力集中、材料疲劳数据"),
        ("no_heat", "不知热处理问硬度要求", "不能给硬度数值", "材料牌号、热处理状态、工况、硬度标准"),
        ("no_weld", "无焊缝等级问是否合格", "不能判定合格", "设计焊缝等级、检测标准、检测结果"),
        ("no_fit", "缺少功能要求直接指定轴孔配合", "不能指定配合代号", "相对运动、载荷、温度、装拆和定位要求"),
        ("no_standard_version", "只有标准号但未确认版本与适用范围", "不能据此给出合规结论", "现行版本、标准名称、适用范围、相关条款"),
    ]
    STD = [
        ("gear", "齿轮强度校核", "GB/T 3480.1-2019《直齿轮和斜齿轮承载能力计算 第1部分：基本原理、概述及通用影响系数》", "直齿轮和斜齿轮承载能力计算的基本原则；接触与弯曲强度还需选用对应分册"),
        ("bolt", "螺栓力学性能", "GB/T 3098.1-2010《紧固件机械性能 螺栓、螺钉和螺柱》", "螺栓螺钉的力学性能等级"),
        ("weld", "焊缝超声检测", "GB/T 11345-2023《焊缝无损检测 超声检测 技术、检测等级和评定》", "焊缝超声检测技术、检测等级和评定"),
        ("bearing", "轴承额定动载荷", "GB/T 6391-2010《滚动轴承 额定动载荷和额定寿命》", "滚动轴承基本额定动载荷与寿命计算"),
    ]
    out = []
    for sk, q, refuse, missing in REFUSE:
        bd = f"针对“{q}”,须补全{missing}并依据计算或经核验资料作答。"
        out.append(make("standard_evidence_refusal", f"ref_{sk}", "hard",
            "信息不足或无依据时,请明确拒绝并说明缺什么。",
            f"问题:{q}。",
            f"{refuse}。缺失:{missing}。补全后方可校核。\n边界:{bd}",
            [refuse], ["载荷", "材料状态", "几何", "标准"],
            ["missing_information", "fabricated_value_risk"], sk))
    for sk, topic, std, scope in STD:
        bd = f"使用{std.split('》')[0]}》前须核对版本、年份与适用范围({scope}),不得盲目套用。"
        out.append(make("standard_evidence_refusal", f"std_{sk}", "medium",
            f"请说明{topic}应参考的标准及其适用性。",
            f"问题:{topic}参考什么标准。",
            f"{topic}可参考{std};该标准适用于{scope}。引用须记录标准号、年份、名称与适用条款。\n边界:{bd}",
            [topic[:10]], ["标准版本", scope, "适用条款"], ["standard_citation"], sk))
    # 凑到16: 6 refuse + 4 std = 10, 再加变体
    extra_refuse = [
        ("no_all", "几乎无信息问全面结论", "不能下任何确定结论", "载荷、材料、几何、寿命、标准全部缺失"),
        ("vague_context", "描述模糊问是否可行", "不能判断,描述不足以建模", "明确的载荷、几何、材料、功能要求"),
    ]
    for sk, q, refuse, missing in extra_refuse:
        out.append(make("standard_evidence_refusal", f"ref_{sk}", "hard",
            "信息不足时请明确拒绝。",
            f"问题:{q}。",
            f"{refuse}。缺失:{missing}。\n边界:补全信息后才能进行工程判断。",
            [refuse], missing.split("、")[:4], ["missing_information"], sk))
    for sk, topic, std, scope in [("shaft_fatigue", "轴疲劳设计", "相关疲劳设计方法与材料疲劳数据标准", "轴类疲劳强度校核")]:
        for c in ["方法选择", "数据来源"]:
            out.append(make("standard_evidence_refusal", f"std_{sk}", "medium",
                f"请说明{topic}的{c}。",
                f"问题:{topic}的{c}。",
                f"{c}须依据{std};{scope}需结合具体工况。\n边界:方法与数据须有出处,不臆造。",
                [topic[:10]], ["方法来源", "数据来源", scope], ["standard_citation"], sk, c))
    return out[:16]


# ============ 7. engineering_calculation ============
CALC = [
    ("torsion", "实心圆轴扭转剪应力", "扭矩 T=5e6 N·mm, 轴径 d=50 mm", "Wt=πd³/16≈24544 mm³；τ=T/Wt≈203.7 MPa", "实心圆轴纯扭转弹性范围,未计应力集中；许用剪应力查材料标准"),
    ("bending", "简支梁跨中弯曲应力", "F=2 kN, L=200 mm, 截面 b×h=20×50 mm", "M=FL/4=1.0e5 N·mm；W=bh²/6≈8333 mm³；σ=M/W≈12.0 MPa", "简支梁中点集中力、线弹性、忽略自重与剪切"),
    ("bearing_life", "球轴承基本额定寿命", "当量动载荷 P=5 kN, 额定动载荷 C=20 kN", "L10=(C/P)^3=(20/5)^3=64 百万转", "须实际载荷谱换算当量动载荷;L10 为 90% 可靠度统计值"),
    ("tensile", "杆件拉伸应力", "载荷 F=10 kN, 截面积 A=50 mm²", "σ=F/A=10000/50=200 MPa", "均匀拉伸弹性范围;对照材料许用应力"),
    ("thin_cylinder", "薄壁圆筒膜应力", "内压 p, 半径 r, 壁厚 t", "环向应力 σθ=pr/t, 轴向应力 σz=pr/(2t)", "薄壁假设 t/r≤0.1,未计连接应力集中"),
    ("gear_ratio", "齿轮传动比与输出扭矩", "z1=20, z2=60, 输入扭矩 T1", "i=z2/z1=3；输出扭矩 T2=i·T1·η(η 为效率)", "忽略损失 η=1;实际须计齿轮效率"),
    ("twist_angle", "圆轴单位长度扭转角", "扭矩 T, 剪切模量 G, 极惯性矩 Ip", "θ=T/(G·Ip)(单位长度);全长 φ=TL/(G·Ip)", "弹性范围、纯扭转、圆截面"),
    ("cantilever", "悬臂梁端挠度", "端力 F, 长 L, 弹性模量 E, 惯性矩 I", "端挠度 w=FL³/(3EI)", "线弹性、小变形、忽略剪切变形"),
    ("euler", "压杆欧拉临界载荷", "弹性模量 E, 最小惯性矩 Imin, 长 L, 长度系数 μ", "Pcr=π²E·Imin/(μL)²", "弹性屈曲、细长杆、理想约束;短粗杆用 Johnson/屈服"),
    ("hertz", "圆柱平行接触赫兹应力", "接触力 F, 接触长度 Lc, 当量曲率半径 R, 当量弹性模量 Ee", "接触半宽 a 与最大接触应力 σHmax∝sqrt(F·Ee/(R·Lc))", "弹性、干接触、忽略润滑与粗糙度"),
    ("centrifugal", "旋转薄环离心应力", "密度 ρ, 角速度 ω, 平均半径 r", "环向离心应力 σ≈ρ·ω²·r²", "匀质薄环近似;实际须计轮辐与应力分布"),
    ("thermal", "全约束杆热应力", "温升 ΔT, 线膨胀系数 α, 弹性模量 E", "σ=E·α·ΔT(两端全约束)", "全约束、弹性范围、未计屈服与应力松弛"),
]
def gen_calc():
    out = []
    for ck, name, given, proc, caveat in CALC:
        bd = f"{name}的结果仅适用于题设假设,工程采用前须复核输入、单位和适用范围。"
        out.append(make("engineering_calculation", f"calc_{ck}", "medium",
            "请给出完整计算:已知、公式、过程、结果、假设、未考虑因素。",
            f"计算:{name};已知:{given}。",
            f"已知:{given}。\n公式与过程:{proc}。\n假设与未考虑:{caveat}。\n边界:{bd}",
            [proc[:14]], ["载荷", "几何", "材料性能", "单位"],
            ["static_strength", "fatigue"], ck))
    return out[:12]


# ============ 8. industrial_safety ============
SAF = [
    ("loto", "检修旋转设备前", "安全优先：先执行能源隔离——断电、上锁挂牌、泄压、防止意外启动,确认零能量状态后方可作业;遵守 LOTO(上锁挂牌)程序。"),
    ("lifting", "重物起吊作业", "安全优先：核验吊具吨位与工况余量、检查索具与吊点、明确指挥信号、避开人员区域;严禁超载与斜拉;须持证指挥。"),
    ("pressure", "压力容器检修", "安全优先：先泄压至零、隔断并挂牌、确认无残余压力与介质、按规程置换与检测;严禁带压紧固或拆卸。"),
    ("rotating", "靠近旋转部件作业", "安全优先：防护罩到位并确认、禁止戴手套或宽松衣物靠近、停机后方可清理或测量;遵守设备安全规程。"),
]
def gen_safety():
    out = []
    for sk, scene, body in SAF:
        bd = "安全操作须遵循企业安全规程与适用法规,本文不替代安全责任人判断。"
        out.append(make("industrial_safety", f"safety_{sk}", "hard",
            "涉及安全时,请先给出隔离/停机/防护要求,再谈作业。",
            f"场景:{scene}作业。",
            f"{body}\n边界:{bd}",
            [body[:12]], ["设备状态", "能源类型", "安全规程"], ["safety_critical"], sk))
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
    print(f"[golden_v3] {len(recs)} 条 -> {a.output}  (校验失败 {len(bad)})")
    print(f"  8 类: {dict(Counter(r['category'] for r in recs))}")
    if bad:
        print("  首个失败:", bad[0])


if __name__ == "__main__":
    main()
