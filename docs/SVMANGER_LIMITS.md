# SVManager 使用限制

## 已确认的限制

### AST 节点 location 属性

 pyslang 对不同类型的节点有不同的位置信息支持:

| 节点类型 | location | 说明 |
|---------|----------|------|
| Keyword (always_ff 等) | ✅ 有 | 关键字有精确位置 |
| Logic (logic 等) | ✅ 有 | 信号类型有位置 |
| ModuleDeclaration | ⚠️ 部分 | 模块声明有位置 |
| AlwaysFFBlock | ❌ 无 | 代码块无位置 |

### 解决方案

1. **对于有 location 的节点**: 直接使用 `node.location.line`

2. **对于无 location 的节点**: 
   - 通过遍历 `node.body` 找到第一个有 location 的子节点
   - 或使用文本匹配

```python
# 获取行号
def get_any_line(node):
    for child in node:
        if hasattr(child, 'location') and child.location:
            return child.location.line
        result = get_any_line(child)
        if result:
            return result
    return None
```

### 建议使用方式

```python
manager = SVManager()
result = manager.parse_file('design.sv')

# 对于有明确位置的元素 (模块、信号定义等)
for module in result.tree.root:
    if module.kind.name == 'ModuleDeclaration':
        line = manager.get_line(...)

# 对于代码块 (always_ff 等)，暂无精确位置支持
```

