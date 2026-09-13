# 从现有能力接入项目

## 先完成一个可观察闭环

确认宿主 `.uproject`、引擎关联、Target、插件依赖及项目已有类栈。取材时实际宿主名为 Game，Editor Target 为 GameEditor；这是该现场的事实，不是以后项目的固定命令。

从教程“快速开始”与相关模块 API 选择接入路线：

- Gameplay 采用现有 Full Foundation 类栈时，核对 GameMode、GameState、PlayerController、PlayerState、HUD 和 Character/Pawn 的实际基类及默认组件。
- Frontend 主菜单使用其独立类栈；不要为了一个菜单继承完整玩法 Controller 并带入全部交互/背包/战斗输入。
- 已有工程按需要接入模块时，先核对框架提供的装配点和依赖。不要直接删除默认子对象来“减负”，也不要在蓝图子类重复添加同职责组件。

项目仍需配置 GAS Globals、Enhanced Input、所选 UI Presenter、AssetManager 扫描和 Cook。沿当前教程中的具体配置项设置，并核对本项目已有值；缺哪项补哪项，不无差别覆盖配置或给所有资产设 AlwaysCook。

创建前先列出真实依赖顺序：资产/蓝图类型 → 其默认配置与引用 → 输入/入口 → 结果消费 → 验证。尚未创建的 Widget、InputAction、Definition 不作为“已经可选”的对象。

## 示例：用蓝图做门交互

以下是利用已有扩展点的方案骨架，门资产和门状态由消费项目定义，并非插件附带的现成内容。

1. 核对当前 `ALInteractableActorBase`。取材版本已默认创建 InteractionComponent 和 AccessPolicyComponent，并启用 Actor 复制。基类默认业务执行失败是“尚未实现具体行为”，不等于蓝图无法扩展。
2. 在项目创建其蓝图子类，配置门 Mesh、基础交互选项和需要的权限策略。若选项动态变化，核对并实现 `K2_BuildDynamicInteractionOptions`；该查询不能顺手修改 Gameplay 真值。
3. 通过 `K2_CanHandleInteractionAuthority` 检查钥匙、锁状态等业务前提；通过 `K2_HandleInteractionAuthority` 执行真实开门并设置业务结果。两者是带 Authority 边界的 BlueprintNativeEvent；以当前头文件的显示名、参数和类别搜索节点。
4. 先创建输入资产/配置，再接玩家拥有侧的 InteractionInput/InteractionAgent 与 Avatar Detector。客户端走现有 `RequestInteract`，不能假设自己拥有世界中的门 Actor 并直接在门上调用 Server RPC。
5. Authority 在通用验证和业务验证通过后改变项目定义的门状态。复制状态驱动远端表现；Host 本地观察者也需刷新。持久开关状态不只用瞬时 Multicast，保证后加入玩家能重建。
6. 提示 Widget 消费 Detector UIData，并按当前 `InteractionWidgetInitializer` 的契约初始化。提交状态只驱动等待/失败提示，最终开门以 Authority 结果和复制状态为准。

最小验证：可开、无钥匙/距离等拒绝、重复点击、Host、Remote Owner、非拥有观察者、后加入客户端。没有编辑器时明确列出待创建资产、节点连线与参数依据，不能报告蓝图已编译或已运行。

## 示例：背包或共享仓库界面

先确认 Inventory、StorageOwnership、玩家请求 Agent 与 UI 模块的现成入口。UI 查询并缓存 UIData/ViewData，按业务身份发起拿取/移动请求；具体节点以当前 API 为准，不从另一个背包项目照搬签名。

一次请求追踪：当前容器/物品与权限 → 拥有侧 Agent → Authority 重新解析并验证 → 库存变更 → FastArray/结果事件 → 当前 UI 实例。不要先改 UI 数量再把快照当真值写回；预测表现若有，必须可撤回并与最终结果关联。

共享可见性、保存业务 ID、请求幂等和 JIP 见[网络与状态](network-and-state.md)。页面/返回/焦点沿[UI 平台](ui-platform.md)，不另建第二个背包页面栈。

## 扩展点不够时

明确缺的是项目配置、已有事件实现、可复用接口还是完整新系统。先给出实际调用链与缺口，再在本轮授权范围内实现最小扩展；保持现有 Blueprint 节点、复制/存档和模块边界。学习、说明或技能维护任务不能自动成为插件重构任务。
