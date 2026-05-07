# sv-trace 文档索引

## 🎯 快速开始

```bash
cd ~/my_dv_proj/sv-trace
make test              # 运行全部测试
make test-unit       # 单元测试
make test-e2e        # E2E 测试
```

## 📁 项目结构

```
sv-trace/
├── src/
│   ├── sv_manager.py     # 统一入口
│   ├── trace/          # 核心分析工具 (7模块)
│   ├── semantic/       # 语义层 (8模块)
│   ├── query/         # 查询工具 (4个)
│   ├── parse/         # 解析器封装
│   └── debug/         # 调试分析器 (29个)
│
├── tests/              # 测试 (单元/集成/E2E)
├── docs/              # 文档
└── benchmarks/         # 基准测试 (10个)
```

## 📖 核心文档

| 文档 | 说明 |
|------|------|
| [STRUCTURE.md](../STRUCTURE.md) | 项目结构 (最新) |
| [DEVELOPMENT_DISCIPLINE.md](DEVELOPMENT_DISCIPLINE.md) | 开发纪律 |
| [TEST_PLAN.md](../TEST_PLAN.md) | 测试计划 |

## 🛠️ 核心模块文档

| 文档 | 模块 |
|------|------|
| [core/driver_collector.md](core/driver_collector.md) | driver |
| [core/connection.md](core/connection.md) | connection |
| [core/dataflow.md](core/dataflow.md) | dataflow |
| [core/controlflow.md](core/controlflow.md) | controlflow |
| [core/timing_path.md](core/timing_path.md) | timing_path |
| [core/load.md](core/load.md) | load |
| [core/pipeline_analyzer.md](core/pipeline_analyzer.md) | pipeline |

## 📚 扩展阅读

| 路径 | 说明 |
|------|------|
| [guides/](guides/) | 开发指南 |
| [reference/](reference/) | API 参考 |
| [adr/](adr/) | 架构决策记录 (31个) |

## 🗂️ 归档

| 路径 | 说明 |
|------|------|
| [archive/](archive/) | 历史文档 |
| [archive/reports/](archive/reports/) | 旧测试报告 |
| [archive/legacy/](archive/legacy/) | 废弃文档 |

---

> 💡 文档过多？大部分归档文档已过时，建议优先阅读根目录的 `STRUCTURE.md` 和 `DEVELOPMENT_DISCIPLINE.md`
