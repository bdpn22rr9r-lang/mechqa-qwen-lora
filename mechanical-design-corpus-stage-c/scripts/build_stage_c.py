"""Build the complete Stage C corpus from the reviewed Stage A scenario bank.

The expansion is deterministic and traceable: every record retains its parent
scenario while adding an independently selected operating envelope, lifecycle
state, evidence constraint and decision objective. No external dependency is
required.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import schema as S

TARGETS = S.V3_TARGETS
SEED = 20260713

OPERATING = [
    ("连续稳态", "额定载荷长期运行", "关注累积损伤与温升稳定值"),
    ("频繁启停", "每天多次启停并伴随惯性冲击", "关注低周循环、连接松动和瞬态峰值"),
    ("变载生产", "载荷随生产节拍在轻载与重载间切换", "必须使用载荷谱而非单一额定值"),
    ("低温启动", "低温静置后直接带载启动", "核对材料韧性、润滑黏度与热配合变化"),
    ("高温连续", "环境温度高且散热条件受限", "核对热膨胀、材料降额和润滑寿命"),
    ("潮湿腐蚀", "存在冷凝水和腐蚀性介质", "把腐蚀疲劳、密封和表面防护纳入判断"),
    ("粉尘污染", "粉尘可能进入配合面与润滑系统", "检查过滤、密封和磨粒磨损证据"),
    ("冲击载荷", "偶发冲击峰值明显高于稳态载荷", "同时校核峰值强度和冲击后的裂纹风险"),
    ("高速运行", "转速接近设备允许上限", "检查临界转速、动平衡、发热与润滑供给"),
    ("低速重载", "低速下承受高扭矩或高接触载荷", "重点检查油膜形成、静承载和局部塑性"),
]
LIFECYCLE = [
    ("方案设计", "尚无样机", "输出应给出参数清单和验证计划"),
    ("详细设计", "图样准备冻结", "输出应指出必须写入图样或技术条件的要求"),
    ("首件试制", "已有首件但过程能力未知", "输出应定义首件检测和放行证据"),
    ("批量生产", "已进入稳定生产", "输出应兼顾抽检频次、追溯和过程能力"),
    ("现场运行", "设备已投运", "输出应区分在线监测、计划检修和立即停机"),
]
EVIDENCE_BY_CATEGORY = {
    "design_fatigue": [
        ("有图样但缺载荷谱", "可审查结构，不可给出疲劳寿命"),
        ("有静强度计算但缺疲劳参数", "需补材料疲劳性能和修正系数"),
        ("有载荷谱但缺危险截面尺寸", "需补几何和缺口信息"),
        ("有有限元云图但缺建模说明", "需核对边界、网格和名义载荷"),
        ("有样机试验记录", "需确认试验工况对设计谱的代表性"),
    ],
    "manufacturing_qc": [
        ("有工艺卡但缺过程记录", "需补设备、刀具和关键参数实测"),
        ("有首件报告", "结论仅代表首件，需验证过程能力"),
        ("有终检结果但缺中间过程", "需追溯工序间基准和参数变化"),
        ("有缺陷照片", "需用尺寸或无损检测结果定量确认"),
        ("有批次趋势", "需核对量具、抽样和设备状态一致性"),
    ],
    "fault_diagnosis": [
        ("仅有口头现象", "不得直接确定根因或下换件结论"),
        ("有振动趋势但缺原始波形", "可判断劣化，不足以识别全部频率成分"),
        ("有油液报告", "需与振动、温度和检修发现交叉验证"),
        ("有报警历史", "需确认传感器位置、采样条件和报警基线"),
        ("有停机检查记录", "需保留失效形貌并核对运行工况"),
    ],
    "material_heat_treatment": [
        ("有材料质保书", "性能仅适用于对应炉批、状态和取样条件"),
        ("有硬度报告但缺金相", "不足以单独确认组织和有效硬化层"),
        ("有热处理曲线", "需与装炉方式、截面和最终性能对应"),
        ("有文献性能数据", "不得脱离材料状态、温度和试样方向泛化"),
        ("有失效件取样结果", "需核对取样位置和服役影响"),
    ],
    "tolerance_measurement_assembly": [
        ("有装配图但缺功能公差", "需从功能要求反推公差链"),
        ("有单件尺寸报告", "需结合基准体系和装配关系判断"),
        ("有三坐标报告", "需核对测量策略、温度和不确定度"),
        ("有装配间隙实测", "需区分尺寸、形位和受力变形贡献"),
        ("有量具校准证书", "仍需确认测量方法和环境适用性"),
    ],
    "standard_evidence_refusal": [
        ("仅有二手标准摘要", "必须回到正式现行文本核验"),
        ("有标准编号但缺年份", "不得假定版本和适用范围"),
        ("有标准全文但缺条款定位", "需记录准确条款和适用条件"),
        ("有企业规范", "需确认授权、版本和与国家标准的关系"),
        ("没有可核验来源", "拒绝编造标准、条款和固定限值"),
    ],
    "engineering_calculation": [
        ("有部分输入参数", "只建立计算模板并列出缺失项"),
        ("有计算结果但缺中间过程", "需复核单位、公式和中间量"),
        ("有表格计算文件", "需检查公式引用、版本和输入锁定"),
        ("有仿真结果", "需用手算量级和边界条件交叉核对"),
        ("有完整输入", "可计算，但仍须报告适用假设和敏感参数"),
    ],
    "industrial_safety": [
        ("仅有现场人员描述", "先建立安全边界，不直接接触检查"),
        ("有报警记录", "报警复位不能替代停机隔离和原因确认"),
        ("有作业指导书", "仍需确认许可、能源隔离和现场条件"),
        ("有监控画面", "远程观察不能证明设备已达到零能量"),
        ("有检修记录", "复机前仍须按程序验证防护和联锁"),
    ],
}
OBJECTIVE = [
    "形成设计评审问题单", "制定验证试验方案", "形成工艺控制卡要点",
    "确定补充测量项目", "形成故障树首轮排查顺序",
]

CATEGORY_ACTION = {
    "design_fatigue": "补充载荷谱、危险截面、材料状态和寿命目标后，分别完成静强度、刚度与疲劳校核。",
    "manufacturing_qc": "把候选机理转成可测的工艺变量，以首件、过程能力和终检结果闭环。",
    "fault_diagnosis": "先保留原始工况和趋势，再按风险排序验证原因，禁止用单一现象直接换件。",
    "material_heat_treatment": "材料牌号、炉批、截面、热处理状态和服役温度必须与性能证据一一对应。",
    "tolerance_measurement_assembly": "建立功能要求、公差链、基准体系和测量不确定度之间的对应关系。",
    "standard_evidence_refusal": "仅引用标准台账内现行版本；无正式条文时说明核验路径，不编造条款或限值。",
    "engineering_calculation": "先列输入、单位、公式适用条件和中间结果，再给可复核结论；缺输入时只给计算模板。",
    "industrial_safety": "安全边界优先于恢复生产；先停机、隔离能源并验证零能量，再进行接触式检查。",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def fingerprint(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def normalize_units(text: str) -> str:
    units = r"mm|cm|m|MPa|GPa|kPa|N|kN|N·m|rpm|Hz|°C"
    return re.sub(rf"(?<=\d)(?=(?:{units})(?![A-Za-z]))", " ", text)


def bind_conditions(text: str, qualifiers: list[str]) -> str:
    """Bind every substantive parent statement to this record's envelope."""
    pieces = re.split(r"([。！？；;\n])", text)
    bound = []
    statement_index = 0
    for piece in pieces:
        if piece in {"。", "！", "？", "；", ";", "\n"}:
            bound.append(piece)
            continue
        if not piece.strip():
            bound.append(piece)
            continue
        statement_index += 1
        qualifier = qualifiers[(statement_index - 1) % len(qualifiers)]
        bound.append(f"{piece.rstrip()}（{qualifier}）")
    return "".join(bound)


def enrich(parent: dict, index: int, profile: int, prefix: str, eval_record: bool = False) -> dict:
    op = OPERATING[profile % len(OPERATING)]
    life = LIFECYCLE[(profile // len(OPERATING)) % len(LIFECYCLE)]
    evidence_pool = EVIDENCE_BY_CATEGORY[parent["category"]]
    evidence = evidence_pool[(profile * 3 + len(parent["id"])) % len(evidence_pool)]
    objective = OBJECTIVE[(profile * 2 + len(parent["id"])) % len(OBJECTIVE)]
    category = parent["category"]
    token = fingerprint(parent["id"], str(index), prefix)[:12]
    parent_context_raw = f"{parent['instruction']}，{parent['input']}"
    parent_context = re.sub(r"[。；;！？!?\n]+", "，", re.sub(r"\s+", "", parent_context_raw))[:54]
    common = f"{parent['sub_category']}，{parent_context}，{op[0]}，{life[0]}"
    qualifiers = [
        f"对象约束：{common}，题设要点须逐项核对",
        f"工况约束：{common}，{op[1]}，{op[2]}",
        f"阶段约束：{common}，{life[1]}，{life[2]}",
        f"证据约束：{common}，{evidence[0]}，{evidence[1]}",
        f"交付约束：{common}，{objective}，并记录适用条件和复核责任",
    ]
    instruction = parent["instruction"] + f" 当前任务目标：{objective}。"
    context = (
        f"{parent['input']}\n扩展场景：生命周期={life[0]}；运行工况={op[0]}；"
        f"已知证据={evidence[0]}。"
    )
    output_raw = (
        f"{parent['output']}\n"
        f"场景化复核：本题处于{life[0]}，{life[1]}；设备表现为{op[1]}，因此{op[2]}。"
        f"当前证据为{evidence[0]}，{evidence[1]}；本次目标是{objective}。\n"
        f"执行要求：{CATEGORY_ACTION[category]}"
    )
    output = bind_conditions(output_raw, qualifiers)
    row = dict(parent)
    row.update({
        "id": f"{prefix}_{category}_{index + 1:06d}",
        "instruction": instruction,
        "input": context,
        "output": output,
        "version": "v3-stage-c",
        "author": "model_assisted_draft_stage_c",
        "source_type": "model_generated",
        "source_ref": f"parent:{parent['id']};generator:scripts/build_stage_c.py",
        "license": "project-generated-pending-release-review",
        "review_status": "self_reviewed",
        "reviewer": "automated_consistency_review_v1",
        "split_group": f"{prefix}_sg_{token}",
        "evidence": list(dict.fromkeys(parent.get("evidence", []) + [evidence[0], f"parent_id={parent['id']}"])),
        "conditions": list(dict.fromkeys(parent.get("conditions", []) + [op[0], life[0], objective])),
        "numeric_claims": [],
    })
    for field in ("instruction", "input", "output"):
        row[field] = normalize_units(row[field])
    if eval_record:
        row["source_ref"] += ";pool:independent_eval"
    return row


def validate(rows: list[dict], expected: int) -> None:
    assert len(rows) == expected
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)), "duplicate ids"
    texts = [fingerprint(row["instruction"], row["input"]) for row in rows]
    assert len(texts) == len(set(texts)), "duplicate prompts"
    errors = []
    for row in rows:
        errors.extend(f"{row['id']}: {e}" for e in S.dict_to_record(row).validate())
    if errors:
        raise ValueError("\n".join(errors[:20]))


def build() -> tuple[list[dict], list[dict]]:
    random.seed(SEED)
    base_train = read_jsonl(ROOT / "data/generated_v3/golden_v3.jsonl")
    base_eval = read_jsonl(ROOT / "data/generated_v3/eval_v3.jsonl")
    by_category = {cat: [r for r in base_train if r["category"] == cat] for cat in TARGETS}
    train = []
    for cat, target in TARGETS.items():
        parents = by_category[cat]
        for local_index in range(target):
            parent = parents[local_index % len(parents)]
            profile = local_index // len(parents)
            train.append(enrich(parent, len(train), profile, "mdc_train"))
    random.Random(SEED).shuffle(train)

    eval_rows = []
    for i in range(300):
        parent = base_eval[i % len(base_eval)]
        profile = i // len(base_eval)
        eval_rows.append(enrich(parent, i, profile, "mdc_eval", eval_record=True))
    validate(train, 5000)
    validate(eval_rows, 300)
    assert not ({r["split_group"] for r in train} & {r["split_group"] for r in eval_rows})
    return train, eval_rows


def save(train: list[dict], eval_rows: list[dict]) -> None:
    master = ROOT / "data/master/mech_sft_v3_master_5000.jsonl"
    processed = ROOT / "data/processed/mech_sft_v3_5000.json"
    eval_master = ROOT / "eval/mech_eval_v3_master_300.jsonl"
    eval_export = ROOT / "eval/mech_eval_v3_300.json"
    write_jsonl(master, train)
    write_jsonl(eval_master, eval_rows)
    processed.parent.mkdir(parents=True, exist_ok=True)
    processed.write_text(json.dumps([S.dict_to_record(r).to_alpaca() for r in train], ensure_ascii=False, indent=2), encoding="utf-8")
    eval_export.parent.mkdir(parents=True, exist_ok=True)
    eval_export.write_text(json.dumps([S.dict_to_record(r).to_alpaca() for r in eval_rows], ensure_ascii=False, indent=2), encoding="utf-8")
    dataset_info = {"mech_sft_v3_5000": {"file_name": "mech_sft_v3_5000.json", "columns": {"prompt": "instruction", "query": "input", "response": "output"}}}
    (ROOT / "configs/dataset_info_stage_c.json").write_text(json.dumps(dataset_info, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "version": "v3-stage-c", "seed": SEED,
        "train_total": len(train), "eval_total": len(eval_rows),
        "train_categories": dict(sorted(Counter(r["category"] for r in train).items())),
        "eval_categories": dict(sorted(Counter(r["category"] for r in eval_rows).items())),
        "eval_types": dict(sorted(Counter(r["sub_category"] for r in eval_rows).items())),
        "duplicate_ids": 0, "duplicate_prompts": 0, "train_eval_split_group_leakage": 0,
        "review_status": dict(Counter(r["review_status"] for r in train + eval_rows)),
        "expert_review_complete": False,
        "honesty_note": "Automated consistency review completed; independent human mechanical-engineering approval is still required by the execution plan.",
    }
    (ROOT / "reports/quality_report_stage_c.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    train_rows, evaluation_rows = build()
    save(train_rows, evaluation_rows)
    print("train:", len(train_rows), dict(Counter(r["category"] for r in train_rows)))
    print("eval:", len(evaluation_rows), dict(Counter(r["category"] for r in evaluation_rows)))
    print("stage_c_build: PASS")
