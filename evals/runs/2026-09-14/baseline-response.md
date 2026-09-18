以下仅为场景诊断方案，未检查或修改实际工程；假设均需在实施时验证。

1. **武器切换被 `WeaponTransition` 阻挡**
   - 优先核对卸下能力的 Tag 所有权、Commit 回调与装备请求的同步重入顺序。
   - 保留“Montage 结束才 `EndAbility`”合同，不能用清空 ASC 上同名 Tag 的方式破坏其他能力持有的状态。
   - 若装备必须等卸下表现结束，将后续装备排队到卸下完成并释放阻挡状态后启动；若设计允许 Commit 后立即装备，应调整该能力自身的阻挡窗口或接续规则，而非提前结束能力。
   - 验证快速连续切换、取消、失败、死亡与远端请求，确认既不重复装备也不残留锁。

2. **双剑姿势延迟约三秒，Root 与身体时长不同**
   - Chooser 输出包含 style 只证明输出数据存在；追踪装备状态复制、动画桥、Chooser 实际求值、选中资产、混合/惯性化及状态退出，定位延迟首次出现的位置。
   - `0.8s` Root 与 `2.4s` 身体动画存在时间域不一致风险。核对播放速率、时间映射、根运动驱动的持续时间与停止条件，避免默认按相同秒数采样。
   - 不凭时长差直接认定延迟原因，也不先强改时长掩盖问题。
   - 25/25 轨迹脚本通过仅覆盖其采样断言；仍需实际移动中切换双剑，观察 owner/proxy 的姿势切换时点和位移。

3. **ServerOnly 攻击 owner 不播，取消后仍自然播完**
   - 分开调查两个问题。owner 漏播先查 Montage 复制/表现分发是否跳过 owner，以及是否错误假定 owner 已本地预测；ServerOnly 情况下该假定需要重新验证。
   - 核对长期 ASC 的当前 Avatar、播放 Mesh 与实际 AnimInstance，确保播放事件送到 owner 的正确对象。
   - 取消返回成功不代表 Montage 停止。追踪取消是否抵达当前能力实例，是否调用对应播放任务或 Montage 的停止接口，以及停止状态是否传到 owner/proxy。
   - 为同一次攻击关联操作身份，避免重复播放或旧取消停止新攻击；验证取消即时停止、自然结束、打断与 Avatar 更换。

4. **原始资产解析与 NullRHI 结果要求重建 WBP**
   - 现有证据不足以支持重建。原始 `Stretch=0` 应对照对应引擎枚举和反射加载值核实，不能直接判为 `None`。
   - NullRHI 下几何为零可能缺少有效视口或布局过程，不能单独证明 Widget 损坏。
   - 用编辑器加载后的属性、WidgetTree、Slot、可见性与 DesiredSize 检查，再在有效渲染视口完成布局后观察实际几何。
   - 仅修复已确认的属性、绑定或局部布局问题；保留引用和现有结构，除非出现足以证明整体结构损坏的证据。

5. **8 个当前网络用例均因缺 Trace socket 失败**
   - 交付应明确：**当前完整网络验收为 0/8 通过，8 个均失败于 Trace socket 前置条件；装备和复制子断言通过；13 个旧回归通过属于独立覆盖。**
   - 不能合并成“21 个通过”，也不能据此声称本轮战斗网络链路通过。
   - 核对服务器实际使用的 AuthorityTrace Mesh、骨骼与 socket 配置；修复测试装配后重跑原 8 个用例，观察此前未到达的命中/伤害断言。
   - 若只能阶段性交付，列明已验证的装备/复制范围与尚未验收的战斗链路，保留本轮运行标识和失败证据。

已读文件：

- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/SKILL.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/network-and-state.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/avatar-and-assets.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/ui-platform.md`
- `D:/Project/Skiils/SkillForge/skills/skillforge-lgf/references/validation-and-evolution.md`
