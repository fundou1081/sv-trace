# SV-TRACE 语义 AST 迁移计划

> 创建时间: 2026-05-31 19:40 GMT+8
> 状态: 规划中，待启动

---

## 背景与动机

### 现状问题

| 问题 | 根因 |
|------|------|
| **Driver 不稳定** | `DriverSignal.source` 为空，表达式提取没有正确绑定到节点；SyntaxTree 节点结构边界模糊导致提取结果跳动 |
| **跨模块不稳定** | SymbolTable 按模块隔离，跨模块信号引用查不到或查错；generate 展开后实例层级变化，符号解析断链 |
| **Generator 展开问题** | 当前处理的是 pre-elaboration 的 SyntaxTree，generate 块还是 AST 中的语法树节点，没有经过 elaboration |

### 迁移目标

使用 **语义 AST** 替代 **SyntaxTree + 分离 Side Table** 的架构，从根本上解决上述问题。

---

## 核心变化：压缩 Pass 数

### 现状 (3-Pass)

```
SyntaxTree (pyslang 原始)
    ↓ Pass 1: ScopeBuilder
ScopeTree + SymbolTable
    ↓ Pass 2: Extractors
SemanticGraph
    ↓ Pass 3: Enricher
EnrichedSemanticGraph
```

### 目标 (1-Pass + 可选 Enrich)

```
SV Source
    ↓ SemanticASTBuilder
SemanticAST (语义节点图，含 generate 展开)
    ↓ 可选 SemanticEnricher
EnrichedSemanticAST
```

---

## 设计原则

### Adapter 模式

核心思路：**内部替换，接口不变**。底层换成 Semantic AST，上层保持旧接口，用 Adapter 翻译。

```
旧 API 消费者 (trace/driver.py 等)
          │
┌─────────▼──────────┐
│   Adapter Layer    │  ← 保持 ScopeTree/SemanticGraph 接口
└─────────┬──────────┘
          │
┌─────────┴──────────┐
│ 旧 Extractors (兼容) │  新 Semantic AST (内部新实现)
│   (fallback/compat) │  (外部不可见)
└────────────────────┘
```

### 新目录结构

```
src/
├── semantic_ast/           # 🆕 新增 (内部实现，对外不可见)
│   ├── nodes.py            # 语义节点类型定义
│   ├── builder.py          # 构建语义 AST (generate 展开等)
│   ├── resolver.py         # 跨模块符号解析
│   └── graph.py            # 语义关系图组织
│
├── scope/                  # 改造为 Adapter
│   ├── builder.py          # → ScopeTree Adapter
│   ├── symbol_table.py     # → SymbolTable Adapter
│   └── models.py           # 节点类型迁移到 semantic_ast/nodes.py
│
├── extractors/             # 改造为 Adapter
│   ├── base.py            # → SemanticGraph Adapter
│   ├── driver.py          # → DriverPoint Adapter
│   ├── load.py            # → LoadPoint Adapter
│   └── connection.py      # → Connection Adapter
│
└── ... 其他模块保持不变
```

---

## 需要新增的文件

| 新文件 | 职责 | 和旧模块对应关系 |
|--------|------|-----------------|
| `semantic_ast/nodes.py` | 定义所有语义节点类型 | 替代 `scope/models.py` 节点定义 |
| `semantic_ast/builder.py` | 从 pyslang AST 构建语义节点图，含 generate 展开 | 合并 `scope/builder.py` + `extractors/` |
| `semantic_ast/resolver.py` | 跨模块符号消歧、构建全局符号图 | 新增，解决跨模块问题 |
| `semantic_ast/graph.py` | 语义关系图的组织方式 | 替代 `extractors/base.py` 的 SemanticGraph |

---

## 需要改动的文件

| 文件 | 改动方向 |
|------|----------|
| `scope/models.py` | 废弃节点类型定义，迁移到 `semantic_ast/nodes.py` |
| `scope/builder.py` | 改为 Adapter，内部调用 `semantic_ast/builder.py`，输出兼容 ScopeTree |
| `scope/symbol_table.py` | 改为 Adapter，内部调用 `semantic_ast/resolver.py` |
| `scope/utils.py` | 保留，作为工具函数给新架构用 |
| `extractors/base.py` | `SemanticGraph` 改为 Adapter，内部调用 `semantic_ast/graph.py` |
| `extractors/driver.py` | 改为 Adapter，内部调用 `semantic_ast` 的驱动节点 |
| `extractors/load.py` | 改为 Adapter，内部调用 `semantic_ast` 的负载节点 |
| `extractors/connection.py` | 改为 Adapter，内部调用 `semantic_ast` 的连接节点 |
| `semantic/models.py` | `EnrichedSignal` 改为基于新语义节点类型 |
| `semantic/enricher.py` | 适配新 SemanticAST 输入 |
| `trace/driver.py` 等 | 适配新 Adapter API（预计改动很小） |

---

## 不需要改动的文件

| 文件 | 说明 |
|------|------|
| `parse/parser.py` | pyslang 解析器封装，仍作为第一层输入 |
| `debug/analyzers/*.py` | CDC、FSM 等分析器，只依赖最终语义图节点，不依赖构建过程 |
| `trace/query/` | query 层只依赖最终语义图，接口不变则无需改动 |
| `trace/area_estimator.py` 等 | 评估工具只读数据，不依赖构建过程 |

---

## 核心设计决策

### 1. 语义节点和 pyslang 节点的关系

**方案 A: 包装型 (推荐)**

```python
class SemanticNode:
    """语义节点包装器"""
    def __init__(self, pyslang_node, sem_ctx: SemanticContext):
        self._node = pyslang_node           # 原始 pyslang 节点
        self._ctx = sem_ctx                  # 语义上下文
        self.scope_id: str = ""             # 作用域 ID (直接内聚)
        self.resolved_type: str = ""         # 解析后的类型
        self.resolved_symbol: 'Symbol' = None # 解析后的符号引用
        self.drivers: List['SemanticDriverNode'] = []  # 驱动关系 (直接内聚)
        self.loads: List['SemanticLoadNode'] = []       # 负载关系
```

**方案 B: 复制型** — 完全抛弃 pyslang 节点，在语义节点内重建 AST，工作量大，不推荐。

### 2. generate 展开在哪个阶段做

pyslang 语义 AST 已支持 generate 展开 → 在 `semantic_ast/builder.py` 中做符号消歧时使用展开后的实例。

### 3. 跨模块符号解析

```python
class SymbolResolver:
    """全局符号解析器"""
    
    def resolve(self, modules: List[ModuleNode]) -> GlobalSymbolTable:
        """
        1. 拓扑排序所有模块（按依赖关系）
        2. 按序解析：先解析被依赖模块，再解析依赖模块
        3. 构建 global_symbol_table: { fully_qualified_name → SemanticNode }
        4. 引用消歧时直接查 global 表
        """
```

---

## 迁移顺序

```
Phase 1: 基础设施 (纯新增，不影响旧代码)
  1. 新建 semantic_ast/nodes.py (定义节点类型)
  2. 新建 semantic_ast/graph.py (图结构)
  3. 新建 semantic_ast/resolver.py (全局符号解析)
  4. 新建 semantic_ast/builder.py (语义 AST 构建)

Phase 2: 核心构建 (最关键)
  5. 调试 semantic_ast/ 内部实现
  6. 添加新旧输出对比脚本，验证结果一致性

Phase 3: Adapter 层替换
  7. 改造 scope/builder.py 为 Adapter
  8. 改造 scope/symbol_table.py 为 Adapter
  9. 改造 extractors/base.py → SemanticGraph Adapter
  10. 改造 extractors/driver.py → DriverPoint Adapter
  11. 改造 extractors/load.py → LoadPoint Adapter
  12. 改造 extractors/connection.py → Connection Adapter

Phase 4: 上层适配
  13. 改写 semantic/enricher.py 适配新输入
  14. 验证 trace/driver.py、trace/load.py 等 API 兼容性

Phase 5: 清理
  15. 跑全量测试，修复不一致问题
  16. 删除旧 scope/extractors 中废弃的冗余代码
  17. 更新文档
```

---

## 风险控制

| 风险 | 缓解方法 |
|------|----------|
| Adapter 转换丢失信息 | 新旧输出逐字段 diff，不一致则修 |
| generate 展开行为不一致 | 在 `semantic_ast/builder.py` 加详细 test case 覆盖 |
| 跨模块符号消歧失败 | 在 `resolver.py` 保留 fallback 走旧 SymbolTable 链路 |
| trace 下游模块接口连锁反应 | 用 Adapter 隔离，上层 API 不变则不下沉改动 |

---

## 验证机制

### 新旧两路并行

```python
# 添加对比脚本，验证新旧输出差异
def compare_driver_outputs(sv_code):
    # 旧路
    old_graph = old_flow(sv_code)  # SyntaxTree → old Extractors
    
    # 新路 (直接调 semantic_ast)
    new_sem = SemanticASTBuilder().build(parse(sv_code))
    
    diff = compare_driver_points(old_graph.drivers, new_sem.drivers)
    if diff:
        print("⚠️ 不一致:", diff)
        return False
    return True
```

### 关键验证指标

- DriverPoint 数量一致
- LoadPoint 数量一致
- 跨模块引用解析结果一致
- generate 展开后实例数量一致
- 所有测试用例通过

---

## 实验发现

### 当前 DriverExtractor 行为实测

**测试1: 同一信号多次赋值 → driver 全是信号自己（BUG）**
```systemverilog
always_ff @(posedge clk) begin
  a <= b;   // driver 应为 b，实际为 'a'
  b <= c;   // driver 应为 c，实际为 'b'
  c <= 8'h0; // driver 应为 8'h0，实际为 'c'
end
```
结果: driver 全是 lhs 本身，rhs 完全没有提取。

**根因**: `_process_assign` 只取 lhs 填入 driver 字段，没有从 rhs 提取驱动源。

**测试2: Scoped name (pkg::data) → 拆成 3 个条目**
```systemverilog
always_comb data = pkg::shared_data;
```
结果:
- `data` ← `data`
- `pkg` ← `pkg`
- `shared_data` ← `shared_data`

正确应为: `data` ← `pkg::shared_data` (完整路径作为 driver)

**测试3: generate 循环内的信号 → 重复计数混乱**
```systemverilog
generate for (i = 0; i < 2; i++) begin : GEN_REG
  logic [7:0] tmp_reg;
  always_ff @(posedge clk) tmp_reg <= 8'h0;  // 正确提取 always_ff
endgenerate
```
结果: `tmp_reg` 出现 3 次 always_ff + 1 次 always_comb，重复且未区分实例

**测试4: 输入端口被标记为驱动信号（不合理）**
输入端口 `in`、`out` 被当作驱动目标，但它们实际不应被任何东西驱动。

### 根因总结

| 问题 | 根因位置 | 问题类型 |
|------|----------|----------|
| driver = lhs | `_process_assign` | 逻辑错误 |
| scoped name 拆分 | `_scan_lhs` / `_process_assign` | 表达式解析不完整 |
| generate 重复计数 | `_process_always_block` | 实例未区分 |
| 输入端口被驱动 | 未过滤端口方向 | 语义判断缺失 |

---


## 待细化事项

- [ ] `semantic_ast/nodes.py` 节点类型体系设计
- [ ] `semantic_ast/resolver.py` 跨模块消歧算法
- [ ] 新旧输出对比脚本实现
- [ ] Adapter 层接口契约定义
---

## pyslang 关键 API 实验结论 (2026-05-31)

### 关键发现 1: pyslang 赋值表达式直接支持 left/right 属性

```python
# NonblockingAssignmentExpression / AssignmentExpression
# 直接有 .left 和 .right 属性，不需要自己解析语法树
nba.left   # → IdentifierNameSyntax
nba.right  # → RHS 表达式节点
```

### 关键发现 2: 从表达式节点提取文本

```python
# IdentifierNameSyntax → identifier.valueText
name = node.identifier.valueText

# IntegerVectorExpression (如 8'hFF) → value.valueText
hex_val = node.value.valueText  # Token 类型, 'FF'

# IntegerLiteralExpression → literal.valueText
txt = node.literal.valueText
```

### 关键发现 3: 二元表达式的递归遍历

```python
# 二元表达式有 left/right 属性，括号表达式有 expression 属性
for prop in ['left', 'right', 'expression', 'operand']:
    sub = getattr(node, prop, None)
    if sub is not None:
        _collect_expr_identifiers(sub, result, visited)
```

### 关键发现 4: Compilation 语义层 (未完全激活)

```python
comp = Compilation()
comp.addSyntaxTree(tree)
comp.freeze()
comp.isElaborated  # False
comp.getPackage('pkg')  # 可获取符号
comp.getRoot()          # RootSymbol 类型
```

### 关键发现 5: ScopedName 结构

`pkg::shared_data` 在 pyslang 中是 ScopedNameSyntax，`text` 属性为空，需要遍历子节点提取。

### 关键发现 6: to_json() 可获取完整文本但有效率问题

会遍历整个子树，生产环境不推荐。

### 根因总结 (对照实验)

| 问题 | 根因位置 | 结论 |
|------|----------|------|
| driver = lhs 自己 | `_process_assign` 只取 lhs | pyslang 直接提供 `.left/.right` |
| scoped name 拆分 | `_scan_lhs` 遍历把 scoped name 拆散 | 需要正确处理 ScopedNameSyntax |
| generate 重复计数 | `_process_always_block` 实例未隔离 | generate 需先展开 |
| 输入端口被驱动 | 未过滤端口方向 | 语义 AST 可在节点内聚方向 |

---

## 实验代码

实验代码位于: `src/semantic_ast_experiment.py`

运行: `python3 src/semantic_ast_experiment.py`

包含 11 个实验:
1. 提取驱动源表达式
2. ScopedName 结构
3. Generate 块结构
4. Compilation 语义层
5. AssignmentExpression 内部结构
6. 标识符解析
7. always_ff 时钟提取
8. 复合 RHS 表达式提取
9. 收集完整 RHS 表达式
10. RHS 收集 tokens
11. **使用 left/right 属性提取 RHS** ← 核心突破

---

## 下一步计划

基于实验结果:

1. **优先实现 `_collect_expr_identifiers` 辅助函数** (已在实验代码中验证)
   - 替换现有 `_process_assign` 中的错误逻辑
   - 直接使用 pyslang 的 `.left/.right` 属性

2. **实现 ScopedName 完整路径提取**
   - 遍历 ScopedNameSyntax 子节点，拼接完整路径

3. **基于 Compilation 构建跨模块符号表**
   - 使用 `comp.getPackage()` 等 API

4. **实现 semantic_ast/ 目录**
   - 按迁移计划 Phase 1 推进
