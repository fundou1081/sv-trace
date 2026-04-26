---
name: cdc-documentation
description: CDC协议文档生成工具，基于CDC分析结果生成标准化的CDC协议文档和检查清单。
---

# CDC Documentation Skill

CDC文档生成

## 功能

- 生成CDC协议文档模板
- 生成CDC检查清单
- 标准化时钟域描述

## 使用

### 1. 分析CDC
```bash
sv-cdc design.sv --output cdc_report.json
```

### 2. 生成文档
使用 templates/cdc_protocol_template.md 作为模板

### 3. 填充以下内容

```markdown
## 模块: <module_name>
## 时钟域数量: <count>

| 时钟域 | 频率 | 来源 |
|--------|------|------|
| clk_a | 100MHz | 外部 |
| clk_b | 50MHz | PLL |

## CDC路径

| 信号 | 源 | 目标 | 同步器 |
|------|-----|------|--------|
| data_b | clk_a | clk_b | 2FF |
```

## 检查清单

使用 templates/cdc_checklist.md

## 模板位置

```
templates/
├── cdc_protocol_template.md
└── cdc_checklist.md
```
