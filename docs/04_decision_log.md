# 04 决策记录(decision log)

> 倒序追加。每条:日期 / 决策 / 理由 / 影响。

## D-004 2026-07-15 · 仓库改名为 agenticqwen-musa-reproduction

- **决策**:GitHub 仓库由 `mechqa-qwen-lora` 改名为 `agenticqwen-musa-reproduction`(用户在 GitHub 网页手动操作;gh CLI 未安装)。
- **理由**:仓库名与项目内容匹配;旧 URL 自动重定向,不破坏既有链接。
- **影响**:改名后需更新本地 `git remote set-url`;改名前 push 仍走旧 URL(重定向可用)。

## D-003 2026-07-15 · 清空 main 保留 git 历史

- **决策**:删除 main 上全部旧内容(mech-qwen-sft-v1/v2、mech-dataset-project、项目文档),但**保留 git 历史**。
- **理由**:旧仓库有 5419 条数据 + 18 脚本 + 完整提交历史,保留历史可随时 `git checkout` 恢复,降不可逆性(用户选定)。
- **影响**:远程 main 内容切换为 AgenticQwen MUSA 复现工程;mechqa 资产在历史中可追溯。

## D-002 2026-07-15 · 与 LightMech / mechqa 资产完全隔离

- **决策**:本项目不复用、不引用、不覆盖原 mechqa-qwen-lora 的数据与代码。
- **理由**:任务书 4.1.1 明确要求;保证复现可审计、来源单一。
- **影响**:独立路径、独立来源登记;mechqa 的 5419 条机械问答数据不进入本项目(如未来需要,作为独立知识库,不混入训练)。

## D-001 2026-07-15 · 立项,采用 00_PROJECT_TASK_BOOK.md V1.0

- **决策**:按任务书执行 AgenticQwen MUSA 分级复现,R0-R7,严格 Go/No-Go。
- **理由**:回答两个问题——公开模型/数据是否产生方向性收益;公开训练栈能否在 MUSA 形成最小闭环。
- **影响**:项目成功 ≠ 必须复现论文分数;兼容失败 + 完整证据也是有效成果(任务书 §9)。

## 待决策

- R0:来源登记逐项冻结(02 待填)。
- R1 前:确认远程登录方式与容器权限。
- R4 前:确认是否需要上游 MUSA 补丁。
