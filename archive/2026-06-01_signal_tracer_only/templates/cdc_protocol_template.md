# CDC协议文档

## 模块: {{module_name}}
## 版本: {{version}}
## 日期: {{date}}
## 作者: {{author}}

---

## 1. 概述

### 1.1 模块功能
{{module_description}}

### 1.2 时钟域数量
本模块共包含 **{{clock_domain_count}}** 个时钟域

---

## 2. 时钟域概览

| 时钟域 | 频率 | 来源 | 用途 | 同步器级数 |
|--------|------|------|------|------------|
{{clock_domains_table}}

---

## 3. CDC路径清单

### 3.1 跨时钟域路径汇总

| 路径ID | 信号名 | 源时钟 | 目标时钟 | 同步器类型 | 数据宽度 | 风险等级 |
|--------|--------|--------|----------|------------|----------|----------|
{{cdc_paths_table}}

### 3.2 详细路径分析

{{#each cdc_paths}}
#### 3.2.{{id}} {{signal_name}}

- **路径**: {{src_clock}} → {{dst_clock}}
- **信号类型**: {{signal_type}}
- **数据宽度**: {{width}} bits
- **同步器类型**: {{sync_type}}
- **风险等级**: {{risk_level}}

**描述**: {{description}}

**验证要点**:
{{verification_points}}

**潜在风险**: {{risks}}

**缓解措施**: {{mitigations}}

---
{{/each}}

## 4. 同步器配置详情

### 4.1 1-bit同步器 (电平同步)

```systemverilog
// {{sync_name}}
always_ff @(posedge {{dst_clk}} or negedge {{rst_n}}) begin
    if (!{{rst_n}}) begin
        {{sync_signal}}_sync <= 1'b0;
        {{sync_signal}}_meta <= 1'b0;
    end else begin
        {{sync_signal}}_meta <= {{async_signal}};
        {{sync_signal}}_sync <= {{sync_signal}}_meta;
    end
end
```

### 4.2 2-bit同步器 (握手同步)

```systemverilog
// {{handshake_sync_name}}
```

### 4.3 多-bit同步器 (格雷码同步)

```systemverilog
// {{gray_sync_name}}
```

---

## 5. 握手协议

### 5.1 {{handshake_name}}

| 阶段 | 信号 | 描述 |
|------|------|------|
{{handshake_table}}

**时序图**:
```
{{timing_diagram}}
```

### 5.2 握手状态机

```systemverilog
{{handshake_fsm}}
```

---

## 6. CDC验证清单

- [ ] 所有跨时钟域路径已识别
- [ ] 同步器类型选择正确
- [ ] 同步器级数满足可靠性要求 (≥2级)
- [ ] 复位同步释放处理正确 (异步复位，同步释放)
- [ ] 多位数据跨时钟域使用格雷码或握手协议
- [ ] CDC路径有相应SVA断言
- [ ] CDC覆盖率达到目标 (>90%)
- [ ] 无 combinational 逻辑直接跨时钟域
- [ ] 快到慢时钟域有确认机制

---

## 7. 已知风险与缓解

| 风险 | 影响 | 缓解措施 | 验证状态 |
|------|------|----------|----------|
{{risks_table}}

---

## 8. 覆盖计划

| CDC路径 | 覆盖类型 | 目标 | 实际 |
|---------|----------|------|------|
{{coverage_plan}}

---

## 9. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | {{date}} | 初始版本 | {{author}} |

---

*本文档由SV-Trace自动生成*
