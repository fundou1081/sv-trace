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
