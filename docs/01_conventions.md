# 01 命名 / 目录 / 日志规范

## 命名

- **阶段前缀**:所有阶段产物用 `R0`~`R7` 前缀(对应任务书第5节),如 `R1_env_check.sh`、`R4_musa_compat_matrix.md`。
- **文档编号**:`docs/` 内文件用两位数字前缀 `01_`~`06_`,保证阅读顺序。
- **报告**:`reports/<阶段>_<主题>_<日期>.md`,如 `reports/R2_checkpoint_compare_20260720.md`。
- **checkpoint**:`checkpoints/<模型>_<阶段>_<step>/`,如 `checkpoints/agenticqwen8b_grpo_smoke_step3/`。
- **时间戳**:统一 `YYYY-MM-DD`(日志可精确到 `YYYY-MM-DD HH:MM`)。

## 目录用途

| 目录 | 用途 | 是否入库 |
|---|---|---|
| `docs/` | 规范文档(R0) | ✅ |
| `env/` | R1 环境验收脚本与输出 | ✅(脚本+摘要,原始大输出可摘要) |
| `models/` | R2 checkpoint 登记(commit/哈希/路径) | ✅(登记),❌(权重文件) |
| `data/` | R3 数据校验脚本与质量报告 | ✅(脚本+报告),❌(原始数据) |
| `eval/` | R2/R6 评测题集、评分器、指标 | ✅(题集+评分器+指标),❌(轨迹大文件) |
| `musa_compat/` | R4 兼容性测试脚本与矩阵 | ✅ |
| `training/` | R5/R6 GRPO 配置与脚本 | ✅ |
| `reports/` | 各阶段验收与结题报告 | ✅ |
| `checkpoints/` `logs/` | 权重与日志 | ❌(.gitignore) |

## 日志规范

- 每次执行命令前 `date` 打时间戳;关键命令 `| tee logs/<阶段>_<动作>_<日期>.log`。
- 日志含:命令、退出码、关键输出摘要、错误全文(不截断)、显存/耗时。
- 验收输出保存为 `reports/<阶段>_acceptance_<日期>.md`,带时间戳,只读复核不改原资产。

## 资产隔离(R0 铁律)

- 本项目路径、容器、挂载与原 LightMech / mechqa-qwen-sft 完全分开。
- 不读取、不引用、不覆盖原项目数据与代码;如需引用论文/公开资料,在 `02_source_registry.md` 登记独立来源。
- 旧仓库(mechqa-qwen-lora)的 git 历史保留(可 checkout 恢复),但 main 内容已切换为本项目。
