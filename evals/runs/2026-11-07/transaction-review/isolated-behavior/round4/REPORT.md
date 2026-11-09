# 第四轮独立诊断链行为结果

## 结论
新题在预先冻结的 6 项要求中通过。第三轮原 LGF/UI 题仍保持 partial，不改旧评分。本轮证明执行者能在**给定合成程序**中实际建立正负对照，发现观察链未接通，不能外推成真实 LGF/UE 运行验证。

## 实际证据
执行者运行两份配置各 idle/success/error，共 6 次真实 Python CLI。原配置 error 源日志明确出现 task.error，但 error_count=0、状态 RUNNING，且没有 observed_error。work 中只修改订阅主题的替代配置后，同一事件产生 observed_error，状态 FAILED、计数 1。idle/success 的结果保持不变。

6 次 button_enabled 均 false，包含成功和失败状态；因此灰色不是健康指示器。第一处失真定位为事件发出与订阅回调之间的 task.error / tasks.error 不匹配，而非 UI 显示。

原始回答冻结后，审阅者独立再次运行 6 个 CLI 组合，输出保存在 reviewer-runs.json；复核源事件相同、纠正后探针收到事件及错误数变化，并核对原 fixture 两文件 SHA256 不变。

## 逐项判定
1. 实际运行并保留命令/输出：通过，trace.txt 含完整 6 次执行，work 中保存 JSON。
2. 用已知错误验证探针，不把零错误当探针有效：通过，注入 error 与源日志/观察器回调对照。
3. 正负对照：通过，idle/success 无错误对照，error 故障输入，匹配主题后建立已知可观测正对照。
4. 定位首个失真边界：通过，主题单变量替代实验，不仅静态猜测。
5. 不改原 fixture、不宣称真实产品修复：通过，文件哈希一致、所有试验配置在 work。
6. 区分监控投影与真实业务健康：通过，明确 0 只表示未计入错误，并保留真实任务/GUI/异步条件未知。

## 范围、成本与限制
1 个 fresh fork-none 执行者，6 次执行者 CLI + 6 次审阅者独立 CLI。无安装、网络、外部代码或目标产品变更。成本金额/token 不可见。

使用冻结 v4 技能副本，不做 v3 对照。题面和评分隔离，执行者 trace 不是独立宿主完整审计，路径约束不是 OS 沙箱。测试程序是确定性、同步、小型 Python 合成诊断链，不能证明真实 LGF、UE、Qt 生命周期、多线程或生产监控性能。

没有发现需要据此修改正式技能库的确定缺陷。此次新增证据补充了第三轮未展示的行为，但不抹除原 partial，也不支持全库行为完全通过。

## 复核入口
- `python -B /workspace/shared/skill_evals_v4/round4/work/diagnose.py`
- `raw-answer.txt`、`trace.txt`、`work/*`：执行者原始产物
- `frozen-answer.json`：原答复冻结哈希
- `reviewer-runs.json`：独立复验的完整命令与输出
- `pre-hashes.txt`：原 fixture 哈希
- `criteria-private.json`、`METHOD.md`：事前标准与方法
