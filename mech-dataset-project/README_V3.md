# V3 阶段 A 交付说明

> 权威来源:`MECH_QWEN_V3_EXECUTION_PLAN.md`。本文件说明 V3 阶段 A(数据规范 + 金样本 + 校验脚本)在本仓库的落地。V3 比 v0.1-seed 严格,直接修复了 v0.1-seed/V2 暴露的问题(边界模板重复、核心风险覆盖不足、标准编号幻觉)。

## 本次交付(V3 阶段 A)

| 项 | 内容 |
|---|---|
| **schema 升级** | `schema.py` 加 V3 字段(category/sub_category/evidence/conditions/author),按 version 分级校验,与 v0.1-seed 共存 |
| **金样本** | 120 条,8 类(design_fatigue 26 / manufacturing_qc 24 / fault_diagnosis 18 / material 12 / tolerance 15 / standard 12 / calc 9 / safety 4) |
| **评测集** | 48 条,严格隔离(高风险 24 / 拒绝给数值 12 / 可给数值 12,均达 V3 下限) |
| **切分** | train 105 / validation 15 / test 24 / challenge 24;**训练池/评测池 split_group 共享=0**(严格隔离) |
| **校验脚本(新增 4)** | check_repeated_templates(n-gram 模板)、check_vague_phrases、check_standard_citations、check_text_anomalies |
| **流水线** | `run_pipeline_v3.py`(golden→train/val,eval→test/challenge,导出,报告) |
| **规范文档** | `docs/v3_spec.md`(8 类配比 + V3 字段 + 禁止重复边界 + 评测约束) |

## 质量指标(V3 release)

| 指标 | 结果 |
|---|---|
| Schema 合法率 | 100%(全集) |
| id 重复 / 文本指纹重复 | 0 / 0 |
| 训练池-评测池泄漏 | 0(共享 split_group) |
| 无来源数值 / 禁止编造表述 | 0 / 0 |
| 文本异常(超长/控制字符/乱码) | 0 |
| 空泛表达 | 0 |
| review_status | 全 v3_pending_review(诚实,非 approved) |

## V3 对 v0.1-seed 的关键修复

1. **边界模板重复根治**:v0.1-seed 每条都复制固定 `BOUNDARY`(V2 失败主因);V3 边界说明由**(对象×工况)组合生成**,每条不同,无固定模板句。`check_repeated_templates` 检测跨样本高频 n-gram。
2. **8 类新配比**(替代 v0.1 的 10 类),补齐制造工艺/公差测量装配/工业安全等 v0.1 缺失类别。
3. **评测集专门构建**:不再从训练集随机 split,而是独立构建且含高风险/拒绝/可答下限。
4. **V3 元数据**:evidence/conditions/author 字段体现"有证据、条件明确"。

## 诚实声明

1. **数量 120 金 + 48 评测 ≈ 168 条**,低于 V3 阶段 A 目标 200+60。配比近似(每类按比例),正式版扩展到严格配比与 5000 条。
2. **review_status 全为 v3_pending_review**,未经真人机械工程师二级审核。V3 第10节要求标准引用/固定数值/安全/材料性能样本二级审核 100%,评测集二级审核 100%——**本批未完成,不得用于正式训练/产品**。
3. **标准引用缺具体年份**(GB/T 3480、GB/T 3098 未带年份):`check_standard_citations` 已标注风险;正式版须补具体年份并核验适用版本。本批未编造年份(诚实)。
4. **n-gram 检测**:manufacturing 类内部分通用正文句(非边界模板)仍跨条重复,V3 第9节要求"报告"(已实现),正式版进一步因题异。

## 与训练衔接

```bash
# 远程 mech-qwen-sft-official 容器:
LF=/workspace/mech-qwen-sft/third_party/LlamaFactory_MUSA
cp <本仓库>/mech-dataset-project/data/releases/v3/train_alpaca.json $LF/data/mech_sft_v3.json
# 合并 dataset_info.json 的 "mech_sft_v3" 条目
MUSA_LAUNCH_BLOCKING=1 MUSA_VISIBLE_DEVICES=0 \
  llamafactory-cli train <config>.yaml   # dataset: mech_sft_v3, bf16 + flash_attn:disabled
```

## 迭代到阶段 B/C

按 V3 第11节:
- **阶段 A**(本批)→ 负责人确认质量后进 B。
- **阶段 B**:扩到 1000 条 + 100 评测 + 单卡试训 + 基础模型对照。
- **阶段 C**:5000 条正式 V3 + 300 评测 + 三模型对照评测 + 8 卡准入结论。

每个阶段质量门槛(无 NaN/Inf、盲评优于基座、标准编号 100% 准确、无依据数值≤2%)未达则**回数据修订**,不扩大训练规模。

## 文件清单

- `scripts/schema.py`(V3 扩展)、`build_golden_v3.py`、`build_eval_v3.py`、`run_pipeline_v3.py`
- `scripts/check_repeated_templates.py`、`check_vague_phrases.py`、`check_standard_citations.py`、`check_text_anomalies.py`
- `data/generated_v3/golden_v3.jsonl`、`data/generated_v3/eval_v3.jsonl`
- `data/releases/v3/`(train/validation/test/challenge × master+alpaca + dataset_info)
- `reports/quality_report_v3.json`
- `docs/v3_spec.md`
