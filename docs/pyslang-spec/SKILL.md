# pyslang SystemVerilog 语法规范

## 概述

本规范将 pyslang 的 SyntaxKind (536个类型) 映射到 Python 类和实际语法结构，帮助开发者理解如何使用 pyslang AST 解析 SystemVerilog。

## 快速参考

```python
import pyslang
from pyslang import SyntaxKind

# 解析
tree = pyslang.SyntaxTree.fromText(sv_code)
root = tree.root

# 遍历
def collector(node):
    if node.kind == SyntaxKind.TargetKind:
        # 处理
    return pyslang.VisitAction.Advance

tree.root.visit(collector)
```

## 目录

1. [语法分类总览](#1-语法分类总览)
2. [声明类 (Declaration)](#2-声明类-declaration)
3. [约束类 (Constraint)](#3-约束类-constraint)
4. [类相关 (Class)](#4-类相关-class)
5. [端口/IO (Port/IO)](#5-端口io-portio)
6. [函数/任务 (Function/Task)](#6-函数任务-functiontask)
7. [覆盖组 (Covergroup)](#7-覆盖组-covergroup)
8. [序列/属性 (Sequence/Property)](#8-序列属性-sequenceproperty)
9. [常用属性参考](#9-常用属性参考)

---

## 1. 语法分类总览

| 类别 | 数量 | 说明 |
|------|------|------|
| Declaration | 44 | 声明类 |
| Statement | 39 | 语句类 |
| Expression | 111 | 表达式类 |
| Type | 29 | 类型类 |
| Port | 34 | 端口类 |
| Module | 6 | 模块/接口类 |
| Class | 3 | 类相关 |
| Property | 23 | 属性相关 |
| Method | 4 | 方法相关 |
| Constraint | 10 | 约束相关 |
| Sequence | 13 | 序列相关 |
| Cover | 11 | 覆盖相关 |
| Other | 209 | 其他 |

---

## 2. 声明类 (Declaration)

### 2.1 ModuleDeclaration

**SystemVerilog:**
```systemverilog
module module_name #(...) (...);
  // ports and body
endmodule
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 模块名 |
| `header` | ModuleHeader | 模块头（包含端口） |
| `items` | list | 模块内容 |
| `kind` | SyntaxKind | 固定为 `ModuleDeclaration` |

**示例:**
```python
for item in root.items:
    if item.kind == SyntaxKind.ModuleDeclaration:
        name = str(item.name)
        # 遍历端口
        for port in item.header.ports:
            port_name = str(port.declarator.name)
```

### 2.2 InterfaceDeclaration

**SystemVerilog:**
```systemverilog
interface interface_name (...);
endinterface
```

**Python 属性:** 与 ModuleDeclaration 类似

---

## 3. 约束类 (Constraint)

### 3.1 ConstraintDeclaration

**SystemVerilog:**
```systemverilog
constraint constraint_name { expression; }
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 约束名 |
| `block` | SyntaxNode | 约束体 |
| `kind` | SyntaxKind | `ConstraintDeclaration` |

**示例:**
```python
def extract_constraints(code):
    import pyslang
    from pyslang import SyntaxKind
    
    results = []
    tree = pyslang.SyntaxTree.fromText(code)
    
    def collect(node):
        if node.kind == SyntaxKind.ConstraintDeclaration:
            results.append({
                'name': str(node.name).strip(),
                'kind': 'constraint'
            })
        return pyslang.VisitAction.Advance
    
    tree.root.visit(collect)
    return results
```

### 约束类型

| SyntaxKind | 说明 |
|------------|------|
| `ConstraintBlock` | 约束块 |
| `ExpressionConstraint` | 表达式约束 |
| `ConditionalConstraint` | 条件约束 (if-else) |
| `ImplicationConstraint` | 隐含约束 (->) |
| `LoopConstraint` | 循环约束 (foreach) |
| `DistConstraintList` | 分布约束 (dist) |
| `SolveBeforeConstraint` | 求解顺序约束 |
| `DisableConstraint` | 禁用约束 |
| `UniquenessConstraint` | 唯一性约束 |

---

## 4. 类相关 (Class)

### 4.1 ClassDeclaration

**SystemVerilog:**
```systemverilog
class class_name extends base_class;
  // members and methods
endclass
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 类名 |
| `items` | SyntaxNode | 类成员列表 |
| `extendsClause` | str | 父类（可选） |
| `implementsClause` | str | 实现的接口 |
| `virtualOrInterface` | str | 虚拟或接口修饰 |

**items 包含的节点类型:**
- `ClassPropertyDeclaration` - 成员变量
- `ClassMethodDeclaration` - 方法
- `ConstraintDeclaration` - 约束
- `ClassMethodPrototype` - 方法原型

### 4.2 ClassPropertyDeclaration

**SystemVerilog:**
```systemverilog
rand bit [7:0] data;
bit [3:0] addr;
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `declaration` | str | 声明字符串 (如 "bit [7:0] data;") |
| `qualifiers` | str | 修饰符 (如 "rand", "randc") |
| `kind` | SyntaxKind | `ClassPropertyDeclaration` |

### 4.3 ClassMethodDeclaration

**SystemVerilog:**
```systemverilog
function bit [7:0] get_data();
  return data;
endfunction
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `declaration` | str | 声明字符串 |
| `prototype` | FunctionPrototype | 方法原型 |
| `qualifiers` | str | 修饰符 |

---

## 5. 端口/IO (Port/IO)

### 5.1 ImplicitAnsiPort

**SystemVerilog:**
```systemverilog
input logic [7:0] data,
output bit valid
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `header` | VariablePortHeader | 端口头（方向+类型） |
| `declarator` | Declarator | 端口名 |
| `kind` | SyntaxKind | `ImplicitAnsiPort` |

**header 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `direction` | Token | input/output/inout |
| `direction.kind` | TokenKind | 如 `InputKeyword` |

### 5.2 端口方向判断

```python
from pyslang import TokenKind

def get_port_direction(port):
    direction = port.header.direction
    if direction.kind == TokenKind.InputKeyword:
        return 'input'
    elif direction.kind == TokenKind.OutputKeyword:
        return 'output'
    elif direction.kind == TokenKind.InoutKeyword:
        return 'inout'
    return 'unknown'
```

---

## 6. 函数/任务 (Function/Task)

### 6.1 FunctionDeclaration

**SystemVerilog:**
```systemverilog
function bit [7:0] foo(input a, input b);
  return a + b;
endfunction
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `prototype` | FunctionPrototype | 函数原型 |
| `items` | list | 函数体 |
| `kind` | SyntaxKind | `FunctionDeclaration` |

### 6.2 FunctionPrototype

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 函数名 |
| `returnType` | str | 返回类型 |
| `portList` | list | 参数列表 |

---

## 7. 覆盖组 (Covergroup)

### 7.1 CovergroupDeclaration

**SystemVerilog:**
```systemverilog
covergroup cg_name;
  coverpoint cp_name;
endgroup
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 覆盖组名 |
| `items` | list | 覆盖点列表 |
| `kind` | SyntaxKind | `CovergroupDeclaration` |

### 7.2 Coverpoint

| SyntaxKind | 说明 |
|------------|------|
| `Coverpoint` | 覆盖点 |
| `CoverCross` | 交叉覆盖 |

---

## 8. 序列/属性 (Sequence/Property)

### 8.1 SequenceDeclaration

**SystemVerilog:**
```systemverilog
sequence seq_name;
  data ##1 valid;
endsequence
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 序列名 |
| `kind` | SyntaxKind | `SequenceDeclaration` |

### 8.2 PropertyDeclaration

**SystemVerilog:**
```systemverilog
property prop_name;
  req |-> resp;
endproperty
```

**Python 属性:**
| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | str | 属性名 |
| `kind` | SyntaxKind | `PropertyDeclaration` |

### Assertion 语句类型

| SyntaxKind | 说明 |
|------------|------|
| `AssertPropertyStatement` | assert property |
| `AssumePropertyStatement` | assume property |
| `CoverPropertyStatement` | cover property |
| `AssertStatement` | assert |
| `AssumeStatement` | assume |
| `CoverStatement` | cover |

---

## 9. 常用属性参考

### 9.1 所有节点通用属性

| 属性 | 说明 |
|------|------|
| `kind` | SyntaxKind 枚举值 |
| `parent` | 父节点 |
| `sourceRange` | 源码位置 |
| `attributes` | 属性列表 |

### 9.2 遍历方法

```python
# 方法1: visit() - 推荐
tree.root.visit(collector)

# 方法2: 直接迭代
for child in node:
    print(child.kind)

# 方法3: 获取特定属性
items = node.items  # 可能是 SyntaxNode 或 list
```

### 9.3 获取节点字符串表示

```python
node_str = str(node)  # 获取源码字符串
```

### 9.4 判断节点类型

```python
# 方法1: 比较 kind
if node.kind == SyntaxKind.ClassDeclaration:
    ...

# 方法2: 检查 kind 名称
if 'Class' in node.kind.name:
    ...

# 方法3: 比较 kind 值
if node.kind.name == 'ClassDeclaration':
    ...
```

---

## 10. 实际使用示例

### 10.1 提取所有类及其成员

```python
import pyslang
from pyslang import SyntaxKind

def extract_classes(code):
    results = []
    
    def collect(node):
        if node.kind == SyntaxKind.ClassDeclaration:
            cls_info = {
                'name': str(node.name).strip(),
                'members': [],
                'methods': [],
                'constraints': []
            }
            
            for item in node.items:
                kn = item.kind.name
                
                if 'Property' in kn or 'Rand' in kn:
                    # 提取成员
                    qualifiers = str(item.qualifiers).strip()
                    decl = str(item.declaration).strip().rstrip(';')
                    cls_info['members'].append({
                        'qualifiers': qualifiers,
                        'declaration': decl
                    })
                
                elif 'Method' in kn and 'Declaration' in kn:
                    decl = str(item.declaration).strip() if item.declaration else ''
                    cls_info['methods'].append({'declaration': decl})
                
                elif 'Constraint' in kn:
                    cls_info['constraints'].append({
                        'name': str(item.name).strip()
                    })
            
            results.append(cls_info)
        
        return pyslang.VisitAction.Advance
    
    tree = pyslang.SyntaxTree.fromText(code)
    tree.root.visit(collect)
    return results
```

### 10.2 提取模块 IO

```python
import pyslang
from pyslang import SyntaxKind

def extract_module_io(code):
    results = []
    
    def collect(node):
        if node.kind == SyntaxKind.ModuleDeclaration:
            io_info = {
                'name': str(node.name).strip(),
                'inputs': [],
                'outputs': []
            }
            
            for port in node.header.ports:
                port_name = str(port.declarator.name).strip()
                direction = port.header.direction.kind.name
                
                if 'Input' in direction:
                    io_info['inputs'].append(port_name)
                elif 'Output' in direction:
                    io_info['outputs'].append(port_name)
            
            results.append(io_info)
        
        return pyslang.VisitAction.Advance
    
    tree = pyslang.SyntaxTree.fromText(code)
    tree.root.visit(collect)
    return results
```

---

## 附录: SyntaxKind 快速查找表

### 声明类 (Declaration)

| SyntaxKind | SystemVerilog 结构 |
|------------|-------------------|
| `ModuleDeclaration` | module...endmodule |
| `InterfaceDeclaration` | interface...endinterface |
| `ClassDeclaration` | class...endclass |
| `PackageDeclaration` | package...endpackage |
| `ProgramDeclaration` | program...endprogram |
| `FunctionDeclaration` | function...endfunction |
| `TaskDeclaration` | task...endtask |
| `ConstraintDeclaration` | constraint...endconstraint |
| `CovergroupDeclaration` | covergroup...endgroup |
| `SequenceDeclaration` | sequence...endsequence |
| `PropertyDeclaration` | property...endproperty |
| `CheckerDeclaration` | checker...endchecker |

### 表达式类 (Expression)

| SyntaxKind | 说明 |
|------------|------|
| `IdentifierName` | 标识符 |
| `IntegerLiteral` | 整数字面量 |
| `StringLiteral` | 字符串字面量 |
| `BinaryExpression` | 二元表达式 (+, -, *, /, etc.) |
| `UnaryExpression` | 一元表达式 (!, ~, etc.) |
| `ConditionalExpression` | 条件表达式 (?:) |
| `MemberAccessExpression` | 成员访问 (.) |
| `ArrayIndexExpression` | 数组索引 ([]) |
| `FunctionCallExpression` | 函数调用 |

### 语句类 (Statement)

| SyntaxKind | SystemVerilog 结构 |
|------------|-------------------|
| `IfStatement` | if...else |
| `CaseStatement` | case...endcase |
| `ForStatement` | for...endfor |
| `ForeachStatement` | foreach... |
| `WhileStatement` | while...endwhile |
| `DoWhileStatement` | do...while |
| `ReturnStatement` | return |
| `BlockingAssignment` | = |
| `NonBlockingAssignment` | <= |
| `AlwaysFfStatement` | always_ff |
| `AlwaysCombStatement` | always_comb |
| `AlwaysLatchStatement` | always_latch |
| `InitialStatement` | initial |
| `FinalStatement` | final |

---

**最后更新**: 2026-04-29
**版本**: 1.0

# 可运行的示例代码

以下示例均经过测试验证，可以直接运行:

## 1. 基本解析 (parse 模块)

```python
from parse import SVParser

code = "module test(input clk, output[7:0] out); endmodule"
p = SVParser()
tree = p.parse_text(code)
print("Parse complete")
```

## 2. 类提取 (class_utils)

```python
from parse.class_utils import ClassExtractor

code = """
class packet;
    rand bit [7:0] addr;
    constraint c { addr < 10; }
endclass
"""
ce = ClassExtractor(None, verbose=False)
classes = ce.extract_from_text(code)
print(f"Found {len(classes)} classes")
for c in classes:
    print(f"  - {c.name}")
```

## 3. VCD解析 (vcd_analyzer)

```python
from trace.vcd_analyzer import VCDAnalyzer

vcd_code = """
$timescale 1ns $end
$scope module tb $end
$var wire 1 ! clk $end
$var wire 8 " data $end
$upscope $end
$enddefinitions $end
#0
b0 !
b00000000 "
#10
b1 !
#20
b10101010 "
"""

va = VCDAnalyzer(verbose=False)
waveforms = va.parse_vcd_text(vcd_code)
print(f"Found {len(waveforms)} signals")
for name, wave in waveforms.items():
    print(f"  - {name}: {len(wave.values)} changes")
```

## 4. 驱动追踪 (driver)

```python
from parse import SVParser
from trace.driver import DriverCollector

code = """
module counter(
    input clk, rst_n,
    output [7:0] count
);
    logic [7:0] cnt;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) cnt <= 0;
        else cnt <= cnt + 1;
    end
    assign count = cnt;
endmodule
"""

p = SVParser()
p.parse_text(code)
dc = DriverCollector(p, verbose=False)
drivers = dc.get_drivers('*')
print(f"Found {len(drivers)} drivers")
for d in drivers:
    print(f"  - {d.signal}: kind={d.kind}")
```

## 5. 连接追踪 (connection)

```python
from parse import SVParser
from trace.connection import ConnectionTracer

code = """
module sub(output [7:0] out);
    assign out = 8'hFF;
endmodule
module top(output [7:0] result);
    wire [7:0] tmp;
    sub u1(.out(tmp));
    assign result = tmp;
endmodule
"""

p = SVParser()
p.parse_text(code)
ct = ConnectionTracer(p, verbose=False)
instances = ct.get_all_instances()
print(f"Found {len(instances)} instances")
for i in instances:
    print(f"  - {i.name}: {i.module_type}")
```

## 6. 接口提取 (interface)

```python
from parse.interface import extract_interfaces

code = """
interface simple_bus(input clk);
    logic [31:0] data;
    logic valid;
    modport master (input data, valid, output ready);
    modport slave (output data, valid, input ready);
endinterface
"""

interfaces = extract_interfaces(code)
print(f"Found {len(interfaces)} interfaces")
```

## 7. 数据路径分析 (datapath)

```python
from parse import SVParser
from trace.datapath import DataPathAnalyzer

code = """
module pipeline(input clk, input[7:0] din, output[7:0] dout);
    logic [7:0] stage1, stage2;
    always_ff @(posedge clk) begin
        stage1 <= din;
        stage2 <= stage1;
    end
    assign dout = stage2;
endmodule
"""

p = SVParser()
p.parse_text(code)
dp = DataPathAnalyzer(p, verbose=False)
paths = dp.get_paths()
print(f"Data paths: {len(paths)}")
```

## 8. 控制流分析 (controlflow)

```python
from parse import SVParser
from trace.controlflow import ControlFlowTracer

code = """
module fsm(input clk, input go, output done);
    typedef enum {IDLE, RUN, DONE} state_t;
    state_t state;
    always_ff @(posedge clk) begin
        case (state)
            IDLE: if (go) state <= RUN;
            RUN: state <= DONE;
            DONE: state <= IDLE;
        endcase
    end
    assign done = (state == DONE);
endmodule
"""

p = SVParser()
p.parse_text(code)
cf = ControlFlowTracer(p, verbose=False)
flows = cf.get_all_flows()
print(f"Control flows: {len(flows)}")
```

