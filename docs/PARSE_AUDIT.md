# parse 模块纪律检查报告

> 检查时间: 2026-05-04

---

## 7个核心模块铁律检查

| 模块 | 铁律1 AST | 铁律1 正则 | 铁律3 不确定 | 铁律10 置信度 | 状态 |
|------|-----------|-----------|-----------|-------------|--------------|------|
| parser.py | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| extractors.py | ✅ | ✅ | ⚠️ | N/A | ⚠️ |
| class_utils.py | ✅ | ✅ | ⚠️ | N/A | ⚠️ |
| package.py | ✅ | ✅ | ⚠️ | N/A | ⚠️ |
| interface.py | ✅ | ✅ | ⚠️ | N/A | ⚠️ |
| covergroup.py | ✅ | ✅ | ⚠️ | N/A | ⚠️ |
| pyslang_helper.py | ✅ | ✅ | ⚠️ | N/A | ⚠️ |

---

## 主要发现

### ✅ 符合

1. **铁律1 (AST)** - 所有模块使用 pyslang，无正则分析源码
2. **警告机制** - 有 ParseWarningHandler 提示不支持的语法

### ⚠️ 需要改进

1. **铁律3 (不确定)** - 没有返回 uncertainty 标注
   - parse_file/parse_text 没有返回 confidence 字段
   - 无法知道解析是否完全成功

2. **铁律10 (置信度)** - API 返回没有 confidence 标注
   - 返回 SyntaxTree 但没有置信度
   - 无法判断解析质量

---

## 具体API分析

### parser.py (主解析器)

| API | 返回类型 | confidence | 备注 |
|-----|---------|------------|------|
| parse_file | SyntaxTree | ❌ | 无置信度 |
| parse_text | SyntaxTree | ❌ | 无置信度 |
| get_modules | List | ❌ | 无置信度 |
| get_diagnostics | List | ❌ | 无置信度 |
| has_errors | bool | ⚠️ | 布尔可接受 |

### extractors.py (提取器)

| API | 返回类型 | confidence | 备注 |
|-----|---------|------------|------|
| extract_signals | List | ❌ | 无置信度 |
| extract_modules | List | ❌ | 无置信度 |
| extract_always_blocks | List | ❌ | 无置信度 |

---

## 结论

**parse 模块符合铁律1** (AST优先) ✅

**parse 模块部分符合铁律3/10** ⚠️
- 有错误处理机制 (has_errors, get_diagnostics)
- 但没有返回 confidence 标注
- 对于底层解析器，这可能是可接受的

### 建议

由于 parser 是底层模块，铁律3/10 可以放宽要求。建议:

1. 添加可选的 confidence 返回 (通过参数控制)
2. 在 extractors 中添加 confidence
3. 文档说明 parse 是底层接口，上层模块负责置信度

