# SV-TRACE 项目结构

> 更新时间: 2026-05-15

## 目录结构

```
sv-trace/
├── src/                    # 核心源代码
│   ├── parse/             # ✅ pyslang 封装 (SVParser)
│   ├── scope/             # ✅ Pass 1: 作用域体系
│   ├── extractors/        # ✅ Pass 2: 提取器体系
│   ├── semantic/          # ✅ Pass 3: 语义增强层
│   ├── trace/             # ✅ 对外 API 层
│   ├── debug/             # ✅ 调试分析器 (已适配 pyslang)
│   └── verify/            # 验证工具
│
├── tests/                 # 测试 (229 tests pass)
│   ├── unit/             # 单元测试
│   ├── trace/            # trace 模块测试
│   └── tools/            # 工具函数测试
│
├── docs/                  # 文档
│   ├── guides/           # 指南
│   ├── core/            # 核心模块文档
│   ├── adr/             # 架构决策记录
│   └── reference/        # 参考文档
│
└── skills/               # Agent Skills
```

## 测试状态 (2026-05-15)

| 套件 | 测试数 | 状态 |
|------|--------|------|
| trace/ + tools/ | 229 | ✅ Pass |
| test_class.py | 18 | ✅ Pass |
| test_targeted.py | 6 | ✅ Pass |
| **总计** | **229** | ✅ **0 warnings** |

### 设计原则

1. **原子化** - 每个解析器专注单一语法类别
2. **组合式** - 可基于现有 parser 派生新 parser
3. **AST 优先** - 使用 pyslang AST 遍历，无正则表达式

---

*最后更新: 2026-05-02*
