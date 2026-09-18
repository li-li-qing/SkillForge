# 大规模物品值语义、稳定句柄与容器事务

用于大量物品、Grid/Slot Inventory、装备/仓库、嵌套容器和多人拖拽事务。核心问题不是“Struct 还是 UObject”二选一，而是为不同成本层选择最小表示，并保证 Authority、稳定身份、复制 Dirty、Host 本地刷新和持久化边界一致。

## 1. 先选表示成本，不先选类层级

建议把物品表示看成四级成本梯度：

| 层 | 适合内容 | 默认网络/内存策略 |
|---|---|---|
| Definition / static Fragment | 名字、描述、图标、Mesh、最大堆叠、静态装备规则、最大耐久 | PrimaryDataAsset / stable DefinitionId；静态内容不按实例复制 |
| Compact Stack | Definition 引用/ID、StackCount、少量常用整数、运行 Handle | 紧凑 USTRUCT + FastArray；高数量默认路线 |
| Typed ItemState | 耐久、实例 metadata、动态 tags、socket state、可选模块状态 | `FInstancedStruct` 或等价 typed value state；只为需要它的实例存在 |
| ItemInstance UObject | 独立网络身份、嵌套 replicated object graph、复杂生命周期/行为、对象 API | 少量按需创建；完整 replicated subobject 生命周期 |

不要把“随机装备”自动等同于 UObject。随机 affix 完全可以是紧凑 struct 状态；只有当物品需要对象身份和生命周期时再升级。

同一物品只能有一个 canonical truth。若 Stack 持有 RuntimeInstance，必须写清：

- ItemId/DefinitionId 由谁保存；
- StackCount、位置、耐久分别属于哪层；
- Save 序列化哪一层；
- UObject 销毁后是否还能仅凭 Stack/Save 恢复；
- Proxy/UI 是否只读投影而不是第二份状态。

## 2. Definition 与运行状态分离

静态展示和规则优先放 Definition：

- `FText` 名称/描述；
- Icon、StaticMesh/SkeletalMesh soft reference；
- MaxStack、GridSize、Weight/Value；
- ItemType/静态 tags；
- 静态 Fragment 配置；
- RuntimeInstanceClass 或状态工厂描述。

实例复制只携带真正会变化的东西。即便 Definition 是 UObject 指针，也要确认客户端能通过 PrimaryAssetId/DefinitionId 建立相同映射；持久化不要保存裸 UObject 地址。

## 3. Fragment 是静态能力，State 是实例变化

Fragment 和 State 不要混为一层：

- **Fragment** 回答“这种物品支持什么、默认怎么初始化”；
- **State** 回答“这一件物品现在是什么状态”。

例如最大耐久属于 Fragment/Definition，当前耐久属于 ItemState。背包容量配置属于 Fragment，实际 NestedInventory 属于 ItemState/ItemInstance。

当运行状态类型很多但每件物品只需要少数几个时，`TArray<FInstancedStruct>` 是有价值的中间层：

- 避免每个状态一个 UObject/GC allocation；
- 保持 typed struct，而不是把所有字段塞进 GameplayTag 数值表；
- 支持按需组合；
- 仍需审查复制粒度，整个 `TArray<FInstancedStruct>` 的 OnRep 不一定适合高 churn 状态，必要时给高频子状态独立 FastArray/serializer。

### Fragment 查找与热冷排序

若 Fragment 数量很小、固定且线性扫描足够，优先保持连续数组，不急着为每类 Fragment 建 Hash Map。可以按查询频率排序：

- hot Fragment 放前面；
- 只在初始化执行一次的 cold Fragment 放后面；
- 只有 profile 证明线性扫描成为热点，再引入索引/cache。

这比无条件增加 TMap 节点分配和 pointer chasing 更符合 cache-friendly 目标。

## 4. Stable Handle：Index + Generation

长期把 `TArray` 下标当物品引用会产生 ABA/stale-reference 问题：槽位 12 的旧物品删除后，新物品复用 12，迟到 UI/网络/异步请求可能误操作新物品。

可使用运行时句柄：

`Handle = Index + Generation`

解引用时同时验证：

1. Handle 格式有效；
2. Index 在 canonical array 范围内；
3. 当前槽位 `Generation == Handle.Generation`；
4. 需要时再验证稳定 ItemId/expected revision。

删除时：

`unregister complex instance -> free-list push index -> generation++ -> reset slot -> MarkItemDirty`

新增时：

`free-list pop or append -> keep current generation -> assign new item -> MarkItemDirty`

这样可以不为删除频繁压缩 canonical item array，也避免 swap/remove 破坏外部 handle。

### Handle 不是 Save ID

Index+Generation 通常只是当前运行会话的稳定引用。必须另外设计跨会话稳定身份，例如 FGuid/业务 ItemId。还要审查：

- index/generation 位宽；
- generation wrap 后的碰撞风险；
- 最大槽位数；
- Handle 是否需要 NetSerialize/packed serializer；
- JIP 后 Handle 是否仍只指向当前 Authority 快照。

FastArray `ReplicationID` 同样不是业务/存档 ID。

## 5. ItemData 与 SlotData 分离

Grid Inventory 中“物品是什么”和“物品放哪里”变化频率不同。不要在每个 Slot 重复存完整 Item。

推荐：

- `ItemData FastArray`：DefinitionId、StackCount、runtime handle、少量动态字段；
- `SlotData FastArray`：SlotHandle、ItemHandle、Orientation、Lock 等布局字段；
- `Section/Tab config`：低频布局/过滤配置；
- 本地派生 cache：ItemHandle -> SlotHandle、占格 bitmap、UI view index。

好处：同一 Inventory 内移动/旋转通常只修改 SlotData；StackCount 变化只修改 ItemData。网络 delta 和 cache 工作集更小。

两个 FastArray 都要独立满足序列化合同。示意：

```cpp
USTRUCT()
struct FReplicatedItemEntry : public FFastArraySerializerItem
{
    GENERATED_BODY()

    /** Replicated runtime identity. Not a persistent save identifier. */
    UPROPERTY()
    FItemHandle Handle;

    /** Replicated mutable business state. */
    UPROPERTY()
    int32 StackCount = 0;
};

USTRUCT()
struct FReplicatedItemList : public FFastArraySerializer
{
    GENERATED_BODY()

    /** Authoritative replicated entries. Local indexes are intentionally excluded. */
    UPROPERTY()
    TArray<FReplicatedItemEntry> Entries;

    bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParams)
    {
        return FastArrayDeltaSerialize<FReplicatedItemEntry, FReplicatedItemList>(Entries, DeltaParams, *this);
    }
};
```

生产代码还需要 Traits、Add/Change/Remove callbacks、Owner pointer、dirty API 与 JIP tests。

## 6. FastArray 回调是投影，不是业务入口

可以使用非复制 previous-state cache 分类客户端事件：

- invalid -> valid：Added；
- same generation：Changed；
- generation changed：Removed(old) + Added(new)；
- valid -> invalid：Removed。

但 callback 只负责：

- rebuild 派生索引/占格；
- 绑定表现依赖；
- 发布 UI/ViewModel delta；
- 清理旧引用。

禁止 Proxy callback 调 `MarkItemDirty` 或再次提交 Authority mutation。

### Listen Host

Authority 本地写不会等待自己的 OnRep。每个成功 mutation 必须主动进入与 Remote callback 等价的 local projection contract。常用方式：

`Authority commit -> BroadcastItem/SlotDelta locally -> replication -> Remote callback -> same presentation message`

避免 Host 既从 mutation 广播一次又从人为调用 callback 再双播。OnRep 手动调用只在合同明确、幂等且不会混淆 Authority/Proxy 语义时使用。

## 7. MutationKey：缩小 C++ 写权限

把 FastArray 条目字段全部 public 会让任何调用方都能绕过 Dirty、Authority 和事件。给整个系统 `friend` 又会开放过多未来字段。

可以采用 passkey / capability token：

- 受保护 setter 额外要求一个不可公开构造的 `MutationKey`；
- 只有 Inventory/Transaction/极少数初始化逻辑可创建 key；
- 新调用方想获得写权限时必须显式加入授权清单；
- 其它代码只能拿 const view/Handle。

但要注意：MutationKey **不是**网络权限。拥有 C++ key 的函数仍必须通过 Authority、handle generation、owner/access 和 transaction validation，而且必须负责 `MarkItemDirty` 与本地表现事件。

批量 mutation 应避免每改一个字段就重复 Dirty/Broadcast；用 transaction/batch 合并最终 commit。

## 8. Pending Slot / Reservation 解决并发，不代替 Authorization

多人拖拽常需要临时 claim：

- Source/Target slot 可标记 Pending；
- claim 记录 instigating controller / transaction；
- 设置过期时间避免掉线永久锁死；
- 只有持有 claim 的请求可以继续；
- commit/abort/disconnect 都释放 reservation。

这解决“两个玩家同时拖同一个格子”的并发，但不能证明玩家有权访问该 Inventory。Authority 还要检查：

- Source/Target Inventory 是否属于玩家、队伍、公会或当前交互会话；
- 距离/LOS/interaction token；
- ItemHandle generation 与 source slot 当前引用；
- stack amount/section filter/ActionLock；
- shared stash ACL 与容量；
- request idempotency/expiry。

## 9. Transaction：客户端命令，Authority 重算结果

客户端发送的 Move/Loot/Drop transaction 只表达意图。生产 Server RPC 不信任：

- `URockInventory*`；
- world actor 指针；
- source/target slot；
- DropLocationOffset；
- Impulse；
- stack amount；
- “客户端说它已经 claim 了”。

服务器按稳定身份重新解析，并再次验证当前状态。

### TransactionID

TransactionID 至少定义：

- 每个连接/玩家的生成域；
- 重复请求是否幂等返回旧结果；
- expiry/window；
- 断线后是否清空；
- prediction result 如何关联；
- stale handle 与 duplicate request 的错误码。

### Prediction

只有当 rollback/reconcile 已实现并测试时才开启预测。占位 `AttemptPredict=true`、失败后只设 `bAwaitingServerSync`、Undo TODO 都不是生产能力。

先实现无预测 Authority transaction，再按必要性增加：

`local predicted delta -> request id -> Authority result -> confirm or rollback -> authoritative snapshot reconcile`

## 10. Drop/Loot 的服务端验证

网络量化只减少比特数：`FVector_NetQuantize*` 不是安全校验。

客户端允许建议 drop direction/location 时，服务器应：

- 限制 offset/impulse magnitude；
- 从 Authority Pawn/View/规则重算方向；
- trace/collision/nav/surface 约束；
- 验证 SourceInventory 属于 Instigator；
- 验证 SlotHandle/current ItemHandle generation；
- 对世界 Loot 验证距离、LOS、loot ownership、是否已被拿取；
- 对共享/队伍 loot 处理并发和 idempotency。

只检查“世界物品离目标 Inventory 1000 units 内”仍可能允许客户端把物品塞进不属于自己的 Inventory。

## 11. Nested Inventory 是递归对象图

背包套背包不能只 `NewObject<Inventory>` 就结束。至少定义：

- top-level replication owner；
- NestedInventory Outer 与业务 owner；
- registered subobject 递归注册/注销；
- detach/reparent 时何时更换 owner；
- 最大嵌套深度；
- cycle prevention：容器不能装自己，不能形成 A -> B -> A；
- capacity/weight 是否包含子树；
- Save stable ContainerId/ItemId；
- JIP、disconnect/reconnect、parent destroy 的恢复顺序；
- relevancy/owner-only/共享查看者条件复制策略。

若 nested tree 很大，不要无条件把整棵对象图复制给所有连接。按 owner/relevancy 或显式 open-container session 决定数据可见性。

## 12. 资源驻留合同

Struct-first 并不能自动解决资源加载。Definition/Fragment 若包含 soft class/config，Item create、NestedInventory create、DragDrop/UI sound 等热路径仍可能同步加载。

规则保持：

- 启动/进入玩法/打开容器前异步预热必要 bundle；
- transaction 只消费 resident dependency；
- 未就绪返回 Pending/AssetNotReady 或异步 continuation；
- 禁止 Tick、FastArray callback、批量装备/掉落/拖拽循环中 `LoadSynchronous`、`StaticLoadObject`、`FObjectFinder`；
- Editor thumbnail/明确 startup-only path 可以单独评估，不把它推广到 runtime hot path。

Registry 若启动时加载所有 Definitions，要测启动时间与内存；大型内容库可按 bundle/category/lazy registry 切分，而不是把所有软引用一次常驻。

## 13. Query、Tag 与 cache locality

组合 Query 的思路可保留：先 Section，再 Slot，再 Item，让最便宜/最有选择性的谓词先 early-out。

但大量槽位上的复杂 TagQuery/Fragment 查找仍要测。建议：

- 构建 Query 一次后复用，不在 Tick/内层循环重复构造；
- 静态 ItemType/Tags 由 Definition 缓存；
- 高频 ItemHandle -> SlotHandle 反查若已成为热点，可加 compact reverse array/map，并明确 swap/reuse 失效；
- occupancy grid 预计算一次用于一笔 transaction，而不是每格重复 rebuild；
- 不因一个 O(N) TODO 就立刻增加永久 cache，先看调用频率和 N。

## 14. 内存布局审查

高数量热结构优先：

- 小整数/bitfield 放一起并检查实际 `sizeof/alignof`；
- Handle 可用紧凑 32-bit 表示，但位宽必须由容量和 wrap 风险决定；
- ItemData 与 SlotData 分离减少无关 cold 字段进入同一 cache line；
- 避免 FastArray entry 放 `FText`、大型 TagContainer、临时 UI 字段；
- 不用 `#pragma pack` 破坏 UE ABI/反射；
- 使用 Unreal Insights/Memory Insights/Net Insights 做证据。

`alignas` 只有在有明确 ABI/cache 目标并验证收益时使用，不能把“4 字节对齐”机械复制到所有 Handle。

## 15. 从第三方实现吸收时的拒绝清单

看到这些情况必须保留为风险，而不是在 Skill 中写成“已解决”：

- README 明确 ongoing refactor；
- transaction prediction/resync/undo 仍 TODO；
- Undo assert/参数透传存在源码疑点；
- NestedInventory owner/replication 仍留 TODO；
- client drop offset/impulse 注释写明尚未 server clamp；
- runtime `LoadSynchronous` 仍存在；
- component 开启 `bCanEverTick` 但无实际 Tick 行为；
- O(N) reverse lookup 只有 TODO，没有 profile 证据。

样例项目可以证明一种设计方向值得研究，不能替目标项目完成生产验收。

## 16. 验收矩阵

至少覆盖：

1. 5 万简单 stack 的 UObject 数量/GC/复制带宽对照；
2. stale handle：remove/reuse 后旧 generation 被拒绝；
3. Host 本地 move 与 Remote move 的 UI delta 次数一致；
4. JIP 从 ItemData + SlotData 建立完整 View；
5. 两个 client 同时 claim/move 同一 slot；
6. 重复 TransactionID、迟到请求、断线中途 transaction；
7. shared inventory unauthorized pointer/request；
8. client 极端 drop offset/impulse 被服务器 clamp/reject；
9. NestedInventory depth/cycle/reparent/destroy/JIP；
10. runtime dependency 未驻留时没有同步 hitch；
11. Save/load 后 stable ItemId 保持，runtime Handle 可重新分配；
12. FastArray callback/OnRep 顺序下没有空引用或双播。
