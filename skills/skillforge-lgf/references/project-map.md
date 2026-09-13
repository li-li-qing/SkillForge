# 项目地图与能力发现

本页基于 2026-09-12 读取的 LGF 1.0.0 源码。当前描述目标为 UE 5.7、Beta；每次任务重新读取描述符及消费工程，不以本页数字判断未来版本。

## 文档各自回答什么

| 项目内入口 | 需要回答的问题 |
|---|---|
| `README.md` | 插件定位、类栈/模块、依赖方向及适用范围 |
| `LGameplayFramework_API.md` | 类型、函数、返回值、Category、蓝图元数据与复制合同 |
| `LGameplayFramework_Tutorial.md` | 创建顺序、配置、接线、最小闭环和验证 |
| `Docs/README.md` | 内部维护资料的现行导航 |
| `Docs/Current/IMPLEMENTATION_STATUS.md` | 指定输入快照的已实现/部分实现/未实现状态 |
| `Docs/Current/DOCUMENTATION_AUDIT.md` | 已改的文档偏差、保留的代码差异、当轮验证范围 |
| `Docs/Architecture/` | 网络与运行时、移动与动画的项目边界 |
| `Docs/Reference/SOURCE_INVENTORY.md` | 模块、依赖、源码、测试声明和资产的定位索引 |
| `Docs/Decisions/README.md` | 方案、历史文档和现行冻结规范的位置 |
| `LGameplayFramework_Backlog.md`、`重构文档/` | 需求与决策背景；不代表功能已实现或本任务获准实施 |

先搜相关章节和符号，再读局部内容。长 API 只命中名称还不够：重要返回值、失败路径、分端差异须阅读实现。旧文档引用已迁移路径时沿决策导航找当前入口，不重建一份历史副本。

## 模块簇：用于找入口，不代替 Build.cs

当前描述符为 53 个模块：32 Runtime、20 ClientOnly、1 Editor。以下省略共同的 `LGameplayFramework` 前缀；具体依赖与模块 Type 必须查当前描述符/Build.cs。

| 功能方向 | 优先定位的模块 |
|---|---|
| 基础协议、身份与类栈 | Core、FoundationCore、Identity、Foundation |
| 输入与本地 UI | FoundationUIInput、UIContracts、UINavigation、UIExtension、UI、UICommon |
| 前端、设置与提供器 | Frontend 及其 Platform/Settings/Save/Online/UICommon 适配，Settings、对应 Settings/Save UICommon |
| 交互、物品与交易 | Interaction、Inventory、StorageOwnership、Equipment、Quickbar、Crafting、Reward；其中已列出的 UI 适配为 InteractionUI、InventoryUI、EquipmentUI、QuickbarUI、CraftingUI |
| 对话与任务 | Dialogue、Quest、QuestDialogue、DialogueUI |
| 战斗、能力与 AI | Ability、Combat、AI、Faction、AbilityUI |
| 社交与在线 | Party、Team、Guild、Online |
| 水与载具 | Water、Vehicle、VehicleWater、VehicleChaos、VehicleMount |
| 世界 UI 与编辑器支持 | WorldUIRuntime、WorldUI、UIEditor |

UI 模块名只是索引；不能从名字推断加载端或随便补依赖。Foundation 当前聚合了较多玩法模块，接入 Full Foundation 会有实际装配成本；把文件拆开不会自动裁剪组件或依赖。

## 四种能力状态

- **已实现：** 找到声明、实现和调用/注册链。例如交互 Actor 的 K2 扩展、UINavigation 的每 LocalPlayer 路由、Quest 的请求结果缓存。
- **需项目配置或实现：** InputAction/MappingContext、物品/技能 Definition、AssetManager/Cook、具体门行为、动画资产、Pawn 移动后端。接口存在不代表成品已装配。
- **仍是方案：** 当前 WorldMap、部分 Holster/通用 Mover 桥等按现行状态和主题决策核对。WorldUI 不等于 WorldMap。
- **当前不支持：** 多 Peer 共同 Authority、Host Migration。原会话 Reconnect 不能替代主机迁移。

需要验证上述状态时按[取材依据](sources.md)定位，再读当前源码，不能只沿用本页。

## 技能与项目说明的关系

本技能负责选入口、守住契约、发现容易误判的情况，并引导完成任务。项目文档负责完整 API、具体资产配置、当前设计和进度。经验证的跨项目 UE 结论可回流通用技能；LGF 专属类型、返回语义和模块布局继续留在本项目技能中。
