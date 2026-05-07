# SV-TRACE 项目结构

## 目录结构

```
sv-trace/
├── src/                    # 核心源代码
│   ├── parse/             # ✅ 解析器 (302 files) - 基于 pyslang AST
│   ├── trace/            # 追踪模块 (22 files)
│   ├── query/           # 查询模块 (13 files)
│   └── debug/           # 调试模块 (21 files)
│
├── docs/                  # 文档 (40+ files)
│   ├── PARSER_SUPPORT.md # ⭐ Parser 支持文档 v1.0
│   ├── adr/              # 架构决策记录 (28 files)
│   ├── pyslang-spec/     # pyslang 语法规范
│   └── *.md              # 各模块文档
│
├── tests/                 # 测试
│   ├── test_*.py         # 基本测试
│   ├── edge_cases/       # 边界测试
│   └── targeted/          # 针对性测试
│
└── [项目根目录文件]       # 配置文件
```

## 统计

| 目录 | 文件数 | 说明 |
|------|--------|------|
| src/parse | **302** | ✅ 基于 pyslang AST 的原子化解析器 |
| src/trace | 22 | 核心追踪引擎 |
| src/query | 13 | 查询功能 |
| src/debug | 21 | 高级分析工具 |
| docs | 40+ | 文档 |
| tests | 60+ | 测试用例 |

---

## Parser Foundation v1.0 里程碑

```
✅ 解析器文件: 302 个
✅ 支持语法: 603 种
✅ 覆盖率: 112%
✅ sv-tests 成功率: 100%
```

### 设计原则

1. **原子化** - 每个解析器专注单一语法类别
2. **组合式** - 可基于现有 parser 派生新 parser
3. **AST 优先** - 使用 pyslang AST 遍历，无正则表达式

---

*最后更新: 2026-05-02*
