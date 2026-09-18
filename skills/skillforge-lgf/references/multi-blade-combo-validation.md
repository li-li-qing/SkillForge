# 多刀刃连击：窗口、连续播放与验收

适用于 LGF 的服务器 Combo/Trace 与 Montage/Mover 相连的工程。这里是可复用机制；具体资产、伤害数值、秒数及当前进度从消费工程读取。与[装备生命周期](equipment-ability-lifecycle.md)、[动画交付](animation-delivery-workflow.md)配合使用。

## 一阶段可有多次挥击；多部件不等于多库存

一个连击阶段可包含左刀、右刀或同时挥击。不要机械地把每把刀拆成独立 Segment，也不要因为同属一个装备槽而把所有 Trace 一起打开。

至少核对四个独立身份：装备实例/槽、表示 PartId、TraceSourceBinding、HitWindow。主部件查找接口可能永远返回 Primary；只添加 OffHand 网格或碰撞端点不能证明服务器 Provider 绑定到副刀。按部件解析是通用扩展，武器模型、Socket与数值属于项目。

在已核验的实现中，显式 HitWindowTag 用精确窗口匹配；空配置保留旧通用 Hit 兼容规则。父 Tag 匹配不能意外把 Left/Right 同时激活。去重粒度来自玩法合同：按刀独立时使用 Trace 配置身份 + 本次窗口身份 + Target；共享去重只在用户明确要求时采用。两刀同中可两次，不等于同刀每Tick重复伤害。

窗口重开从当前Socket建立采样起点，不沿用上一次关闭前的轨迹扫过空档。Damage callback可同步取消/切段；先登记命中再广播，并验证代次/运行集合仍有效，不能在回调后继续使用已失效引用。Authority拥有激活/结算真值，Notify只由既有服务器时间线消费。

## 完整 Montage 的五类时间不能混写

分别记录：完整动画绝对秒、Section起止、段内相对窗、输入缓存、续招交接和可行动。连续源优先保留一个完整Montage多Section；缓存/预约不等于当场跳段或重播Montage。

逐项核对 NextSection（是否无输入仍自动连）、服务器段尾推进、BlendOutTriggerTime（是否在合法续招窗结束前已blendout）、重复同资产实例身份，以及 Montage Notify 与 DataAsset window 的真实优先级。只校验数量不够，需比对类型、窗口Tag、时点、刀刃映射和实际运行。

段边界可行动Notify可能归到下一段或提前释放刚续上的攻击，应按当前Notify/Section归属机制设计，不普遍在每个边界插可行动。最后段可以先释放动作限制，保留后摇；新输入接管与取消/受击强停是不同生命周期。测试时同时看Ability、Hit窗、Montage和Mover，不用动画自然播完证明取消成功。

## 网络续招：发送不代表接受

每次记录同一world下的服务器段/Sequence、客户端段/Sequence、窗口、发送时刻、服务器到达及最终Accept/Reject原因。ServerOnly起播和复制延迟可能让客户端得知当前Sequence时窗口已经很窄；但看到晚发日志仍不能证明服务器拒绝原因。

测试若以服务器窗口作输入oracle再经客户端RPC提交，必须声明它不等于玩家本地预测输入。先区分测试发送策略、真实复制时序和合法迟到拒绝。不能用SubmittedToServer当Accepted，也不能为凑五段放宽审核窗、接收过期Sequence或删严格断言。先检查已有ForceNetUpdate，别凭延迟猜测重复加刷新。

失败后只加诊断便复测成功，不等于修复完成。保留无延迟首次失败、高延迟复现与各轮版本，不把局部重跑拼成完整矩阵通过。

## 用真实伤害夹具隔离刀刃

可在测试世界临时将未挥刀放在目标旁、挥刀放远，验证未挥刀不伤人；再交换。双刀窗两刀都触及同目标应按合同得到独立DamageId；一刀同窗不重复。使用真实装备请求、Authority Trace和GAS扣血，不直接调用Damage冒充整链。

明确夹具主动摆放了目标/Trace，它能证明通道隔离和伤害链，不能证明自然动画接触、握持、身后敌人的视觉轨迹或锁定推进。基础伤害与防御后HealthDamage分开记录。

## 人工反馈后的两个诊断分支

- **锁定连击从目标旁穿过**：先查正式Montage是否实际有Warp窗口、目标名匹配、服务器Target校验与每段更新、原始Root侧移、旋转限幅/停距、Mover桥消费及局部到世界转换次数。存在WarpTarget不证明窗口生效；无窗口不能先叫“修正太弱”。优先官方受限Motion Warping与原有Mover桥，避免每Tick瞬移/全局追踪旋转、双重推进或客户端决定命中。
- **起步低速立即播跑循环**：同帧观察输入、期望/实际速度、加速度、步态、Trajectory、Start/Pivot/Loop选择、实际候选播放时间、BlendStack/覆盖曲线与PlayRate。不能仅凭观感断定PSD数量不够、GASP插值错误或缺BlendSpace。保留标准PSS/Chooser/MM/Mover，按证据定位过渡素材/选择/退出或速度匹配，不靠固定延迟强切。

这些分支是诊断顺序，当前没有已验证的通用修复值。

## 取材与证据等级

UE5.7消费工程2026-09-14：LCombatComponent::RefreshHitWindow、FLCombatHitTraceConfig::HitWindowTag、Foundation表示部件绑定、LGameBuildTwinKatanaAttackCommandlet及真实输入/刀刃隔离测试。原运行记录覆盖完整多段、末段可行动接管与真实GAS独立伤害；正式网络矩阵含失败。技能维护只核对源码与既有日志，不冒充重新执行UE测试。固定伤害/半径/窗口长度不提升为框架默认建议。

## GAS Prediction Window 与 Section/HitWindow 是两套身份

多 Section 连招使用 LocalPredicted GAS 时，首段激活得到的 PredictionKey 不自动覆盖后续 latent Section、输入缓存、Montage Notify 或异步 Trace callback。每个异步边界都记录 ActivationKey、当前 ScopedKey、Combo Sequence、Section 与 HitWindow generation；需要继续预测时使用目标 UE 版本正式 scoped prediction/sync 机制，否则让 Authority 继续业务、客户端只保持 presentation prediction。

客户端 Montage/Section 自然结束不等于服务器伤害窗口结束。高延迟测试除了 Submitted/Accepted/Rejected，再记录 remote termination/security policy 和服务器实际 Ability end reason；禁止为了“本地播完了”强制提前结束 Authority 五段链。

TargetData 可以传 lock/trace/traversal 候选，但不是命中授权。客户端数据按 activation identity consume-once，Authority 重验距离、LOS、装备来源、PartId、Sequence、HitWindow 和动作几何；处理 data-before-listener、duplicate、late/cancel replay。完整合同见 [GAS 战斗预测](gas-combat-prediction.md)。
