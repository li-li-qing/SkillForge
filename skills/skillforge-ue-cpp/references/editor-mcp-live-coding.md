# UE 5.8 MCP 与 Live Coding 迭代

用于编辑器已开着时加载 C++ 改动、判断是否必须重启，以及验证代码是否真正生效。UE 5.8 及以后优先发现当前工程插件提供的 MCP 与 Live Coding 能力，减少重复手工操作；MCP 是操作入口，实际构建和重载由 UE 完成。

## 先按改动选择

| 当前变化 | 合理入口与完成证据 |
|---|---|
| 已有函数体、普通原生逻辑 | 优先检查 Live Coding。读取构建终态、补丁加载/重载日志，再复测实际调用。 |
| 覆盖基类既有虚函数 | 属于原生 C++ 变化，不因头文件改动就判定为新增反射；用新实例验证虚调用实际派发。 |
| UPROPERTY/USTRUCT/UCLASS 等反射或布局变化 | 检查当前版本的 UHT、Live Coding 重实例化支持与对象缓存清理；支持时可迭代，但须读回真实反射、编译调用方并验证新实例。确认当前加载/重实例化路径不支持，或构建重载成功后运行反射仍旧时，再安排适用的常规构建/重启；编译错误先修源码，功能失败先诊断。 |
| 新增 MCP Tool 的 UFUNCTION | UE 5.8 官方 MCP 文档要求重启编辑器；RefreshTools 不能补出未进入运行反射的声明。已有 Tool 函数体修改可用 Live Coding 后刷新工具。 |
| Build.cs、模块/插件装载或工具链变化 | 依据 UBT 和实际加载限制选择常规构建及重开，不将全部配置变化都假定可热更。 |

“有反射宏就必须关闭”和“开启重实例化就能热更一切”都缺少必要条件。Live Coding 与旧 Hot Reload 不等同；热补丁也不能单独证明下次启动、Game 或 Cook 目标可用，按本次交付目标补适用的普通构建。

## 通过现有 MCP 操作

1. 确认连接的是目标工程的 Editor 进程，记录本轮输入、PIE 是否运行、未保存状态和共用编辑器的使用归属。用户正在使用的 PIE 不由本轮随意停止。
2. 先发现实际 toolsets 并读取 schema。已连接的 MCP 没有直接 Compile 工具，不代表不能使用编辑器提供的 Live Coding 入口。官方 Slate UI 或 Python 控制台可作为当前能力允许的替代入口，不虚构 ExecuteConsoleCommand 工具或工具命名空间。
3. 读取真实 Live Coding 设置，包含 bEnabled、bEnableReinstancing。使用当前版本已确认的入口；本地 UE 5.8 源码注册了异步命令 `LiveCoding.Compile` 和同步命令 `LiveCoding.CompileSync`。由游戏线程处理 MCP 时优先异步发起、再观察终态，避免同步等待阻塞工具服务。
4. UI 路径先取当前窗口和控件引用，再向确认为 Cmd 的输入框发送命令。快捷键或 Type 返回 true 仅表示工具接受输入；没有构建起始日志时先检查焦点、上下文和正确入口，不重复启动竞争构建。
5. 读取 UBT/Live Coding 结果及 Editor 的重载/重实例化结果；失败则保留原始错误。重新发现受影响反射/蓝图节点，按需刷新 MCP 工具 schema；创建新 PIE 或新实例验证本次真实功能。只结束本轮启动的 PIE，保留用户已有工作。

多聊天先确认实际共用的Editor、源码输入、构建输出和端口。同Editor的MCP调用按服务合同依次发起；热编译与依赖该Editor代码稳定的PIE、同包保存等会互相影响的操作，以及同输出的构建需要互斥。不同文件编辑、互不影响的包和输入/输出/端口均隔离的Host不因此整组停工。P4的独立CL不能隔离同工作树的编译输入；运行前只核对受影响输入和真实占用，实际冲突才协调，不每步发送状态或重做全仓快照。临时 Python Remote 只有确需且能力允许时使用，限制在本机，用完恢复本轮改变的设置，不顺手保存项目配置。

## 重载后仍要核验

- 重实例化可能替换对象；已有裸指针、原生缓存与委托绑定不能仅因 UObject 同名就继续使用。维护这些缓存的代码可按当前引擎的 ReloadReinstancingCompleteDelegate、ReloadCompleteDelegate 做失效和重建。
- 热编译后Python旧类包装或snake_case别名可能落后于运行反射。先用原生字段名读取当前UClass/CDO，并按完整类路径重新取得本轮引用；原生反射正确而旧包装失败时先隔离绑定/命名缓存问题，不直接重启或改产品字段迁就包装。若当前原生反射本身仍旧，再回到UHT/重载诊断。
- `.cpp` 构造函数改默认值不能保证既有实例同步变化。分别检查类默认值、蓝图覆盖、关卡实例覆盖和新生成实例；避免保存一个陈旧实例把新默认值覆盖回去。
- 虚函数修正须验证实际虚调用；例如改变实例方向后，眼位查询应沿真实 ActorUp，不能在 ActorUp 仍为世界 +Z 时声称验证了倒挂修正。测试动作限定在本轮 PIE 内，并恢复临时改动。
- 渲染、碰撞、伤害、联机与持久化各看对应运行证据。热编译通过、资产保存、新 PIE 和普通目标构建分别报告。

验证只覆盖本次变化及真实风险，不默认穷举全部目标和运行场景。B 模式下的动画、画面、视频和交互表现，给用户简短操作步骤、观察点及预期，由用户验收；AI 完成所需的构建、加载、数据和网络检查，不为替代人工观感重复搭建采集脚本。已有检查充分且没有新变化或失败时停止扩大验证。

确需关闭时，说明具体原因和证据，例如新增 MCP Tool 声明、当前重实例化未支持的变化、仍旧的运行反射或加载模块限制；沿用已有保存/关闭授权。没有证据时先完成能做的检查，不把反复手工关开变成默认流程。

## 依据与适用边界

- [Epic UE 5.8 Unreal MCP](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?application_version=5.8)：工具发现、注册刷新，以及新增 Tool 声明的重启限制。
- [Epic Live Coding](https://dev.epicgames.com/documentation/unreal-engine/using-live-coding-to-recompile-unreal-engine-applications-at-runtime?application_version=5.8)：重实例化、对象缓存和默认值行为。
- 本地对应引擎的 LiveCodingModule.cpp / LiveCodingSettings.h：命令与设置仍须按当前版本核对。

UE 5.8.3 现场分别验证过原生函数/虚调用热更，以及一次新增反射属性和内部回调后的UHT重实例化、Native/BP CDO读回及新PIE消费。它们证明相应变化在该环境可行，不证明所有反射变更、平台、Cook或网络拓扑都已实测。
