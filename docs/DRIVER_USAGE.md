# Driver 使用指南

## 基本使用

```python
from parse import SVParser
from trace.driver import DriverCollector

# 1. 解析
parser = SVParser()
parser.parse_file('design.sv')

# 2. 创建收集器
collector = DriverCollector(parser)

# 3. 查找驱动
drivers = collector.find_driver('signal_name')

for d in drivers:
    print(f"驱动: {d.source}")
```

## Driver 属性

| 属性 | 说明 |
|------|------|
| source | 驱动信号名 |
| kind | 驱动类型 |
| line | 行号 |
| file | 文件名 |

## 更多方法

```python
# 查找所有驱动
all_drivers = collector.find_all_drivers()

# 清除缓存
collector.clear_cache()
```

