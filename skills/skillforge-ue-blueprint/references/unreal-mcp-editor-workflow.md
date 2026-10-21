# UE 5.8 原生 MCP 编辑器工作流

用户已连接 UE MCP 时，先使用实际编辑器能力读取资产、场景和运行实例。UE 5.8 提供实验性的 Unreal MCP（插件标识 ModelContextProtocol）；服务与工具集可分别启用，版本号本身不证明连接和所有工具可用。

## 连接与发现

- 先确认当前工程、Editor 进程和实际连接端点。默认本机 HTTP 端点为 `http://127.0.0.1:8000/mcp`，不把它硬编码成所有工程的地址。
- 工具搜索模式通常只列出 `list_toolsets`、`describe_toolset`、`call_tool` 三个元工具；继续发现所需 toolset，读取当前 schema 后调用。只看到三个工具不等于没有资产或场景能力。
- 检查 ModelContextProtocol、ToolsetRegistry 和当前所需工具集是否加载；AllToolsets 可集合启用工具。已经有可靠连接时沿用，不擅自全量启用插件、重写客户端配置或重启用户工程。
- 连接失败先看服务/端口、日志与插件状态。当前能力允许且需要时用官方 `ModelContextProtocol.StartServer`；工具变化可用 `ModelContextProtocol.RefreshTools` 后重新发现，必要时重连。不要清空未知客户端配置或把本机服务暴露到外网。

## 资产与场景

1. 从准确包路径读取资产、父类、图和组件，再追踪场景放置实例与 PIE 实例。Editor World 和 PIE World、蓝图默认值和实例覆盖分开记录，Actor Label 不作为类身份的证明。
2. 优先调用实际存在的资产/图表/StateTree/动画工具。安全编排工具可以组合已暴露工具，但受限脚本环境不等于可以任意 import unreal；确需官方 Python 时先确认可用的编辑器入口。
3. 修改后读回关键节点、引用和参数，编译受影响蓝图，只保存本轮明确修改的包。不能用字符串替换或猜测二进制修改 `.uasset`。
4. Slate 操作先读取当前窗口与 Snapshot；对当前控件调用 Type/Click。返回 true 只证明输入已接受，随后检查日志、资产或运行结果；不重复使用旧进程的控件引用。
5. 工具支持时做新 PIE 验证。先读取 IsPIERunning；已有用户会话保持原样，空闲且本轮任务已授权运行测试时才启动本轮 PIE，并在结束后停止它。不要为方便验证覆盖未保存地图、保存全部资产或擅自关闭编辑器。

## 工具输出与画面证据

按实际schema和返回结构解码；纯文本工具结果不强行JSON.parse。某种AnimGraph的DSL导出为空，不等于图没有节点：用支持该图类型的列图、find_nodes/get_node_infos等入口交叉核对；工具能力缺口不由猜测连线补齐。

Editor图像、资产thumbnail和游戏viewport截图观察的对象不同。截图前核对World、相机及所需角色；“捕获成功”或Montage时间前进不能证明可见角色动作正确。读原PNG确认实际内容，有争议先重看同一原图，不凭空白/天空/被窗口挡住的画面修改产品。

## 与 C++ 热编译衔接

MCP 可以驱动编辑器，但不自动保证 C++ 已编译/加载。没有直接 Compile 工具时继续检查官方 Slate/控制台或已启用 Python 入口；不能直接断言只能让用户手动关闭 UE。

已有原生函数修改可先检查 Live Coding。反射布局需核对 UHT、重实例化和调用方；新增 MCP Tool 的 UFUNCTION 则按 UE 5.8 官方限制重启。刷新工具列表不能代替 C++ 声明进入运行反射。重载后重新取得对象引用与 schema，再检查新生成实例；旧 PIE 仍运行或包时间戳变化不证明新逻辑生效。

完整 C++ 构建/重实例化职责留在相关 C++ 技能；本技能独立使用时至少交付当前源码、实际加载版本、受影响蓝图和运行验证的分别状态，不宣称仅靠蓝图工具完成了 C++ 构建。

## 依据

[Epic UE 5.8 Unreal MCP](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?application_version=5.8) 及当前安装版本的插件、Toolset schema。接口处于实验阶段，每次以当前能力为准；本参考不把 HCJCGame 的工具命名空间和路径当其他项目默认值。
