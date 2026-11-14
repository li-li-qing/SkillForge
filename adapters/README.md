# 可选宿主适配

此目录不是运行核心，也不自动安装。保留原包的宿主metadata在 orchestrator/openai/openai.yaml；只有目标宿主确实支持该格式且用户要求部署时，按其当前文档应用overlay，不覆盖用户现有配置。

元数据只是发现和显示提示，不是安全拦截、权限授权或跨宿主记忆机制。本轮未运行对应宿主做兼容验证。

[WorkBuddy 使用检查](workbuddy/README.md)记录技能启用、读取证据、模型/上下文条件及配对检查方法。它是手动排查说明，不修改运行核心，不自动安装或更改用户配置；尚无 WorkBuddy、DeepSeek 或 GLM 的实际对照结果。
