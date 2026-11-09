# C++ 类恢复实案（教学合成证据）
此例不是实际样本实测。假设 Windows x64、MSVC ABI、未发现继承，所有地址是教学 IDB VA：
- 0x140001000 构造函数将 0x140004000 写到 [rcx]，把 edx 写到 [rcx+8]。
- 0x140001080 读取 dword ptr [rcx+8] 并返回 eax。
- 0x140001100 将 r8 指针写到 [rcx+0x10]。
- 0x140002000 分配 0x18 字节后调用构造函数；需要核对是否为对象独占分配。
- 0x140004000 表项指向合法 executable segment，相关间接 call 使用 [rax+8]；仅凭连续地址还不能确认虚表。

候选输出（名称为分析者命名）：
```cpp
#include <cstddef>
#include <cstdint>
// 教学候选布局：Windows x64；真实使用前验证 ABI 和对象起点。
struct CandidateObject {
    void** vptr;                  // 0x00：构造写入的虚表候选。
    std::uint32_t value;          // 0x08：读写宽度已约束，业务含义未知。
    std::uint8_t unknown_0c[4];   // 0x0c：可能为对齐或未知字段。
    void* linked_object;         // 0x10：指针宽度写入，目标类型未确认。
};
static_assert(offsetof(CandidateObject, linked_object) == 0x10);
static_assert(sizeof(CandidateObject) == 0x18);
```
sizeof 与分配大小相符只支持该布局，不证明字段语义。验证：找到额外 getter/setter、检查构造/析构各阶段 vptr、捕获独立实例动态地址与成员写入、核对调用方 this 是否已调整。不要使用这份教学地址修改任意 IDB。

多继承可能包含多个 vptr 与 this-adjusting thunk；虚继承与 MSVC vtordisp/vbtable、Itanium vtable prefix 不能混用。RTTI 可能关闭或被剥离；析构函数可能包含多个编译器变体。先记录子对象偏移，再推测继承，不能将所有 this+offset 访问扁平化。
没有 RTTI 时使用大小、构造写入、虚调用索引、成员访问宽度和生命周期合并候选。应用结构体以前保留原类型并记录范围；重要变更按已授权流程。
