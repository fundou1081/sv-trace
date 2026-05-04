# pyslang AST 结构

本文档记录 pyslang 的 SyntaxKind/TokenKind 与 SystemVerilog 语法的对应关系。

## Interface 模块

### SyntaxKind

| SyntaxKind | SystemVerilog | 提取方式 |
|----------|-------------|---------|
| InterfaceDeclaration | interface...endinterface | node.members 遍历 |
| InterfacePortDeclaration | interface 内的信号声明 | str(node) |
| ModportDeclaration | modport...endmodport | node 完整遍历 |
| ModportItem | modport NAME (ports) | str(node) |
| ModportSimplePortList | output/input NAME | - |
| ModportNamedPort | 单个端口 | IdentifierName 子节点 |
| ClockingDeclaration | clocking...endclocking | node 完整遍历 |
| ClockingItem | clocking 内单项 | - |

### TokenKind

| TokenKind | 说明 | 使用场景 |
|----------|------|
| Identifier | 标识符 (module/信号名) | 从 Token.lexeme 获取 |
| InputKeyword | input | Modport 方向 |
| OutputKeyword | output | Modport 方向 |
| InOutKeyword | inout | Modport 方向 |
| At | @ | Clocking 事件 |
| IdentifierName | 与 Identifier 类似 | - |

## 正确提取模式

### 1. Modport 提取示例

```python
# 收集节点
def collect_nodes(node):
    nodes = []
    def c(n): nodes.append(n); return VisitAction.Advance
    node.visit(c)
    return nodes
all_nodes = collect_nodes(modport_node)

# 遍历找 ModportNamedPort
for n in all_nodes:
    if n.kind == SyntaxKind.ModportNamedPort:
        # 找子节点 IdentifierName
        for child in n:
            if child.kind == SyntaxKind.IdentifierName:
                port_name = str(child)
```

### 2. Clocking 提取示例

```python
# 时钟事件 - 从字符串提取
str_repr = str(node)
match = re.search(r'@(\([^)]+\))', str_repr)
event = '@' + match.group(1) if match else None

# 端口
for match in re.finditer(r'(input|output)\s+(\w+)', str_repr):
    direction = match.group(1)
    name = match.group(2)
```

## 常见问题

### Token vs Syntax
- TokenKind 用于**叶子节点** (Keyword, Identifier, Literal)
- SyntaxKind 用于**语法结构** (Declaration, Statement, Expression)

### 获取节点文本
- `str(node)` - 获取完整文本表示
- `node.name.valueText` - 获取 Identifier 的值 (如果是 Token)
- `node.kind.name` - 获取 kind 名称 (字符串)

### visit() 遍历
```python
tree.root.visit(lambda node: (
    process(node) if condition else VisitAction.Advance
))
```

## AST 检查工具

```python
def dump_ast(node, depth=0):
    """打印节点结构"""
    prefix = "  " * depth
    kind = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    print(f"{prefix}{kind}: {str(node)[:40]}")
    for child in node:
        dump_ast(child, depth + 1)
```

---

**最后更新**: 2026-04-30

## AST 提取限制说明

### pyslang AST 覆盖情况

| 语法 | 是否支持 SyntaxKind | 提取方式 |
|------|---------------------|---------|
| ModuleDeclaration | ✅ | node.members 遍历 |
| InterfaceDeclaration | ✅ | node.members 遍历 |
| ClassDeclaration | ✅ | node.items 遍历 |
| CovergroupDeclaration | ✅ | node.items 遍历 |
| ConstraintDeclaration | ✅ | node.block 遍历 |
| PackageDeclaration | ✅ | node.members 遍历 |
| ModportDeclaration | ✅ | visit() 遍历 |
| ClockingDeclaration | ✅ | node.event 遍历 |
| **Fork/Join** | ❌ 标记 | 特殊处理 |
| **#<time> 延迟** | ❌ 标记 | 特殊处理 |
| **$system 函数** | ❌ 标记 | 特殊处理 |
| **DPI Import** | ✅ | DPIImport |

### 未能直接 AST 化的语法

有些 SystemVerilog 语法**没有专门的 SyntaxKind**，需要通过以下方式处理：

1. **字符串遍历**：使用 `visit()` 遍历提取
2. **混合提取**：AST + 字符串解析组合
3. **完全字符串**：从节点 `str(node)` 提取

```python
# 混合提取示例 (special_syntax.py)
def _extract_system_call(node):
    # 1. 检查 Kind
    if 'FunctionCall' in node.kind.name:
        # 2. 获取完整字符串
        func_str = str(node)
        # 3. 解析函数名
        if '$' in func_str:
            # 提取 $name
            pass
```

### 最佳实践

1. **优先使用 AST**：`node.kind.name`, `node.members`, `node.items`
2. **字符串提取备选**：`str(node)` + 正则解析
3. **混合方案**：先 AST 判断结构，后字符串提取细节

---

**最后更新**: 2026-04-30
