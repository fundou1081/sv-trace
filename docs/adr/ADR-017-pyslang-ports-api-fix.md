# ADR-017: DanglingPortDetector - pyslang Ports API 修复

## 状态
已接受

## 日期
2026-04-25

## 问题
DanglingPortDetector 无法检测到输出端口悬空问题，所有测试返回空结果。

## 原因分析

### 问题 1: Ports 提取方式错误

pyslang 的 `ModuleDeclaration.header.ports` 返回的是 `AnsiPortListSyntax`，它包含:
- `TokenKind.OpenParenthesis` - `(`
- `SyntaxKind.SeparatedList` - 包含实际端口的列表
- `TokenKind.CloseParenthesis` - `)`

原代码尝试使用 `ports_attr.count` 获取端口数量，但 `AnsiPortListSyntax` 没有 `count` 属性。

### 问题 2: 迭代方式错误

`SeparatedList` 中包含:
- `ImplicitAnsiPort` - 实际端口
- `Comma` - 逗号分隔符

原代码没有正确过滤掉 `Comma` 节点。

### 问题 3: 端口名称获取方式错误

对于 `ImplicitAnsiPort`，端口名称在 `declarator.name`，不是 `header.name`。

## 解决方案

```python
def _extract_ports(self, module) -> Dict[str, PortDirection]:
    ports = {}
    
    try:
        ports_attr = getattr(module, 'ports', None)
        if not ports_attr and hasattr(module, 'header'):
            ports_attr = getattr(module.header, 'ports', None)
        
        if not ports_attr:
            return ports
        
        # Find the SeparatedList
        for item in ports_attr:
            if hasattr(item, 'kind') and 'SeparatedList' in str(item.kind):
                port_list = item
                break
        
        if not port_list:
            return ports
        
        # Iterate over ports, skip Comma tokens
        for port in port_list:
            if not port or not hasattr(port, 'kind'):
                continue
            
            kind_name = str(port.kind)
            if 'Comma' in kind_name:  # Skip commas
                continue
            
            # Get port name from declarator
            port_name = None
            if hasattr(port, 'declarator') and port.declarator:
                if hasattr(port.declarator, 'name') and port.declarator.name:
                    port_name = str(port.declarator.name).strip()
            
            # Get direction from header
            direction = PortDirection.INPUT
            if hasattr(port, 'header') and port.header:
                header = port.header
                if hasattr(header, 'direction') and header.direction:
                    dir_str = str(header.direction).lower()
                    if 'output' in dir_str:
                        direction = PortDirection.OUTPUT
                    elif 'inout' in dir_str:
                        direction = PortDirection.INOUT
            
            if port_name:
                ports[port_name] = direction
                
    except Exception:
        pass
    
    return ports
```

## 修改文件
- `src/debug/analyzers/dangling_port.py`

## 影响
- DanglingPortDetector 现在可以正确提取模块端口
- 能够检测到输出端口悬空问题
