# DriverCollector 实现分析

> 信号驱动追踪 - 核心分析模块

## 1. 模块引用

```python
# 导入
from parse import SVParser          # 解析器
from trace.driver import DriverCollector  # 驱动收集器

# 直接导入 pyslang
import pyslang
from pyslang import SyntaxKind
```

## 2. 核心类 DriverCollector

### 初始化

```python
class DriverCollector:
    def __init__(self, parser, verbose: bool = True):
        self.parser = parser  # SVParser 实例
        self.verbose = verbose
        self._driver_cache = {}  # 驱动缓存
```

### 主要方法

| 方法 | 功能 |
|------|------|
| find_driver() | 查找信号的驱动源 |
| find_all_drivers() | 查找所有驱动 |
| _collect() | 收集驱动关系 |

## 3. AST 遍历方式

### 访问方式: pyslang.VisitAction

```python
# 遍历 AST
def visitor(node):
    if node.kind == SyntaxKind.XXX:
        # 处理
    return pyslang.VisitAction.Advance  # 继续遍历
```

### 处理的语法类型

| 语法类型 | 说明 |
|----------|------|
| ContinuousAssign | assign 语句 |
| AlwaysFFBlock | always_ff 块 |
| AlwaysCombBlock | always_comb 块 |
| AlwaysLatchBlock | always_latch 块 |
| ProceduralAssign | 过程赋值 |
| VariableDecl | 变量声明 |

## 4. 核心逻辑

### find_driver() 流程

```
1. 接收信号名
2. 从缓存查找 (如有)
3. 遍历 AST 找赋值语句
4. 提取右边的驱动信号
5. 返回驱动列表
```

### 关键代码

```python
def find_driver(self, signal_name: str, include_bit_select: bool = False):
    # 1. 先检查缓存
    if signal_name in self._driver_cache:
        return self._driver_cache[signal_name]
    
    # 2. 收集驱动
    drivers = self._collect(signal_name)
    
    # 3. 缓存结果
    self._driver_cache[signal_name] = drivers
    
    return drivers
```

## 5. 与 parser 的关系

```
SVParser.parse_file()
    ↓ 返回 SyntaxTree
DriverCollector._collect()
    ↓ 遍历 AST
找到驱动
```

### 具体使用

```python
# Step 1: 解析文件
parser = SVParser()
tree = parser.parse_file('design.sv')  # 返回 SyntaxTree

# Step 2: 创建收集器
collector = DriverCollector(parser)

# Step 3: 使用
# 注意：传入 parser 对象
# driver 使用 parser.trees 访问解析结果
```

**关键点**: DriverCollector 接收 parser 对象，并从 `parser.trees` 获取解析结果。

## 6. AST 遍历示例

```python
# 查找 always_ff 块中的赋值
def _collect(self, signal_name):
    for fname, tree in self.parser.trees.items():
        # 遍历 AST
        def visitor(node):
            if node.kind == SyntaxKind.AlwaysFFBlock:
                # 在 always_ff 中查找 signal_name 的赋值
                for child in node:
                    if is_assignment_to_signal(signal_name):
                        # 提取右边表达式
                        driver = extract_rhs(child)
            
            return pyslang.VisitAction.Advance
        
        tree.root.visit(visitor)
```

## 7. 遵守的铁律

| 铁律 | 实现 |
|------|------|
| 1: AST 唯一数据源 | ✅ 使用 pyslang AST |
| 13: 金标准测试 | ✅ 有测试用例 |
| 5: 原子化 | ✅ 一个文件一个功能 |

## 8. 核心代码示例

```python
from parse import SVParser
from trace.driver import DriverCollector

# 创建解析器
parser = SVParser()
parser.parse_file('design.sv')

# 创建驱动收集器 (传入 parser)
collector = DriverCollector(parser)

# 查找 data_out 的驱动
drivers = collector.find_driver('data_out')

for d in drivers:
    print(f"驱动: {d.source}, 类型: {d.kind}")
```

## 9. 总结

- **直接使用 pyslang**: 不是通过 parse 模块
- **传入 SVParser**: 用于访问 `parser.trees`
- **AST 遍历**: 通过 `tree.root.visit()`
- **返回结果**: Driver 对象列表

