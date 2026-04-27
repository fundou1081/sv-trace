# sv-ast 测试套件

## 定位
基于 pyslang 的 SystemVerilog AST 解析工具库

## 对应源码
- `src/parse/` - 解析器核心
- `src/core/` - 核心数据模型

## 测试文件

| 文件 | 测试内容 |
|------|----------|
| test_parse.py | SVParser 基础解析 |
| test_class.py | Class/constraint 提取 |
| test_all.py | 全面功能测试 |

## 运行测试
```bash
cd tests/unit/sv_ast
PYTHONPATH=../../src python3 test_*.py
```
