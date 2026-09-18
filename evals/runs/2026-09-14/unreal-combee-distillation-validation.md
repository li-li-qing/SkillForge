# unreal-combee R10 蒸馏验证记录

日期：2026-09-14

## 固定外部快照

- Repository: `nulla-sutra/unreal-combee`
- Commit: `971fa227179a99d308956b7031d5422634cefbfd`
- Commit date: 2026-06-30
- License: MPL-2.0
- Freshness classification: `Current source / Experimental adoption`
- 原因：源码近期维护，但 `Combee.uplugin` 标记 `IsExperimentalVersion=true` 且没有固定 EngineVersion。

## 研究范围

- Container / Cell / FastArray
- Item / Fragment / Unique / Shared / Link
- registered subobject helper
- Transaction / Bridge
- Move / Swap / Assign / Eject
- Snapshot
- README 与 active code path 对照

未执行 Combee UBT、Editor/PIE、Dedicated Server、Iris runtime、JIP、reconnect、packet loss、GC/Net Insights 或 large-inventory benchmark。

## RED

R9 正式参考语料在写回前检查以下 10 个新合同，全部缺失：

1. `runtime-active` / active-code evidence
2. registered subobject descendant symmetric unregister
3. frame-coalesced presentation delta
4. FRWLock reader/writer thread ownership contract
5. server-owned operation allowlist / registry
6. transaction write-set / single commit point
7. snapshot second-pass link resolution
8. global current play world rejection
9. Hotbar/link by stable ItemId
10. container capability/access contract

这说明 R10 不是只换项目名重复既有 FastArray/Transaction 文档。

## GREEN

写回后使用同一语义探针复查，10/10 命中。

新增 UE C++ 行为样本：CPP-52..59。
新增 LGF 行为样本：LGF-37..40。

## Fresh verification

### Skill validator

`python scripts/validate_skills.py --self-contained`

结果：

`Validated 6 skill(s): 0 error(s); 6 standalone copies validated.`

### Targeted validator tests

运行 6 项：

- self-contained relative resources
- main file line budget
- broken links
- absolute local paths
- eval arrays
- behavior expectations / fixture paths

结果：`Ran 6 tests ... OK`。

### LGF Inspector

`python -m unittest discover -s skills/skillforge-lgf/tests -p 'test_*.py'`

结果：`Ran 10 tests ... OK`。

### JSON

最终交付加入 changed-files manifest 后，仓库内 41 份 JSON 全部成功解析。

行为数量：

- UE C++: 59，last `CPP-59`
- LGF: 40，last `LGF-40`
- UI: 9，last `UI-09`
- Blueprint: 5，last `BP-04`

## Full validator suite limitation

尝试：

`python -m unittest -v tests.test_validate_skills`

220 秒工具预算内，前 12 项均显示 `ok`；执行到：

`test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`

时工具超时，完整 suite 没有完成。

随后该测试单独运行：

- R10 当前工作区：1/1 PASS，约 9.19s（进程约 9.79s）
- R9 baseline：1/1 PASS，约 9.04s（进程约 9.64s）

因此本轮不宣称 full validator suite 通过；证据只支持“超时前无 failure，阻塞点单独在当前版和基线均通过”。

## Active-code evidence 结论

固定提交源码推翻/收紧了以下 README 级宣称：

- Hive 虽 include Iris FastArray，但 active inheritance 仍是传统 `FFastArraySerializer`；Iris 分支在 `#if 0`。
- README 描述 rollback，但 active base transaction rollback 实现被注释。
- README 称 Swap atomic，但 active Swap 是 Eject -> Assign -> Assign，多步 mutation 没有 active rollback。
- Assign 对底层 `AssignCell()` failure 的 transaction failure 检查被注释。
- Eject 不检查 child clear success 就继续 reparent item。
- `FRWLock` 只有 writer lock 使用证据，没有 read lock。
- registered subobject remove helper存在，但 code search 没找到 active caller。
- Snapshot active structures没有 stable ItemId/ContainerId/SchemaVersion；ApplyContainerSnapshot 先清空容器，也没有 active item graph reconstruction。

因此这些机制只按 active source 事实写入 Skill，没有按 README 宣称升级成熟度。

## 交付边界

本轮改变的是 SkillForge 的研究/审查合同，不是 LGF runtime 实现。

没有声称：

- Combee 在 UE5.7/5.8 可直接构建；
- Combee Iris path 已运行；
- Combee transaction 已实现原子 rollback；
- Combee Snapshot 是 production Save/Load；
- LGF 已实际迁移这些规则。
