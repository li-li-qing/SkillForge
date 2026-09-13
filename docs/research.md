# 第一版取材与技术核验

检查日期：2026-09-12。正文为本项目重新组织的中文指导；本版没有复制第三方技能文件、脚本或大段原文。下表区分方法借鉴、候选材料与已核验机制，不以星数作为正确性证据。

## GitHub 来源快照

| 来源与固定版本 | 本次采纳 | 本次舍弃或限定 | 许可核查 |
|---|---|---|---|
| [OpenAI skill-creator](https://github.com/openai/skills/blob/49f948faa9258a0c61caceaf225e179651397431/skills/.system/skill-creator/SKILL.md) | 短入口、条件引用、按任务补充资源 | 宿主 UI 元数据与专属安装命令不进入通用正文 | 对应目录 `LICENSE.txt`：Apache-2.0 |
| [Anthropic skill-creator](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/skills/skill-creator/SKILL.md) | 同输入有/无新技能对比，检查实际输出 | 不强制依赖其评测工具链；单次冒烟不写成统计改善 | 对应目录 `LICENSE.txt`：Apache-2.0 |
| [Superpowers systematic-debugging](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging/SKILL.md) | 复现、证据链、对照正常路径、最小假设实验 | 排障深度按问题调整；不采用固定补丁次数作为通用停工或重构阈值 | 仓库：MIT |
| [游戏开发蓝图候选技能](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/b105e1cf617adf0b68ed98790a716bbb60993179/skills/unreal/unreal-blueprints/SKILL.md) | 按图表类型、通信方式和数据职责组织 | 其 UE 5.8 目标不能代替项目版本；“Construction Script 不在游戏中运行”的绝对说法不采用 | 仓库：Apache-2.0 |
| [Anthropic frontend-design](https://github.com/anthropics/skills/blob/34040c9c568585f6929bedeaad110ad08f079624/skills/frontend-design/SKILL.md) | 根据任务、受众和真实内容确定设计方向 | 网站首屏、特定审美偏好不推广到 HUD 或 MFC 工作台 | 对应目录 `LICENSE.txt`：Apache-2.0 |

上述提交通过公开 GitHub API 获取。许可信息按目录文件或仓库元数据核对；未来若直接复制、改编并分发具体文件，需同时保留其适用许可与声明。本库没有替原始本机资料重新授权。

## 标准与可移植性

采用 [Agent Skills 规范](https://agentskills.io/specification) 的目录和 `name`/`description` 头部。名称前缀减少与既有技能撞名；相关内容在需要时读取。宿主的自动发现不属于本库实现，单独复制测试也不等于多个 Agent 的实测认证。

本库 v1 选择只含 `name` 与 `description` 的最小头部；描述是一行 JSON 风格双引号字符串，也是有效的 YAML 字符串。名称使用无歧义 plain 标量或 JSON 风格双引号字符串；数字开头及 YAML 保留标量必须加引号，避免名称被宿主解释成数值、布尔或空值。校验器明确只支持这个写作子集，不冒充通用 YAML 解析器。

## 本机项目资料的取舍

本次读取了原有 LGF 的 UMG/构建笔记、Replicated Suite 的 API 能力与刷新链约束，以及 Advanced UI 的 HUD/工作台/实时布局规则。这些目录在取材时由本机 Git exclude 排除，未作为新技能依赖；完成第一版后已按用户要求删除，并移除相应的本机排除条目。

| 原始记录 | 核验和收录结果 |
|---|---|
| LGF：“Hidden 仍可点击” | 错误；本机 UE 5.7.4 的枚举注释明确不可命中。新参考记录修正后的条件 |
| LGF：“BindWidget 只找直接子控件” | 对同一 WidgetTree 的普通 Panel 嵌套不成立；初始化遍历 WidgetTree。独立嵌套 UserWidget 的内部树是另一边界，不能混为一谈 |
| LGF：“Canvas Offsets 总是位置与宽高” | 已核对布局源码：不作为通用规则；拉伸轴的 Right/Bottom 作为远侧边距，非拉伸轴才按尺寸参与布局，还需考虑 AutoSize |
| LGF：固定构建路径、DebugGame、Listen Server 约束 | 留作项目背景，不搬入 UE 通用正文 |
| Replicated Suite：未知 API 与真实空数据应分开 | 收录为诊断/显示方法；当前 RU 客户端可用 API、具体服务名和性能没有运行验证 |
| Advanced UI：实时数值不应打乱布局与用户选择 | 收录为目标和检查方法；具体布局效果尚需目标 UI 的实际验证 |

原始材料没有作为本仓库的已跟踪版本分发，以下用取材时的 SHA-256 记录内容指纹。表中的历史相对路径仅用于溯源，原文件现已删除，不是可访问链接或新技能运行时依赖；指纹本身不能恢复原文件。

| 材料路径 | SHA-256 | 主要使用位置 |
|---|---|---|
| `lgf-ue5-devkit/SKILL.md` | `C54E5E1CB9941CF4C6C2CA2370979AAA0118176CCC810790E7BFD1F9A80E5188` | C++ 所有权/生命周期与项目边界 |
| `lgf-ue5-devkit/references/project/umg-pitfalls.md` | `4A427789C0AE9FA203970D8F38562D66CF6DC4E2A5D726EF0AD2979FE8E13002` | 排障、蓝图、UI 的旧规则反例 |
| `lgf-ue5-devkit/references/project/build-debug.md` | `7446B1A248DA46DF9E0B1A5BB022831823EAA1B6398AD82875F803CD041B9BF5` | 固定构建配置不得泛化的案例 |
| `replicated-suite-maintenance/SKILL.md` | `73655E8E8548824DBAA1CB80C5AD4E9FB2B42FB3102DF5DB52A61F77E97DE111` | 排障证据链、能力未知与空数据、UI 职责 |
| `Advanced_UI_Layout_Skill_v4/advanced-ui-layout/SKILL.md` | `D160DAA41DAB75F70DB42622CEE7F70AC107B34B57D0940CA9B55CD272EAEC05` | HUD/工作台分区、实时几何稳定 |
| `Advanced_UI_Layout_Skill_v4/advanced-ui-layout/PRO_TOOL_PATTERNS.md` | `0D4B66F18CBBE97E758E20B00E419B4467C3A661456F3B93ADEACA0BE30DF234` | 布局职责、错误定位链；去除强制完整停靠系统 |

## UE 证据账本

本机 `Engine/Build/Build.version`：UE **5.7.4**，Changelist **51494982**，分支 `++UE5+Release-5.7`。以下路径均相对引擎根目录，没有把引擎源码复制到仓库。

| 结论 | 已检查证据 | 检查层级 |
|---|---|---|
| Hidden 占位但不可命中；两种 HitTestInvisible 对子控件影响不同 | `Engine/Source/Runtime/UMG/Public/Components/SlateWrapperTypes.h`，`ESlateVisibility`；[Epic API 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/ESlateVisibility) | 本机 5.7.4 源码与读取时显示 5.8 的 API 页；未跑输入回归 |
| 普通容器嵌套不等于超出 WidgetTree | `Engine/Source/Runtime/UMG/Private/WidgetTree.cpp` 的 `ForEachWidget` / `ForWidgetAndChildren`，`WidgetBlueprintGeneratedClass.cpp` 的 `InitializeWidgetStatic` 遍历与属性赋值 | 本机源码；未创建示例资产 |
| Canvas Offsets 解释取决于轴上锚点和布局模式 | `Engine/Source/Runtime/Slate/Private/Widgets/Layout/SConstraintCanvas.cpp` 的水平/垂直拉伸分支，结合 `UMG/Private/Components/CanvasPanelSlot.cpp` 的 SetSize | 本机源码；未执行布局视觉检查 |
| 运行期生成 Actor 的构造路径不能等同“只在编辑器” | `Engine/Source/Runtime/Engine/Private/Actor.cpp` 的 `FinishSpawning` 调用 `ExecuteConstruction`；`ActorConstruction.cpp` 的用户构造逻辑 | 本机源码；未运行 PIE 或打包 |
| UObject 指针类型分别处理保活、观察、资源路径 | [Object Pointers，UE 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/object-pointers-in-unreal-engine?application_version=5.7) | 版本匹配官方资料；没有编译修复示例 |
| UMG 刷新方式应根据更新频率和实际成本选择 | [UMG Optimization，UE 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine?application_version=5.7) | 官方资料；没有性能测量 |

源码复核指纹（SHA-256）：

- `SlateWrapperTypes.h`：`AB4C66FA84A4C96C644ECF1ACCCBBA1CFD396053899153D58D61B20B83860BDA`
- `WidgetTree.cpp`：`1C9A3214CE84D0ADCF8EA7BDAF173B43A9FDA2D1668B5BCFED991F5B534D3200`

UE5 通用入口不宣称全部小版本一致；调用时仍检查目标版本、源码分支和任务条件。规范或来源更新后，先验证受影响的结论，再修改技能。

资料读取限制：本次网络工具未能打开带 5.7 参数的 `ESlateVisibility` 和 Actor Lifecycle 页面；相关 5.7 行为以实际读取的本机 5.7.4 源码为证据。Object Pointers 和 UMG Optimization 的 5.7 页面已读取。不要把链接中的版本参数当成已成功核验该版本的证明。
