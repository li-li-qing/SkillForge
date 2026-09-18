# 动画补充问题：基于技能参考的文字验证

本答复仅阅读指定技能及其参考，不读取 LGame 工程、evals 内容或旧回答。下述工程检查均为待执行方案；没有运行 UE、检查当前生成类或修改资产，因此不声称任何运行结果已通过。

## 1. 单一源 Socket 共用什么

该方案共用的是源 Socket 相对于父手骨的局部校准，不是源 Socket 的世界坐标。源骨架与 Runtime Retarget 后的可见骨架可能有不同手骨位置、骨长、姿态与组件变换。直接给可见剑赋源 Socket 世界 Transform，会让剑跟源骨架手的位置走，无法保证贴合重定向后的可见手。

按参考中的 UE FTransform 组合约定：

`VisibleWeaponWorld = ItemOffset * SourceSocketLocal * VisibleHandWorld`

- `SourceSocketLocal`：源 Socket 相对于其父手骨的变换。不是源 Mesh Component Space，也不是 World Space。
- `VisibleHandWorld`：当前可见 Mesh 上对应手骨的世界变换。
- `ItemOffset`：装备表示自身的额外局部校准，必须核对当前实现的语义与组合方向。

落地时以当前实现和旋转后的基向量验证乘法顺序，不能直接推广到其他数学库。手骨名称不同必须显式映射；缺映射应明确失败，不回退到根骨。Runtime Retarget 不会自动复制另一 Skeleton 上的 Socket。

这里存在两套用途不同的表示：可见武器服务外观握持，使用上述源局部校准加可见手骨；服务器的权威 Trace 表示仍跟随服务器源骨架，供命中计算。它们消费同一装备真值，不建立第二份装备状态。成对武器也可由多个表示部件组成，但仍共享一个库存身份和一次事务。

握持 Socket 与武器模型的 `trace_start/trace_end` 是不同内容。剑贴手不能证明隐藏 Trace Mesh 的端点存在、方向正确或实际能命中。换模型必须分别检查可见与权威模型、端点及窗口过滤。可见附件在姿势更新之后刷新，并检查隐藏动画源的可见性继承；局部复用仍可能需要外观手指校准，但不应为一个外观反复改公共源 Socket。

## 2. Coverage 为 1 仍不更新：先证明执行链

如果本次 BasePose 求值中的有效覆盖量确实为 1，合同要求静态持剑 Overlay 权重为零，这是正常抑制。调试器中某条曲线显示 1，并不证明活动节点本次读到了正确风格的曲线，也不证明姿势本帧发生了求值。

具体检查顺序：

1. 确认实际 Pawn、源 Mesh、源 AnimInstance、当前 AnimBP 生成类与活动节点，记录世界、帧号、风格快照和曲线名。不能只检查编辑器图或未使用示例类。
2. 检查自定义节点是否实现正确的 `PreUpdate`，以及 `HasPreUpdate` 是否使节点满足预更新登记条件。只有函数定义不证明引擎会调它。
3. 重新编译 AnimBP，检查本次生成类的预更新节点登记是否包含该节点，并核对运行实例确实使用该新生成类。可在编译登记及实际 `PreUpdate` 路径设置断点或诊断计数，关联同一实例与节点；登记结构的准确成员名必须从所用引擎版本确认，不能凭记忆编造。
4. 在全新生成类和新实例中验证 Game Thread 的 `PreUpdate` 调用及快照更新，再与 Update/Evaluate 消费值对照，避免旧类缓存掩盖漏登记。换风格时按项目同步约定先处理已有并行动画任务；参考案例使用 `GetProxyOnGameThread` 后同步更新单 Tag 和容器，但这不授权任意 UObject 跨线程访问。
5. 排查 URO、暂停、隐藏 Mesh Tick、LOD、无有效源和 AnimInstance 重建。没有新求值就没有新视觉，不能承诺同帧热更新。AnyThread 只读快照，不能反射遍历 ASC/Equipment。

曲线合同为普通浮点动画曲线 `LGame_WeaponPoseCoverage_<完整StyleTag>`，不是 Metadata 曲线。采用：

`SafeCoverage = 缺失或非有限值 ? 0 : clamp(Coverage, 0, 1)`

`EffectiveAlpha = clamp(MaxAlpha, 0, 1) * (1 - SafeCoverage)`

缺失、NaN、无穷值按 0，即不凭无效数据抑制原持剑层；有限负值和大于 1 的值钳制到端点。部分覆盖例如 0.4 时保留 0.6 倍最大 Overlay 权重，并继续既有逐骨混合和必要的曲线/属性传播。曲线是美术遮罩，不是每根手臂的精确贡献或 Gameplay 真值。

不采用“第一遍探测曲线、第二遍重求基础动画”的双遍 Evaluate。一次评估 BasePose，读取该 PoseContext 的 Curve，完整覆盖直接输出已取得的基础结果；部分覆盖继续组合 Overlay，复用这次基础结果。双遍会重复基础链工作，也不能用来修复快照或登记错误。

还须验证当前 BlendStack 的缺失曲线混合规则、BlendProfile、淡入淡出和旧风格残留；不能关掉曲线修复配置来让测试通过。原地切风格、收纳、无源、重建及暂停恢复都要覆盖。装备 Tag 或 Chooser 结果不能替代本次实际姿势的覆盖量。

## 3. 有 Walk/Run、缺过渡：分阶段接入与交付

接入所有具备质量和状态语义条件的素材；缺过渡明确保留已有回退。不能用 Idle 填每个空缺、把攻击/死亡塞入移动库，或为赶进度立即发布未经逐击审核的五段伤害。

1. **建立当前链路与覆盖表。** 核对 Source/Visible Mesh、Skeleton、实际 Pawn/Mover、主 ABP、Chooser、状态枚举、PSD/PSS、Slot 和 Retargeter。表列状态、步态/方向、源片段/骨架、身体与 Root 时长和周期、Phase/Loop、候选与回退。Walk 与 Run 先分清方向和真实输入，不能按文件名断言方向；同时列 Idle、蹲伏、Sprint、起停、转向以及空中/Traversal 边界。
2. **验证素材后生成派生。** 核对身体与根的周期、接触时点、播放率、距离和速度；同名 Root/Inplace 或相同归一化时间不证明配对。保留源素材、搜索根轨迹及来源记录。合格重定向结果复用，错误派生从原始来源修复。检查曲线、Notify、Loop 与重新加载结果。
3. **先接 Walk/Run 的实际选择路径。** 搜索特征兼容时复用 PSS，按真实状态分组候选。检查当前状态实际命中哪张表哪一行；完整核对条件、枚举掩码、风格容器绑定、优先级、输出、镜像以及其他武器/空手回退。缺 Start/Stop 等用经验证可达的现有回退，不机械复制 row 0 或随意加枚举 bit。Setup/Verify/Gate 共用严格契约。
4. **证明持续播放与切换。** 从真实输入观察选择结果、实际候选和播放时间。覆盖原地装备、持续移动换风格、方向/步态变化与无候选退出。不能只在 OnStateEntry 更新，也不能每帧重启片段。静态 Chooser 返回正确资产不能证明换装延迟已消失。
5. **再接分层、附件和移动边界。** 基础动作正确后使用覆盖曲线抑制重复持剑，再校准手指。保留既有脚部、Warping、Offset Root 与 Slot 顺序。检查单剑回归、双部件、拔收刀、失败清理、远端重建和权威 Trace。若开放 Sprint，还要验证输入许可、体力、服务器限速及旧 Mover Handle 清理，不能只改 AnimBP Gait。
6. **第一批攻击只交完整零伤害预览。** 走真实 Request/Ability 路径播放完整源片段，验证骨架、全身 Slot、Root 单次消费、取消和停止；不伪装成正式五段连击。若需要先预留五段配置结构，只能明确标记待审核、禁用正式伤害，不能填写猜测帧窗并宣称可用。
7. **人工逐击审核后交正式战斗。** 根据实际动作确认段数、Section 边界和稳定身份、命中/输入缓存/续招/可行动窗口、推进区间及拔收刀交接。不能平均切五段、照搬旧武器窗口或用名称推断五次命中。保持连续动作时间轴，测试跨窗口提取、Section 跳转、取消、受击与 Mover 重模拟；坐标转换一次。服务器校验目标与受限 Warp；同窗双刃按合同去重，不同挥击有独立窗口身份，客户端 Notify 不决定伤害。
8. **生成器与交接同时交付。** 修生成器并检查写前参数互斥、白名单、来源版本、幂等、保存、重新加载、失败退出码与恢复；不能仅修资产等下次生成覆盖。交接明确实际入口、输入、编辑字段、预览、保存/重装备要求、预期和诊断值。这些项目细节本次未检查，不能填入猜测路径或按键。

可交付门禁分别记录，任何一项未执行都保留未执行：

| 交付层 | 放行证据 |
|---|---|
| Walk/Run 静态接入 | 合格骨架/引用、周期/Loop/Phase/曲线/Notify、PSS/PSD 有效索引、完整条件及缺素材回退、重新加载一致 |
| 运行选择 | 原输入到状态、候选与实际播放时间，装备/换风格/方向切换和恢复有效 |
| 人工视觉 | 起停循环衔接、方向、脚滑、双手手指、穿模和位移观感；缺过渡范围明确 |
| 零伤害攻击预览 | 完整源动作经真实能力入口播放，Slot/Root/停止/中断有效；不得标成正式伤害通过 |
| 真实联网 | Authority、owner、旁观者，Listen/Dedicated、JIP、延迟丢包下表现与清理；配置值与实际连接观测分别记录 |
| 正式五段战斗 | 逐击人工批准配置，服务器实际命中/击空/伤害、双刃去重、受击取消和重模拟副作用验证 |

构建成功、静态选择命中、索引重建或最终位置收敛均不能替代后续门禁。当前只交付文字方案，所有 UE/资产/联网/人工视觉门禁均未执行。

## 实际读取文件

- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/SKILL.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/weapon-animation-diagnostics.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/animation-delivery-workflow.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/equipment-ability-lifecycle.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/gasp-mover-integration.md`