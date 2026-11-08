# 独立诊断链路新题

不修改第三轮题面、标准或 partial 结论。第四轮使用自写可执行 Python 合成 fixture，显式不是 LGF/UE 运行环境。

监控配置订阅 tasks.error，事件源发 task.error。无错误事件时计数 0 合理；明确错误事件时计数仍 0 表示观察链断裂；work 内替代配置可验证接通后的正对照。原 fixture 不得改。

执行者是 fresh fork-none 新上下文。只见自己的题面/fixture 与冻结 v4 技能（排除 evals），不得读预先冻结评分或其他结果。只许写 work/、trace 和 raw-answer。真实执行范围为可信自写 Python，无网络、外部代码或第三方项目。

记录实际命令、原始输出、文件完整性及事后独立复验。共享宿主、提示范围约束不是 OS 沙箱，trace 不是完整独立工具审计。不做新旧版对照，不推广为真实 LGF/UE 或全库行为通过。
