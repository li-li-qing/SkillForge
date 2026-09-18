# XistCommonGameSample R9 验证记录

日期：2026-09-14

## 固定外部证据

- `XistGG/XistCommonGameSample@7e01e1fed344a741f80fa82b7161c86c494a410b`
- MIT
- `.uproject` `EngineAssociation = 5.7`
- README 明确：single-player Lyra-like CommonUI + Enhanced Input 教学样例
- Epic 当前 UE5.8 CommonUI 文档用于现代性校准

## RED

在 R8 正式参考中检查以下合同时均不存在完整规则：

1. Root Layout 应属于 LocalPlayer 而不是 Pawn。
2. Enhanced Input Mapping Context 必须 source-owned add/remove，复杂项目不使用 `ClearAllMappings()` 做全局清理。
3. GameplayMessageRouter 是本地事件总线，不是 replication/JIP/canonical truth。
4. 普通 Activatable Widget 默认不应各自抢 input mode；顶层 route/modal 才拥有 input policy。
5. blank widget 遮层不作为通用 modal 权限模型。
6. LGF CommonUI Presenter 不得建立第二套 Route Stack/Back truth。

## GREEN / 定向语义

R9 正式参考写回后，同一组语义断言 6/6 命中。

新增 behavior cases：

- UI-05..09
- CPP-50..51
- LGF-36

最终数量：

- UE C++：51
- LGF：36
- UI：9
- UE Blueprint：5（未改）

## SkillForge validator

`python scripts/validate_skills.py --self-contained`

结果：

`Validated 6 skill(s): 0 error(s); 6 standalone copies validated.`

定向 validator unittest：6/6 PASS：

- self-contained relative resources
- main file line budget
- inline/reference links
- absolute local paths rejection
- eval JSON arrays
- behavior expectations / fixture paths

LGF inspector tests：10/10 PASS。

仓库 JSON：39/39 parse。

## 完整 unittest

尝试：`python -m unittest -v tests.test_validate_skills`

210 秒工具预算内前 16 项均 `ok`，包括此前常见慢点 `test_json_quoted_names_allow_yaml_ambiguous_but_valid_skill_names`；超时时正在运行 `test_name_constraints_and_directory_match`。

该阻塞点单独运行：

- R9：PASS，约 5.6 秒（命令总约 6.2 秒）
- R8 baseline：PASS，约 5.4 秒（命令总约 6.0 秒）

因此记录为：完整 suite 在工具时限内未完成；不能宣称 full suite 全量通过，也没有当前证据表明 R9 引入该测试回归。

## 未执行

- 未在 UE5.7/5.8 编译 XistCommonGameSample。
- 未在 LGF 消费工程实现 CommonUI Presenter adapter。
- 未运行 PIE split-screen / travel / controller replacement / possession / gamepad focus。
- 未运行 Dedicated Server 或 packaged build。
- 未做 CommonUI + Enhanced Input 发行平台成熟度验证。
