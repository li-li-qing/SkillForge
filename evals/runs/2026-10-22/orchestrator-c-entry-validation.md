# C 入口定向验证

范围：补充 C（先反问澄清需求），保留 A/B 协作等级；源目录 skills/skillforge-orchestrator，并同步本机安装副本。未提交或推送。

## 基线

独立只读执行者 /root/verify_c_entry 读取修改前安装副本，对两个新对话给出实际模拟回复：

- “使用 skillforge-orchestrator，我想做动画工具，思路还没理清。” → 只提供 A/B。
- “选 C，先通过反问帮我明确动画工具的需求。” → 回答“当前版本没有定义 C级，协作等级只有 A级和 B级”，然后仍要求选择 A/B。

结论：显式 C 被未选 A/B 的入口规则阻塞。此为对话行为证据，不是产品运行结果。

## 修改后独立样例

独立只读执行者 /root/check_c_behavior 读取修改后的仓库技能及必要参考页，未读取含预期的 development/evals 题库，未访问 UE 工程或写文件。下列六题在同一次独立上下文中分别模拟；未做多次重复采样，不宣称全量行为回归或统计稳定性通过。

| 场景 | 实际回复要点 | 状态及判定 |
|---|---|---|
| 新任务未选择入口 | “这次选 A、B 还是 C？”并逐项解释 | awaiting_mode；未实施；符合 |
| 明确选 C | 问“你最希望它先帮你解决哪个具体操作” | clarify / unset；未先问 A/B；符合 |
| 此前 A，要求先反问 | 保留 A，围绕第一版减少重复操作或处理重定向问题提问 | clarify / A；未实施；符合 |
| C 收敛，无 A/B，要求实现 | “方案已明确，执行阶段采用 A 还是 B？” | 等待等级；未重开访谈；符合 |
| 此前 B，C 收敛，要求实现 | 沿用 B，说明核对基线后推进实现与验证 | direct / B；仅模拟，不实际实施；符合 |
| C 检查点恢复 | 只问首轮批量规模，不重问用途和使用者 | clarify / unset；未实施；符合 |

新增 SFO-V3-31 至 SFO-V3-36 为可重复运行的行为规格。以上定向样例不替代按题库固定环境的完整执行，所以题库 execution_status 保持 not_run；SFO-V3-36“方案可以，整理一下”尚未独立采样。

## 静态与现有测试

- python -B scripts/validate_skills.py skills/skillforge-orchestrator --self-contained：0 errors，隔离副本验证通过。
- python -B -m unittest discover -s tests -p test_orchestrator_portability.py -v：5/5 通过。
- quick_validate.py：源目录和安装副本均通过。初次调用因 Windows 默认 GBK 解码失败，改用 python -X utf8 -B 后通过；未修改校验器。
- git diff --check：通过。
- 修改文件 UTF-8 无 BOM、CRLF，JSON 可解析；运行核心源目录与安装副本逐文件字节一致。

原始工具和子代理输出保留在本次对话。没有运行 UE 构建、PIE 或动画验收；本次修改仅涉及技能规则和验证资料。
