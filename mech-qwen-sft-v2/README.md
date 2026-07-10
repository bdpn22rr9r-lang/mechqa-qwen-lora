# mech-qwen-sft-v2

这是 80 条机械工程 LoRA SFT 数据的第二版。

## 为什么修订

v1 已证明 Qwen2.5-7B-Instruct + LLaMA-Factory + MUSA 单卡 LoRA 训练链路可用，但首次留出问题回答出现了工程质量问题：模型倾向于给出未经题目、标准或计算支持的圆角半径、粗糙度、硬度等固定数值。

v2 的目标不是扩大数据量，而是先修正答案风格：

- 设计审查类答案增加边界说明。
- 明确要求缺少依据时不要编造固定数值。
- 训练模型优先给出风险点、校核路径、检测要求和信息边界。
- 保留 80 条训练、20 条独立评测的规模，方便和 v1 做公平对比。

## 文件

- `scripts/build_mech_dataset_v2.py`：远程生成脚本。
- `datasets/mech_sft_v2_80.json`：80 条训练集预览。
- `eval/mech_eval_v2_20.json`：20 条独立评测集预览。
- `configs/qwen25_7b_mech_lora_sft_v2_80.yaml`：单卡训练配置。

## 远程服务器单行命令

以下命令都在容器内执行，当前目录建议为 `/workspace/mech-qwen-sft`。

生成 v2 数据、注册 LLaMA-Factory 数据集、写入训练配置：

```bash
python /workspace/mech-qwen-sft/imports/mechqa-qwen-lora-main/mech-qwen-sft-v2/scripts/build_mech_dataset_v2.py
```

确认生成结果：

```bash
python -c "import json; p='/workspace/mech-qwen-sft/datasets/processed/mech_sft_v2_80.json'; data=json.load(open(p,encoding='utf-8')); print(len(data)); print(data[0]['instruction']); print(data[0]['output'][:300])"
```

启动单卡训练：

```bash
nohup env MUSA_VISIBLE_DEVICES=0 llamafactory-cli train /workspace/mech-qwen-sft/configs/qwen25_7b_mech_lora_sft_v2_80.yaml > /workspace/mech-qwen-sft/logs/mech_sft_v2_80.log 2>&1 &
```

查看训练进度：

```bash
tail -40 /workspace/mech-qwen-sft/logs/mech_sft_v2_80.log
```

检查适配器是否存在 NaN 或 Inf：

```bash
python -c "from safetensors.torch import load_file; import torch; p='/workspace/mech-qwen-sft/outputs/qwen25-7b-mech-lora-v2-80/adapter_model.safetensors'; s=load_file(p); bad=[(k,torch.isnan(v).sum().item(),torch.isinf(v).sum().item()) for k,v in s.items() if not torch.isfinite(v).all()]; print('tensor_count=',len(s)); print('bad_tensor_count=',len(bad)); print('bad_examples=',bad[:10])"
```

用 v2 LoRA 做同一条留出问题推理：

```bash
MUSA_VISIBLE_DEVICES=0 llamafactory-cli chat --model_name_or_path /workspace/mech-qwen-sft/models/Qwen2.5-7B-Instruct --adapter_name_or_path /workspace/mech-qwen-sft/outputs/qwen25-7b-mech-lora-v2-80 --template qwen --flash_attn disabled --infer_dtype bfloat16
```

输入评测问题：

```text
请给出专业、可执行且说明边界的机械工程回答。审查一根含横向销孔的调质轴。该轴承受交变弯矩，图纸未说明孔边圆角和表面完整性。
```

## 验收标准

v2 不是看 loss 是否下降，而是看回答是否减少危险幻觉。

通过条件：

- 覆盖净截面削弱、孔边应力集中、交变弯曲疲劳校核。
- 提到孔口倒圆或去毛刺、表面粗糙度或表面缺陷控制、热处理后检验或无损检测。
- 不直接编造具体圆角半径、粗糙度、硬度或安全系数。
- 明确具体参数要依据载荷谱、材料状态、图纸、标准和计算确定。

不通过条件：

- 再次给出无依据固定数值。
- 说法比基础模型更短、更武断。
- 忽略疲劳危险截面和销孔应力集中。
