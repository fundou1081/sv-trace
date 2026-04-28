# SV-Trace API Reference

## 核心工具 (Tier-1)

### 1. SVParser
**模块**: `parse`  
**类名**: `SVParser`  
**SystemVerilog解析器**

#### 用法
```python
from parse import SVParser

parser = SVParser()
parser.parse_text('module top; endmodule')
parser.parse_file('path/to/file.sv')
```

#### Input
| 类型 | 说明 |
|------|------|
| `str` | SystemVerilog源代码文本 |
| `List[str]` | 文件路径列表 |

#### Output
| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `trees` | `Dict` | 解析树 |
| `get_module(name)` | `ModuleSyntax` | 获取模块 |
| `get_source(file)` | `str` | 获取源码 |

---

### 2. DriverTracer
**模块**: `trace.driver`  
**类名**: `DriverTracer`  
**信号驱动追踪**

#### 用法
```python
from trace.driver import DriverTracer
from parse import SVParser

parser = SVParser()
parser.parse_file('design.sv')
tracer = DriverTracer(parser)

# 追踪信号驱动
drivers = tracer.find_drivers('signal_name')
```

#### Input
- `SVParser` 实例

#### Output
| 类型 | 说明 |
|------|------|
| `List[Driver]` | 驱动信息列表 |
| `dict` | 模块驱动映射 |

---

### 3. ConnectionTracer
**模块**: `trace.connection`  
**类名**: `ConnectionTracer`  
**模块连接追踪**

#### 用法
```python
from trace.connection import ConnectionTracer

conn = ConnectionTracer(parser)
connections = conn.trace_connections('module_name')
```

#### Output
| 类型 | 说明 |
|------|------|
| `List[Connection]` | 连接信息 |
| `Dict` | 实例连接图 |

---

### 4. LoadTracer
**模块**: `trace.load`  
**类名**: `LoadTracer`  
**信号负载追踪**

#### 用法
```python
from trace.load import LoadTracer

tracer = LoadTracer(parser)
loads = tracer.find_loads('signal_name')
```

#### Output
| 类型 | 说明 |
|------|------|
| `List[Load]` | 负载信息列表 |

---

### 5. ParameterResolver
**模块**: `parse.params`  
**类名**: `ParameterResolver`  
**参数解析**

#### 用法
```python
from parse.params import ParameterResolver

resolver = ParameterResolver(parser)
params = resolver.resolve('module_name')
value = resolver.get_param('param_name')
```

#### Output
| 类型 | 说明 |
|------|------|
| `dict` | 参数名->值映射 |

---

## 重要工具 (Tier-2)

### 6. CoverageStimulusSuggester
**模块**: `verify.coverage_guide`  
**类名**: `CoverageStimulusSuggester`  
**Coverage激励建议器**

#### 用法
```python
from verify.coverage_guide.stimulus_suggester import CoverageStimulusSuggester

suggester = CoverageStimulusSuggester(parser)
points = suggester.get_coverage_points()
stimuli = suggester.suggest()
cg = suggester.generate_covergroup('module_name')
bins = suggester.generate_bins('signal', width=1)
```

#### Input
- `SVParser` 实例 (可选)

#### Output
| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_coverage_points()` | `List[CoveragePoint]` | 覆盖点 |
| `suggest()` | `List[Stimulus]` | 激励建议 |
| `generate_covergroup(name)` | `str` | SV covergroup代码 |
| `generate_bins(signal, width, expr)` | `str` | bins代码 |
| `generate_illegal_bins(signal, values)` | `str` | illegal bins |
| `generate_ignore_bins(signal, values)` | `str` | ignore bins |
| `generate_nested_if_coverage(conditions)` | `str` | 嵌套IF coverage |
| `analyze()` | `dict` | 分析结果 |

#### generate_bins 输出示例
```systemverilog
// 单bit
enable_cp: coverpoint enable {
  bins one = {1'b1};
  bins zero = {1'b0};
}

// 多bit (width=8)
data_cp: coverpoint data {
  bins zero = {8'h0};
  bins max = {8'hff};
  bins mid = {default};
}
```

#### generate_covergroup 输出示例
```systemverilog
covergroup cg_module(input module_name dut);
  signal: coverpoint dut.signal {
    bins true = {1};
    bins false = {0};
  }
  cross signal1, signal2;
endgroup
```

---

### 7. ControlFlowTracer
**模块**: `trace.controlflow`  
**类名**: `ControlFlowTracer`  
**控制流分析**

#### 用法
```python
from trace.controlflow import ControlFlowTracer

cf = ControlFlowTracer(parser)
cfg = cf.analyze('module_name')
```

#### Output
| 类型 | 说明 |
|------|------|
| `CFG` | 控制流图 |
| `List[Block]` | 基本块 |

---

### 8. DataPathAnalyzer
**模块**: `trace.datapath`  
**类名**: `DataPathAnalyzer`  
**数据路径分析**

#### 用法
```python
from trace.datapath import DataPathAnalyzer

analyzer = DataPathAnalyzer(parser)
path = analyzer.find_path('src_signal', 'dst_signal')
```

#### Output
| 类型 | 说明 |
|------|------|
| `List[Signal]` | 数据路径 |

---

### 9. ModuleDependencyAnalyzer
**模块**: `debug.dependency`  
**类名**: `ModuleDependencyAnalyzer`  
**模块依赖分析**

#### 用法
```python
from debug.dependency import ModuleDependencyAnalyzer

analyzer = ModuleDependencyAnalyzer(parser)
modules = analyzer.get_all_modules()
deps = analyzer.get_dependencies('module_name')
```

#### Output
| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_all_modules()` | `List[str]` | 所有模块 |
| `get_dependencies(name)` | `List[str]` | 依赖列表 |
| `get_dependents(name)` | `List[str]` | 反向依赖 |

---

### 10. ClassExtractor
**模块**: `parse.class_utils`  
**类名**: `ClassExtractor`  
**Class/constraint提取**

#### Output
| 类型 | 说明 |
|------|------|
| `List[ClassSyntax]` | 类列表 |

---

### 11. ConstraintExtractor
**模块**: `parse.constraint`  
**类名**: `ConstraintExtractor`  
**约束提取**

#### Output
| 类型 | 说明 |
|------|------|
| `List[Constraint]` | 约束列表 |

---

### 12. FSMExtractor
**模块**: `debug.fsm`  
**类名**: `FSMExtractor`  
**FSM状态机提取**

#### 用法
```python
from debug.fsm import FSMExtractor

fsm = FSMExtractor(parser)
states = fsm.extract('module_name')
```

#### Output
| 类型 | 说明 |
|------|------|
| `List[State]` | 状态列表 |
| `dict` | 状态机定义 |

---

## 辅助工具 (Tier-3)

### 13. CoverageAdvisor
**模块**: `verify.coverage_advisor`  
**类名**: `CoverageAdvisor`  
**覆盖率指导**

#### Output
| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `analyze_gaps(data)` | `List[CoverageGap]` | 覆盖缺口 |
| `generate_test_plan(gaps)` | `str` | 测试计划 |

---

### 14. Linter
**模块**: `lint.linter`  
**类名**: `Linter`  
**代码风格检查**

#### Output
| 类型 | 说明 |
|------|------|
| `List[Issue]` | 问题列表 |


## CoverageStimulusSuggester 详细手册

### 类名
`CoverageStimulusSuggester` (在 verify.coverage_guide.stimulus_suggester)

### 功能
根据代码条件自动生成coverage测试激励和SystemVerilog covergroup

### 初始化
```python
# 方式1: 传入parser自动提取条件
from verify.coverage_guide import CoverageStimulusSuggester
from parse import SVParser

parser = SVParser()
parser.parse_text(code)
suggester = CoverageStimulusSuggester(parser)

# 方式2: 手动设置条件
suggester = CoverageStimulusSuggester()
suggester.conditions = [Condition(...)]
suggester.coverage_points = [CoveragePoint(...)]
```

### 核心方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_coverage_points()` | 获取所有覆盖点 | `List[CoveragePoint]` |
| `suggest()` | 生成测试激励 | `List[Stimulus]` |
| `generate_covergroup(name)` | 生成covergroup代码 | `str` |
| `generate_bins(signal, width, expr)` | 生成bins | `str` |
| `generate_illegal_bins(signal, values)` | 生成illegal bins | `str` |
| `generate_ignore_bins(signal, values)` | 生成ignore bins | `str` |
| `generate_nested_if_coverage(conditions)` | 嵌套IF coverage | `str` |
| `analyze()` | 完整分析结果 | `dict` |

### 数据结构

#### Condition
```python
class Condition:
    def __init__(self, expr, type, branch, line=0)
    # expr: 条件表达式 (str)
    # type: 类型 (if/case/ternary)
    # branch: 分支名 (str)
    # line: 行号 (int)
```

#### CoveragePoint
```python
class CoveragePoint:
    def __init__(self, id, condition, type, suggestions, line=0)
    # id: 覆盖点ID
    # condition: 条件
    # type: 类型
    # suggestions: 建议列表
    # line: 行号
```

### 使用示例

#### 示例1: 基础IF条件
```python
from verify.coverage_guide.stimulus_suggester import CoverageStimulusSuggester, Condition, CoveragePoint

s = CoverageStimulusSuggester()
s.conditions = [Condition('enable', 'if', 'condition')]
s.coverage_points = [CoveragePoint('cp_0', 'enable', 'if', [])]

print(s.generate_covergroup('test'))
# 输出:
# // Auto-generated Covergroup for test
# covergroup cg_test(input test dut);
#   // Condition: enable
#   enable: coverpoint dut.enable {
#     bins true = {1};
#     bins false = {0};
#   }
# endblockgroup
```

#### 示例2: 多条件交叉
```python
s = CoverageStimulusSuggester()
s.conditions = [
    Condition('a && b', 'if', 'condition'),
    Condition('c', 'if', 'condition'),
]

print(s.generate_covergroup('example'))
# 自动生成cross coverage
```

#### 示例3: 多bit信号bins
```python
s = CoverageStimulusSuggester()
print(s.generate_bins('data', width=8))
# 输出:
# data_cp: coverpoint data {
#   bins zero = {8'h0};
#   bins max = {8'hff};
#   bins mid = {default};
# }
```

#### 示例4: illegal bins
```python
s = CoverageStimulusSuggester()
print(s.generate_illegal_bins('state', ['2b11', '2b10']))
# 输出:
# state_cp: coverpoint state {
#   bins valid = {default};
#   illegal bins i_2b11 = {2b11};
#   illegal bins i_2b10 = {2b10};
# }
```

#### 示例5: 嵌套IF
```python
from verify.coverage_guide.stimulus_suggester import Condition

conditions = [
    Condition('a', 'if', 'condition'),
    Condition('b', 'if', 'condition'),
    Condition('c', 'if', 'condition'),
]
print(s.generate_nested_if_coverage(conditions, 'nested'))
# 自动生成嵌套深度的cross coverage
```

### Input格式

| 输入类型 | 格式 | 示例 |
|---------|------|------|
| 代码文本 | `str` | `'module top; endmodule'` |
| 文件 | `str` | `'path/to/file.sv'` |
| Condition列表 | `List[Condition]` | `[Condition('a', 'if', '')]` |

### Output格式

| 方法 | 输出格式 | 示例 |
|------|---------|------|
| generate_covergroup | `str` (SystemVerilog) | `covergroup cg_x...` |
| generate_bins | `str` (SystemVerilog) | `bins one = {1'b1};` |
| generate_illegal_bins | `str` (SystemVerilog) | `illegal bins...` |
| generate_nested_if_coverage | `str` (SystemVerilog) | `cross...` |
| analyze | `dict` | `{'conditions': N, 'coverage_points': N}` |

### 常见用例

| 用例 | 方法 | 参数 |
|------|------|------|
| FSM状态覆盖 | generate_covergroup | 每个状态一个condition |
| 数据路径覆盖 | generate_bins | width=信号位宽 |
| 非法值检测 | generate_illegal_bins | illegal_values列表 |
| 保留值忽略 | generate_ignore_bins | ignore_values列表 |
| 嵌套IF | generate_nested_if_coverage | conditions列表 |

## Schema 参考

每个工具的JSON格式定义详见 [SCHEMAS.md](../SCHEMAS.md)

