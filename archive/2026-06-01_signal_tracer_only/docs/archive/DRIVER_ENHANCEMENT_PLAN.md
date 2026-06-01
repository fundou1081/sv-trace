# Driver 增强计划

> 目标: 全面使用 AST，支持跨模块、generate、bit级别、参数化模块等复杂场景

---

## 当前实现 (v1)

```python
# 当前功能
- 基本信号驱动关系提取
- Single bit assignment tracking
- Simple always_ff/always_comb blocks
```

---

## 目标功能 (v2)

### 1. 跨模块追踪 (Cross-module)

```systemverilog
// 模块 A
mod_a inst_b(.clk(clk), .sig(sig));

// 需要追踪:
// clk → mod_a.clk → inst_b.clk
// sig → mod_a.sig → inst_b.sig
```

**实现**:
- ModuleInstantiation 节点遍历
- PortConnection 追踪
- InterfaceInstantiation 支持

### 2. Generate 块支持

```systemverilog
// gen_i: for genvar i = 0...
// generate
//   assign sig[i] = data[i];
// endgenerate
```

**实现**:
- GenerateBlock 节点
- LoopGenerate 节点
- ConditionalGenerate 节点

### 3. Bit级别追踪

```systemverilog
assign data[7:0] = 8'hFF;
assignsig[3] = 1'b1;
```

**实现**:
- BitSelect 节点
- PartSelect 节点
- Range 保留完整信息

### 4. 参数化模块支持

```systemverilog
#(.DEPTH(8), .WIDTH(16))
mod #(.PARAM(param))
```

**实现**:
- Parameter 节点
- Override 连接
- GenericMapping 追踪

### 5. 其他复杂场景

- **Interface信号**: InterfacePort, InterfacePortImmediate
- **Clocking**: ClockingBlock
- **Structure**: Struct/Union 类型

---

## 数据模型扩展

```python
@dataclass
class Driver:
    signal_name: str
    source_module: str
    source_type: str  # always_ff, always_comb, assign, etc.
    source_line: int
    
    # 新增字段
    bit_select: Optional[Tuple[int, int]]  # (msb, lsb) for [7:3]
    generate_loop: Optional[str]           # genvar name
    cross_module: Optional[str]             # instance name
    parameter_override: Optional[Dict]     # param -> value mapping
    generate_condition: Optional[str]      # if (cond) generate
```

---

## 需要新增的 SyntaxKind 节点支持

| 类别 | SyntaxKind |
|------|------------|
| Generate | GenerateBlock, LoopGenerate, ConditionalGenerate |
| Instantiate | ModuleInstantiation, InterfaceInstantiation |
| Parameters | Parameter, ParamAssignment, GenericMapping |
| Bit选择 | BitSelect, PartSelect, Range |
| Port | PortConnection,InterfacePort |

---

## 实现计划

1. Phase 1: 增强现有节点遍历 (BitSelect, PartSelect)
2. Phase 2: 添加跨模块追踪 (ModuleInstantiation)
3. Phase 3: Generate块支持 (GenerateBlock)
4. Phase 4: 参数化模块 (Parameter处理)
5. Phase 5: 集成测试与验证
