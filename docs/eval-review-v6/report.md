# v6评测门禁与评分措辞修订

基线为独立保存的v5；未覆盖旧包或用户安装。当前版本验收以本报告及本目录change-manifest.json为准。docs/transaction-review和其测试日志、清单是保留的v5历史证据，不是v6现行哈希或数量。

## 修订

- 全库评测JSON解析拒绝所有对象层级的重复键，避免expected/id或嵌套context被静默覆盖。真实临时CLI夹具三个负例先失败后通过；并非现有题库已经损坏。
- Qt README同步28行为题、每题至少三项观察点，未为凑数量增加评分点。
- CPP-10/CPP-18旧评分限定AbilitySpec、独立持续GE、聚合贡献/层数、Instant和已发生周期execution及AttributeSet各自撤销合同；修复措辞歧义，未声称旧行为评测失败或新行为改善。

## 验证

六套testsRun为106+40+50+30+36+66=328，全部exit0，无失败，8条skip记录（含子测试），不能通过相减计算精确通过方法数。红绿记录和六套输出见evals/runs/2026-11-07/eval-review-v6。14技能和14独立副本校验0错误，动态索引一致；修改Python的AST通过。现有全部26份评测JSON严格重复键扫描通过，Qt实际数量与最少观察点已核对。

保留全部v5历史原始证据。IDA/UE/Windows/Qt/游戏实机与MCP拦截未运行，本轮不增加此类声明。打包排除缓存，完整保留Skills根结构。新manifest相对v5计算，排除自身；实际变更数为entries+1。
