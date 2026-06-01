# SV Trace Library 规划

## 项目结构
```
sv-trace/
├── docs/
│   └── adr/           # 架构决策记录
├── src/               # 源码
│   ├── core/          # 核心模型
│   ├── parse/         # 解析器
│   ├── trace/         # 追踪器
│   ├── query/         # 查询接口
│   │   └── hierarchy/ # 层级解析
│   └── utils/         # 工具
│   ├── debug/         # 调试分析工具
│   │   └── uvm/       # UVM 分析
│   └── lint/          # Linting
└── tests/             # 测试
```

## 功能清单

### 核心功能 (Core)
| 功能 | 状态 | 说明 |
|------|------|------|
| SVParser | ✅ | pyslang 解析 |
| ParameterResolver | ✅ | parameter 解析 |
| SignalQuery | ✅ | 信号查询 |

### 追踪器 (Trace)
| 功能 | 状态 | 说明 |
|------|------|------|
| DriverTracer | ✅ | assign/always_ff/comb/latch 驱动 |
| LoadTracer | ✅ | 信号负载追踪 |
| DataFlowTracer | ✅ | 数据流连接 |
| ConnectionTracer | ✅ | 模块实例连接 |

### 提取器 (Extractors)
| 功能 | 状态 | 说明 |
|------|------|------|
| ClassExtractor | ✅ | class 成员/方法/约束/继承 |
| ConstraintExtractor | ✅ | constraint 块 |
| CovergroupExtractor | ✅ | covergroup/coverpoint |
| AssertionExtractor | ✅ | assertion/sequence/property |
| ClassRelationExtractor | ✅ | 类关系/方法调用图 |
| ClassHierarchyBuilder | ✅ | 类继承层次 |
| ClassInstantiationTracer | ✅ | 类实例化追踪 |

### 应用层 (Application)
| 功能 | 状态 | 说明 |
|------|------|------|
| HierarchicalResolver | ✅ | 层级路径解析 |
| 简单信号解析 | ✅ | `resolve_signal("data")` |
| 层级信号解析 | ✅ | `resolve_signal("top.cpu.signal")` |
| 模块端口提取 | ✅ | input/output/inout (兼容两种语法) |
| 实例端口连接 | ✅ | 端口→信号+方向 |
| CodeExtractor | ✅ | 代码片段提取 |
| SourceViewer | ✅ | 信号完整信息展示 |

### UVM 分析 (v0.4)
| 功能 | 状态 | 说明 |
|------|------|------|
| UVMComponentInfo | ✅ | UVM 组件信息 |
| UVMConnectionInfo | ✅ | TLM 连接信息 |
| UVMExtractor | ✅ | UVM testbench 结构提取 |
| TLM 连接分析 | ✅ | analysis/put/get/transport 端口 |
| Phase 方法提取 | ✅ | build/run/connect_phase 等 |

### Lint 检查
| 功能 | 状态 | 说明 |
|------|------|------|
| Linter | ✅ | 基础 linting |

### 真实项目测试
| 项目 | 状态 | 备注 |
|------|------|------|
| tiny-gpu | ✅ 12/12 | 12 模块, 7 实例 |
| basic_verilog | ✅ 20/20 | 20 模块, 38 实例 |
| ethernet_10ge_mac | ✅ | GitHub UVM 项目 |

### 测试
| 功能 | 状态 |
|------|------|
| test_all.py | ✅ 10/10 passed |
| test_real_projects.py | ✅ |
| test_class.py | ✅ 18/18 passed |

---

## 开发记录

### v0.1 (2026-04-17)
- 初始化项目
- 克隆 slang 库到 ~/my_dv_proj/slang
- 安装 pyslang Python binding
- 克隆 sv-tests 测试素材
- 实现所有核心模块
- 批量测试: 57/60 sv-tests 通过

### v0.2 (2026-04-18)
- Class/Constraint/Covergroup/Assertion 提取器
- ConnectionTracer
- 全面测试 10/10 通过

### v0.3 (2026-04-18)
- 层级路径解析器 (HierarchicalResolver)
- 端口方向识别 (input/output/inout)
- 代码片段提取器 (CodeExtractor, SourceViewer)
- 跨模块信号追踪
- 详细文档 ADR-003

### v0.3.1 (2026-04-18)
- 真实项目测试: tiny-gpu, basic_verilog
- 支持 NetPortHeaderSyntax (input wire) 端口语法
- 更新测试框架

### v0.3.2 (2026-04-18)
- 创建 ControlFlowTracer (控制流分析框架)
- 创建 DependencyAnalyzer (依赖分析框架)
- 创建 Idea.md 功能想法池
- 修复 DriverTracer 支持 AlwaysComb 语法

### v0.3.3 (2026-04-19)
- **修复 if/else 驱动提取**: 支持所有 if/else if/else 嵌套结构
- **修复 Case 语句**: 使用 `item.clause` 替代 `item.body`
- **支持 Generate 语句**: IfGenerate/LoopGenerate/CaseGenerate/GenerateBlock

### v0.3.4 (2026-04-19)
- **参数化模块实例化支持**: `#(.PARAM(value))` 语法
- **支持多参数实例化**: `.A(4), .B(16)`
- **支持数组实例化**: `u_sub[0:3]`

### v0.4 (2026-04-21)
- **ClassExtractor 修复**:
  - 添加 `extract()` 方法
  - 属性限定符提取 (rand/randc/local/protected/static/const)
  - 数组维度提取 (从 declarator)
  - Soft constraint 检测
  - Dist constraint 解析
- **UVM 分析**:
  - UVMExtractor 实现
  - TLM 连接提取
  - Phase 方法提取
  - 从真实 UVM testbench 测试
- **ClassRelationExtractor**:
  - 修复 MethodCallInfo constraint_name 字段

---

## 未来规划 (v0.5+)

### 增强功能
| 功能 | 优先级 |
|------|--------|
| UVM Config DB 提取 | P1 |
| UVM Sequence 追踪 | P1 |
| Coverage 分析集成 | P2 |
| 报告生成器 (HTML) | P2 |

### DebugAssistant - AI 辅助调试
| 场景 | 功能 |
|------|------|
| 信号追踪 | 自然语言查询驱动/负载 |
| 数据流分析 | 端到端数据流追踪 |
| 问题诊断 | X值/多驱动根因分析 |
| 批量检查 | 一键全量问题检测 |
| 跨模块追踪 | 层级路径驱动追踪 |
| 时钟域分析 | clock domain 识别 |

详细设计见 `docs/adr/ADR-006-ai-debug.md`

## 其他文档

- **Idea.md** - 功能想法池，记录待实现的功能
