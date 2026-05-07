# sv-trace 测试管理方案

## 1. 测试分层架构

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
