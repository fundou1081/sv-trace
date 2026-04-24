# SV-Trace

SystemVerilog 静态分析工具库 - 用于信号追踪、TLM 连接分析、UVM testbench 结构提取

## 功能

### 核心分析
- **SV 解析**: 使用 pyslang 解析 SystemVerilog 代码
- **信号追踪**: 驱动追踪、负载追踪、数据流分析
- **层级解析**: 跨模块信号追踪

### Class 分析
- **Class 提取器**: 提取类成员、方法、约束、继承关系
- **类关系图**: 方法调用图、继承层次
- **UVM 组件**: 自动识别 agent/monitor/driver/sequencer

### UVM Testbench 分析
- **组件结构**: 提取 testbench 层次
- **TLM 连接**: analysis/put/get/transport 端口
- **Phase 方法**: build/connect/run 等

## 使用

```python
from parse.parser import SVParser
from debug.class_extractor import ClassExtractor
from debug.uvm.uvm_extractor import UVMExtractor

parser = SVParser()
parser.parse_file('testbench.sv')

extractor = ClassExtractor(parser)
uvm = UVMExtractor(extractor, relation_extractor)
uvm.extract_tlm_connections(code)

print(uvm.get_report())
```

## 测试

```bash
python tests/unit/test_class.py   # 18/18 passed
python test_all.py              # 10/10 passed
```

## 版本

- v0.4: UVM 分析 + ClassExtractor 修复
- v0.3: 层级解析、代码召回
- v0.2: Class/Constraint 提取器

## 文档

- [PLAN.md](PLAN.md) - 开发计划
- [Idea.md](Idea.md) - 功能想法池

## 项目结构

```
src/
├── parse/      # SVParser
├── trace/      # 追踪器
├── query/      # 查询接口
├── debug/      # 分析工具
│   └── uvm/   # UVM 分析
└── lint/      # Linting
```
