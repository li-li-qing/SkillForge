---
name: skillforge-ida-pro
description: "Use when executing authorized IDA Pro binary analysis, Hex-Rays decompilation, IDAPython automation, IDA MCP/RPC, native class recovery or Unreal Engine binary investigation. 用于 EXE/DLL/SO 静态分析、调用链、结构体、UE 反射与动态证据；普通源码开发、仅出现 exe 文件名、纯 CE 扫描或其他工具专属操作不触发。"
---
# IDA Pro 专业分析
从当前问题出发，以可复核的地址和字节证明结论。该技能可独立使用；可发现时复用通用逆向技能的文件身份/地址工具、UE C++ 的源码契约、排障技能的方法。它们不是安装前提，不重新启动协作等级选择。

## 前置检查
1. 明确样本与授权范围，保存原文件及 SHA-256。记录格式、处理器、位宽、端序、ABI、加载基址；EXE/DLL/SO 后缀不是架构证据。未知样本只在隔离环境动态运行，不上传二进制或 IDB。
2. 发现真实 IDA GUI/批处理/idalib、版本、Python、Hex-Rays 架构插件及授权。记录数据库路径、输入路径和 hash 是否一致，检查自动分析完成情况。没有 IDA 时仍可检查文件和脚本，但不得制造反编译结果。
3. MCP 读取当前 schema、实例和数据库身份；官方与社区适配器分别管理。未发现 MCP 不能假设已安装。见 [接入与权限](references/mcp-adapters.md)。
4. 默认只读；重命名、类型、结构体、注释、重新分析都算 IDB 修改。先记录具体地址、旧值、新值、理由和授权范围；重要修改需确认或明确授权流程。执行 Python 不是只读能力。仅改工作 IDB，不改原二进制。
5. 先低成本汇总，再按函数/范围深入。所有查询记录覆盖范围、分页、截断、耗时；大批量任务分块、可取消、可续接，缓存绑定 hash/IDA版本/数据库变更代次。

## 任务路由
| 用户目标 | 执行路径 | 按需资料 |
|---|---|---|
| 陌生 EXE/DLL/SO | 文件身份 → 加载核对 → imports/exports/strings → 关键函数 → 报告 | [工作流](references/workflows.md) |
| 地址、字符串、某个函数或调用链 | 边界/汇编 → xrefs → 双向调用 → 数据流 → 局部反编译 | [静态与反编译](references/static-and-decompiler.md) |
| IDA 脚本/批量导出 | 探测 API → 小范围试跑 → 有界批处理 → 完整性核验 | [API与示例](references/idapython-api.md) |
| C++ 类、结构体、虚表 | 构造/析构 → this → 偏移证据 → 候选布局 → 验证 | [类恢复](references/class-recovery.md) |
| UE4/UE5 程序 | 版本/构建 → UObject/反射 → 目标类 → RPC/复制/Blueprint | [UE 专项](references/unreal-engine.md) |
| 运行时行为 | 目标实例/模块 → 最小断点试验 → 寄存器/栈/内存 → 对照静态假设 | [动态验证](references/dynamic-debugging.md) |
| MCP/RPC 接入 | 适配器与依赖 → 身份探测 → 只读查询 → 权限与错误恢复 | [接入](references/mcp-adapters.md) |

详细 API、运行方式和十五项示例见 [IDAPython参考](references/idapython-api.md)。来源及版本核实见 [知识索引](references/sources.md)。

## 证据与交付门槛
使用 [报告模板](assets/analysis-report.md) 和 [变更台账](assets/change-log.json)。每项结论包含：目标/hash/架构/IDA版本/时间、函数地址与地址空间、名称及其来源、xrefs、相关结构体、关键指令或伪代码、判断依据、置信度、未决问题。无对应字段写 unknown 或不适用并说明原因，不填虚假数据。

置信度：已验证（直接证据）、高可信（多个独立证据）、推测（合理但待证）、未知。静态字节事实与运行时观测分开；伪代码不是原始 C++。调用图中间接调用/尾调用/内联的缺口必须保留。

完成时检查：问题是否回答、样本是否正确、关键推断是否回看指令、分页是否完整、修改是否读回、报告是否可从地址重现、局限是否明确。没有实际 IDA 执行就只能报告文档/语法/契约检查。
