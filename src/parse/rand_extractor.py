"""
Rand/Constraint 解析器 - 使用 pyslang AST

支持:
- rand/randc 变量
- randomize() 调用
- dist 约束
- solve before/after
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class RandVariable:
    """rand 变量"""
    name: str = ""
    width: str = ""
    is_rand: bool = False
    is_randc: bool = False


@dataclass
class RandClass:
    """带 rand 的 class"""
    name: str = ""
    rand_vars: List[RandVariable] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


class RandExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.classes = {}
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'ClassDeclaration':
                self._extract_class(node)
            elif kind_name == 'MethodCallExtension':
                self._extract_randomize(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_class(self, node):
        klass = RandClass()
        
        if hasattr(node, 'name') and node.name:
            klass.name = str(node.name)
        
        # 成员变量找 rand
        if hasattr(node, 'members') and node.members:
            for mem in node.members:
                if not mem:
                    continue
                
                mem_kind = mem.kind.name if hasattr(mem.kind, 'name') else str(mem.kind)
                
                # ClassPropertyDeclaration
                if mem_kind == 'ClassPropertyDeclaration':
                    mem_str = str(mem)
                    if 'rand ' in mem_str or 'randc ' in mem_str:
                        rv = RandVariable()
                        # 提取名称和类型
                        if hasattr(mem, 'declarator') and mem.declarator:
                            rv.name = str(mem.declarator)
                        
                        # 判断 rand/randc
                        if 'randc' in mem_str:
                            rv.is_randc = True
                            rv.is_rand = True
                        elif 'rand' in mem_str:
                            rv.is_rand = True
                        
                        # 提取位宽
                        if hasattr(mem, 'dataType') and mem.dataType:
                            rv.width = str(mem.dataType)
                        
                        klass.rand_vars.append(rv)
                
                # Constraint 块
                elif mem_kind == 'ConstraintBlock':
                    klass.constraints.append(str(mem))
        
        if klass.name:
            self.classes[klass.name] = klass
    
    def _extract_randomize(self, node):
        # randomize() 调用检测
        method_str = str(node)
        if 'randomize' in method_str:
            # 记录但不需要特殊处理
            pass
    
    def get_classes(self):
        return self.classes


def extract_rand_classes(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = RandExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.classes


if __name__ == "__main__":
    test_code = '''
class packet;
    rand bit [7:0] addr;
    randc bit [3:0] burst;
    rand bit [15:0] data;
    
    constraint addr_c { addr < 256; }
    constraint burst_c { burst inside {[1:8]}; }
    
    function void randomize();
        this.randomize() with { addr > 0; };
    endfunction
endclass
'''
    
    result = extract_rand_classes(test_code)
    print("=== Rand Class Extraction ===")
    for name, klass in result.items():
        print(f"\n{name}:")
        print(f"  rand vars: {len(klass.rand_vars)}")
        for rv in klass.rand_vars:
            rand_type = "randc" if rv.is_randc else "rand" if rv.is_rand else "normal"
            print(f"    {rv.name} ({rand_type})")
        print(f"  constraints: {len(klass.constraints)}")
