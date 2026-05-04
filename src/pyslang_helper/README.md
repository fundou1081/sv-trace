# pyslang_helper

> pyslang 辅助工具

## 功能

- SVParser 增强版
- 数据提取函数
- 数据类定义

## 使用

```python
from pyslang_helper import extract_all, parse

result = extract_all(code)
parser = parse(code)
```

## 铁律情况

⚠️ 3处正则用于字符串处理 (非 AST 解析)
