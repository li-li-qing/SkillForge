# UE Editor 自动化的真实前提

用于已有PIE被Automation意外结束、跨GI/多LocalPlayer夹具和Editor脚本执行。它不要求普通改动扩展为所有拓扑测试；测试匹配数量、失败/警告与版本关联分别核对。

## 独立Host的输入是否真的独立

检查源码、插件、Content、构建输出及端口的实际路径和Junction/符号链接。宿主源码冻结而Content链接主工程时，新资产仍可能引用宿主没有的原生Struct/类；先核对资产依赖的类型/模块闭包。缺类型告警消失只证明该兼容缺口关闭，不足以解释另一功能失败。同步按实际闭包限定，所有待写成员预检后再应用，不为小宿主复制全工程，也不把Host通过当主工程已加载。

## 先证明实际拓扑

PIE客户端数量不等于同一个GameInstance内的LocalPlayer数量。跨GI/同GI多LP用例应从真实WorldContext、GameInstance、Viewport、LocalPlayer、PlayerController及自动创建的Subsystem关系证明前提；仅NewObject一个LP或native票据不能代替真实消费者。缺少所需角色时先报夹具前置失败，不让产品逻辑背锅，也不把这种拓扑搭建当网络权限验收。

## Automation可改变PIE寿命

UE5.8的`AutomationCommandline`在RunTests路径调用`StopTests`；`AutomationControllerManager::StopTests`在`bKeepPIEOpen=false`时可请求EndPIE。依赖预建PIE的独立测试宿主，先核对当前实现；确需时只对同一个Controller暂存/设置KeepPIEOpen，结束原用例后正常EndPIE、等待World退场并恢复原内存值。不要把这个例外设成用户Main的常驻配置，也不SaveConfig或盲目InitializeStandalone/Shutdown去补角色。

普通测试自己创建PIE时沿其既有生命周期即可。进程退出0、队列空、测试完成与正常清理分别取证；NullRHI只覆盖它能观察的逻辑，渲染/发行目标另验。

## 蓝图可用性按风险取得证据

公开opaque句柄时，C++的operator==不会自动生成蓝图节点。按需提供廉价的BlueprintPure有效性/完整身份比较查询，保留内部字段不可写；两空句柄可相等，形状有效也不授权。关键蓝图接入可用真实K2连线→FKismet编译→生成字节码→实际调用取得证据，普通小改不强制自动生成整套资产。瞬态图成功不替代正式蓝图、LocalPlayer或网络消费。

版本依据：当前引擎的AutomationController/Private/AutomationCommandline.cpp、AutomationControllerManager.cpp，以及真实测试宿主与生成图执行记录。移植到其他UE版本时复核调用和清理路径。
