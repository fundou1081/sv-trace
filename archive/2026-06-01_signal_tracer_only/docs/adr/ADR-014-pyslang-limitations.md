# ADR-014: pyslang 已知限制

> **状态**: Known Limitations
> **日期**: 2026-04-20

---

## pyslang 解析限制

### 1. HierarchyInstantiationSyntax.type 属性

**问题**: `HierarchyInstantiationSyntax.type` 返回实例名而非模块类型

**示例**:
```systemverilog
module cell;
endmodule

module top;
    cell u0();  // type 应返回 "cell"，实际返回 "u0"
endmodule
```

**影响**: ModuleDependencyAnalyzer 无法获取实例化的模块类型

**状态**: 已知限制，暂无解决方案

---

### 2. EmptyMemberSyntax

**问题**: 空模块声明 `module x();` 被解析为 EmptyMemberSyntax 而非 ModuleDeclarationSyntax

**示例**:
```systemverilog
module empty;  // 空模块，被解析为 EmptyMemberSyntax
endmodule
```

**影响**: 模块遍历时无法识别空模块

**状态**: 已知限制

---

### 3. Generate 块内实例化

**问题**: generate 块内的实例化可能无法被正确识别

**示例**:
```systemverilog
module top;
    genvar i;
    for (i = 0; i < 4; i = i + 1) begin : gen
        cell u_cell();  // 可能无法识别
    end
endmodule
```

**影响**: DriverTracer、ModuleDependencyAnalyzer 可能无法追踪 generate 块内的驱动

**状态**: 待修复

---

*最后更新: 2026-04-20*
