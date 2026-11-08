# UE 二进制专项
以匹配版本源码、生成代码与目标字节交叉验证；以下是分析方法，不是跨版本偏移表。UE4/UE5 的差异不能仅由主版本概括：小版本、定制分支、平台 ABI、编译优化和资源格式均可能变化。
## 版本与构建矩阵
记录引擎版本证据（符号、版本字符串、build-id/PDB、注册代码、项目配置），主/次/补丁或版本区间、平台/位宽/ABI、Development/Shipping、符号剥离、LTO、匹配源码/PDB。一个 libUE4.so/libUnreal.so 文件名只是线索。
没有符号不等于没有反射；有类名不等于全部字段保留。Shipping 可能裁剪编辑器 metadata；LTO 可能合并/内联注册和实现。UProperty→FProperty/FField 的历史演变需核对应源码，不能机械宣布所有新版本完全不存在 UProperty，UPROPERTY 宏也不是 C++ UProperty 类型。
## 类型与机制检索表
| 主题 | 在有权访问的匹配引擎源码中检查 | 二进制证据 |
|---|---|---|
| UObject | CoreUObject 的 UObject 定义、身份/outer/class 契约 | 构造、注册、类引用，不能硬套对象偏移 |
| UClass/UStruct | UObject/Class.h、继承和字段描述 | 类型注册/父类关系/成员访问 |
| UFunction | FunctionFlags、native 函数与 script 数据 | 注册 thunk、标志和真实调用路径 |
| FProperty/FField | UnrealType.h、Field.h 与版本演变 | 字段类型、owner、偏移/宽度/bit mask |
| UObject 对象集合 | 对应分支对象管理实现 | 多个一致结构约束，不只一个特征码 |
| UHT | 该构建生成的 .gen.cpp 与注册代码 | Z_Construct 等符号仅为线索，裁剪后可能不留名称 |
| Blueprint | 版本匹配字节码枚举/执行器与资产 | script 数据、native thunk、字节码/资产相互引用 |
| Actor/ActorComponent | Engine 的 Actor/组件生命周期与复制设置 | 构造、owner、函数/属性注册、调用 |
| UWorld/ULevel | Engine 的世界/关卡实现与生命周期 | 引用关系、实例切换和访问路径 |
| RPC | flags、生成包装、调用空间/网络实现 | 标志+注册/调用链+可选运行证据 |
| 属性复制 | lifetime 注册、条件、legacy/Iris/Push Model | 属性标志、注册路径及实际更新，资格不等于已发送 |
| 序列化 | Archive、对象保存加载、网络/包格式分别检查 | 输入输出、字段读写，磁盘与内存偏移不等价 |
| 游戏模块 | Build.cs/链接信息/PDB/注册 package | 单体链接中模块不一定独立 DLL |
| 虚函数/接口 | this 调整、vtable 与接口 dispatch | 真实调用点和候选目标集合 |

## 按问题取证
类归属：注册包/类描述 → UFunction owner 候选 → thunk/实现地址 → xrefs；只有字符串相邻不足以确认为类成员。
对象类型：对象 class 关系、构造/虚表、独立实例和使用契约共同支持。不要把 FField 描述实例当 UObject。
成员偏移：注明对象/基类子对象基准、字节偏移、访问宽度、bitfield mask 和指令地址。伪代码数组索引先转成字节并核对类型宽度。
RPC：Server/Client/_Implementation 名字不是充分证据；结合匹配版本 flags 位值、生成 thunk 和网络分派。RPCId 不是所有版本通用识别器。旧版本 _Validate 规则不强推到全部 UE5。
复制：记录 flags、lifetime 注册/条件、对象复制资格、运行时代码；OnRep 名字和 Serialize 调用不能独自证明复制。记录是否验证过网络行为。
原生/Blueprint：区分原生实现、Blueprint 实现及相互调用。ProcessEvent 不是所有原生调用的总入口。缺资产时不能排除 Blueprint 参与。
资源：只读取已授权资产；核版本、压缩/加密状态、包与 IoStore/PAK 实际配置；不假定 UE4=PAK、UE5=IoStore，不默认解密或重打包。
无符号策略：从导出/字符串/构造/虚表/UHT 注册入手，用匹配源码局部比对；未知部分标未知，不以搜索未命中证明不存在。

## 专项报告与验证
每项答案都记录 hash、版本依据、地址/RVA、函数、xrefs、结构体/偏移、指令/伪代码、置信度和未决项。复用报告模板。
建议自有 fixture 含 Actor、组件、普通 native 函数、Blueprint 可覆盖事件、条件复制属性、RPC；保存源码/生成代码/PDB与配置，对 Development/Shipping 分别验证。没有 fixture 时只做证据表演练，不能写真实游戏验证通过。
## 官方资料
最后核实 2026-11-07。官方语义可信，不代表目标布局已验证。
- [UHT](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-header-tool-for-unreal-engine)：当前正文；旧版工具实现另核。
- [UFunction 5.5](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/CoreUObject/UObject/UFunction?application_version=5.5)、[FProperty 5.5](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/CoreUObject/UObject/FProperty?application_version=5.5)：本轮只核实官方摘要，目标源码未取得。
- [RPC](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-procedure-calls-in-unreal-engine)、[属性复制](https://dev.epicgames.com/documentation/en-us/unreal-engine/replicate-actor-properties-in-unreal-engine)、[组件复制](https://dev.epicgames.com/documentation/en-us/unreal-engine/replicating-actor-components-in-unreal-engine)：在线文档，执行表和实现以目标版本全文为准。
- [awake UE 页面](https://github.com/zahidaz/awake/blob/main/docs/reversing/frameworks/unreal-engine.md)：第三方 Android Wiki，仅作线索；不采纳其通用布局/完整反射假设或占位虚表偏移。
