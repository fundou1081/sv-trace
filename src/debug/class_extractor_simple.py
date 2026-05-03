"""SimpleClassExtractor - 简化版类提取器。

使用字符串匹配作为备选的类提取器。
用于快速提取类定义信息。

Example:
    >>> from debug.class_extractor_simple import SimpleClassExtractor
    >>> extractor = SimpleClassExtractor(parser)
    >>> for name, cls in extractor.classes.items():
    ...     print(f"Class: {name}")
"""

import sys
import re
from debug.class_info import ClassInfo, PropertyInfo, ConstraintInfo, MethodInfo


class SimpleClassExtractor:
    """简化类提取器。
    
    使用字符串匹配快速提取类定义信息。

    Attributes:
        parser: SVParser 实例
        classes: 类名字典
    
    Example:
        >>> extractor = SimpleClassExtractor(parser)
        >>> print(f"Found {len(extractor.classes)} classes")
    """
    
    def __init__(self, parser):
        """初始化提取器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.classes = {}
        self._extract()
    
    def _is_class(self, node):
        """检查节点是否为类声明。
        
        Args:
            node: 语法树节点
        
        Returns:
            bool: 是否为类声明
        """
        return 'ClassDeclaration' in type(node).__name__
    
    def _get_name(self, name_node):
        """获取节点名称。
        
        Args:
            name_node: 名称节点
        
        Returns:
            str: 名称字符串
        """
        if not name_node:
            return ""
        if hasattr(name_node, 'value'):
            return str(name_node.value).strip()
        return str(name_node).strip()
    
    def _extract(self):
        """提取类定义。"""
        for fname, tree in self.parser.trees.items():
            code = open(fname).read() if hasattr(tree, 'source') else str(tree)
            
            # Use regex to find class definitions as fallback
            class_pattern = r'class\s+(\w+)\s*(?:extends\s+(\w+))?'
            matches = re.findall(class_pattern, code)
            
            for class_name, parent in matches:
                if class_name not in self.classes:
                    self.classes[class_name] = ClassInfo(name=class_name, extends=parent if parent else None)
        
        print(f"SimpleClassExtractor found: {list(self.classes.keys())}")


class ClassExtractor(SimpleClassExtractor):
    """主类提取器。
    
    基于 AST 的完整类提取器，继承自 SimpleClassExtractor。

    Attributes:
        parser: SVParser 实例
        classes: 类名字典
    
    Example:
        >>> extractor = ClassExtractor(parser)
        >>> for name, cls in extractor.classes.items():
        ...     print(f"Class: {name}, extends: {cls.extends}")
    """
    
    def __init__(self, parser):
        """初始化提取器。
        
        Args:
            parser: SVParser 实例
        """
        self.parser = parser
        self.classes = {}
        self._extract()
