# Capability Contract：能力优先，不识别品牌

本入口不根据 Agent、IDE、模型或产品名称分支。每次只记录**当前会话可观察到的能力**；不可观察就填 `unknown`。能力可以来自宿主工具清单、明确权限提示、真实调用结果或用户提供的环境说明。

## 核心字段

```text
skill_discovery      = native-list | scoped-filesystem | provided-metadata | none | unknown
skill_loading        = native-invoke | read-file | inline-text | none | unknown
context_meter        = exact | approximate | signal-only | none | unknown
context_compaction   = callable | user-action | automatic | none | unknown
file_read            = available | restricted | none | unknown
file_write           = available | restricted | none | unknown
command_execution    = available | restricted | none | unknown
artifact_delivery    = file-link | attachment | text-only | mixed | none | unknown
network_access       = available | restricted | none | unknown
isolated_worker      = available | none | unknown
```

这些值描述能力，不代表授权。`available` 也必须继续遵守当前任务范围、用户确认和宿主权限。

## 发现顺序

1. 宿主明确提供技能清单时，优先使用真实清单。
2. 没有原生清单但允许读取已知 Skill 根时，只读取候选目录的元数据；不要扫描整台机器或用户目录。
3. 只能读用户提供的文件/文本时，只依据这些材料，不声称发现了其他 Skill。
4. 完全无法发现 Skill 时，仍可生成执行简报并标明 `skill_discovery = none/unknown`；不要阻塞与 Skill 无关的工作。

## 调用与读取必须分开

- `native-invoke`：宿主有明确的 Skill 调用机制，并返回可观察结果。
- `read-file`：只能读取 `SKILL.md`；报告“已读取”，不要说“已原生调用”。
- `inline-text`：用户粘贴了规则；报告“已提供正文”，不要说已安装。
- `unknown`：宿主没有暴露加载状态；不要用模型记忆猜测。

## 上下文能力

`context_meter` 与 `context_compaction` 独立。能看到上下文压力不代表能主动压缩；能请求压缩也不代表知道精确 token 数。

只有出现宿主成功反馈，`COMPACT` 的 execution_status 才能写 `completed`。若只能由用户手动操作，写 `user-action-required`；若完全没有该能力，改用 `CHECKPOINT` 或 `HANDOFF`。

## 写入、命令与交付

确认前的“只读”必须以实际能力理解：有些命令即使名称像查询也可能产生缓存、锁文件或生成物。无法判断副作用时不要在准备阶段运行。

交付格式按 `artifact_delivery` 选择：能生成文件就交文件；只能文本则提供完整可复制内容与路径建议。不要因为用户习惯偏好 ZIP 就在不支持文件产出的宿主中伪造附件。

## 适配层原则

若某个宿主需要专用 metadata、命令或安装路径，把它放在**宿主外部适配层**，先映射成上述能力，再进入 Orchestrator 核心。核心不得出现：

- `if <product-name>` 分支；
- 专用命令符号；
- 固定用户目录；
- 特定模型窗口大小；
- 专有权限字段作为通用规则。

未来新 Agent 只要能映射到这份能力契约，就不需要修改核心流程。
