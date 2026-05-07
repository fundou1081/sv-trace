# sv-trace 项目结构

> 2026-05-07 整理

## 目录结构

```
sv-trace/
├── src/                    # 源代码
│   ├── core/              # 核心模型
│   ├── parse/             # 解析器
│   ├── semantic/          # 语义层
│   │   ├── utils.py       # 公共工具函数
│   │   ├── clock.py       # 时钟域 (ClockExtractor)
│   │   ├── driver.py      # 驱动 (DriverExtractor)
│   │   ├── load.py        # 负载 (LoadExtractor)
│   │   └── ...
│   ├── trace/             # 追踪层
│   │   ├── driver.py      # DriverCollector
│   │   ├── load.py        # LoadTracer
│   │   └── ...
│   └── query/             # 查询层
│
├── tests/                 # 测试
│   ├── sv_cases/          # 测试用例
│   │   └── driver/        # Driver 测试用例
│   ├── test_driver_*.py   # Driver 测试
│   └── ...
│
├── docs/                  # 文档
│   ├── DEVELOPMENT_DISCIPLINE.md  # 开发纪律
│   ├── adr/               # 架构决策记录
│   ├── core/              # 核心文档
│   ├── guides/            # 指南
│   └── reference/         # 参考文档
│
├── archive/               # 归档
│   └── deprecated/        # 已弃用代码
│
├── Makefile               # 构建脚本
├── pytest.ini             # pytest 配置
├── STRUCTURE.md           # 项目结构 (本文件)
├── TEST_PLAN.md           # 测试计划
└── TODO.md                # 开发计划
```

## 核心架构

### 语义层 (semantic/)

使用 **Extractor 模式** 提取硬件语义：

| Extractor | 功能 | 符合铁律 |
|-----------|------|----------|
| ClockExtractor | 时钟/复位提取 | 1, 17 |
| DriverExtractor | 驱动关系提取 | 1, 17 |
| LoadExtractor | 负载关系提取 | 1, 17 |

### 追踪层 (trace/)

使用 **Collector 模式** 收集设计信息：

| Collector | 功能 |
|-----------|------|
| DriverCollector | 驱动信息收集 |
| LoadTracer | 负载信息收集 |

## 开发纪律

详见 [docs/DEVELOPMENT_DISCIPLINE.md](docs/DEVELOPMENT_DISCIPLINE.md)

### 核心铁律

1. **铁律 1**: AST 唯一数据源
2. **铁律 17**: 提取逻辑封装为独立 Visitor 类

### 测试

```bash
make test                  # 运行所有测试
pytest tests/test_driver_*.py  # 运行 Driver 测试
```
