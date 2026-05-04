# src/ 源代码拆分分析

> 分析时间: 2026-05-04

---

## 当前 src/ 目录结构

```
src/
├── parse/           # 302个语法解析器
├── trace/          # 28个核心分析工具
├── query/         # 11个查询接口
├── lint/          # 4个代码检查
├── apps/          # 4个应用
├── pyslang_helper # 辅助工具 ⚠️
└── ...
```

---

## pyslang_helper 分析

### 文件位置
`src/pyslang_helper/` - pyslang 封装

### 铁律检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 铁律1 AST | ⚠️ | 使用正则 (3处) |
| 铁律1 允许场景 | ? | 仅用于字符串处理 |

### 正则使用详情 (3处)

| 行号 | 用途 | 是否违反铁律 |
|------|------|-------------|
| 536 | `re.search(r'\[(\d+):0\]')` | ⚠️ 处理维度字符串 |
| 554 | `re.match(r'(\w+)\s*\[(\d+):0\]')` | ⚠️ 处理声明字符串 |
| 585 | `re.search(r'(function\|task)')` | ⚠️ 处理关键字 |

### 分析

这些正则用于处理**字符串表示** (如 `[7:0]`), 不是解析实际 SystemVerilog 代码。

根据铁律1例外条款:
> 仅允许在非语义场景使用正则，如日志格式化、CLI 参数解析

维度字符串 `[7:0]` 是非语义场景，可以接受。但建议改进。

---

## 文档参考结构

```
docs/
├── pyslang-semantic/     # 语义解析用法 (支撑项目)
│   ├── README.md
│   ├── SKILL.md
│   └── SV_UNIQUE.md
│
└── pyslang-ast-ref/    # AST结构参考 (仅供对照)
    ├── README.md
    ├── ast_structure.md
    ├── node_attribute_mapping.md
    └── syntaxkind_mapping.md
```

---

## 源代码结构建议

```
src/
├── pyslang_helper/      # 辅助工具 (直接支撑)
│   └── __init__.py   # 封装 pyslang
│
├── parse/           # 语法解析器 (302个)
│   └── ...
│
└── trace/          # 核心分析工具
    └── ...
```

当前结构已经合理。只需要记录 pyslang_helper 的特殊情况。

---

## 引用检查

| 模块 | 引用 pyslang_helper |
|------|-----------------|
| parse/__init__.py | ✅ 1处 |
| 其他 | 0处 |

---

## 结论

### ✅ 已符合

1. **文档拆分** - docs/pyslang-semantic/ vs docs/pyslang-ast-ref/
2. **源代码结构** - 已经按功能分离

### ⚠️ 需注意

1. **pyslang_helper** - 使用3处正则，处理字符串可接受
2. **引用** - 仅1处引用 (parse/__init__.py)

### 建议

1. 记录 pyslang_helper 的特殊情况到 docs
2. 考虑移除正则，改用 AST 遍历

