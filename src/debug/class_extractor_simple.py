"""Simple class extractor - debug version."""

import sys
import re
from debug.class_info import ClassInfo, PropertyInfo, ConstraintInfo, MethodInfo

class SimpleClassExtractor:
    def __init__(self, parser):
        self.parser = parser
        self.classes = {}
        self._extract()
    
    def _is_class(self, node):
        return 'ClassDeclaration' in type(node).__name__
    
    def _get_name(self, name_node):
        if not name_node:
            return ""
        if hasattr(name_node, 'value'):
            return str(name_node.value).strip()
        return str(name_node).strip()
    
    def _extract(self):
        """Extract classes using string matching as fallback."""
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
    """Main class extractor - extends simple one with AST-based extraction."""
    
    def __init__(self, parser):
        self.parser = parser
        self.classes = {}
        self._extract()
