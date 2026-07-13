# MUSA 远程训练执行手册

以下命令均在现有 `mech-qwen-sft-official` 容器中执行，不删除镜像、不重建容器、不升级 Torch/MUSA/LLaMA-Factory。每次只复制并执行一行。

1. 进入项目目录：

```bash
cd /workspace/mech-qwen-sft
```

`cd` 表示切换目录，不会删除文件。

2. 把阶段 C 数据复制到 LLaMA-Factory：

```bash
cp /workspace/mech-qwen-sft/imports/mechqa-qwen-lora-main/mechanical-design-corpus-stage-c/data/processed/mech_sft_v3_5000.json /workspace/mech-qwen-sft/third_party/LlamaFactory_MUSA/data/mech_sft_v3_5000.json
```

`cp` 表示复制；源文件保留。若仓库解压目录不同，只调整第一个路径。

3. 合并数据注册项：不要覆盖已有 `dataset_info.json`，使用项目已有的 JSON 合并脚本或 Python 读取、增加 `mech_sft_v3_5000` 后再写回。

4. 复制单卡配置：

```bash
cp /workspace/mech-qwen-sft/imports/mechqa-qwen-lora-main/mechanical-design-corpus-stage-c/configs/qwen25_7b_mech_lora_sft_v3_5000.yaml /workspace/mech-qwen-sft/configs/qwen25_7b_mech_lora_sft_v3_5000.yaml
```

5. 启动单卡训练：

```bash
nohup env MUSA_LAUNCH_BLOCKING=1 MUSA_VISIBLE_DEVICES=0 llamafactory-cli train /workspace/mech-qwen-sft/configs/qwen25_7b_mech_lora_sft_v3_5000.yaml > /workspace/mech-qwen-sft/logs/mech_sft_v3_5000.log 2>&1 &
```

`nohup` 使训练在终端断开后继续；`MUSA_VISIBLE_DEVICES=0` 只使用第 0 张卡；`>` 把日志写入文件；末尾 `&` 让任务在后台运行。

6. 查看训练进度：

```bash
tail -50 /workspace/mech-qwen-sft/logs/mech_sft_v3_5000.log
```

7. 查看 GPU：

```bash
mthreads-gmi
```

8. 训练结束后检查 LoRA 权重：

```bash
python /workspace/mech-qwen-sft/imports/mechqa-qwen-lora-main/mechanical-design-corpus-stage-c/scripts/check_adapter_finite.py /workspace/mech-qwen-sft/outputs/qwen25-7b-mech-lora-v3-5000/adapter_model.safetensors
```

只有输出 `bad_tensor_count=0` 才能进入三模型评测。三模型评测全部达到硬门槛后，才允许使用独立 8 卡配置做通信和吞吐验证。
