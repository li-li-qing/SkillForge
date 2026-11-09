# SkillForge 全库定向审查与增强交付

本轮基于已交付IDA v3建立独立副本，保留14个技能、动态元数据路由及A/B/C和个人协作习惯；没有安装到用户电脑、推送仓库或覆盖旧交付。核实日期2026-11-07。用户提供约9小时可用窗口；本轮按已确认问题完成审查、修复和验证，没有为凑时间空转，也不宣称覆盖了所有技术断言。

## 主要结果

- 更新器：目标已改变但日志写失败时返回结构化incomplete及备份、已验证/不确定路径；旧未完成记录在already_current前阻断，新增只读inspect-pending。补跨平台设备路径拒绝。保留显式恢复与现有锁，不自动回滚或重试。
- 校验器：runtime assets Markdown也检查引用；显式symlink循环成为可读错误。真实库未发现assets既有断链，新增fixture覆盖的是门禁盲点。
- IDA：严格拒绝bool/float地址与游标，MCP JSON-RPC响应验证；samefile拒绝硬链接伪备份；JSON先partial再无覆盖发布，失败不留下看似完整正式文件。
- Lua：按Lua5.1实际loadfile规则识别shebang后的字节码，128MiB累计输入预算避免最多约7.8GiB缓存；未执行未知字节码。
- 经验库：promote/rollback已尝试写入后发生审计故障返回recovery_required、当前哈希或unknown，保持pending/recover合同。
- LGF：不把无效Plugins、缺Enabled或重复声明静默当禁用；仅工程Plugins搜索的缺失明确限定范围。
- MFC/UI/Qt：窗口关闭前后payload所有权、STA消息泵与重入、快照/订阅窗口和可访问性验收条件。
- UE：版本化Iris UObject合同、MCP代理与Editor可达性区分、并发依安装版本和冲突而定、Shipping runtime服务按实际启动监听判断、纯二进制任务路由边界。
- 方法：有选择地吸收官方/优质外部Skills的行为对照、弱断言检查、工具错误合同和有源码证据的信任边界；不新增同义技能、不照搬强制流程。

## 检查范围

| 技能或组件 | 本轮检查/修改重点 | 限制 |
|---|---|---|
| orchestrator | 入口/习惯/路由保护、索引与更新器、测试 | 核心路由文件逐字保持，未改变宿主实际加载 |
| engineering-preflight | 单写者条件、风险探针与信任边界 | 不强制全任务威胁建模 |
| experience-maintenance | 恢复可观测性、可选评测方法 | 离线故障注入，非断电试验 |
| debugging | 观测正对照、历史案例状态 | 未调试用户实际程序 |
| reverse-engineering | 只读样本探测与证据合同 | 原脚本无需修改，未新跑目标二进制 |
| ida-pro | 输入、RPC、备份、发布和故障回归 | fake-module离线测试，未运行IDA |
| cheat-engine | JNI线程归属/pending exception | 未启动CE或Java目标 |
| ue-cpp / ue-blueprint / lgf | 入口、54参考结构/主题扫描、重点全文与LGF脚本 | 大篇Graph/Quest等抽查，非逐行全部断言审计 |
| mfc / qt / ui-design | 生命周期、消息、快照/订阅、语义与放大验收 | 未运行Windows/Qt/辅助工具 |
| archerage-addon | 四脚本与回归、Lua输入界限 | 真实Lua与游戏未配置 |

## 验证结果

| 套件 | 总数 | 通过 | 跳过 |
|---|---:|---:|---:|
| 根库 | 94 | 92 | 2 |
| 动态索引 | 40 | 40 | 0 |
| ArcheRage | 40 | 38 | 2 |
| LGF | 16 | 16 | 0 |
| 经验库 | 30 | 26 | 4 |
| IDA离线合同 | 57 | 57 | 0 |
| 合计 | 277 | 269 | 8 |

全部命令退出0；具体跳过原因见日志，跳过不是通过。14技能及14独立副本引用/元数据检查0错误；28个Python文件ast.parse语法检查通过。当前索引13个候选有意排除orchestrator。四题旧新版独立计划输出均符合预期边界，不能宣称行为提升或真实执行通过。原始输出、红灯/绿灯和最终日志见[本轮证据](../../evals/runs/2026-11-07/overnight/)。

## 来源与采用

[外部Skills研究](external-skills-research.md)记录固定提交、目录级许可证、具体源码、维护证据、采用与拒绝项。另见[UE审查](ue-audit.md)、[桌面审查](desktop-audit.md)、[方法审查](methods-audit.md)、[逆向审查](reverse-audit.md)。这些分组报告保留发现时的历史状态，以上最终整包日志为验收依据。未复制第三方实现或安装第三方技能；参考页使用原创归纳并保留固定来源。第三方说明不等于IDA/UE官方API保证。

根脚本新增路径规则依据Microsoft [Naming Files](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)，assets检查与[Agent Skills规范](https://agentskills.io/specification)的资源组织一致；本轮读取日期2026-11-07。Windows保留名静态检查不等于Windows实机认证。

## 使用与剩余风险

交付是完整Skills目录ZIP，不是自动安装器或增量payload。解压到新的位置，对照变更清单及用户本地当前差异再接入Codex；本轮没有替用户安装、联网启动MCP或修改现有数据库。核心总入口保持不变，具体能力按动态元数据发现，专业技能仍可单独复制。

LGF消费者需注意：缺Enabled现在输出null；未找到项目插件的status为not_found_in_project，found布尔仍在但只指搜索范围。更新器CLI新增exit3表达不完整结果；经验库CLI新增exit3表达需恢复。调用方不能把所有非零返回当作零修改。

未验证：实际IDA GUI/idalib/Hex-Rays/MCP连接、UE构建/PIE/网络/Shipping、Windows COM/MFC/Qt、真实Lua与游戏、掉电和非协作写入竞争。硬链接发布依赖文件系统支持；不支持时安全失败并保留partial供调查。更新器不是多文件原子事务，手动reconciled是协调者声明，不是程序证明。没有把大型知识库的抽查宣称完整语义审计。
