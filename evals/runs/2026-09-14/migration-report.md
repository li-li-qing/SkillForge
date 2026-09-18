# 旧 Skills 迁移与 LGame 经验收录

日期：2026-09-14。范围为 SkillForge 技能库与用户指定的旧资料目录；未修改 LGame 源码/资产、已安装技能、宿主设置或个人记忆，未创建提交。开始时 SkillForge Git 工作树干净。

## 迁移结果

保留六个正式技能入口，新增八份按需参考；旧目录 91 个文件逐项登记，其中 25 个后续文件与先前内容完全相同。不是将旧目录整包复制进正式技能，也不是只根据文件名删除。

| 旧来源 | 处理 |
|---|---|
| lgf-ue5-devkit | GASP/Mover、Root、武器生命周期与资产知识重新提炼进 LGF/蓝图/C++/排障；原只读工作区工具与 10 项回归迁移 |
| 三个 _skill_backup 技能 | 内容相同项合并；旧版入口与宿主名称退役，主题经验随对应新参考保留 |
| replicated-suite-maintenance | 复用现有 ArcheRage 丰富资料；补数据/代码回滚、容量、降级和发布边界，不覆盖其 2026-09-13 增量 |
| Advanced_UI_Layout_Skill_v4 | 复用 UI 布局/交互参考，补诊断定位、图层/Inspector、批量操作与恢复；不把未经本轮复核的推荐仓库清单当技术规则 |
| 重复校验脚本、旧名称/旧禁令断言 | 不迁移；沿用 SkillForge 校验与行为案例。旧资料全文在恢复备份中保留，不作为正式技能依赖 |

逐文件来源、SHA-256、重复对应与目标见 [migration-inventory.json](migration-inventory.json)。新库已替代旧入口，但**物理清理未完成**：删除旧目录的命令被自动审批以 blocked by policy 拒绝，未执行删除，也未用其他通道绕过。旧库 91 文件仍在，见 [deletion-result.json](deletion-result.json)。

## 收录的重点问题

- 真实 AnimBP/Chooser/BranchIn/MM 选择与实际播放；PSS/PSD 职责、过渡占用与方向输入。
- Root/Inplace 周期配对、独立骨骼验证、Phase、有效采样范围、Notify 身份与索引。
- 双剑全身姿势与持剑层重复叠加；不以风格 Tag 或粗移动状态冒充覆盖量。
- 官方 Socket/Preview、单一源挂点与外观手部补偿；握持与 Authority Trace 分开。
- 同步装备事务阻挡和解除重试；ServerOnly owner Montage、真正取消与任务清理。
- 原始资产解析误读、UMG 根修复、保留美术布局、NullRHI 与实际窗口几何。
- 版本基线、共享锁、长任务检查点、持久化负测、失败正文与分层验收。

本轮重读了相关 LGame 源码、项目规范与已有报告，并核对本地引擎的 GAS OnRep/PlayMontageAndWait、PoseSearch BranchIn/有效采样和 ScaleBox 默认实现。历史运行结果仍标为历史：本轮未重跑 UE、PIE、视觉或联网。源码/报告指纹见 [lesson-source-hashes.json](lesson-source-hashes.json)。未解决的 Trace/人工逐击窗口/UI 可访问性问题没有被写成已完成方案。

## 验证及过程纠错

| 检查 | 实际结果 |
|---|---|
| 迁移前全库校验 | 15 项错误：头部不兼容、路径示例/脚本工作目录，以及文件名误判为宿主 API |
| 校验器缺陷红灯 | 可选元数据、verification-tools 文件名两例先失败；空 compatibility 反例亦先失败后修复 |
| 最终库校验 | 6 个技能、0 错误、6 个独立复制包通过；见 packages-final2.txt |
| 库校验器回归 | 31 项：30 通过、1 跳过（宿主不能创建符号链接）；见 validator-tests-final2.txt |
| 迁移工作区工具回归 | 10/10 通过，另真实只读清点 LGame；见 inspector-tests-final.txt、workspace-inspection-utf8.json |
| ArcheRage 自身结构 | passed；原四个工具保留 |
| ArcheRage 工具回归 | 38 项：35 通过、3 跳过（两项缺真实 Lua5.1，一项符号链接条件）；见 addon-tests-final.txt |
| 旧 eval 数据 | 12 份原用例文件中的所有既有案例对象原样保留；新增 9 个行为题、2 个触发题，不冒充全部已执行 |
| 官方 quick_validate | 5/6 通过；本机该脚本不接受 compatibility，保留完整失败输出，不改官方脚本骗绿 |

官方 quick_validate 的差异是已核实的规则范围差异：[Agent Skills 规范](https://agentskills.io/specification)将 compatibility 列为可选环境说明（1–500 字符），metadata 为字符串映射。本库保留 ArcheRage 既有字段，按该受限格式验证；不因此宣称任意宿主已兼容。证据见 [official-quick-validation.json](official-quick-validation.json)。

ArcheRage 首次工具回归还暴露默认 GBK 读取 UTF-8 的四处异常，以及将旧修订号固定为成功条件的断言。已明确文件编码、保留旧案例内容校验并去掉固定旧修订号要求；初次失败日志 addon-tests.txt 保留。首个汇总打印也遇到编码错误，随后改为原始字节留档；不能把首轮称为通过。

## 文本行为样本

两个独立新上下文分别读取迁移前/后技能，处理同样五个场景，不读取评分答案或实际游戏工程。原始答复见 [基线](baseline-response.md)与[更新后](updated-response.md)，逐项审阅见 [行为审阅](behavior-review.md)。

基线已有正确的权威/证据边界，不虚构“全部基线失败”。更新后补足重试唤醒、周期复算、EndTask/OnDestroy 等具体步骤。仅一组小样本，由本轮主作者审阅；更新后可选读取 Blueprint 参考，加载量并非完全受控，因此不作统计改善、独立终审或跨模型正确率声明。其余新题仅登记，未逐题运行。

## 备份、删除与恢复

修改前备份根：`D:/Project/Skiils/MigrationBackups/20260914_102325`。其中 `旧的Skiils/` 为全部 91 个旧文件，`SkillForge/` 为改前工作文件（不复制 .git），`SHA256.csv` 登记 190 个文件。删除前再核对旧源与备份逐文件 SHA 相同、目标参考存在，无新增漏项。

清理是用户已授权的范围，阻塞来自工具自动审批而非缺少用户意图。本轮保留旧目录及备份，不能声称迁移和删除全部完成。后续具备允许的删除通道时，仍需重新核验旧目录是否新增或变化；不能只凭本次清单删除未来内容。

恢复旧库时，将备份中的 `旧的Skiils` 复制回原父目录；若该目标已被重新创建，先比较并备份新内容，不能无条件覆盖。恢复 SkillForge 只按迁移清单恢复需要的改前文件，并谨慎处理本轮新增文件，不能覆盖后续用户修改。备份不属于技能发布内容，未删除。

本次没有自动安装、同步或替换任何 Agent 的技能目录；日常使用从库根 README 的六个入口选择，保留完整技能目录结构。
