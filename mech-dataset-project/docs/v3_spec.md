# V3 执行规格(阶段 A)

> 权威来源:`MECH_QWEN_V3_EXECUTION_PLAN.md`(上游 model-training 项目)。本文件是 V3 阶段 A 在本仓库的落地规格。V3 比 v0.1-seed 更严格,直接针对 v0.1-seed/V2 暴露的问题(边界模板重复、核心风险覆盖不足、标准编号幻觉)。

## 1. 8 类配比(5000 目标 / 阶段A 200 按比例缩放)

| category | 5000 目标 | 阶段A(200) | 主要能力 |
|---|---:|---:|---|
| design_fatigue | 1200 | 48 | 轴/孔/键槽/轴肩/齿轮/连接/焊接/载荷路径/失效模式 |
| manufacturing_qc | 900 | 36 | 机加工/热处理/焊接/铸造/表面处理/检验控制点 |
| fault_diagnosis | 900 | 36 | 旋转机械/液压/气动/传动/振动/温升/润滑/证据闭环 |
| material_heat_treatment | 700 | 28 | 选材/组织性能/热处理状态/性能条件/材料证据(MechQA≤400) |
| tolerance_measurement_assembly | 500 | 20 | 尺寸链/基准/形位/公差/配合/装配测量 |
| standard_evidence_refusal | 400 | 16 | 标准适用性/来源核验/信息不足/禁止伪精确 |
| engineering_calculation | 300 | 12 | 疲劳/轴承寿命/螺栓/传动/单位换算 输入输出规范 |
| industrial_safety | 100 | 4 | 能源隔离/起吊/压力/旋转件/停机检查/安全升级 |
| **合计** | **5000** | **200** | |

## 2. V3 主数据字段(schema.py version=v3)

`id, category, sub_category, instruction, input, output, source_type, source_ref, license, evidence[], conditions[], risk_tags[], difficulty, author, reviewer, review_status, version`。为兼容 pipeline,同时填 `task_type=category` 与 `split_group`(防泄漏切分用)。

V3 新增字段含义:
- `evidence`:答案所依据的事实/来源摘要(数组),体现"有证据"。
- `conditions`:结论依赖的输入条件(载荷谱/材料状态/尺寸/寿命等,数组),体现"条件明确"。
- `author`:执行者编号;`reviewer`:审核者编号。
- `source_type` 用 `expert_authored`(V3)。

## 3. 答案规范要点(反 v0.1-seed 教训)

⚠️ **禁止重复边界模板**(V2 失败主因):
- **不得**在多条答案末尾复制完全相同的"边界说明"。v0.1-seed 的固定 `BOUNDARY` 文本是反面教材。
- 边界说明必须**因题而异**:针对该题缺的具体条件、涉及的具体数值类型说明,或多数题不写固定边界声明。

其他强制(计划书第7节):
- 不得用"经客户批准""与图纸一致"等空泛句代替工程判断。
- 没有来源/版本/适用范围时,不得引用标准编号;引用标准必须记录标准号、年份、名称、适用条款。
- 没有载荷/尺寸/材料/环境/寿命条件时,不得编造圆角/粗糙度/硬度/安全系数等数值。
- 不得把"可能原因"写成唯一故障结论;不得把相关性写成因果;不得把论文局部数据写成普适常数。

## 4. 评测集约束(阶段A 60 条;正式 300 条)

- 与训练集严格隔离:相同 DOI/设备故障案例/零件参数组合/模板变体不得跨集。
- ≥高风险题(标准编号/固定参数/安全操作/材料状态/疲劳寿命/信息不足)。
- ≥"应拒绝给固定数值"题。
- ≥"可依据证据给明确数值"题(防过度拒答)。
- (阶段A 60 条按 300 的 1/5 缩放下限:≥12 高风险 / ≥6 拒绝 / ≥6 可答。)

## 5. 校验项(V3 第9节,v0.1-seed 之外新增)

已有:v0.1 的 schema/empty/duplicates/near_duplicates/numeric/forbidden/units/leakage。
**V3 新增**(本阶段实现):
- `check_repeated_templates`:重复前缀/后缀/高频 n-gram(检测边界模板复制)。
- `check_vague_phrases`:"应按相关标准""需客户批准"等空泛表达频率。
- `check_standard_citations`:标准编号格式(GB/T xxx-YYYY 等)+ 标准核验台账关联。
- `check_text_anomalies`:中文乱码/异常控制字符/超长样本。

## 6. 与 v0.1-seed 的差异

| 维度 | v0.1-seed | V3 |
|---|---|---|
| 类别 | 10 类 task_type | 8 类 category |
| 字段 | task_type/domain/requires_tool/requires_rag/numeric_claims | category/sub_category/evidence/conditions/author |
| 边界 | 固定 BOUNDARY 模板(重复) | 因题而异,禁止重复 |
| 评测 | 简单 split | 专门构建,高风险/拒绝/可答下限 |
| 审核 | seed_pending_review | v3_pending_review(阶段A)/approved(二审后) |

两版数据共存于本仓库,以 `version` 字段区分;pipeline 按 version 分流。
