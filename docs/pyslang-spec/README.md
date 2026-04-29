# pyslang 语法规范

SystemVerilog 语法与 pyslang AST 的完整映射规范。

## 文档列表

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 主规范文档 - 语法分类、节点属性、实际示例 |
| `syntaxkind_mapping.md` | 536个 SyntaxKind 完整映射表 |
| `node_attribute_mapping.md` | 节点属性参考 |

## 辅助工具

位于 `src/pyslang_helper/`

```python
from pyslang_helper import SVParser, extract_all

code = '''
module test;
    input clk;
    output [7:0] data;
endmodule
'''

parser = SVParser(code)
result = extract_all(code)

print(result['modules'])  # 模块信息
print(result['classes'])   # 类信息
```

## 参考

- pyslang: https://pypi.org/project/pyslang/
- slang 文档: https://sv-lang.com/
