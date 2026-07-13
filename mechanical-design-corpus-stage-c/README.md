# Mechanical Design Corpus Stage C

面向 Qwen2.5-7B-Instruct LoRA/SFT 的机械设计专家语料工程。该目录是独立于 `mech-dataset-project` 的阶段 C 交付，保留阶段 A 作为历史基线。

## 一键构建

```bash
python scripts/build_stage_c.py
python scripts/review_stage_c.py
python scripts/prepare_model_comparison.py
```

主要产物：

- `data/master/mech_sft_v3_master_5000.jsonl`
- `data/processed/mech_sft_v3_5000.json`
- `eval/mech_eval_v3_master_300.jsonl`
- `eval/mech_eval_v3_300.json`
- `reports/quality_report_stage_c.json`
- `configs/qwen25_7b_mech_lora_sft_v3_5000.yaml`

## 配比

设计与疲劳 1200、制造质量 900、故障诊断 900、材料热处理 700、公差测量装配 500、标准证据拒答 400、工程计算 300、工业安全 100，总计 5000。

## 责任边界

本交付完成模型自审与自动数据工程验收，不冒充真人机械工程师审核。正式训练和产品使用前必须执行 `docs/STAGE_C_ACCEPTANCE.md` 中的人工复核、单卡训练、三模型盲评及准入流程。
