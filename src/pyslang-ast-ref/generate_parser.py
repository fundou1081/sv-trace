"""
Generate Parser - 使用正确的 AST 遍历

提取 generate 块：
- LoopGenerate (for generate)
- CondGenerate (if generate, case generate)
- GenerateBlock
- ForLoop (用于 generate)

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class GenerateLoop:
    variable: str = ""
    start: str = ""
    end: str = ""
    step: str = ""


@dataclass
class GenerateConditional:
    condition: str = ""
    gen_type: str = ""  # if, case


@dataclass
class GenerateBlock:
    name: str = ""
    block_type: str = ""  # loop, cond, block


class GenerateExtractor:
    def __init__(self):
        self.loops: List[GenerateLoop] = []
        self.conditionals: List[GenerateConditional] = []
        self.blocks: List[GenerateBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'LoopGenerate':
                gl = GenerateLoop()
                if hasattr(node, 'variable') and node.variable:
                    gl.variable = str(node.variable)
                if hasattr(node, 'initial') and node.initial:
                    gl.start = str(node.initial)
                if hasattr(node, 'condition') and node.condition:
                    gl.end = str(node.condition)
                if hasattr(node, 'step') and node.step:
                    gl.step = str(node.step)
                self.loops.append(gl)
            
            elif kind_name == 'CondGenerate':
                gc = GenerateConditional()
                gc.gen_type = 'if'
                if hasattr(node, 'condition') and node.condition:
                    gc.condition = str(node.condition)
                self.conditionals.append(gc)
            
            elif kind_name == 'CaseGenerate':
                gc = GenerateConditional()
                gc.gen_type = 'case'
                if hasattr(node, 'condition') and node.condition:
                    gc.condition = str(node.condition)
                self.conditionals.append(gc)
            
            elif kind_name == 'GenerateBlock':
                gb = GenerateBlock()
                if hasattr(node, 'name') and node.name:
                    gb.name = str(node.name)
                gb.block_type = 'block'
                self.blocks.append(gb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return {
            'loops': [{'var': gl.variable, 'start': gl.start, 'end': gl.end} for gl in self.loops],
            'conditionals': [{'type': gc.gen_type, 'cond': gc.condition[:30]} for gc in self.conditionals],
            'blocks': [{'name': gb.name} for gb in self.blocks]
        }


def extract_generate(code: str) -> Dict:
    return GenerateExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
generate
    for (genvar i = 0; i < 8; i++) begin : gen_block
        logic [7:0] data;
    end
    
    if (ENABLE) begin : gen_if
    end
endgenerate
'''
    result = extract_generate(test_code)
    print(f"Loops: {len(result['loops'])}, Conditionals: {len(result['conditionals'])}, Blocks: {len(result['blocks'])}")
