# driver.testplan.md - 驱动提取工具测试计划

> 状态: 2026-05-06
> 工具: src/trace/driver.py
> 负责人: 

---

## 一、工具定位

**功能**: 从 SystemVerilog RTL 中提取时钟、复位、驱动信号关系

**核心 API**:
```python
class Driver:
    def extract(code: str) -> DriverResult  # 从源码提取
    def analyze(tree: SyntaxTree) -> DriverResult  # 从 AST 分析
    
class DriverResult:
    clocks: List[ClockInfo]
    resets: List[ResetInfo] 
    drivers: List[DriverInfo]
    confidence: str  # "high" | "medium" | "uncertain"
    caveats: List[str]
```

---

## 二、测试覆盖矩阵

| 功能点 | 测试用例 | 边界/异常 |
|--------|--------|-----------|
| 时钟检测 | `test_detect_clock_simple` | 参数化时钟、函数生成时钟 |
| 时钟检测 | `test_detect_clock_multiple` | 多时钟输入 |
| 复位检测 | `test_detect_reset_sync` | 同步复位 |
| 复位检测 | `test_detect_reset_async` | 异步复位 |
| 复位检测 | `test_detect_reset_complex` | 组合复位表达式 |
| 驱动提取 | `test_driver_always_ff` | AlwaysFF |
| 驱动提取 | `test_driver_always_comb` | AlwaysComb |
| 驱动提取 | `test_driver_assign` | 连续赋值 |
| 驱动提取 | `test_driver_nonblocking` | 非阻塞赋值 |
| 时钟关系 | `test_clock_relationship` | 派生时钟、门控时钟 |

---

## 三、金标准用例

### 金标准 1: AlwaysFF 驱动

```systemverilog
module dut(
    input  clk,
    input  rst_n,
    input  data_in,
    output logic data_out
);
    always_ff @(posedge clk or negedge rst_n)
        if (!rst_n) data_out <= 1'b0;
        else       data_out <= data_in;
endmodule
```

**金标准输出**:
| 字段 | 预期值 |
|------|--------|
| clocks | [clk (posedge)] |
| resets | [rst_n (async, negedge)] |
| drivers.data_out | [data_in (nonblocking)] |
| drivers.enable | [无] |
| confidence | "high" |

---

### 金标准 2: AlwaysComb + 门控时钟

```systemverilog
module dut(
    input clk, input clk_en,
    input a, b,
    output logic y
);
    always_comb begin
        if (a & clk_en) y = b;
        else y = 1'b0;
    end
endmodule
```

**金标准输出**:
| 字段 | 预期值 |
|------|--------|
| clocks | [] |
| resets | [] |
| drivers.y | [b (blocking), const 0] |
| confidence | "medium" (无时钟，时序敏感) |

---

### 金标准 3: 跨模块驱动

```systemverilog
// sub.sv
module sub(input clk, input d, output logic q);
    always_ff @(posedge clk) q <= d;
endmodule

// top.sv
module top(input clk, input din, output logic dout);
    sub u_sub(.clk(clk), .d(din), .q(dout));
endmodule
```

**金标准输出**:
| 字段 | 预期值 |
|------|--------|
| cross_module.dout.driver | sub.u_sub.q |
| cross_module.path | top.dout → sub.q ← sub.d ← top.din |
| confidence | "high" |

---

## 四、通过标准

| 指标 | 目标值 |
|------|--------|
| 覆盖率 | ≥90% 代码覆盖率 |
| 金标准通过率 | 100% |
| 边界用例覆盖 | ≥10 个边界/异常 |
| 真实项目覆盖 | ≥3 个开源项目 |
| 置信度准确率 | ≥95% |

---

## 五、测试文件

| 文件 | 行数 | 状态 |
|------|------|------|
| `tests/unit/tools/test_driver.py` | 85 | ✅ 已创建 |
| `tests/integration/test_driver_integration.py` | - | ⏳ 待创建 |
| `tests/e2e/test_driver_opentitan.py` | - | ⏳ 待创建 |

---

## 六、依赖

- `src/trace/driver.py`
- `src/trace/semantic/driver.py` (可选)
- `pyslang >= 10.0`

---
