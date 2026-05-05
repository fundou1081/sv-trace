# sv-trace 开发纪律

> 项目状态: 2026-05-03
> 维护: fsm_analyzer 重构完成

---

## 一、技术路线铁律（不可妥协）

### 铁律 1：AST 唯一数据源

**规则**：所有硬件语义提取（信号追踪、时钟域、控制流、数据流、时序路径、CDC、FSM）必须且仅能通过 **pyslang AST** 遍历实现。**严禁**将 SystemVerilog 源代码转为字符串后用正则表达式分析。

**原因**：正则无法正确处理拼接赋值、宏展开、注释、字符串字面量、位选择、数组索引等。用正则 = 输出不可信。

**验证标准**：代码审查中，任何 `re.findall/re.match/re.search` 作用于 SystemVerilog 源码文本的行为，一律判为违规。

**例外**：仅允许在非语义场景使用正则，如日志格式化、CLI 参数解析、测试框架中的辅助字符串处理。

> ✅ **当前实现**：FSMAnalyzer 完全基于 pyslang AST，re 仅用于 Pragma 解析（注释不在 AST 中，符合例外规则）

---

### 铁律 2：位精确性不可妥协

**规则**：信号追踪必须保留完整的位级信息。`data[7:0]` 和 `data[15:8]` 必须是不同的信号实体。**严禁**截断位选择、位拼接、数组索引。

**原因**：硬件设计的正确性建立在位精确性之上。丢失位信息 = 输出在工程上无意义。

---

### 铁律 3：不可信则不输出

**规则**：当 AST 结构无法被正确解析时（如遇到不支持的 SystemVerilog 语法、AST 节点类型未知），必须显式报错或返回 `confidence: "uncertain"` 并附带详细错误信息。**严禁**静默跳过或返回部分结果。

**原因**：静默吞掉异常 = 错误隐藏。Agent 拿到不完整数据会产生错误推理。

---

## 二、架构铁律（设计约束）

### 铁律 4：模型即契约

**规则**：`models.py` 中定义的每个数据字段，都必须有对应的 AST 遍历代码负责填充。未实现的字段一律删除或标注 `# TODO(version, assignee)`。

**原因**："僵尸字段"消耗维护者的心智，损害 Agent 对数据模型的信任。

---

### 铁律 5：原子化必须保持

**规则**：原子化设计（一个语法节点一个解析器文件）是项目的核心架构选择，不可放弃。但每增加一个原子文件，必须回答：

- 它提供的接口是否可以被已有原子组合替代？
- 它的输出 Schema 是否与同级原子一致？
- 它是否真的独立对应于一个不可再分的硬件语义？

---

### 铁律 6：Schema 即宪法

**规则**：所有模块的输出必须严格遵循 `sv-trace.schema` 定义。Schema 的每次修改，必须同步更新所有相关模块。

---

## 三、开发流程铁律（工程纪律）

### 铁律 7：新功能必须先有边界测试

**规则**：任何新功能（或功能修复），必须同时提交对应的测试用例。

---

### 铁律 8：文档与代码同步更新

**规则**：每次 API 变更、Schema 修改、新增模块，必须同步更新对应文档。

---

### 铁律 9：任何公开承诺必须在代码中可验证

**规则**：README 或文档中的任何性能声明、覆盖率数字、功能支持列表，必须能通过自动化脚本从代码中直接验证。

---

## 四、用户导向铁律（Agent 优先）

### 铁律 10：每次 API 返回必须有置信度标注

**规则**：所有对外 API 的返回值，必须包含 `confidence` 字段和 `caveats` 列表。

---

### 铁律 11：必须提供 Agent 调用示例

**规则**：`skills/` 目录下必须有至少一个完整的 Agent 调用示例。

---

### 铁律 12：速度优化必须在正确性之后

**规则**：任何性能优化（如用正则替代 AST 遍历以提速）**严禁**以牺牲正确性为代价。

---

## 五、金标准测试原则

### 铁律 13：金标准测试（核心分析功能专用）

**规则**：为任何核心分析功能（如 driver/load/connection/dataflow 追踪）添加或重构测试时，必须：

1. **先推导金标准**：脱离被测代码，从 RTL 源码中人工推导正确的信号驱动/负载关系
2. **明确记录**：在测试代码注释中以表格形式记录金标准
3. **对比验证**：运行被测代码，将实际输出与金标准逐项对比
4. **完全一致才能提交**：任何差异都必须修复或合理化，否则提交不得通过

**示例格式**：

```python
# 金标准 (Golden Standard)
# ============================================
# 测试设计: data_out = always_ff 时钟驱动 data_in
# 预期结果:
#   - data_out 的驱动: [data_in] (always_ff)
#   - data_in 的负载:  [data_out] (always_ff)
#   - 无时钟/复位关联
# ============================================
#
# 实际输出必须与上述完全一致
```

**原因**：避免测试被错误的实现带偏。金标准是"真理"，代码输出必须符合真理，而非相反。

---

## 五、核心原则

这 14 条铁律可以归纳为三个核心原则：

1. **AST 是唯一的数据源**。正则不能碰 SystemVerilog 源码。
2. **信息不全等于不可信**。不确定时宁可标 uncertain，也不输出错误结果。
3. **文档与代码同步，承诺与实现一致**。Agent 需要精确的能力地图。

---

## 检查清单（新功能提交流程）

- [ ] 是否使用 pyslang AST 而非正则分析源码？
- [ ] 信号是否保留完整的位级信息？
- [ ] 无法解析时是否返回 confidence: "uncertain"？
- [ ] 数据字段是否都有对应的 AST 填充代码？
- [ ] 数据模型变更是否同步更新 Schema？
- [ ] 新功能是否附带边界测试用例？
- [ ] 新增/修改是否同步更新文档？
- [ ] API 返回是否包含 confidence 和 caveats？
- [ ] 性能优化是否通过正确性验证？

---

## 相关文档

- [ADR-011: 状态机提取](./docs/adr/ADR-011-fsm-extraction.md)
- [IEEE 1800-2017 Section 40.4](./SV_FSM_Recognition.md)
- [pyslang-spec](./docs/pyslang-spec/SKILL.md)

---

## 六、pyslang-spec 参考

### pyslang-spec 子项目说明

项目路径: `docs/pyslang-spec/`

**目的**：显示 pyslang 解析后的 AST 代码范本，为后续功能开发提供参考。

**使用原则**：
- ✅ **可以参考**：查阅 AST 节点结构、SyntaxKind 名称、属性访问方式
- ✅ **可以借鉴**：学习如何遍历 AST、如何处理特定语法结构
- ❌ **禁止直接引用**：不得复制 pyslang-spec 中的代码作为项目功能代码

**原因**：pyslang-spec 是参考文档，不是生产代码。直接引用会导致：
- 代码与项目 Schema 不一致
- 难以维护和追踪
- 违背"模型即契约"原则

**示例学习流程**：

```
1. 在 pyslang-spec 中查找目标 SyntaxKind (如 CaseStatement)
2. 理解其属性结构 (expr, items, caseKeyword 等)
3. 在项目中按相同模式实现解析逻辑
4. 确保输出遵循 Schema 定义
```

---

## 七、检查清单（新功能提交流程）

- [ ] 铁律13: 是否先推导金标准再对比验证？
- [ ] 是否使用 pyslang AST 而非正则分析源码？
- [ ] 信号是否保留完整的位级信息？
- [ ] 无法解析时是否返回 confidence: "uncertain"？
- [ ] 数据字段是否都有对应的 AST 填充代码？
- [ ] 数据模型变更是否同步更新 Schema？
- [ ] pyslang-spec 是否仅作为参考而非直接引用？
- [ ] 新功能是否附带边界测试用例？
- [ ] 新增/修改是否同步更新文档？
- [ ] API 返回是否包含 confidence 和 caveats？
- [ ] 性能优化是否通过正确性验证？

---

## 八、语义层重构方法（Driver/Load/Clock/Reset 通用）

### 背景

项目采用**双层架构**：

```
┌─────────────────────────────────────────────────┐
│  semantic/          → 语义类型定义 (SUPPORTED_KINDS)    │
│  - driver.py       → DriverSignal, NonBlockingAssign  │
│  - clock.py      → ClockSignal               │
│  - reset.py     → ResetSignal             │
│  - base.py      → SemanticItem, SemanticCollector │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  trace/           → 具体分析工具实现          │
│  - driver.py     → DriverCollector (使用semantic) │
│  - clock_domain.py  → CDC 分析              │
└─────────────────────────────────────────────────┘
```

### 重构流程

#### 步骤 1: 定义语义类型（semantic/）

```python
# semantic/driver.py
@dataclass
class DriverSignal(SemanticItem):
    """驱动信号 - 语义类型"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {
        'NonblockingAssignmentExpression',
        'AssignmentExpression',
        'ContinuousAssign',
    }
    signal_path: str = ""
    
    @property
    def is_nonblocking(self) -> bool:
        return self.kind_name == 'NonblockingAssignmentExpression'
```

#### 步骤 2: 实现收集器（semantic/base.py）

```python
# SemanticCollector 自动遍历 AST，通过 SUPPORTED_KINDS 匹配
class SemanticCollector:
    def collect(self, tree, filename):
        for cls in SemanticItem.__subclasses__():
            if cls.matches(node):
                item = cls(node, module_path=...)
                self.items.append(item)
```

#### 步骤 3: 扩展为完整分析（trace/）

```python
# trace/driver.py - 基于 semantic 层增强
from semantic.base import SemanticCollector
from semantic.driver import DriverSignal, NonBlockingAssign

class DriverAnalyzer:
    def __init__(self, use_semantic=True):
        self.collector = SemanticCollector()
    
    def analyze(self, tree, filename):
        self.collector.collect(tree, filename)
        # 增强: 提取 clock/reset/enable
        for driver in self.collector.get_by_type(DriverSignal):
            clock = self._extract_clock(driver)
            reset = self._extract_reset(driver)
            yield Driver(...)  # 兼容模型
```

### 依赖管理原则

| 文件 | 状态 | 说明 |
|------|------|------|
| `semantic/*.py` | ✅ 可引用 | 语义类型定义，无外部依赖 |
| `trace/*.py` | ⚠️ 条件 | 可引用 semantic，需处理 ImportError |
| `core/models.py` | ✅ 保留 | 对外兼容接口 |

### 迁移检查清单

- [ ] 语义类型是否在 `semantic/` 中定义 SUPPORTED_KINDS？
- [ ] trace/ 模块是否优先使用 SemanticCollector？
- [ ] 是否保持对 core/models.py 的兼容？
- [ ] ImportError 是否妥善处理？
