# SV-Trace JSON Schema Reference

每个工具的输入输出格式定义。

---

## 目录

1. [底层解析 (Parse)](#底层解析-parse)
2. [信号追踪 (Trace)](#信号追踪-trace)
3. [验证相关 (Verify)](#验证相关-verify)
4. [代码检查 (Lint)](#代码检查-lint)
5. [Debug分析](#debug分析)

---

## 底层解析 (Parse)

### 1. SVParser

SystemVerilog 解析器主入口。

**Input:**
```json
{
  "source": "module test; endmodule",
  "files": ["/path/to/file.sv"],
  "options": {
    "top": "test"
  }
}
```

**Output:**
```json
{
  "success": true,
  "trees": {
    "test": { "root": "...", "kind": "ModuleDeclaration" }
  },
  "errors": []
}
```

---

### 2. ModuleIOExtractor

模块端口和参数提取。

**Input:**
```json
{
  "source": "module uart (input clk, output tx); endmodule"
}
```

**Output:**
```json
{
  "module": "uart",
  "ports": [
    { "name": "clk", "direction": "input", "width": 1 },
    { "name": "tx", "direction": "output", "width": 1 }
  ],
  "params": [
    { "name": "BAUD", "value": "9600" }
  ]
}
```

---

### 3. ClassExtractor

Class 成员、方法、约束提取。

**Input:**
```json
{
  "source": "class Packet; rand bit [7:0] data; endclass"
}
```

**Output:**
```json
{
  "name": "Packet",
  "members": [
    { "name": "data", "type": "bit", "width": 8, "rand": "rand" }
  ],
  "methods": [
    { "name": "new", "kind": "function", "return_type": "" }
  ],
  "constraints": []
}
```

---

### 4. ConstraintExtractor

Constraint 内容提取。

**Input:**
```json
{
  "source": "constraint c_data { data < 100; }"
}
```

**Output:**
```json
[
  {
    "name": "c_data",
    "class": "Packet",
    "expr": "data < 100;"
  }
]
```

---

## 信号追踪 (Trace)

### 5. DriverTracer

信号驱动追踪。

**Input:**
```json
{
  "signal": "uart.tx",
  "scope": "top.uart"
}
```

**Output:**
```json
{
  "signal": "uart.tx",
  "drivers": [
    {
      "type": "always",
      "source": "always @(posedge clk)",
      "stmt": "tx <= data_out;"
    }
  ],
  "loads": []
}
```

---

### 6. LoadTracer

信号负载追踪。

**Input:**
```json
{
  "signal": "clk",
  "scope": "top"
}
```

**Output:**
```json
{
  "signal": "clk",
  "loads": [
    { "type": "flipflop", "name": "ff_0", "pin": "D" }
  ]
}
```

---

### 7. ConnectionTracer

模块实例连接追踪。

**Input:**
```json
{
  "instance": "uart_0"
}
```

**Output:**
```json
{
  "instance": "uart_0",
  "module": "uart",
  "connections": [
    { "port": "clk", "net": "sys_clk" },
    { "port": "tx", "net": "uart_tx" }
  ]
}
```

---

### 8. ControlFlowTracer

控制流分析。

**Input:**
```json
{
  "module": "fsm_controller"
}
```

**Output:**
```json
{
  "module": "fsm_controller",
  "blocks": [
    { "id": 1, "type": "always", "stmt": "if (state == IDLE)" }
  ],
  "edges": [
    { "from": 1, "to": 2, "cond": "start" }
  ]
}
```

---

### 9. DataPathAnalyzer

数据路径分析。

**Input:**
```json
{
  "module": "alu"
}
```

**Output:**
```json
{
  "module": "alu",
  "input_ports": ["a", "b", "op"],
  "output_ports": ["result", "zero"],
  "registers": ["acc", "tmp"],
  "operations": [
    { "type": "add", "inputs": ["a", "b"], "output": "tmp" }
  ]
}
```

---

## 验证相关 (Verify)

### 10. CoverageStimulusSuggester

Coverage 点和激励生成。

**Input:**
```json
{
  "source": "if (valid && ready) data_out = data_in;",
  "conditions": [
    { "expr": "valid && ready", "type": "if", "kind": "condition" }
  ]
}
```

**Output:**
```json
{
  "coverage_points": [
    {
      "id": "cp_0",
      "condition": "valid && ready",
      "type": "if",
      "suggestions": ["valid=1 && ready=1", "valid=0", "ready=0"]
    }
  ],
  "covergroup": "covergroup cg_design @(posedge clk); ..." 
}
```

---

### 11. CoverageAdvisor

覆盖率分析与建议。

**Input:**
```json
{
  "current_coverage": 75.5,
  "total_points": 100,
  "covered_points": 75
}
```

**Output:**
```json
{
  "coverage": 75.5,
  "grade": "B",
  "recommendations": [
    { "priority": "high", "point": "tx_en && state==TX", "suggestion": "add directed test" }
  ]
}
```

---

### 12. ConstraintGenerator

约束生成。

**Input:**
```json
{
  "class": "Packet",
  "members": [
    { "name": "data", "type": "bit", "width": 8, "rand": "rand" }
  ]
}
```

**Output:**
```json
{
  "constraints": [
    { "name": "c_data", "expr": "data inside {[0:100]};" }
  ]
}
```

---

## 代码检查 (Lint)

### 13. Linter

代码风格检查。

**Input:**
```json
{
  "source": "module test; wire [7:0] data; endmodule",
  "rules": ["naming", "whitespace"]
}
```

**Output:**
```json
{
  "issues": [
    {
      "severity": "warning",
      "rule": "naming",
      "line": 1,
      "message": "Identifier 'data' should use camelCase",
      "suggestion": "iData"
    }
  ],
  "summary": { "errors": 0, "warnings": 1 }
}
```

---

### 14. SyntaxChecker

语法检查。

**Input:**
```json
{
  "source": "module test; endmodule"
}
```

**Output:**
```json
{
  "valid": true,
  "errors": []
}
```

---

## Debug分析

### 15. FSMAnalyzer

状态机分析。

**Input:**
```json
{
  "module": "uart_ctrl"
}
```

**Output:**
```json
{
  "module": "uart_ctrl",
  "states": ["IDLE", "TX", "DONE"],
  "state_vars": ["state", "next_state"],
  "transitions": [
    { "from": "IDLE", "to": "TX", "cond": "tx_start" },
    { "from": "TX", "to": "DONE", "cond": "tx_done" }
  ]
}
```

---

### 16. CDCAnalyzer

跨时钟域分析。

**Input:**
```json
{
  "module": "top"
}
```

**Output:**
```json
{
  "clock_domains": [
    { "name": "clk_a", "freq": 100 },
    { "name": "clk_b", "freq": 50 }
  ],
  "cdc_paths": [
    {
      "from": "clk_a",
      "to": "clk_b",
      "signals": ["data_sync"],
      "safe": false,
      "recommendation": "add synchronizer"
    }
  ]
}
```

---

### 17. DependencyAnalyzer

依赖分析。

**Input:**
```json
{
  "module": "cpu"
}
```

**Output:**
```json
{
  "module": "cpu",
  "dependencies": [
    { "module": "alu", "type": "instantiation" },
    { "module": "regfile", "type": "instantiation" }
  ],
  "dependents": ["top", "soc"]
}
```

---

## 通用格式

### Port Direction
```json
"input" | "output" | "inout" | "ref"
```

### Signal Type
```json
"wire" | "reg" | "logic" | "bit"
```

### Severity
```json
"error" | "warning" | "info" | "hint"
```

---

