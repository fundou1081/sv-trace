# API 参考

## 导入

```python
# 解析器
from parse.parser import SVParser

# 驱动收集
from trace.driver import DriverCollector, DriverKind, AssignKind

# 时序分析
from trace.timing_depth import TimingDepthAnalyzer

# 报告生成
from trace.reports import generate_report, TimingReportGenerator, ReportConfig

# CDC 分析
from trace.reports.cdc_analyzer import CDCAnalyzer, CDCReport, CDCPath
```

## SVParser

```python
parser = SVParser()
parser.parse_file('design.sv')
parser.parse_dir('/path/to/files')
```

## DriverCollector

```python
collector = DriverCollector(parser)

# 所有驱动
collector.drivers  # Dict[str, List[Driver]]

# 获取特定信号的驱动
collector.get_drivers('signal_name')
```

## TimingDepthAnalyzer

```python
analyzer = TimingDepthAnalyzer(parser)

# 分析
analyzer.analyze()                    # 所有路径
analyzer.analyze(domain='clk_a')     # 特定域

# 查找
analyzer.find_critical_path()       # 最深时序
analyzer.find_worst_logic_path()    # 最深逻辑

# 数据结构
analyzer.registers    # Dict[str, Register]
analyzer.domains      # Dict[str, DomainInfo]
analyzer.flow_graph   # 数据流图
analyzer.edge_ops     # 边运算符数
```

## TimingReportGenerator

```python
config = ReportConfig(
    title='Report',
    output_format='html',
    max_paths=50
)

generator = TimingReportGenerator(parser, config)
generator.generate('output.html')
```

## CDCAnalyzer

```python
analyzer = CDCAnalyzer(parser)
report = analyzer.analyze()

report.cdc_paths       # List[CDCPath]
report.domains         # Dict[str, DomainInfo]
report.risky_paths     # int
```

## 数据模型

### DriverKind / AssignKind

```python
class DriverKind(Enum):
    Continuous = 0
    AlwaysComb = 1
    AlwaysFF = 2
    AlwaysLatch = 3
    Always = 4

class AssignKind(Enum):
    Blocking = 0      # =
    Nonblocking = 1  # <=
```

### Driver

```python
@dataclass
class Driver:
    signal: str
    kind: DriverKind
    module: str
    sources: List[str]
    clock: str
    assign_kind: AssignKind
    operator_count: int
```

### TimingPath

```python
@dataclass
class TimingPath:
    start_reg: str
    end_reg: str
    timing_depth: int
    logic_depth: int
    signals: List[str]
    domains: List[str]
```

### CDCPath

```python
@dataclass
class CDCPath:
    source_domain: str
    dest_domain: str
    start_reg: str
    end_reg: str
    signals: List[str]
    timing_depth: int
    path_type: str
    issues: List[str]
```
