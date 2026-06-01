# pyslang AST 编码参考

> 本目录仅提供 AST 结构参考，不可直接引用

## 定位

显示 pyslang 解析后的 AST 代码范本，供对照参考。

## 内容

| 文件 | 用途 |
|------|------|
| ast_structure.md | AST 节点结构 |
| node_attribute_mapping.md | 节点属性映射 |
| syntaxkind_mapping.md | SyntaxKind 映射 |

## 使用原则

✅ **可以**:
- 查阅 AST 节点结构
- 理解 SyntaxKind 名称
- 学习如何遍历 AST

❌ **禁止**:
- 直接引用文档中的代码作为项目代码
- 复制示例到生产代码

详见: [DEVELOPMENT_DISCIPLINE.md](../DEVELOPMENT_DISCIPLINE.md) 第七节

## 为什么分开

pyslang-spec 原文档包含两类内容:
1. **语义解析用法** - 直接支撑项目功能 → pyslang-semantic/
2. **AST 结构参考** - 仅供对照参考 → pyslang-ast-ref/

