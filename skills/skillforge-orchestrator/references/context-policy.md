# 上下文决策：工作集优先于固定阈值

五个动作是语义选择，不是产品命令，也不是必须按顺序升级的等级。决策基于有效证据密度、无关历史、后续预计读取规模和 capability snapshot；不设统一 token 百分比。

## 观察与状态

```text
budget_evidence = host-reported | approximate | signal-only | unknown
action          = KEEP | NARROW | CHECKPOINT | COMPACT | HANDOFF
execution_status= not-needed | recommended | requested | user-action-required | completed | unavailable | unknown
```

若宿主没有精确计量，就不能把“聊天很长”换算成伪精确百分比。

| 动作 | 适用条件 | 实际含义 |
|---|---|---|
| KEEP | 当前资料集中，继续读取成本可控 | 保持当前工作集，不重复总结 |
| NARROW | 历史主题很多，但当前任务证据足够 | 停止引入无关资料；不声称卸载已读内容 |
| CHECKPOINT | 阶段边界、多轮失败、即将交接，或缺少压缩能力 | 输出可恢复状态；默认不写仓库 |
| COMPACT | 有真实压力，且宿主存在可用压缩能力 | 先留恢复事实，再请求/执行合法压缩机制 |
| HANDOFF | 切换会话/环境/执行者，或旧上下文隔离更合适 | 生成自包含交接包，新环境重新核实基线 |

## COMPACT 边界

Orchestrator 不能靠摘要自行释放模型上下文。只有宿主实际支持、当前权限允许并返回成功证据，才能标 `completed`。

- `callable`：可由当前工具直接请求，按宿主规则执行。
- `user-action`：只给用户动作建议，状态写 `user-action-required`。
- `automatic`：宿主已经自动处理时记录已观察事件，不重复请求。
- `none/unknown`：使用 CHECKPOINT/HANDOFF，不伪造 compact 命令。

不要从模型名推断上下文窗口，也不要为了“节省上下文”擅自切模型或新建会话。

## Checkpoint 必须保留

使用 [checkpoint 模板](../assets/checkpoint.md) 保留：原始请求和增补、硬约束、项目/基线、未提交修改、简报版本与批准来源、已做/未做、实际文件变化、错误证据、失败尝试、真实测试结果、下一步、所需 Skill 与能力缺口。

不能把“怀疑根因”压成“已确认根因”，不能把 `not_run` 压成 PASS，不保存隐藏推理、凭据或无关个人信息。

Checkpoint 是恢复记录，不是授权令牌。进入新会话或新宿主后仍需核实当前基线及用户对该范围的采用。
