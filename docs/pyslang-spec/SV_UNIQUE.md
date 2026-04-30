# SystemVerilog 独有语法

本文档补充 SystemVerilog 相比 Verilog-2005 独有的语法结构。

## 语法覆盖状态

| 语法 | 解析器 | 状态 |
|------|--------|------|
| Interface | interface.py | ✅ 基础 |
| Modport | interface.py | ✅ 基础 |
| Clocking Block | interface.py | ✅ 基础 |
| Package | package.py | ✅ 基础 |
| Program | package.py | ✅ 基础 |
| Generate | generate.py | ✅ 基础 |
| Covergroup | covergroup.py | ✅ 基础 |
| Constraint | constraint.py | ✅ 完整 |
| Class | class_utils.py | ✅ 完整 |
| Sequence/Property | assertion.py | ✅ 基础 |

---

## 1. Interface 语法

### SyntaxKind

| SyntaxKind | 说明 |
|------------|------|
| InterfaceDeclaration | interface...endinterface |
| InterfacePortDeclaration | interface 内的端口声明 |
| ModportDeclaration | modport...endmodport |
| ModportItem | modport 端口列表 |
| ModportExplicitPort | 带方向的端口 |
| ModportSimplePortList | 简单端口列表 |
| ClockingDeclaration | clocking...endclocking |
| ClockingItem | clocking 内的项 |

### 代码示例

```systemverilog
interface axi_if (input clk, input rst);
    logic [31:0] wdata;
    logic valid;
    
    // modport
    modport master (
        input clk, rst,
        output wdata, valid
    );
    
    // clocking block
    clocking cb @(posedge clk);
        input #1step valid;
        output #0 wdata;
    endclocking
endinterface
```

### Python 属性

```python
import pyslang
from pyslang import SyntaxKind

tree = pyslang.SyntaxTree.fromText(code)
root = tree.root

def collect(node):
    if node.kind == SyntaxKind.InterfaceDeclaration:
        name = str(node.header.name.valueText)
        
        # 遍历 members
        for m in node.members:
            if m.kind == SyntaxKind.ModportDeclaration:
                # modport 名称
                modport_name = str(m).split('(')[0].strip()
            
            elif m.kind == SyntaxKind.C lockingDeclaration:
                # clocking 块
                clock_event = str(m.clockingEvent)
    return pyslang.VisitAction.Advance
```

---

## 2. Package 语法

### SyntaxKind

| SyntaxKind | 说明 |
|------------|------|
| PackageDeclaration | package...endpackage |
| ProgramDeclaration | program...endprogram |

### 代码示例

```systemverilog
package my_pkg;
    parameter int P1 = 8;
    function bit [7:0] add(input bit [7:0] a, b);
        return a + b;
    endfunction
endpackage

program test_prog (input clk, output data);
    initial begin
        data = 0;
    end
endprogram
```

---

## 3. Generate 语法

### SyntaxKind

| SyntaxKind | 说明 |
|------------|------|
| GenerateRegion | generate...endgenerate 容器 |
| IfGenerate | if (condition) begin...end |
| ElseClause | if-else 的 else 部分 |
| LoopGenerate | for (genvar) begin...end |
| CaseGenerate | case (expr) ... endcase |
| GenerateBlock | begin: Label ... end |

### 代码示例

```systemverilog
module tb;
    generate
        if (1) begin : GEN_IF
            logic [7:0] data;
        end else begin
            logic [7:0] data;
        end
    endgenerate
    
    for (genvar i = 0; i < 8; i++) begin : GEN_FOR
        logic [i:0] bits;
    end
    
    case (sel)
        1: begin
            logic a;
        end
    endcase
endmodule
```

### Python 属性

```python
# IfGenerate 属性
if hasattr(node, 'condition'):  # 条件表达式
if hasattr(node, 'block'):  # begin...end 块
if hasattr(node, 'elseClause'):  # else 部分

# LoopGenerate 属性  
if hasattr(node, 'loopVariable'):  # genvar
if hasattr(node, 'stopExpression'):  # 终止条件
if hasattr(node, 'expression'):  # 步进
if hasattr(node, 'block'):  # 循环体
```

---

## 4. Checker 语法 (待实现)

```systemverilog
checker parity_checker (input data, input valid);
    always @(posedge clk) begin
        assert property (!valid |-> $stable(data));
    end
endchecker
```

### SyntaxKind

- CheckerDeclaration
- CheckerInstance

---

## 5. 端口方向关键词

| TokenKind | SystemVerilog |
|-----------|---------------|
| InputKeyword | input |
| OutputKeyword | output |
| InoutKeyword | inout |
| RefKeyword | ref (类类型) |

---

## 6. 常用语法检查

```python
import pyslang
from pyslang import SyntaxKind

# 检查代码是否使用 SV 特有语法
def check_sv_features(code):
    features = {
        'interface': False,
        'modport': False,
        'clocking': False,
        'package': False,
        'program': False,
        'class': False,
        'covergroup': False,
        'constraint': False,
    }
    
    tree = pyslang.SyntaxTree.fromText(code)
    
    def collect(node):
        kn = node.kind.name
        if kn == 'InterfaceDeclaration':
            features['interface'] = True
        elif kn == 'ModportDeclaration':
            features['modport'] = True
        elif kn == 'ClockingDeclaration':
            features['clocking'] = True
        elif kn == 'PackageDeclaration':
            features['package'] = True
        elif kn == 'ProgramDeclaration':
            features['program'] = True
        elif kn == 'ClassDeclaration':
            features['class'] = True
        elif kn == 'CovergroupDeclaration':
            features['covergroup'] = True
        elif kn == 'ConstraintDeclaration':
            features['constraint'] = True
        return pyslang.VisitAction.Advance
    
    tree.root.visit(collect)
    return features
```

---

**最后更新**: 2026-04-30
