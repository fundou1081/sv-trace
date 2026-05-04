"""
Config Parser - 使用 pyslang AST

支持:
- ConfigDeclaration
- CellConfigRule
- ConfigLiblist
- ConfigUseClause
- Design statement
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class ConfigRule:
    """config rule"""
    kind: str = ""  # cell, liblist, use
    instance: str = ""
    library: str = ""


@dataclass
class ConfigDef:
    """config block"""
    name: str = ""
    design: str = ""
    rules: List[ConfigRule] = field(default_factory=list)


class ConfigParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.configs = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'ConfigDeclaration':
                self._extract_config(node)
            elif kind_name in ['CellConfigRule', 'ConfigLiblist', 'ConfigUseClause']:
                self._extract_rule(node, kind_name)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_config(self, node):
        config = ConfigDef()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            config.name = str(node.name)
        
        # design
        if hasattr(node, 'design') and node.design:
            config.design = str(node.design)
        
        # rules
        if hasattr(node, 'rules') and node.rules:
            for rule in node.rules:
                if rule:
                    config.rules.append(str(rule))
        
        self.configs.append(config)
    
    def _extract_rule(self, node, kind_name):
        # cell/liblist/use rule
        pass  # 在 config block 中处理
    
    def get_configs(self):
        return self.configs


def extract_configs(code):
    tree = pyslang.SyntaxTree.fromText(code)
    parser = ConfigParser(None)
    parser._extract_from_tree(tree)
    return parser.configs


if __name__ == "__main__":
    test_code = '''
config config0;
    design work.top;
    
    cell use instance work.top.uart -libaxis;
    cell use config work.top.fifo -library mylib;
    
    liblist default mylib;
endconfig
'''
    
    result = extract_configs(test_code)
    print("=== Config Parser ===")
    print(f"configs: {len(result)}")
    for cfg in result:
        print(f"  {cfg.name}: {cfg.design}")
