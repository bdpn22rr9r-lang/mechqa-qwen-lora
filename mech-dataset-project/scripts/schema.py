"""主数据 schema: 字段定义、枚举、校验、IO、投影。

零依赖(Python 3.10+ 标准库)。支持两个版本:
  - v0.1-seed: 原始 schema(task_type/domain/subdomain/requires_tool/requires_rag/numeric_claims/split_group)
  - v3: V3 计划书 schema(category/sub_category/evidence/conditions/author)

两版共存: v0.1-seed 数据保留旧字段; V3 数据用新字段。validate 按 version 分级校验。
为兼容 pipeline 统计与防泄漏切分, V3 数据的 task_type/split_group 也填充(task_type=category)。
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import hashlib

# ---------- v0.1 枚举(保留) ----------
TASK_TYPES = {
    "structural_strength", "fatigue_failure", "info_insufficient",
    "material_heat_treatment", "engineering_calculation", "fea_interpretation",
    "fault_diagnosis", "basic_concept", "context_extraction", "tool_awareness",
    "design_review", "process_planning", "safety_boundary", "material_evidence",
}
DOMAINS = {
    "shaft", "gear", "bearing", "bolted_joint", "weldment",
    "spring_coupling", "beam_plate", "hydraulic_seal", "general",
}
RISK_TAGS = {
    "net_section_reduction", "stress_concentration", "fatigue", "static_strength",
    "stiffness_deflection", "buckling_stability", "wear_contact_fatigue",
    "vibration_resonance", "thermal_deformation", "surface_integrity",
    "heat_treatment", "manufacturing_process", "assembly_tolerance",
    "inspection_ndt", "corrosion", "fastener_loosening",
    "missing_information", "fabricated_value_risk",
    # V3 新增
    "unsupported_number", "standard_citation", "safety_critical",
}
REVIEW_STATUSES = {
    "model_generated", "seed_pending_review", "self_reviewed",
    "expert_approved", "rejected",
    "v3_pending_review", "approved",  # V3 计划书用 approved(仅真人审核后)
}
DIFFICULTIES = {"easy", "medium", "hard"}
SOURCE_TYPES = {
    "expert_constructed", "mechqa_converted", "model_generated",
    "literature_extract", "v1v2_migrated",
    "expert_authored",  # V3
}

# ---------- V3 枚举(计划书第5节8类) ----------
CATEGORIES_V3 = {
    "design_fatigue",              # 机械设计审查与疲劳强度
    "manufacturing_qc",            # 制造工艺与质量控制
    "fault_diagnosis",             # 设备故障诊断
    "material_heat_treatment",     # 材料与热处理
    "tolerance_measurement_assembly",  # 公差配合、测量与装配
    "standard_evidence_refusal",   # 标准核验、证据与拒绝编造
    "engineering_calculation",     # 工程计算与工具调用
    "industrial_safety",           # 工业安全与操作边界
}

# V3 8 类 -> 5000 条目标配比
V3_TARGETS = {
    "design_fatigue": 1200,
    "manufacturing_qc": 900,
    "fault_diagnosis": 900,
    "material_heat_treatment": 700,
    "tolerance_measurement_assembly": 500,
    "standard_evidence_refusal": 400,
    "engineering_calculation": 300,
    "industrial_safety": 100,
}


def is_v3(version: str) -> bool:
    return bool(version) and version.startswith("v3")


@dataclass
class MasterRecord:
    # 通用(两版共有)
    id: str
    instruction: str
    input: str
    output: str
    version: str = "v0.1-seed"
    # v0.1 字段
    task_type: str = ""
    domain: str = ""
    subdomain: str = ""
    difficulty: str = "medium"
    language: str = "zh"
    risk_tags: list = field(default_factory=list)
    numeric_claims: list = field(default_factory=list)
    requires_tool: bool = False
    requires_rag: bool = False
    split_group: str = ""
    # V3 新字段
    category: str = ""
    sub_category: str = ""
    evidence: list = field(default_factory=list)
    conditions: list = field(default_factory=list)
    author: str = ""
    # 共用元数据
    source_type: str = "expert_constructed"
    source_ref: str = ""
    license: str = "internal-approved"
    review_status: str = "seed_pending_review"
    reviewer: str = ""

    def validate(self) -> list:
        errs = []
        if not self.id:
            errs.append("id 为空")
        for f in ("instruction", "input", "output"):
            if not getattr(self, f) or not str(getattr(self, f)).strip():
                errs.append(f"{f} 为空")
        if self.difficulty not in DIFFICULTIES:
            errs.append(f"difficulty 非法: {self.difficulty}")
        if not isinstance(self.risk_tags, list):
            errs.append("risk_tags 非列表")
        else:
            for t in self.risk_tags:
                if t not in RISK_TAGS:
                    errs.append(f"risk_tag 非法: {t}")
        if self.source_type not in SOURCE_TYPES:
            errs.append(f"source_type 非法: {self.source_type}")
        if self.review_status not in REVIEW_STATUSES:
            errs.append(f"review_status 非法: {self.review_status}")

        if is_v3(self.version):
            # V3 必填
            if self.category not in CATEGORIES_V3:
                errs.append(f"V3 category 非法/缺失: {self.category}")
            if not self.sub_category:
                errs.append("V3 sub_category 缺失")
            if not isinstance(self.evidence, list):
                errs.append("V3 evidence 非列表")
            if not isinstance(self.conditions, list):
                errs.append("V3 conditions 非列表")
            if not self.author:
                errs.append("V3 author 缺失")
        else:
            # v0.1 必填
            if self.task_type not in TASK_TYPES:
                errs.append(f"task_type 非法: {self.task_type}")
            if self.domain not in DOMAINS:
                errs.append(f"domain 非法: {self.domain}")
            if not self.subdomain:
                errs.append("subdomain 缺失")
            if not isinstance(self.numeric_claims, list):
                errs.append("numeric_claims 非列表")
            if not isinstance(self.requires_tool, bool):
                errs.append("requires_tool 非布尔")
            if not isinstance(self.requires_rag, bool):
                errs.append("requires_rag 非布尔")
        return errs

    def to_alpaca(self) -> dict:
        return {"instruction": self.instruction, "input": self.input, "output": self.output}

    def text_fingerprint(self) -> str:
        key = (self.instruction.strip() + "\n" + self.input.strip()).lower()
        return hashlib.sha1(key.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)


# ---------- IO 工具 ----------
def load_jsonl(path) -> list:
    path = Path(path)
    out = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{i} JSON 解析失败: {e}") from e
    return out


def save_jsonl(records: list, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(obj, path, indent=2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=indent), encoding="utf-8")


def dict_to_record(d: dict) -> MasterRecord:
    """从 dict 构造 MasterRecord,忽略未知字段,缺失字段用默认值。"""
    valid = set(MasterRecord.__dataclass_fields__.keys())
    kwargs = {k: v for k, v in d.items() if k in valid}
    return MasterRecord(**kwargs)


if __name__ == "__main__":
    # V3 自检
    v3 = MasterRecord(
        id="design_fatigue_000001", version="v3",
        category="design_fatigue", sub_category="shaft_cross_hole_fatigue",
        difficulty="hard", language="zh",
        instruction="请识别风险并给出可执行的设计审查意见。",
        input="调质传动轴中部有横向销孔,承受交变弯曲。",
        output="关键风险是孔边应力集中与净截面削弱,交变载荷下需疲劳校核。",
        evidence=["横向孔削弱净截面", "孔边应力集中"],
        conditions=["载荷谱", "材料状态", "尺寸", "寿命目标"],
        risk_tags=["fatigue", "stress_concentration", "unsupported_number"],
        source_type="expert_authored", source_ref="", license="pending",
        review_status="v3_pending_review", author="claude",
    )
    print("v3 validate:", "PASS" if not v3.validate() else v3.validate())
    print("v3 alpaca keys:", list(v3.to_alpaca().keys()))
    # v0.1 自检(向后兼容)
    v01 = MasterRecord(
        id="shaft_cross_hole_000001", version="v0.1-seed",
        task_type="design_review", domain="shaft", subdomain="cross_hole",
        instruction="审查。", input="销孔轴。", output="需疲劳校核。",
    )
    print("v0.1 validate:", "PASS" if not v01.validate() else v01.validate())
