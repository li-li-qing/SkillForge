# 执行简报模板

这是结构模板，不是新的授权。短任务只保留必要字段。

## 身份与原始需求

任务 ID / 修订号：
状态：pending / approved / running / blocked / done / prompt-only
原始请求：逐字保留，或引用可复查的原始消息/附件。
本轮增补：
批准来源与范围：没有就写“尚未批准”。

## 只读核实

项目 / 技术栈 / 实际基线：
证据位置：文件、版本、提交或附件；不可见写 unknown。
相关模块 / 当前未提交修改 / 不可读取部分：
已核实事实：
假设与待确认项：

## Capability Snapshot

只列与任务有关的字段：

```text
skill_discovery=
skill_loading=
context_meter=
context_compaction=
file_read=
file_write=
command_execution=
artifact_delivery=
```

不可观察填 `unknown`，不要从产品或模型名称猜测。

## 路由与上下文

拟用 Skill：名称、来源/作用域、状态（candidate/discoverable/readable/read/invocable/invoked/unknown）、唯一职责。
排除：只列容易混淆且有理由排除的候选。
上下文：action + budget_evidence + execution_status + 一句依据。

## 可复制的执行提示词

```text
请在【已核实项目/基线】中完成【目标】；原始请求为【原文或随包位置】。
先读取【实际适用的项目指令与相关文件】，不得把未核实假设当事实。
根据当前可发现 Skill 元数据选择最小充分集合；优先使用【已核实候选及职责】，但真实环境变化时以实际发现结果为准。
允许范围：【模块/文件类型与必要相邻影响】。
明确不做：【非目标】。
硬约束：【数量、方向、API/兼容、交付要求】。
已有批准：【当前简报对应的用户确认；没有则保持 pending】。
执行前复核基线；新增重大范围或外部副作用只对新增部分重新确认。
验证：【实际可运行检查】；不能运行的检查标 not_run/unavailable。
交付：按宿主真实 artifact_delivery 能力提供修改文件或完整文本，并附验证结果、风险、未验证项和交接摘要。
```

## 结束状态

- `pending`：等待用户确认当前版本。
- `approved`：进入已批准工作，不重复确认。
- `prompt-only`：提示词交付后停止。
