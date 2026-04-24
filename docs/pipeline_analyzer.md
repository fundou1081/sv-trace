# PipelineAnalyzer - 流水线分析器

## 概述

分析流水线结构，识别：
- 流水线阶段
- 寄存器
- Handshaking 信号 (valid/ready)
- 关键路径

## 模型

### StageInfo

```python
@dataclass
class StageInfo:
    name: str              # 阶段名
    registers: List[str]    # 寄存器列表
    combinational: List[str]  # 组合逻辑
    clock: str            # 时钟
    reset: str            # 复位
    enable: str          # 使能
    stage_id: int         # 阶段ID
```

### HandshakeChannel

```python
@dataclass
class HandshakeChannel:
    name: str
    source_stage: str
    dest_stage: str
    valid_signal: str     # valid 信号
    ready_signal: str     # ready 信号
    data_signals: List[str]
    protocol: str = "valid_ready"
```

### PipelineInfo

```python
@dataclass
class PipelineInfo:
    name: str
    stages: List[StageInfo]
    handshakes: List[HandshakeChannel]
    stats: PipelineStats
    data_path: List[str]
```

## 使用方法

```python
from trace.pipeline_analyzer import PipelineAnalyzer

analyzer = PipelineAnalyzer(parser)

# 查找流水线
pipeline = analyzer.find_pipeline('top')

# 获取阶段
for stage in pipeline.stages:
    print(f"Stage: {stage.name}")
    print(f"  Registers: {stage.registers}")
    print(f"  Clock: {stage.clock}")

# 可视化
print(pipeline.visualize())
```

## PipelineStats

```python
@dataclass
class PipelineStats:
    total_stages: int           # 阶段数
    total_registers: int          # 寄存器数
    max_fanout: int              # 最大扇出
    critical_path_depth: int     # 关键路径深度
    has_handshaking: bool        # 是否有握手
```

## 示例

```systemverilog
module pipeline (
    input clk,
    input rst_n,
    input [7:0] data_in,
    output [7:0] data_out
);
    reg [7:0] stage0, stage1, stage2;
    reg valid_in, valid_out;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage0 <= '0;
            stage1 <= '0;
            stage2 <= '0;
            valid_out <= '0;
        end else begin
            stage0 <= data_in;
            stage1 <= stage0;
            stage2 <= stage1;
            valid_out <= valid_in;
        end
    end
endmodule
```

解析结果：

```python
PipelineInfo(
    name="pipeline",
    stages=[
        StageInfo(name="stage0", registers=["stage0"], clock="clk", stage_id=0),
        StageInfo(name="stage1", registers=["stage1"], clock="clk", stage_id=1),
        StageInfo(name="stage2", registers=["stage2"], clock="clk", stage_id=2),
    ],
    handshakes=[],
    stats=PipelineStats(
        total_stages=3,
        total_registers=4,
        has_handshaking=False
    )
)
```

## Handshaking 检测

自动识别 valid/ready 协议：

```python
# 检测到 valid_ready 握手
HandshakeChannel(
    name="ch0",
    source_stage="stage0",
    dest_stage="stage1",
    valid_signal="valid_in",
    ready_signal="ready_out",
    protocol="valid_ready"
)
```
