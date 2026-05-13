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

---

## 九、测试管理铁律

### 铁律 14：测试分层强制化

**规则**：每个工具的测试必须放在 `tests/unit/tools/` 下的独立文件中，遵循：
- `test_{tool_name}.py` 命名（如 `test_driver.py`）
- 文件内按功能分类：`class Test{Component}`
- 包含三层用例：**基础用例 → 边界用例 → 真实项目用例**

**目录结构**：
```
tests/
├── unit/tools/          # 工具单元测试
│   ├── test_driver.py
│   ├── test_load.py
│   ├── test_signal_chain.py
│   └── ...
├── integration/         # 集成测试
└── e2e/               # 端到端测试
```

---

### 铁律 15：工具必须有独立 Test Plan

**规则**：每个工具模块必须有一个对应的 `.testplan.md` 文件，内容包括：
1. **工具定位**：功能说明、核心 API
2. **测试覆盖矩阵**：功能点 → 测试用例 → 边界/异常
3. **金标准用例**：至少 3 个可验证的正确输出示例
4. **通过标准**：量化指标（如覆盖率、错误率）

**Test Plan 命名**：`{tool_name}.testplan.md`

**示例**：`tests/docs/driver.testplan.md`

---

### 铁律 16：统一 Test Runner

**规则**：项目必须提供统一的测试入口，不允许手动 PYTHONPATH 运行：
- `Makefile` 包含 `make test` 等标准目标
- `pytest.ini` 包含 testpaths 和 markers
- CI 必须能通过 `make test` 执行全部测试

---

### 检查清单（测试管理）

- [ ] 铁律14: 工具测试是否在 `tests/unit/tools/` 下独立文件？
- [ ] 铁律15: 是否为每个工具创建了 `.testplan.md`？
- [ ] 铁律16: 是否可通过 `make test` 运行全部测试？
- [ ] 测试是否包含：金标准推导 → 对比验证 → 边界覆盖？
- [ ] 是否满足：基础用例 + 边界用例 + 真实项目用例？

---

### 铁律 17：提取逻辑封装为独立 Visitor 类

**规则**：语义提取逻辑必须封装为独立的 `pyslang.SyntaxVisitor` 子类，不能分散在 `__post_init__` 中。

**原因**：
- **单一职责**：将 AST 遍历与语义建模分离
- **可测试性**：Visitor 类可单独单元测试
- **可维护性**：修改提取逻辑不影响 SemanticItem 数据结构
- **性能**：避免重复遍历 AST

**正确方式**：
```python
# semantic/clock.py
class ClockExtractor(pyslang.SyntaxVisitor):
    """时钟/复位提取器"""
    
    def on_AlwaysFFBlock(self, node):
        # 提取时钟信号
        ...
    
    def on_EventControl(self, node):
        # 提取事件控制
        ...


# SemanticItem 只负责语义建模
@dataclass
class AlwaysFFItem(SemanticItem):
    """时序块语义"""
    SUPPORTED_KINDS: ClassVar[Set[str]] = {'AlwaysFFBlock'}
    
    clock: str = ""
    reset: str = ""
```

**错误方式**（不允许）：
```python
# 在 __post_init__ 中提取 - 违反铁律
def __post_init__(self):
    self._extract_clock_reset()  # 分散的处理逻辑
```

**实施检查**：
- [ ] semantic/clock.py 中是否有 `ClockExtractor` 类？
- [ ] semantic/driver.py 中是否有 `DriverExtractor` 类？
- [ ] 提取逻辑是否与 SemanticItem 分离？

---

### 铁律 18：Extractor 设计原则

**规则**：所有语义提取器必须：
- 继承 Extractor 基类
- 接收 ScopeTree 作为构造参数
- 使用 pyslang.visit() 遍历
- 输出结果写入 SemanticGraph

**原因**：
- **可测试性**：Extractor 可独立于其他模块测试
- **可组合性**：多个 Extractor 可并行执行
- **职责分离**：Extractor 只负责 AST 遍历，不做语义增强

**正确方式**：
```python
class LoadExtractor(Extractor):
    def __init__(self, scope_tree: ScopeTree, symbol_table: SymbolTable):
        super().__init__(scope_tree, symbol_table)
    
    def extract(self, tree: SyntaxTree) -> None:
        def visitor(node):
            self._on_node(node)
            return pyslang.VisitAction.Advance
        tree.root.visit(visitor)
```

**错误方式**：
```python
# 直接接收 parser 或 tree，不接收 ScopeTree
class BadExtractor:
    def __init__(self, parser):  # ❌
        self.parser = parser
```

---

### 铁律 19：ScopeTree 即上下文

**规则**：所有跨作用域的引用解析必须通过 ScopeTree，不得在 Extractor 内部手动实现作用域查找。

**原因**：
- **统一性**：所有引用解析逻辑集中在 ScopeTree
- **可维护性**：修改作用域规则只需改一处
- **正确性**：避免各 Extractor 实现不一致

```python
class LoadExtractor(Extractor):
    def extract(self, tree: SyntaxTree) -> None:
        # 引用解析通过 symbol_table
        ref = self.symbols.resolve_reference("data", current_scope)
        # 不手动实现：不要在这里写 scope 查找逻辑
```

---

### 铁律 20：多轮执行纪律

**规则**：
- Pass 1 (ScopeBuilder) 必须先于所有 Extractor 执行
- Extractor 之间不得有依赖关系（可并行执行）
- QueryInterface 是唯一对外接口

**原因**：
- **正确性**：Extractor 依赖 ScopeTree 的上下文信息
- **性能**：无依赖的 Extractor 可并行加速
- **清晰性**：数据流方向明确

**执行顺序**：
```
Pass 1: ScopeBuilder → ScopeTree + SymbolTable
          ↓
Pass 2: Extractors (可并行)
          ↓
Pass 3: SemanticEnricher → EnrichedSemanticGraph
          ↓
Pass 4: QueryInterface → 对外 API
```

---

### 铁律 21：Semantic 层定位

**规则**：semantic/ 是语义增强层，消费 extractors 输出的 SemanticGraph，不得直接遍历 AST。

**原因**：
- **职责分离**：AST 遍历由 extractors 负责，semantic 层专注语义增强
- **AGENT 友好**：semantic 层提供 AGENT 填充业务语义的接口

**正确方式**：
```python
# semantic/enricher.py
class SemanticEnricher:
    def __init__(self, base_graph: SemanticGraph):
        self.graph = base_graph  # ✅ 消费 SemanticGraph
    
    def enrich(self, agent_context: AgentContext = None) -> EnrichedSemanticGraph:
        # 在 SemanticGraph 基础上做增强
        ...
```

**错误方式**：
```python
# ❌ semantic 层直接遍历 AST
class BadEnricher:
    def enrich(self, tree: SyntaxTree):  # ❌ 接收 SyntaxTree
        tree.root.visit(...)  # ❌ 直接遍历
```

---

### 铁律 22：Enricher 置信度

**规则**：SemanticEnricher 必须为每个信号标注 confidence 和 caveats，不得输出不可信的原始数据。

**原因**：
- **铁律 3 延续**：不可信则不输出
- **AGENT 友好**：AGENT 需要知道数据的置信度才能正确决策

```python
@dataclass
class EnrichedSignal:
    raw: SignalRef
    confidence: ConfidenceLevel  # high / medium / low / uncertain
    caveats: List[str]         # 不确定项说明
    
    def __post_init__(self):
        if self.confidence == ConfidenceLevel.UNCERTAIN and not self.caveats:
            raise ValueError("uncertain 信号必须提供 caveats")
```

---

### 铁律 23：pyslang-ast-ref 禁止引用

**规则**：`src/pyslang-ast-ref/` 目录下的参考代码仅供学习，严禁在任何生产代码中 import。

**原因**：
- 该目录为"AST 节点参考范本"，不代表生产级实现
- 直接引用会导致架构混乱

---

### 铁律 24：方案评估与用户确认（实施前置）

**规则**：任何新增、修改、修复功能，在开始实施前必须完成以下评估流程：

1. **代码现状评估**：
   - 盘点项目中已实现的相关代码
   - 分析现有实现的边界和能力
   - 识别可复用的模块和接口

2. **架构符合性评估**：
   - 对照 `docs/ARCHITECTURE.md` 分析功能应属于哪一层
   - 判断是否需要新增模块或修改现有模块
   - 评估对架构的影响范围

3. **理想方案推导**：
   - 基于代码现状和架构约束，推导**理想方案**
   - 理想方案应是：正确性、完整性、可维护性的最优平衡
   - 明确标注方案的限制和假设

4. **用户确认后才实施**：
   - 将**现状分析**、**理想方案**、**推荐方案**呈现给用户
   - 与用户讨论方案的利弊和优先级
   - **获得用户明确确认**后再开始编码

**原因**：
- 避免基于不完整的现状理解做决策，导致返工
- 架构一致性需要全局视角
- 用户对需求的理解可能与实现者不同，需要对齐
- 理想方案 vs 可行方案需要用户参与决策

**示例**：

```
用户需求：支持多驱动检测

评估报告：
1. 代码现状：
   - DriverCollector 已实现 always_ff/always_comb/continuous 驱动提取
   - 尚未实现多驱动聚合和冲突判定
   - 已有 CDCAnalyzer 可检测多时钟问题

2. 架构位置：
   - 应属于 trace/ 层，在 DriverCollector 之上
   - 需要使用 SemanticGraph 的 drivers 信息

3. 理想方案：
   - DriverCollector 标记每个信号的多个驱动点
   - MultiDriverDetector 聚合并判定冲突
   - 输出包含冲突报告和时钟关系

4. 推荐方案 vs 用户确认：
   - 简化版：仅检测 case 语句多分支（推荐）
   - 完整版：检测 always 块 + case + 跨模块
   - [ ] 请确认采用哪个方案？
```

---

## 检查清单（更新版）

### 多轮架构检查

- [ ] 铁律 18：Extractor 是否继承 Extractor 基类并接收 ScopeTree？
- [ ] 铁律 19：引用解析是否通过 symbol_table？
- [ ] 铁律 20：ScopeBuilder 是否在 Extractor 之前执行？
- [ ] 铁律 21：semantic/ 是否消费 SemanticGraph 而非直接遍历 AST？
- [ ] 铁律 22：EnrichedSignal 是否包含 confidence 和 caveats？
- [ ] 铁律 23：是否没有 import pyslang-ast-ref？

### 新功能检查

- [ ] 是否使用 pyslang AST 而非正则分析源码？
- [ ] 信号是否保留完整的位级信息？
- [ ] 无法解析时是否返回 confidence: "uncertain"？
- [ ] 数据字段是否都有对应的 AST 填充代码？
- [ ] 新功能是否附带边界测试用例？
- [ ] API 返回是否包含 confidence 和 caveats？
- [ ] pyslang-ast-ref 是否仅作为参考而非直接引用？
- [ ] 铁律 24：是否已进行方案评估并获得用户确认？

### 迁移检查（从旧架构）

- [ ] semantic/ 模块是否已迁移为 SemanticEnricher？
- [ ] trace/load.py 是否已迁移为 extractors/load.py？
- [ ] 是否已删除 pyslang-ast-ref/？
- [ ] 是否已清理冗余文件？
- [ ] ScopeBuilder 是否能正确处理所有 scope 类型？

---

## 架构迁移说明

### 旧架构 vs 新架构

| 组件 | 旧架构 | 新架构 |
|------|--------|--------|
| AST 遍历 | semantic/base.py (SUPPORTED_KINDS) | extractors/ (独立 Extractor) |
| 作用域 | 无 | scope/builder.py → ScopeTree |
| 语义建模 | semantic/*.py (__post_init__) | extractors/ → SemanticGraph |
| 语义增强 | 无 | semantic/enricher.py → EnrichedSemanticGraph |
| AGENT 接口 | 无 | semantic/agent_interface.py |

### 迁移原则

1. **不破坏现有功能**：在 trace/ 层保留兼容接口，内部调用新架构
2. **逐步迁移**：每个模块独立迁移，完成后验证
3. **文档同步**：迁移完成即更新对应文档

---

## 相关文档

- `docs/MULTI_PASS_ARCHITECTURE_PLAN.md` - 详细迁移计划
- `STRUCTURE.md` - 项目结构
- `docs/pyslang-spec/` - pyslang AST 参考
