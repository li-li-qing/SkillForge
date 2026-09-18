# GASP-ALS-R 第五轮蒸馏验证

日期：2026-09-14  
外部源码：`SAM-tak/GASP-ALS-R@a227dfecfcb2719c2541218cf026c05dfe3290ec`

## 研究边界

本轮静态阅读了当前 Mover main 的项目文档与关键 C++：Character/Mover input+sync、AnimInstance、MotionMatch/Montage/Traversal、Overlay/Linked Layers、PhysicsControl/Ragdoll、GameplayCamera。没有把第三方仓库拉入 SkillForge，也没有执行它的 UBT、Editor、PIE、Dedicated Server 或二进制动画资产检查。

许可按仓库 README 的分层记录：UE-only Content、MIT C++ 区域与 Unreal Engine source-derived 文件不能合并成一个统一 MIT 结论。当前文档含 custom UE 5.8.2 证据，SkillForge/LGF 目标 UE5.7 时只迁移模式，API 必须回目标引擎复核。

## RED

在 R4 baseline 的正式 references 上检查 7 个计划新增的合同。结果：`7/7` 缺失。

缺口：

1. custom Mover state 的 `NetSerialize + ShouldReconcile + Interpolate + Merge` replay contract；
2. `NativeThreadSafeUpdateAnimation` 与 PoseHistory parallel-evaluation fence；
3. client-selected Traversal TargetData 的 authoritative envelope validation；
4. Montage RootMotion -> Mover LayeredMove 的显式 cancel handle 生命周期；
5. PhysicsControl/Mover/Anim 的 single ragdoll lifecycle owner；
6. GameplayCamera desired intent 与 local possession context；
7. Linked Anim Layer 的 state-boundary Link/Unlink 与 Avatar rebuild。

因此本轮不是对既有 GASP 文档换措辞。

## GREEN

写回正式 references 后用同一语义检查：`7/7` 命中。

新增/强化：

- UE C++：`references/mover-animation-network-patterns.md`；
- LGF：`gasp-mover-integration.md`、`avatar-and-assets.md`、`external-project-patterns.md`；
- Blueprint：`references/linked-animation-layer-boundaries.md`；
- 项目完整蒸馏：`docs/project-distillations/gasp-als-r.md`。

## 行为 eval

- UE C++：23 -> 29，新增 `CPP-24..29`；
- LGF：20 -> 22，新增 `LGF-21..22`；
- Blueprint：3 -> 4，新增 `BP-03`；
- UI：保持 4。

新增场景覆盖 replay-safe Mover、AnimThread、Traversal Authority、RootMotion cancel、Ragdoll owner、GameplayCamera、Avatar animation rebind 与 Linked Layer responsibility。

## 结构/回归验证

已重新执行：

- `python scripts/validate_skills.py --self-contained` -> 6 Skills / 0 errors / 6 standalone copies valid；
- validator 定向 6 tests -> 6 passed；
- LGF workspace inspector -> 10/10 passed；
- repository JSON parse -> 37 files / 0 errors；
- 新增 7 项语义 contract -> 7/7 covered。

### Root validator 全量 suite

`python -m unittest discover -s tests -v` 在 180 秒执行预算内未完整结束。超时前连续完成的 12 项均为 `ok`，随后正在运行 quoted-name 测试。

该测试随后单独运行：

- R5 当前工作区：1/1 pass，约 8.7 s；
- R4 修改前 baseline：1/1 pass，约 8.9 s。

因此最终状态是：**全量 suite 未完成；定向 suite 与当时阻塞点单测通过。** 不宣称全量 unittest 已通过。

## 未验证项

- GAR custom UE 5.8.2 本地编译；
- LGF UE5.7 对应 API 的真实编译接入；
- GASP 二进制 AnimBP/PSS/PSD/Chooser 内容；
- Mover NetworkPrediction correction/resim 真实多人行为；
- Traversal cheat/reject；
- Ragdoll Dedicated Server；
- GameplayCamera 多 LocalPlayer；
- Unreal Insights / Anim Insights 性能数据。

这些属于后续把模式真正落到 LGF 工程时的 runtime acceptance，不由本次 Skills 静态蒸馏替代。
