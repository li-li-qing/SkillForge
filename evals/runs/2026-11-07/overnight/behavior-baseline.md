以下是四题的原始行为答案。本轮只读指定技能文件，没有执行目标分析工具、修改文件或运行验证。

1. **仅有 Shipping.exe，定位可能的 RPC UFunction**

   我会选择 `skillforge-ida-pro`，配合 `skillforge-reverse-engineering` 的样本身份与证据规范。不会因为出现 UFunction 就把任务路由成 UE C++ 源码开发；`skillforge-ue-cpp` 只能在取得匹配源码后辅助核对契约。

   具体步骤：

   - 记录样本 SHA-256、实际格式/架构/ABI、加载基址、Shipping 与引擎版本的证据；无源码/PDB 的缺口明确保留。
   - 发现实际可用的 IDA 与数据库，核对输入样本和数据库身份。没有 IDA 执行能力就不声称取得 xrefs、反编译或内存结果。
   - 从字符串、构造/虚表、反射注册代码切入，建立“注册包/类描述 → UFunction owner → 注册 thunk/实现地址 → xrefs”链条。字符串相邻或函数名带 Server、Client、`_Implementation` 仅作线索。
   - 恢复候选函数 flags 的读取位置、字段宽度与原始值；依据匹配版本核实位值，再结合生成包装/thunk 与网络分派调用链判断 RPC。不能硬套跨版本偏移、RPCId 或 `_Validate` 规则。
   - 若静态证据不足且允许动态分析，再用最小触发场景记录正确实例的调用路径与参数。RPC 资格与“本次确实通过网络发送”分开报告。
   - 每个候选交付地址/RVA、名称来源、owner 依据、flags 证据、关键指令/xrefs、置信度及缺失证据；未命中不等于不存在，`ProcessEvent` 也不是所有原生调用的统一入口。

2. **PostMessage 成功后、handler 前关窗，Result* 谁释放**

   `PostMessage` 成功只解决投递结果，不能保证 handler 将执行。若唯一释放代码在 handler 中，此路径没有可靠释放者，会留下泄漏风险；系统不会替业务释放这个堆对象。参考里的“成功转交 receiver、handler 用 unique_ptr”模式必须补上 receiver 的关闭清理协议。

   我优先设计为：独立、可跨越窗口关闭时刻存活的 receiver state/线程安全队列拥有 `unique_ptr<Result>`，消息只负责唤醒，不携带拥有型裸指针。

   - worker 在队列接收成功前拥有结果；队列关闭或拒收时由 worker 的 RAII 释放。
   - 接收成功后队列拥有结果；正常 handler 取走为局部 `unique_ptr`，验证 generation/request-id 后处理或丢弃。
   - 关闭时先关闭接收入口并失效 generation，再取消任务；队列在同一同步协议下清空并释放待处理结果。保证 worker 已停止，或仍存活的 shared state 能安全拒收、释放迟到结果。
   - 投递失败也要有明确的队列回收/失败处理路径，不能让无人唤醒的数据无限滞留。
   - 若保留裸指针消息，必须让关闭路径在停止所有生产者后排空并释放该协议的剩余 payload；不能只做一次 `IsWindow` 检查，也不能只依赖 handler。
   - 验证成功投递后立即关闭、投递失败、取消、反复开关窗与旧 HWND 被复用；检查无泄漏、双重释放、旧结果覆盖与等待死锁。

3. **单维护者、本地 Git、无并发，调整一条已确认经验**

   不新建锁或事务系统。选择 `skillforge-experience-maintenance`，读取最新内容与 Git 差异，确认适用条件和证据，直接对原规则作最小修改，然后审阅 diff、检查受影响引用及行为案例，用既有 Git 历史记录与恢复。

   不为这次修订额外建立候选副本、旧内容快照或备份目录。只有实际出现多个写入者时，才引入独占锁或版本条件写入；可选存储工具不是每次更新的必经步骤。本题仅给出判断，不实际改文件。

4. **日志未出现，尚未确认 probe 开关**

   下一步先验证观测手段，不能得出“调用没发生”。

   - 核实实际运行实例/版本、probe 是否编译与启用、运行时开关值、日志级别和过滤条件。
   - 核实输出位置、采样/限流策略以及是否查看了当前进程的输出。
   - 用已知必经路径产生一次最小正向探针，确认整条观测链确实可见。
   - 再用相同输入重现，并关联实例/request-id 检查调用边界；必要时以断点或计数器交叉核对。
   - 探针有效性未证实前，结论保持“观测不足，调用是否发生未知”，不改业务逻辑或加入固定等待。

读过的文件如下，路径均相对于 `/workspace/scratch/54a565457947/ida_delivery_work/Skills/`：

- `skills/skillforge-ida-pro/SKILL.md`
- `skills/skillforge-ida-pro/references/unreal-engine.md`
- `skills/skillforge-reverse-engineering/SKILL.md`
- `skills/skillforge-ue-cpp/SKILL.md`
- `skills/skillforge-mfc/SKILL.md`
- `skills/skillforge-mfc/references/threading-com-sta.md`
- `skills/skillforge-mfc/references/window-lifetime-resources.md`
- `skills/skillforge-experience-maintenance/SKILL.md`
- `skills/skillforge-experience-maintenance/references/concurrent-updates.md`
- `skills/skillforge-debugging/SKILL.md`
- `skills/skillforge-debugging/references/diagnostic-boundaries.md`
- `skills/skillforge-orchestrator/SKILL.md`

未读取 eval、报告、期望答案或其它版本。
