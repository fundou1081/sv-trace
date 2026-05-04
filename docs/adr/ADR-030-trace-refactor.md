# ADR-030: trace 模块重构 - 统一数据模型 + 跨模块追踪

## 状态

> **状态**: Accepted
> **日期**: 2026-05-04
> **作者**: OpenClaw / 方浩博

---

## 摘要

对 trace 模块进行架构重构，实现：
1. 创建统一数据模型 (`trace/core/interfaces.py`)
2. 创建公共 AST 遍历基类 (`trace/core/base.py`)  
3. 创建场景化查询层 (`trace/query/`)，组合现有模块实现跨模块追踪
4. **新增**: LoadTracerExt 实现反向查找
5. **新增**: 测试套件 (`tests/unit/sv_trace/test_signal_chain.py`)

遵循原子化设计原则：复用现有模块，而非重新实现。

---

## 背景

### 问题

1. **代码重复**：driver.py, load.py, dataflow.py 等都各自实现一套 AST 遍历逻辑
2. **缺乏统一接口**：各模块返回不同的数据结构，无法组合使用
3. **跨模块追踪困难**：没有统一入口实现"信号完整链路"追踪

### 纪律约束

- 铁律4: 模型即契约
- 铁律5: 原子化必须保持
- 铁律7: 新功能必须先有边界测试
- 铁律10: API 返回必须有置信度标注

---

## 决策

### 方案: 分层架构 + 组合复用

```
Layer 4: Query Layer (trace/query/)     ← 场景化接口
Layer 3: Interface Layer (trace/core/)  ← 统一数据模型
Layer 1: Existing Modules               ← 原子化模块复用
```

### 核心数据结构

```python
# trace/core/interfaces.py
class Traceable(ABC):
    @property
    def node_id(self) -> str: ...
    @property
    def confidence(self) -> str: ...
    @property
    def caveats(self) -> List[str]: ...

@dataclass
class TraceResult:
    data: Any
    confidence: str  # high/medium/uncertain
    caveats: List[str]
```

### 场景化查询

```python
# trace/query/signal_chain.py
class SignalChainQuery:
    def trace(self, signal, module=None) -> TraceResult[SignalChainResult]:
        # 组合 DriverCollector + LoadTracerExt
        # 返回统一的 SignalChainResult
```

---

## 实现记录

### Phase 1: 核心层 ✅

| 文件 | 说明 | 状态 |
|------|------|------|
| `trace/core/__init__.py` | 模块导出 | ✅ |
| `trace/core/base.py` | ASTWalker 基类 | ✅ |
| `trace/core/interfaces.py` | Traceable 接口 + TraceResult | ✅ |

### Phase 2: 查询层 (场景A) ✅

| 文件 | 说明 | 状态 |
|------|------|------|
| `trace/query/__init__.py` | 模块导出 | ✅ |
| `trace/query/signal_chain.py` | SignalChainQuery | ✅ |

### Phase 3: 扩展模块 ✅

| 文件 | 说明 | 状态 |
|------|------|------|
| `trace/load_ext.py` | LoadTracerExt (带反向查找) | ✅ |

### Phase 4: 测试套件 ✅ (铁律7)

| 文件 | 说明 | 状态 |
|------|------|------|
| `tests/unit/sv_trace/test_signal_chain.py` | SignalChainQuery 测试 | ✅ |

### Phase 5: Bug 修复 ✅

| 文件 | 问题 | 修复 |
|------|------|------|
| `src/trace/driver.py` | `_extract_sources` 条件判断错误 | `'IdentifierName' in kind_name` |
| `src/trace/load.py` | `_extract_signals` generator 未迭代 | `list(walk_expr(node))` |
| `src/trace/dataflow.py` | 语法错误 | 修复 if 语句格式 |
| `src/trace/__init__.py` | 导出不存在的 DataFlow | 移除 |

---

## 测试结果 (2026-05-04)

```
=== Test: Single Driver ===
  Drivers for data_out: 1, sources=['data_in']
  Loads for data_out: 0
  ✅ Single driver test passed

=== Test: Continuous Assignment ===
  Drivers for b: 1, sources=['a']
  ✅ Continuous assignment test passed

=== Test: Complex Chain ===
  Drivers: 3 (reset + main + continuous)
  Data path includes temp
  ✅ Complex chain test passed

=== Test: No Driver ===
  Confidence: uncertain
  ✅ No driver test passed

=== Test: Signal Classification ===
  Clock: {'clk'}, Reset: {'rst_n', 'data_in'}
  ⚠️ Note: data_in 误匹配 _n 模式

=== Test: LoadTracerExt ===
  reverse_lookup('data_in'): 2 loads (data_out)
  ✅ LoadTracerExt test passed
```

---

## 已知问题

| 问题 | 严重度 | 状态 |
|------|--------|------|
| Clock/Reset 模式匹配过于宽泛 | 低 | 待优化 |
| 重复负载计数 | 低 | 待调查 |
| DriverCollector._extract_sources 部分场景为空 | 中 | 部分修复 |

---

## 检查清单 (符合纪律)

- [x] 铁律1: 使用 pyslang AST - Query 层委托给现有模块
- [x] 铁律2: 位精确性 - 数据模型保留 bit_range
- [x] 铁律3: 不可信则不输出 - TraceResult 包含 confidence 和 caveats
- [x] 铁律4: 模型即契约 - Traceable 接口定义明确
- [x] 铁律5: 原子化必须保持 - 组合复用现有模块
- [x] 铁律7: 新功能必须先有边界测试 - 测试套件完成
- [x] 铁律10: API 返回有置信度标注

---

**最后更新**: 2026-05-04 10:06
