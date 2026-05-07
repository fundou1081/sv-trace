# sv-trace 项目结构

> 2026-05-06 整理

## 目录结构

```
sv-trace/
├── Makefile                 # 统一测试运行器
├── pytest.ini              # pytest 配置
├── requirements.txt         # 依赖
├── STRUCTURE.md            # 本文档
│
├── src/                    # 源代码
│   ├── sv_manager.py       # 统一入口
│   ├── trace/             # 核心分析工具
│   │   ├── driver.py      # 驱动提取
│   │   ├── load.py       # 文件加载
│   │   ├── connection.py # 模块连接
│   │   ├── dataflow.py  # 数据流分析
│   │   ├── controlflow.py # 控制流
│   │   ├── dependency.py # 依赖图
│   │   ├── timing_path.py # 时序路径
│   │   ├── query/        # Query 工具
│   │   │   ├── signal_chain.py
│   │   │   ├── module_connections.py
│   │   │   ├── clock_domain.py
│   │   │   └── timing_path.py
│   │   ├── semantic/     # 语义层
│   │   │   └── builder.py
│   │   └── core/         # 核心基类
│   │       ├── base.py
│   │       └── interfaces.py
│   │
│   └── parse/            # 解析模块
│
├── tests/                 # 测试
│   ├── unit/tools/       # 工具单元测试
│   │   └── test_driver.py
│   ├── integration/      # 集成测试
│   └── e2e/              # 端到端
│
├── docs/                  # 文档
│   ├── index.md          # 文档索引
│   ├── README.md         # 项目概览
│   ├── DEVELOPMENT_DISCIPLINE.md # 开发纪律
│   ├── tier/             # 分层文档
│   └── guides/           # 指南
│
├── skills/               # Agent Skills
│
└── archive/               # 归档
    ├── deprecated/       # 已废弃的脚本
    └── USER_REQUIREMENTS.md # 需求记录
```

## 核心模块 (17 个)

| 模块 | 功能 |
|------|------|
| driver | 时钟/复位提取 |
| load | 文件加载 |
| connection | 模块连接分析 |
| dataflow | 数据流分析 |
| controlflow | 控制流分析 |
| dependency | 依赖图 |
| timing_path | 时序路径分析 |
| flow_analyzer | 流程分析 |
| parse_warn | 警告解析 |
| load_ext | 扩展加载 |
| signal_classifier | 信号分类 |
| area_estimator | 面积估算 |
| power_estimation | 功耗估算 |
| resource_estimation | 资源估算 |
| timing_depth | 时序深度 |
| pipeline_analyzer | 流水线分析 |
| query/* | 4 个 Query 工具 |

## 测试运行

```bash
make test              # 全部
make test-unit        # 单元
make test-int         # 集成
make test-e2e         # E2E
make test TOOLS=xxx   # 指定工具
```

## 归档模块 (11 个)

见 `archive/deprecated/`
