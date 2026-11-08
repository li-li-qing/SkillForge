# FastArray删除回调与索引缓存澄清

日期：2026-11-07。只修改UE C++两份参考及新增CPP-123行为规格，没有修改任何UE项目源码。

原文framework-composition-patterns只列Add/Change后重建；arpg-item-inventory-patterns列PreReplicatedRemove清索引，未明确剩余index变化与删除尚未应用。这里存在指导歧义，并非已证实消费工程bug。

官方核验：PreReplicatedRemove页面明确数组元素删除前调用、indices仅当前调用有效。PostReplicatedReceive独立方法页读取失败；使用官方FPostReplicatedReceiveParameters及FFastArraySerializer类型页核验可选钩子在接收端NetDeltaSerialize之后执行，并覆盖未映射引用后续解析。页面当前显示UE5.8，未持有目标引擎源码，未确认其他版本或所有复制路径。

补充合同：删除前记录稳定身份/清投影/令cache失效；删除应用后按实际数组重建或增量修正，包含纯删除批次；临时index/view不跨异步，后续按身份/代次解析；目标支持才使用PostReplicatedReceive，重复回调处理幂等。未规定每次收包全表重建，不把next tick当完成证据，保留Authority本地维护。

来源：
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/NetCore/FFastArraySerializer/PreReplicatedRemove
- https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/NetCore/FFastArraySerializer/FPostReplicatedReceiveParameters
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/NetCore/FFastArraySerializer

新增CPP-123为行为规格，未执行agent评测；未执行UE编译、PIE或网络回归。已执行 python scripts/validate_skills.py skills/skillforge-ue-cpp --self-contained：1技能0错误，1个独立副本通过；这仅验证结构/引用，不代表行为规格通过。

文件哈希：
[
  {
    "file": "skills/skillforge-ue-cpp/references/framework-composition-patterns.md",
    "before": "47432f7935fb0002099a88741bd7dbc9d57c6d240117410954cebdc10ffcd3b1",
    "after": "fb34ae78a86a1b53820555d87fc95dd87b60e052e2492c0ccec0cc95f5967ff8"
  },
  {
    "file": "skills/skillforge-ue-cpp/references/arpg-item-inventory-patterns.md",
    "before": "859797bbfcf850e69906ba2bfec6068f4a112aedd94c3bb463deacf0ef19d6b4",
    "after": "fe33aeb5828c5fca4192577cfe6fb4dd51d6cd0864591dfcc9025f1c65c20532"
  },
  {
    "file": "skills/skillforge-ue-cpp/evals/behavior-cases.json",
    "before": "f8ec13059be9c2f7055298674646b58de7d148f8320186d4285b8c0e01d2969c",
    "after": "4447ade83af63055a00ec0839a38af77b709193920ac948b26be6fd2010eb369"
  }
]
