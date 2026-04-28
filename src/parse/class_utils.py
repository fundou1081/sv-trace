"""
Class 解析器 - class 成员、方法、约束提取
"""
from dataclasses import dataclass
from typing import Dict, List
import re


@dataclass
class ClassMethod:
    name: str = ""
    kind: str = "function"
    return_type: str = ""
    
    def to_dict(self):
        return {"name": self.name, "kind": self.kind, "return_type": self.return_type}


@dataclass  
class ClassMember:
    name: str = ""
    data_type: str = "logic"
    width: int = 1
    rand_mode: str = ""
    
    def to_dict(self):
        return {"name": self.name, "type": self.data_type, "width": self.width, "rand": self.rand_mode}


@dataclass
class ClassConstraint:
    name: str = ""
    expr: str = ""
    
    def to_dict(self):
        return {"name": self.name, "expr": self.expr}


class ClassExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.classes: Dict[str, Dict] = {}
        if parser:
            self._extract_all_classes()
    
    def _extract_all_classes(self):
        if not self.parser or not self.parser.trees:
            return
        
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            
            root = tree.root
            name = str(root.name).strip() if hasattr(root, 'name') else ""
            
            if not name:
                continue
            
            info = {'name': name, 'members': [], 'methods': [], 'constraints': []}
            
            items = getattr(root, 'items', [])
            
            for item in items:
                if not item:
                    continue
                
                item_type = type(item).__name__
                item_str = str(item)
                
                if 'Property' in item_type:
                    member = self._extract_member(item)
                    if member:
                        info['members'].append(member)
                
                elif 'Method' in item_type:
                    method = self._extract_method(item)
                    if method:
                        info['methods'].append(method)
                
                elif 'Constraint' in item_type or 'constraint' in item_str.lower():
                    constraint = self._extract_constraint(item)
                    if constraint:
                        info['constraints'].append(constraint)
            
            self.classes[name] = info
    
    def extract_from_text(self, code: str) -> List:
        """从源码文本提取"""
        results = []
        
        class_pattern = r'class\s+(\w+)\s*;(.+?)endclass'
        for m in re.finditer(class_pattern, code, re.DOTALL):
            name = m.group(1).strip()
            body = m.group(2)
            
            info = {'name': name, 'members': [], 'methods': [], 'constraints': []}
            
            # 提取属性
            for mem_m in re.finditer(r'(randc?)\s+(\w+)\s*\[(\d+):0\]\s*(\w+)', body):
                rand_mode = mem_m.group(1)
                data_type = mem_m.group(2)
                width = int(mem_m.group(3)) + 1
                var_name = mem_m.group(4)
                info['members'].append(ClassMember(
                    name=var_name, data_type=data_type, width=width, rand_mode=rand_mode
                ))
            
            # 提取方法 - 方式1: function bit [7:0] name();
            for func_m in re.finditer(r'(function|task)\s+(?!new\b)([\w\s\[\]:]+)\s+(\w+)\s*\(', body):
                kind = func_m.group(1)
                return_type = func_m.group(2).strip()
                rt = return_type.replace("function ", "").replace("task ", "").strip()
                # 如果结果不含空格和[]（不是有效类型），设为空
                return_type = rt if rt and (' ' in rt or '[' in rt) else ""
                func_name = func_m.group(3)
                info['methods'].append(ClassMethod(name=func_name, kind=kind, return_type=return_type))
            
            # 提取方法 - 方式2: function new();
            for func_m in re.finditer(r'(function|task)\s+new\s*\(\)', body):
                info['methods'].append(ClassMethod(name='new', kind=func_m.group(1), return_type=''))
            
            # 提取约束
            for c_m in re.finditer(r'constraint\s+(\w+)\s*\{([^}]+)\}', body):
                info['constraints'].append(ClassConstraint(name=c_m.group(1), expr=c_m.group(2).strip()))
            
            results.append(info)
            self.classes[name] = info
        
        return results
    
    def _extract_member(self, item):
        item_str = str(item)
        
        rand_mode = "rand" if 'rand' in item_str and 'randc' not in item_str else ("randc" if 'randc' in item_str else "")
        
        match = re.search(r'(randc?)\s+(\w+)\s*\[(\d+):0\]\s*(\w+)', item_str)
        if match:
            data_type = match.group(2)
            width = int(match.group(3)) + 1
            name = match.group(4)
            return ClassMember(name=name, data_type=data_type, width=width, rand_mode=rand_mode)
        
        return None
    
    def _extract_method(self, item):
        item_str = str(item)
        
        # 匹配 function bit [7:0] name();
        match = re.search(r'(function|task)\s+(?!new\b)([\w\s\[\]:]+)\s+(\w+)\s*\(', item_str)
        if match:
            kind = match.group(1)
            return_type = match.group(2).strip()
            name = match.group(3)
            return ClassMethod(name=name, kind=kind, return_type=return_type)
        
        # 匹配 function new();
        match2 = re.search(r'(function|task)\s+new\s*\(', item_str)
        if match2:
            return ClassMethod(name='new', kind=match2.group(1), return_type='')
        
        return None
    
    def _extract_constraint(self, item):
        item_str = str(item)
        
        match = re.search(r'constraint\s+(\w+)', item_str)
        if match:
            return ClassConstraint(name=match.group(1), expr=item_str.strip())
        
        return None
    
    def get_class(self, name):
        return self.classes.get(name)
    
    def list_classes(self):
        return list(self.classes.keys())
    
    def to_dict(self):
        result = {}
        for name, info in self.classes.items():
            result[name] = {
                'members': [m.to_dict() for m in info['members']],
                'methods': [m.to_dict() for m in info['methods']],
                'constraints': [c.to_dict() for c in info['constraints']]
            }
        return result


__all__ = ['ClassExtractor', 'ClassMember', 'ClassMethod', 'ClassConstraint']
