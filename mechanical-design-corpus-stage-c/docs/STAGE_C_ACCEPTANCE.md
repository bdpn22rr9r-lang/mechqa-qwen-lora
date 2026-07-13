# 阶段 C 工程验收记录

## 已实现范围

- 5000 条主训练数据及 Alpaca 导出。
- 300 条独立主评测数据及 Alpaca 导出。
- 八类配比、schema、来源、标准、风险、证据和审核状态字段。
- 可复现构建、自动一致性审阅、去重、泄漏与格式验收。
- 单卡和 8 卡独立训练配置、适配器有限性检查脚本。
- 三模型同题评测规范与结果记录模板。

## 审核声明

本项目由模型完成数据起草和自动一致性审阅，`review_status=self_reviewed` 只表示通过自动规则，不表示机械工程师签字。依据任务书第 10 节，标准引用、固定数值、安全、高风险设备、材料性能及全部评测题仍须真人二级工程审核。未取得审核记录前，不得把数据描述为 `expert_approved`，不得用于产品安全决策。

## 训练与 8 卡结论

当前代码仓库不包含 MTT S5000、官方 MUSA 容器、Qwen 权重或 V2/V3 适配器，因此未在本机伪造训练日志和三模型评分。现阶段结论为：**数据工程交付完成，正式模型验收未完成，8 卡暂不准入**。远程单卡训练、权重有限性检查、300 题三模型盲评全部通过后，负责人方可改为准入。

## 远程执行顺序

1. 运行 `python scripts/build_stage_c.py` 并确认 `stage_c_build: PASS`。
2. 将 `data/processed/mech_sft_v3_5000.json` 复制到 LLaMA-Factory `data/`，合并 `configs/dataset_info_stage_c.json`。
3. 使用单卡配置训练，保留完整日志，不覆盖 V2 结果。
4. 运行 `python scripts/check_adapter_finite.py <adapter_model.safetensors>`。
5. 对基础模型、V2 LoRA、V3 LoRA运行同一套 300 题、相同推理参数的评测。
6. 填写 `reports/model_comparison_stage_c.md`；满足所有硬门槛后再运行 8 卡通信小测。
