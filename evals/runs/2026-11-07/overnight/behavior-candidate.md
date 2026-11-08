以下是四题的原始回答；仅阅读技能资料，未执行目标分析、修改或测试。

1. **只有 Shipping.exe，要定位可能的 RPC UFunction**

   我会选择 `skillforge-reverse-engineering`，实际具备 IDA 时组合 `skillforge-ida-pro`，重点使用 UE 二进制专项。不会因出现 UFunction 就假定有源码、编辑器、蓝图资产或 Live Coding 条件。

   先确认样本 SHA-256、格式、架构、位宽、加载基址与可取得的引擎版本证据，再核对分析数据库确实对应该样本。无 PDB 时，从字符串、注册代码、构造和虚表关系寻找目标类及 UFunction 候选，建立“注册包/类 → UFunction owner → thunk/实现地址 → xrefs”的链条。

   对 RPC 候选，核对匹配版本的 `FunctionFlags` 位值、注册 thunk、生成包装或网络分派调用链；`Server`、`Client`、`_Implementation` 名称只能作为线索，不能单独证明 RPC。不硬套固定偏移、RPCId 或所有版本通用的 `_Validate` 规则。若能取得授权运行条件，再用一次可区分假设的触发，记录目标实例、模块地址、参数及实际分派路径。

   交付每个候选的 RVA/地址空间、相关字节或指令、xrefs、版本依据、名称来源、置信度及缺口。分别写清“静态证据支持 RPC 候选”和“已观察到网络执行”；未运行时不宣称实际发送，搜索未命中也不证明不存在。

2. **PostMessage 成功，但 handler 前关窗，Result* 谁释放**

   `PostMessage` 成功只证明入队。Windows 不会自动为自定义裸指针 payload 执行 `delete`；handler 未运行时，handler 内的 `unique_ptr` 也无从接管。若现有协议只有“发送失败 sender 删除，发送成功 handler 删除”，这个关闭路径缺少释放者，会泄漏。generation 检查只能拒绝过期结果，不能修复所有权缺口。

   我会让独立于窗口寿命的 mailbox/线程安全队列持有 `unique_ptr<Result>`，消息只负责唤醒。worker 创建结果后，将所有权移入队列；接收入口已关闭则拒绝入队，由仍持有结果的 RAII 对象释放。UI 从队列取出所有权，检查 request/generation 后应用或丢弃，均自动释放。

   关闭与入队采用同一同步协议：关闭接收入口并使 generation 失效，停止或隔离 producer，清空并释放队列，然后销毁窗口。队列状态存活到 producer 不再访问它，唤醒投递也必须与关闭协调，不能依赖关闭后的 handler 或单次 `IsWindow`。通知失败必须有明确取消/回收路径，不能留下永久无人消费的结果。

   回归会覆盖成功 Post 后立即关闭、Post 失败、重复关闭、producer 与关闭竞争、HWND 复用，并验证每个结果恰好释放一次。若保留裸指针消息，则必须补足可靠的停止发送与显式排空协议，不能只在 handler 加智能指针。

3. **单维护者、本地 Git、调整一条已确认经验**

   不新建锁或事务系统。先读目标最新内容、Git 状态与差异，核对经验的证据、适用条件和已有规则关系，然后直接在所属位置做最小修改，用 Git diff 审阅并做受影响的结构/引用检查。

   不为这一次修订额外建立候选副本、旧内容快照或备份目录。确实出现多个写入者时才采用并发协议；当前没有该需求。也不会把“已确认经验”自动扩大成不受条件限制的通用规则。

4. **日志没出现，但尚未确认 probe 开启**

   下一步先验证观测链路。确认当前实例和构建确实含该探针、运行时开关已打开、类别和级别未过滤、采样没有抑制、输出位置正确且可读；再触发一个已知必然发生的事件，确认探针能产生可见输出。

   正对照通过后，用同一实例/request 标识重跑原路径，在事件源与消费者等相邻边界补最少量记录，判断调用未发生、没有到达、提前返回还是输出丢失。正对照未通过前，“没有日志”只能记为观测未成立，不能推出调用没发生，更不能据此修改业务逻辑或添加固定延迟。

读取的文件均位于 `/workspace/scratch/54a565457947/overnight_review_20261107/Skills/skills/`：

- `skillforge-orchestrator/SKILL.md`
- `skillforge-reverse-engineering/SKILL.md`
- `skillforge-ida-pro/SKILL.md`
- `skillforge-ida-pro/references/unreal-engine.md`
- `skillforge-ue-cpp/SKILL.md`
- `skillforge-ue-blueprint/SKILL.md`
- `skillforge-mfc/SKILL.md`
- `skillforge-mfc/references/threading-com-sta.md`
- `skillforge-mfc/references/window-lifetime-resources.md`
- `skillforge-experience-maintenance/SKILL.md`
- `skillforge-experience-maintenance/references/concurrent-updates.md`
- `skillforge-debugging/SKILL.md`
- `skillforge-debugging/references/diagnostic-boundaries.md`

没有读取 eval、报告或其它版本，没有修改文件。
