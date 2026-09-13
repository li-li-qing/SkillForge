# 案例与证据

## DBG-K01：把旧经验当作输入规则

| 字段 | 内容 |
|---|---|
| 状态 | 本机源码已核验，并与当前官方 API 页对照；未执行真实界面的输入回归 |
| 症状与条件 | 子按钮可见却不可点击，祖先可能使用 `HitTestInvisible` |
| 版本 | 核验 UE 5.7.4；其他版本调用时复核 |
| 证据 | 引擎相对路径 `Engine/Source/Runtime/UMG/Public/Components/SlateWrapperTypes.h` 的 `ESlateVisibility`；[Epic API 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/UMG/ESlateVisibility)（本次读取显示 5.8，5.7 结论依据本机源码） |
| 原因 | `Hidden` 占位但不可命中；`HitTestInvisible` 同时禁止自身及子控件命中；`SelfHitTestInvisible` 只排除自身。历史 LGF 笔记中的“Hidden 仍可点击”不成立 |
| 修复方向 | 对只绘制、自身无需输入且包含交互子控件的容器，核对是否应使用 `SelfHitTestInvisible`；父级也需输入时另查需求 |
| 验证结果 | 枚举语义已确认，特定故障根因未确认；应检查运行实例、命中路径和一次点击对应的业务动作，并回归动态隐藏与重复打开 |

这里收录的是机制与诊断方法，不是“所有点不到的按钮都改这一属性”。遮挡、启用状态、焦点、捕获与绑定仍可能造成相同症状。

## DBG-K02：面板不更新时直接加延迟

| 字段 | 内容 |
|---|---|
| 状态 | 方法候选；来自项目维护资料，当前插件未运行验证 |
| 症状与条件 | 订阅或加载入口发生变化后，界面偶发不刷新 |
| 版本 | 客户端与框架版本须在任务现场识别 |
| 证据 | Replicated Suite 维护资料中的加载入口、能力状态与刷新链约束；具体案例必须再补当前入口、日志或复现 |
| 原因 | 尚未确认；可能是注册、实例过期、状态未提交或刷新请求未消费 |
| 修复方向 | 沿入口至展示找首个断点；若证实数据未就绪，等待明确就绪条件，而不是凭旧笔记追加秒数 |
| 验证结果 | 没有游戏运行数据；准备实例/请求/状态关联记录后重跑原路径，不能宣称延迟修复有效 |

方法参考：[Superpowers 排障流程](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/systematic-debugging/SKILL.md)。本技能按任务调整调查深度，并保留未确认状态。
