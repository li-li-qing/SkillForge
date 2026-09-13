# 初始化与通信

## 分开三个问题

“引用非空”“类型正确”“数据可用”不能互相替代。拿到对象后仍需确认它属于当前玩家、Pawn、世界和界面会话；Cast 失败应沿引用来源检查，不能盲目增加 Cast 或 Delay。

| 条件 | 检查依据 | 常见处理 |
|---|---|---|
| 来源对象尚未创建 | 当前创建入口、所属玩家、生命周期日志 | 由创建者传入引用或等待真实就绪事件 |
| 对象已存在但数据迟到 | 数据初始化/复制完成条件 | 加载状态、读取当前快照并订阅变化 |
| 来源已更换 | Pawn/组件/请求标识 | 解除自己在旧来源上的绑定，再绑定新来源 |
| 界面重开或复用 | 现有 UI 框架打开/关闭协议 | 幂等绑定；补读当前状态，避免只等待未来事件 |

界面对象初始化与每次显示/激活并不总是同一生命周期。先检查项目的 UI 管理方式，选择合适的初始化与清理入口；普通隐藏不必然触发 Destruct。

## 背包 Widget 的节点说明示例

下面是**建议的新建函数与变量**，不是声明它们在项目中已经存在，也不是引擎内置背包 API。把来源类型和更新通知映射到项目当前接口；没有对应通知时先定义需要的就绪契约。

- 变量 `InventorySource`：项目的库存组件对象引用或现有接口类型；默认 None。
- 变量 `BoundSource`：当前实际绑定的来源对象引用，用于辨别旧来源。
- 自定义函数 `SetInventorySource(NewSource)`：在创建者确认来源后调用；也用于玩家/Pawn 更换。
- 自定义事件 `HandleInventoryChanged`：签名匹配来源的实际更新 Dispatcher，调用项目已有快照读取与界面刷新逻辑。

执行流：

1. 创建界面的拥有者用正确的 Owning Player 创建 Widget；来源可用后调用 `SetInventorySource`，不要依赖某个全局玩家序号替所有场景找对象。
2. 在 `SetInventorySource` 中比较 `NewSource` 与 `BoundSource`。同一来源且已绑定时不重复绑定，但仍可刷新当前快照。
3. 来源变化时，对有效 `BoundSource` 解除**本 Widget 自己的处理事件**，清空旧状态；不无条件 Unbind All。
4. 将 `NewSource` 数据引脚接到引用设置和 `Is Valid` 检查。有效执行分支绑定匹配的更新事件并立即读取快照；无效分支显示“等待数据/来源不可用”，由真实就绪事件重新进入，不永久停在 DoOnce 后。
5. 关闭或结束当前会话时按项目协议解绑自己的事件；再次打开和来源变更时重新同步。快照与订阅顺序按当前数据源的事件契约处理，避免丢掉首次状态或重复绑定。

调用函数、事件和 Target 引脚均需按实际类型核对。若只能访问接口而 Dispatcher 在具体类上，不凭空在接口引脚上绑定它，应通过已有的订阅服务或明确的实现契约连接。

## Construction Script 的适用边界

本机 UE 5.7.4（CL 51494982）中，`Engine/Source/Runtime/Engine/Private/Actor.cpp` 的 `FinishSpawning` 会进入 `ExecuteConstruction`；`ActorConstruction.cpp` 的构造流程可进入 `ProcessUserConstructionScript` / `UserConstructionScript`。这证明它不能当作仅编辑器逻辑。

编辑器重建、动态生成、从关卡加载及 cooked 构造结果并非相同路径。可重建的组件配置或预览适合按构造流程处理；运行期玩家数据、外部订阅和业务提交应由对应的运行生命周期管理。不要把 Construction Script 或 BeginPlay 当作所有依赖都就绪的证明。

[Epic Actor Lifecycle 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-actor-lifecycle) 可用于查找整体路径；本次 5.7 判断依据上述本机源码，官方当前页读取时为 5.8。目标版本不同需复核。

验证覆盖首次打开、数据迟到、重复打开、来源切换、销毁与新建；只有任务本身涉及多人时，再按实际网络角色验证所属玩家和复制时序。
