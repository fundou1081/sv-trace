# 多轮架构迁移计划

> 创建时间: 2026-05-08
> 更新时间: 2026-05-08
> 状态: 讨论完成，待执行

---

## 讨论结论

| 议题 | 结论 |
|------|------|
| Phase 0 | 先建立骨架 |
| pyslang-ast-ref/ | 直接删除 |
| semantic/ | 保留，但重新设计为**语义增强层**（消费 extractors 输出） |
| 优先级 | Phase 0 → Phase 1 → Phase 2 → 其他 |

---

## 目标架构

### 整体分层

```
┌─────────────────────────────────────────────────────────────┐
│  Parse (pyslang)                                           │
│  输入: .sv 源码 → 输出: SyntaxTree                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 1: ScopeBuilder                                       │
│  输入: SyntaxTree → 输出: ScopeTree + SymbolTable           │
│  - 模块/接口/program 定义边界                               │
│  - 过程块 (always_ff/comb/always) 边界                     │
│  - generate/genvar 作用域                                   │
│  - 实例层级 (module → instance → sub_instance)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Pass 2-N: Extractors (可并行)                             │
│  输入: SyntaxTree + ScopeTree + SymbolTable                 │
│  输出: SemanticGraph                                        │
│  - LoadExtractor     → 负载关系                             │
│  - DriverExtractor   → 驱动关系                             │
│  - ConnectionTracer  → 端口连接                             │
│  - ClockExtractor    → 时钟域                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Semantic Enricher                                          │
│  输入: SemanticGraph + AgentContext                         │
│  输出: EnrichedSemanticGraph                                │
│  - 置信度评估                                              │
│  - 自然语言描述生成                                         │
│  - caveats 标注                                            │
│  - AGENT 填充 business_meaning / tags / user_notes         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  QueryInterface (对外 API)                                  │
│  - find_load(sig, scope?)                                  │
│  - find_driver(sig, scope?)                                │
│  - find_cross_module_path(src, dst)                        │
│  - resolve_alias(sig)                                       │
│  - get_enriched_signal(sig)  → 含 AGENT 增强信息            │
└─────────────────────────────────────────────────────────────┘
```

### 核心数据结构

```python
# scope/models.py
@dataclass
class ScopeInfo:
    scope_id: str                     # "top.u_dut.always_ff_0"
    kind: str                        # MODULE / ALWAYS_FF / ALWAYS_COMB / GENERATE / ...
    parent_scope: Optional[str]
    declared_signals: Dict[str, 'SignalDecl']
    port_map: Dict[str, str]
    instance_of: Optional[str]        # 模块名（如果是实例）

@dataclass
class SignalRef:
    signal_name: str
    resolved_scope: str
    resolved_name: str
    ref_context: str                  # ALWAYS_FF / ALWAYS_COMB / ASSIGN / ...
    is_lhs: bool

# semantic/models.py
@dataclass
class EnrichedSignal:
    raw: SignalRef                   # 来自 extractors
    
    # Enricher 自动填充
    confidence: str                   # high / medium / low / uncertain
    description: str                  # 自然语言描述
    caveats: List[str]                # 不确定项
    
    # AGENT 填充
    business_meaning: str             # 商业含义
    tags: List[str]                   # 标签
    user_notes: str                  # 用户备注

# semantic_graph.py
class SemanticGraph:
    signals: Dict[str, SignalRef]
    loads: Dict[str, List[LoadPoint]]
    drivers: Dict[str, List[DriverPoint]]
    connections: List[Connection]
    scope_tree: ScopeTree
```

### Semantic Enricher 设计

```python
# semantic/enricher.py
class SemanticEnricher:
    def __init__(self, base_graph: SemanticGraph):
        self.graph = base_graph
    
    def enrich(self, agent_context: 'AgentContext' = None) -> 'EnrichedSemanticGraph':
        """用 agent 上下文增强语义图"""
        enriched = {}
        for sig in self.graph.all_signals:
            raw = self.graph.get_signal(sig)
            enriched[sig] = EnrichedSignal(
                raw=raw,
                confidence=self._assess_confidence(raw),
                description=self._generate_description(raw),
                caveats=self._assess_caveats(raw),
                business_meaning=agent_context.get(sig) if agent_context else "",
                tags=agent_context.get_tags(sig) if agent_context else [],
            )
        return EnrichedSemanticGraph(base=self.graph, enriched=enriched)

# semantic/agent_interface.py
class AgentContext:
    """AGENT 上下文，填充业务语义"""
    def set_business_meaning(self, signal: str, meaning: str): ...
    def set_tags(self, signal: str, tags: List[str]): ...
    def set_user_note(self, signal: str, note: str): ...
    def to_json(self) -> dict: ...   # 持久化
    @classmethod
    def from_json(cls, data: dict) -> 'AgentContext': ...
```

---

## 新建模块

```
src/
├── scope/                          # 🆕 Scope 体系
│   ├── __init__.py
│   ├── models.py                   # ScopeInfo, SignalRef, ScopeKind
│   ├── builder.py                  # ScopeBuilder (Pass 1)
│   ├── symbol_table.py             # SymbolTable, SignalDecl
│   └── cross_module.py             # CrossModuleResolver
│
├── extractors/                     # 🆕 纯 AST 遍历
│   ├── __init__.py
│   ├── base.py                    # Extractor 基类
│   ├── load.py                    # LoadExtractor
│   ├── driver.py                  # DriverExtractor
│   ├── connection.py               # ConnectionExtractor
│   └── clock.py                   # ClockExtractor
│
├── semantic/                      # 🔄 重新设计：语义增强层
│   ├── __init__.py
│   ├── enricher.py                # 🆕 SemanticEnricher
│   ├── agent_interface.py         # 🆕 AgentContext
│   └── models.py                  # 🆕 EnrichedSignal, EnrichedSemanticGraph
│
└── semantic_graph.py              # 🆕 SemanticGraph 数据结构
```

---

## 需要修改的文件

### src/semantic/ — 完全重构

| 原文件 | 操作 | 原因 |
|--------|------|------|
| `base.py` | **删除** | SUPPORTED_KINDS 模式废弃 |
| `driver.py` | **删除** | 功能迁移到 extractors/ |
| `load.py` | **删除** | 功能迁移到 extractors/ |
| `clock.py` | **删除** | 功能迁移到 extractors/ |
| `reset.py` | **删除** | 功能迁移到 extractors/ |
| `connection.py` | **删除** | 功能迁移到 extractors/ |
| `signal.py` | **删除** | 功能迁移到 extractors/ |
| `fsm.py` | **删除** | 功能迁移到 extractors/ |
| `utils.py` | 迁移到 `scope/` | 公共工具函数 |

**新建**: `enricher.py`, `agent_interface.py`, `models.py`

### src/trace/ — 适配新架构

| 文件 | 操作 |
|------|------|
| `load.py` | 迁移到 extractors/，使用 ScopeTree |
| `load_ext.py` | **删除**（冗余） |
| `driver.py` | 迁移到 extractors/，使用 ScopeTree |
| `connection.py` | 迁移到 extractors/ |
| `controlflow.py` | 适配 ScopeTree |
| `dataflow.py` | 适配 SemanticGraph |
| `dependency.py` | 适配 SemanticGraph |
| 其他 trace/ 模块 | 适配 SemanticGraph |

### src/query/ — 重构

| 文件 | 操作 |
|------|------|
| `signal.py` | 重构，基于 EnrichedSemanticGraph |
| `path.py` | 重构，基于 ScopeTree |
| `stimulus_path_finder.py` | 适配 SemanticGraph |
| `condition_relation_extractor.py` | 适配 ScopeTree |
| `sample_condition_analyzer.py` | 适配 ScopeTree |
| `hierarchy/resolver.py` | 重构，基于 ScopeTree |
| `nested_condition_expander.py` | 适配 ScopeTree |

### src/debug/analyzers/ — 适配

| 文件 | 操作 |
|------|------|
| `multi_driver.py` | 适配 SemanticGraph |
| `multi_driver_detector.py` | 适配 SemanticGraph |
| `clock_domain.py` | 适配 ScopeTree |
| `reset_domain_analyzer.py` | 适配 ScopeTree |
| `fsm_analyzer.py` | 适配 Extractor |
| `coverage_analyzer.py` | 适配 ScopeTree |
| `xvalue.py` | 适配 SemanticGraph |
| `uninitialized.py` | 适配 SemanticGraph |
| `cdc.py` | 适配 ScopeTree |
| `timing_analyzer.py` | 适配 SemanticGraph |

---

## 需要删除的文件

### src/pyslang-ast-ref/ — 全部删除

200+ 参考文件，docstring 明确说"仅供参考，不可引用"。

### src/debug/_archive/ — 全部删除

### 冗余文件

| 文件 | 冗余原因 |
|------|---------|
| `src/trace/load_ext.py` | 被 load.py 覆盖 |
| `src/semantic/driver_cross.py` | 功能重叠 |
| `src/debug/class_extractor_simple.py` | 被 class_extractor.py 覆盖 |
| `src/debug/class_quality.py` | 功能重叠 |
| `src/debug/complexity.py` | 被 code_metrics_analyzer.py 覆盖 |

---

## 新增纪律（修订 docs/DEVELOPMENT_DISCIPLINE.md）

```markdown
### 铁律 18: Extractor 设计原则
所有语义提取器必须：
- 继承 Extractor 基类
- 接收 ScopeTree 作为构造参数
- 使用 pyslang.visit() 遍历
- 输出结果写入 SemanticGraph

### 铁律 19: ScopeTree 即上下文
所有跨作用域的引用解析必须通过 ScopeTree。

### 铁律 20: 多轮纪律
- Pass 1 (ScopeBuilder) 必须先于所有 Extractor 执行
- Extractor 之间不得有依赖关系（可并行）

### 铁律 21: Semantic 层定位
semantic/ 是语义增强层，消费 extractors 输出的 SemanticGraph，
不得直接遍历 AST。AGENT 通过 AgentContext 填充业务语义。

### 铁律 22: Enricher 置信度
SemanticEnricher 必须为每个信号标注 confidence 和 caveats，
不得输出不可信的原始数据。
```

---

## 工作量估算

| 阶段 | 工作项 | 优先级 |
|------|--------|--------|
| **Phase 0** | 新建 `scope/` 模块 + `extractors/base.py` | P0 |
| **Phase 1** | 迁移 `load.py` 到 `extractors/`（已验证方案） | P0 |
| **Phase 1** | 废弃 `pyslang-ast-ref/` + 清理冗余文件 | P1 |
| **Phase 2** | 新建 `semantic/enricher.py` + `models.py` + `agent_interface.py` | P1 |
| **Phase 2** | 迁移 `driver.py`, `clock.py`, `connection.py` 到 `extractors/` | P1 |
| **Phase 3** | 更新 `trace/` 模块适配新架构 | P2 |
| **Phase 4** | 更新 `query/` 和 `debug/` 适配 | P2 |
| **Phase 5** | 更新文档 + 迁移指南 | P3 |

---

## Phase 0 详细计划

### Step 1: scope/models.py

```python
# 核心数据模型
class ScopeKind(Enum):
    MODULE = "module"
    INTERFACE = "interface"
    PROGRAM = "program"
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    ALWAYS_LATCH = "always_latch"
    ALWAYS = "always"
    GENERATE_IF = "generate_if"
    GENERATE_FOR = "generate_for"
    GENERATE_CASE = "generate_case"
    CLASS = "class"

@dataclass
class SignalDecl:
    name: str
    scope_id: str
    width: int = 1
    declaration_kind: str = ""  # wire, reg, logic, etc.

@dataclass
class SignalRef:
    signal_name: str
    resolved_scope: str
    resolved_name: str
    ref_context: str
    is_lhs: bool
    is_cross_module: bool = False

@dataclass
class ScopeInfo:
    scope_id: str
    kind: ScopeKind
    parent_scope: Optional[str]
    declared_signals: Dict[str, SignalDecl]
    port_map: Dict[str, str]
    instance_of: Optional[str]
```

### Step 2: scope/symbol_table.py

```python
class SymbolTable:
    def __init__(self):
        self._scopes: Dict[str, ScopeInfo] = {}
    
    def declare(self, scope_id: str, sig: SignalDecl): ...
    def lookup(self, name: str, scope_id: str) -> Optional[SignalDecl]: ...
    def resolve_reference(self, name: str, scope_id: str) -> Optional[SignalRef]: ...
    def get_scope(self, scope_id: str) -> Optional[ScopeInfo]: ...
    def get_child_scopes(self, scope_id: str) -> List[str]: ...
```

### Step 3: scope/builder.py

```python
class ScopeBuilder:
    def build(self, tree: SyntaxTree) -> Tuple[ScopeTree, SymbolTable]:
        """Pass 1: 从 AST 构建完整作用域树"""
        self._symbol_table = SymbolTable()
        self._scope_stack = []
        
        def visitor(node):
            self._on_node(node)
            return VisitAction.Advance
        
        tree.root.visit(visitor)
        return ScopeTree(...), self._symbol_table
    
    def _on_node(self, node) -> VisitAction:
        kind = self._get_kind(node)
        if kind == 'ModuleDeclaration':
            return self._enter_module(node)
        elif kind == 'AlwaysFFBlock':
            return self._enter_always_ff(node)
        # ...
```

### Step 4: extractors/base.py

```python
class Extractor(ABC):
    """Extractor 基类"""
    def __init__(self, scope_tree: ScopeTree, symbol_table: SymbolTable):
        self.scope = scope_tree
        self.symbols = symbol_table
    
    @abstractmethod
    def extract(self, tree: SyntaxTree) -> None:
        pass
    
    def _resolve_signal(self, name: str, scope_id: str) -> SignalRef:
        return self.symbols.resolve_reference(name, scope_id)

class SemanticGraph:
    """所有 extractors 的输出聚合"""
    def __init__(self):
        self.loads: Dict[str, List[LoadPoint]] = {}
        self.drivers: Dict[str, List[DriverPoint]] = {}
        self.connections: List[Connection] = []
    
    def all_signals(self) -> List[str]: ...
```

---

## 关键风险

1. **pyslang-ast-ref/ 删除前需确认无隐藏引用**
2. **现有测试覆盖率参差，重构后需逐模块验证**
3. **debug/ 分析器耦合紧密，适配工作量大**

---

## 相关文档

- `docs/DEVELOPMENT_DISCIPLINE.md`
- `STRUCTURE.md`
