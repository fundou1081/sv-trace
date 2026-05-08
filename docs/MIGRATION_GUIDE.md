# 迁移指南

> 创建时间: 2026-05-08
> 适用版本: v2.0+ (多轮架构)

---

## 概述

sv-trace v2.0 引入多轮架构，将原有的单次 AST 遍历拆分为多个阶段：

| 阶段 | 模块 | 输入 | 输出 |
|------|------|------|------|
| Pass 1 | ScopeBuilder | SyntaxTree | ScopeTree + SymbolTable |
| Pass 2 | Extractors | SyntaxTree + ScopeTree | SemanticGraph |
| Pass 3 | SemanticEnricher | SemanticGraph | EnrichedSemanticGraph |

---

## API 变更

### LoadTracer

**旧 API (v1.x):**
```python
from trace.load import LoadTracer
lt = LoadTracer(verbose=False)
lt.collect(tree, 'file.sv')
loads = lt.find_load('signal')
```

**新 API (v2.0):** ✅ 兼容，底层已重构
```python
from trace.load import LoadTracer
lt = LoadTracer(verbose=False)
lt.collect(tree, 'file.sv')
loads = lt.find_load('signal')
# 输出格式不变
```

### DriverCollector

**旧 API (v1.x):**
```python
from trace.driver import DriverCollector
dc = DriverCollector(parser=parser)
dc.collect(tree, 'file.sv')
drivers = dc.drivers
```

**新 API (v2.0):** ✅ 兼容
```python
from trace.driver import DriverCollector
dc = DriverCollector(parser=parser)
dc.collect(tree, 'file.sv')
drivers = dc.drivers
```

### 新增: 3-Pass 架构

**新 API (推荐):**
```python
from parse import SVParser
from scope import ScopeBuilder
from extractors import SemanticGraph, LoadExtractor
from semantic import SemanticEnricher, AgentContext

parser = SVParser(verbose=False)
tree = parser.parse_text(code)

# Pass 1
builder = ScopeBuilder()
scope_tree, symbol_table = builder.build(tree)

# Pass 2
graph = SemanticGraph(scope_tree, symbol_table)
LoadExtractor(scope_tree, symbol_table, graph).extract(tree)

# Pass 3
ctx = AgentContext()
ctx.set_business_meaning('data', '数据总线')
enriched = SemanticEnricher(graph).enrich(ctx)

# 查询
sig = enriched.get_enriched_signal('data')
print(f"置信度: {sig.confidence}")
print(f"商业含义: {sig.business_meaning}")
print(f"描述: {sig.description}")
```

---

## 废弃 API

### semantic.base.SemanticCollector

**已废弃:** `from semantic.base import SemanticCollector`

**替代:** 使用 trace 层 API 或新的 3-Pass 架构

```python
# ❌ 旧方式 (已废弃)
from semantic.base import SemanticCollector

# ✅ 新方式
from trace.driver import DriverCollector
from trace.load import LoadTracer

# ✅ 或使用 3-Pass 架构
from scope import ScopeBuilder
from extractors import SemanticGraph, LoadExtractor
```

### semantic/driver.py, semantic/load.py 等

**已废弃:** 直接 import semantic 下的模块

**替代:** 使用 trace/ 模块或 extractors/ 模块

---

## AGENT 上下文使用

AGENT 可以通过 AgentContext 为信号填充业务语义：

```python
from semantic import AgentContext, SemanticEnricher

# 创建上下文
ctx = AgentContext()

# 填充业务语义
ctx.set_business_meaning('clk', '系统时钟')
ctx.set_business_meaning('data', '数据总线')
ctx.set_tags('clk', ['clock', 'timing'])
ctx.set_tags('rst_n', ['reset', 'active_low'])
ctx.set_user_note('data', '用户备注: 该信号在复位时应保持 0')

# 执行增强
enriched = SemanticEnricher(graph).enrich(ctx)

# 查询
sig = enriched.get_enriched_signal('clk')
print(f"商业含义: {sig.business_meaning}")
print(f"标签: {sig.tags}")
```

---

## 置信度等级

EnrichedSignal 包含 confidence 字段：

| 等级 | 含义 |
|------|------|
| HIGH | 完全可信 |
| MEDIUM | 部分可信（如跨模块引用） |
| LOW | 可信度低（如复杂表达式） |
| UNCERTAIN | 不可信 |

---

## 测试迁移

### 旧测试写法

```python
from semantic.base import SemanticCollector
from trace.load import LoadTracer

# 测试 SemanticCollector (已废弃)
```

### 新测试写法

```python
from trace.load import LoadTracer

# LoadTracer 底层使用新架构，API 不变
lt = LoadTracer(verbose=False)
lt.collect(tree, 'file.sv')
assert lt.find_load('q') == expected
```

### 3-Pass 测试

```python
from parse import SVParser
from scope import ScopeBuilder
from extractors import SemanticGraph, LoadExtractor
from semantic import SemanticEnricher

parser = SVParser(verbose=False)
tree = parser.parse_text(code)

builder = ScopeBuilder()
scope_tree, symbol_table = builder.build(tree)

graph = SemanticGraph(scope_tree, symbol_table)
LoadExtractor(scope_tree, symbol_table, graph).extract(tree)

enriched = SemanticEnricher(graph).enrich()
assert 'q' in enriched.all_signals
```

---

## 常见问题

### Q: 如何选择使用旧 API 还是 3-Pass 架构？

**推荐:** 
- 简单使用 → 继续用 LoadTracer / DriverCollector（旧 API）
- 需要置信度/业务语义 → 使用 3-Pass 架构

### Q: semantic/ 模块还能用吗？

**⚠️ 警告:** semantic/ 下的模块（base.py, driver.py 等）已废弃，内部重定向到 extractors/。继续使用会收到 DeprecationWarning。

### Q: 如何获取信号的置信度？

```python
# 方式 1: 使用 3-Pass + Enricher
enriched = SemanticEnricher(graph).enrich()
sig = enriched.get_enriched_signal('signal')
print(sig.confidence)  # ConfidenceLevel

# 方式 2: 旧 API 不提供置信度
```

### Q: 如何让 AGENT 填充业务语义？

```python
ctx = AgentContext()
ctx.set_business_meaning('clk', '时钟信号')
ctx.set_tags('clk', ['clock'])
ctx.set_tags('rst', ['reset'])

enriched = SemanticEnricher(graph).enrich(ctx)
```

---

## 迁移检查清单

- [ ] 代码中是否还有 `from semantic.base import`？
- [ ] 代码中是否还有直接 import `semantic.driver`, `semantic.load` 等？
- [ ] 旧 API (LoadTracer, DriverCollector) 是否仍正常工作？
- [ ] 是否需要使用置信度/业务语义功能？
- [ ] 测试是否通过？
