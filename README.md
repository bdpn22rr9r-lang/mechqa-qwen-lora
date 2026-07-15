# AgenticQwen MUSA 开源复现项目

> 在 8×MTT S5000(摩尔线程 MUSA)服务器上,分级复现 AgenticQwen 的公开模型、公开数据流水线、工具交互评测和最小 GRPO 训练闭环。
>
> 版本 V1.0 · 立项 2026-07-15 · 平台 worker31005 / 8×MTT S5000 / MUSA

## 核心原则(铁律)

1. **可审计、可重复、不夸大。** 每个结论必须有命令、日志、checkpoint 和错误记录支撑。
2. **兼容性失败也是有效结论。** 不预设 GRPO 一定能在 MUSA 跑通;定位不到最小阻塞点并给出可复查证据,同样是成功。
3. **与原 LightMech / mechqa-qwen-lora 资产完全隔离。**(任务书 4.1.1)本仓库不复用、不覆盖原项目的数据与代码。
4. **MUSA-only。** 除任务书明确的条件范围,不切换到 H100/CUDA 或外部云 GPU。
5. **不静默改 SFT 冒充 GRPO。**(任务书 4.3)只有 R5 最小 GRPO 闭环通过,才允许表述"完成训练链路复现"。

复现等级与 Go/No-Go 见 [docs/05_reproduction_levels.md](docs/05_reproduction_levels.md);禁止表述见 [docs/06_forbidden_claims.md](docs/06_forbidden_claims.md)。

## 目录结构

```text
.
├── 00_PROJECT_TASK_BOOK.md      # 项目任务书(权威)
├── README.md                     # 本文件
├── docs/                         # R0 工程冻结文档
│   ├── 01_conventions.md         #   命名/目录/日志规范
│   ├── 02_source_registry.md     #   来源登记(论文/仓库/模型/数据/评测 commit+哈希)
│   ├── 03_risk_register.md       #   风险登记
│   ├── 04_decision_log.md        #   决策记录(倒序)
│   ├── 05_reproduction_levels.md #   复现等级 R0-R7 + Go/No-Go
│   └── 06_forbidden_claims.md    #   禁止表述(防夸大)
├── env/                          # R1 只读环境验收(GPU/驱动/容器/网络)
├── models/                       # R2 checkpoint 登记与对比(大文件不入库)
├── data/                         # R3 公开数据流水线(校验/质量/泄漏)
├── eval/                         # R2/R6 同协议评测题集与评分器
├── musa_compat/                  # R4 MUSA 兼容矩阵(verl/SGLang/Ray/FSDP/MCCL)
├── training/                     # R5/R6 GRPO 配置/脚本
├── reports/                      # 各阶段验收与结题报告
└── .gitignore                    # 忽略 checkpoint/大模型/原始数据/日志
```

`checkpoints/`、`logs/` 在 `.gitignore` 中,不入库(只记录路径与哈希)。

## 当前进度

- **R0 工程冻结(进行中)**:任务书、规范、来源/风险/决策/复现等级/禁止表述文档已建立。
- R1-R7:未开始,严格按 Go/No-Go 顺序推进。

## 快速开始

```bash
# R0: 通读任务书与 docs/ 全部规范,确认来源登记与禁止表述
# R1: 按 env/ 的验收清单做只读环境复核(不改原资产)
# R2-R7: 逐阶段执行,每阶段产出报告到 reports/,过 Go/No-Go 才进下一阶段
```

## 来源

论文、作者仓库、模型、数据、评测的具体 commit 与哈希见 [docs/02_source_registry.md](docs/02_source_registry.md)(R0 阶段逐项冻结填写)。

## 成功定义(任务书 §9)

满足以下**任一**且证据完整,均为有效成果:① MUSA 上完成公开 checkpoint 与数据流程的可重复复现;② MUSA 上完成最小 GRPO 闭环;③ 明确定位无法完成 GRPO 的最小兼容性阻塞点并给可复查证据。**只有第②项完成,才能表述为"MUSA 上完成 AgenticQwen 训练链路复现"。**
