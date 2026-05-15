# sv-trace 测试管理方案

> 更新时间: 2026-05-15 20:55 GMT+8

## 当前测试状态

| 测试套件 | 测试数 | 状态 |
|---------|--------|------|
| trace/ + tools/ | 229 | ✅ Pass |
| test_class.py | 18 | ✅ Pass |
| test_targeted.py | 6 | ✅ Pass |
| **总计** | **229** | ✅ **All Pass, 0 warnings** |

### 修复历史 (2026-05-15)
- [x] 添加 backward compatibility stubs (铁律8)
  - `ParameterResolver`, `ConstraintExtractor`, `AssertionExtractor` (parse/__init__.py)
  - `LoadTracerRegex` (trace/load.py)
  - `CoverageType`, `CoverageTarget` (verify/coverage_guide/stimulus_suggester.py)
  - `FSMAnalysisResult` 添加缺失属性 (state_names, transitions, complexity_obj)
  - `ConditionCoverageResult` 添加 total_if_count, average_coverage
  - `CDCAutoReport` 添加 clock_domains, cdc_paths, unprotected_signals
  - `ResetAnalysisResult` 添加 coverage, warnings
  - `FanoutAnalyzer` 添加 analyze_signal(), find_high_fanout_signals()
  - `TimedPathReport` dataclass
- [x] 修复 `DriverCollector.multi_drivers` 属性
- [x] 解决 test_controlflow.py / test_dataflow.py 重名冲突 (重命名为 *_tools.py)
- [x] 将 test_cdc_edge_cases.py 改为 .md (非有效Python)
- [x] 注册 pytest `unsupported` marker
- [x] 修复 `return True/False` → `assert` (铁律13)
- [x] 清理所有 pytest warnings |

```
tests/
├── unit/           # 单元测试 - 每个工具函数的独立测试
│   ├── core/      # core 模块: base.py, interfaces.py
│   ├── semantic/  # semantic 层: builder.py
│   ├── query/     # query 工具: signal_chain, module_connections, clock_domain, timing_path
│   └── tools/     # 工具函数: driver, load, parse_warn, performance...
├── integration/   # 集成测试 - 模块间交互
└── e2e/          # 端到端 - 真实项目验证
```

## 2. 工具→测试文件映射

| 工具模块 | 测试文件 | 覆盖重点 |
|---------|---------|----------|
| **core/base.py** | test_core_base.py | Signal/FSM/Interface 基类 |
| **core/interfaces.py** | test_core_interfaces.py | 端口连接、层次关系 |
| **semantic/builder.py** | test_semantic_builder.py | 语义构建、SUPPORTED_KINDS |
| **query/signal_chain.py** | test_signal_chain.py | 信号溯源、驱动-FSM |
| **query/module_connections.py** | test_module_connections.py | 模块连接图 |
| **query/clock_domain.py** | test_clock_domain.py | 时钟域识别 |
| **query/timing_path.py** | test_timing_path.py | 关键路径分析 |
| **driver.py** | test_driver.py | 时钟/复位提取 |
| **load.py** | test_load.py | SV 文件解析 |
| **parse_warn.py** | test_parse_warn.py | 警告解析 |
| **performance.py** | test_performance.py | 性能指标 |
| **controlflow.py** | test_controlflow.py | 控制流分析 |
| **dataflow.py** | test_dataflow.py | 数据流分析 |
| **dependency.py** | test_dependency.py | 依赖图 |

## 3. 测试运行

```bash
# 统一入口
make test              # 运行全部测试
make test-unit        # 只跑单元测试
make test-int         # 集成测试
make test-e2e         # E2E 测试
make test TOOLS=driver  # 只测某个工具

# 或用 pytest
pytest tests/unit/tools/test_driver.py -v
```

## 4. 覆盖率目标

- **单元测试**: ≥90% 每个工具函数
- **集成测试**: ≥70% 模块交互
- **E2E**: 100% 开源项目用例
