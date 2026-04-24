# ControlFlowTracer - 控制流分析器

## 概述

追踪信号的控制依赖关系，包括：
- if 语句条件
- case 语句
- always_ff 条件

## 模型

### ControlCondition

```python
@dataclass
class ControlCondition:
    condition_expr: str      # 条件表达式
    signal_name: str         # 被控制的信号
    condition_signals: List[str]  # 条件中的信号
    statement_type: str     # if/case/always_ff
    line: int              # 行号
```

### ControlFlow

```python
@dataclass
class ControlFlow:
    signal_name: str
    controlling_signals: List[str]  # 直接控制它的信号
    dependent_signals: List[str]    # 它控制的信号
    conditions: List[ControlCondition]
```

## 使用方法

```python
from trace.controlflow import ControlFlowTracer

tracer = ControlFlowTracer(parser)

# 获取所有控制流
all_flows = tracer.analyze_all()

# 获取特定信号的控制流
flow = tracer.get_flow('data_out')

# 获取控制信号
ctrl = tracer.get_controlling_signals('data_out')

# 可视化
print(flow.visualize())
```

## 示例

```systemverilog
always_ff @(posedge clk) begin
    if (enable) begin
        data_out <= data_in;
    end else begin
        data_out <= '0;
    end
end
```

解析结果：

```python
ControlFlow(
    signal_name="data_out",
    controlling_signals=["enable"],
    dependent_signals=[],
    conditions=[
        ControlCondition(
            condition_expr="enable",
            signal_name="data_out",
            condition_signals=["enable"],
            statement_type="if",
            line=2
        )
    ]
)
```

## 应用

- 识别门控时钟
- 分析使能信号
- 条件赋值分析
