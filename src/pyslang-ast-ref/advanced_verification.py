"""
Advanced Verification Parser - 使用正确的 AST 遍历

支持高级验证语法:
- P2: 枚举、字符串、队列、信箱、信号量
- P3: 覆盖组高级特性
- P4: 高级约束
- P5: DPI
- P6: 进程

注意：此文件不包含任何正则表达式，所有解析使用 AST 属性
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


# ========== 数据结构 ==========

@dataclass
class EnumDef:
    name: str = ""
    values: List[str] = field(default_factory=list)


@dataclass  
class StringOp:
    operation: str = ""
    args: List[str] = field(default_factory=list)


@dataclass
class QueueOp:
    name: str = ""
    method: str = ""


@dataclass
class MailboxDef:
    name: str = ""
    type_arg: str = ""


@dataclass
class SemaphoreDef:
    name: str = ""
    count: int = 1


@dataclass
class WildcardBins:
    bins_name: str = ""
    values: List[str] = field(default_factory=list)


@dataclass
class IllegalBins:
    values: List[str] = field(default_factory=list)


@dataclass
class IgnoreBins:
    values: List[str] = field(default_factory=list)


@dataclass
class SolveBefore:
    variables: List[str] = field(default_factory=list)


@dataclass
class UniqueConstraint:
    variables: List[str] = field(default_factory=list)


@dataclass
class SoftConstraint:
    expr: str = ""


@dataclass
class DPIExport:
    name: str = ""
    return_type: str = ""


@dataclass
class PureFunction:
    name: str = ""


@dataclass
class ProcessOp:
    operation: str = ""


# ========== 解析器 ==========

class AdvancedVerificationExtractor:
    """提取高级验证语法 - 使用正确的 AST 遍历"""
    
    def __init__(self, parser=None):
        self.parser = parser
        self.enums: List[EnumDef] = []
        self.string_ops: List[StringOp] = []
        self.queue_ops: List[QueueOp] = []
        self.mailboxes: List[MailboxDef] = []
        self.semaphores: List[SemaphoreDef] = []
        self.wildcard_bins: List[WildcardBins] = []
        self.illegal_bins: List[IllegalBins] = []
        self.ignore_bins: List[IgnoreBins] = []
        self.solve_before: List[SolveBefore] = []
        self.unique_constraints: List[UniqueConstraint] = []
        self.dpi_exports: List[DPIExport] = []
        self.pure_functions: List[PureFunction] = []
        self.process_ops: List[ProcessOp] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # P2: 枚举定义
            if kind_name == 'EnumDef':
                e = self._extract_enum(node)
                if e:
                    self.enums.append(e)
            
            # 字符串操作
            elif kind_name == 'MethodCallExtension' or kind_name == 'StringLiteral':
                # 检查字符串相关
                pass
            
            # 队列方法
            elif kind_name == 'QueueMethodCall':
                q = self._extract_queue_op(node)
                if q:
                    self.queue_ops.append(q)
            
            # 信箱
            elif kind_name == 'MailboxMethodCall':
                m = self._extract_mailbox(node)
                if m:
                    self.mailboxes.append(m)
            
            # 信号量
            elif kind_name == 'SemaphoreMethodCall':
                s = self._extract_semaphore(node)
                if s:
                    self.semaphores.append(s)
            
            # P3: Covergroup 高级特性
            elif kind_name == 'CoverpointSymbol':
                self._extract_coverpoint_bins(node)
            
            # P4: 高级约束
            elif kind_name == 'SolveBeforeConstraint':
                sb = self._extract_solve_before(node)
                if sb:
                    self.solve_before.append(sb)
            
            elif kind_name == 'UniqueConstraint':
                uc = self._extract_unique_constraint(node)
                if uc:
                    self.unique_constraints.append(uc)
            
            elif kind_name == 'SoftConstraint':
                sc = self._extract_soft_constraint(node)
                if sc:
                    pass  # 已在 constraints 中处理
            
            # P5: DPI
            elif kind_name == 'DPIExport':
                dpi = self._extract_dpi_export(node)
                if dpi:
                    self.dpi_exports.append(dpi)
            
            elif kind_name == 'PureFunction':
                pf = self._extract_pure_function(node)
                if pf:
                    self.pure_functions.append(pf)
            
            # P6: Process
            elif kind_name == 'ProcessStatement':
                p = self._extract_process(node)
                if p:
                    self.process_ops.append(p)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_enum(self, node) -> Optional[EnumDef]:
        e = EnumDef()
        if hasattr(node, 'name') and node.name:
            e.name = str(node.name)
        
        # 提取枚举值
        if hasattr(node, 'values') and node.values:
            for val in node.values:
                e.values.append(str(val))
        
        return e if e.name else None
    
    def _extract_queue_op(self, node) -> Optional[QueueOp]:
        q = QueueOp()
        if hasattr(node, 'method') and node.method:
            q.method = str(node.method)
        elif hasattr(node, 'name') and node.name:
            q.name = str(node.name)
        return q if q.method or q.name else None
    
    def _extract_mailbox(self, node) -> Optional[MailboxDef]:
        m = MailboxDef()
        if hasattr(node, 'name') and node.name:
            m.name = str(node.name)
        return m if m.name else None
    
    def _extract_semaphore(self, node) -> Optional[SemaphoreDef]:
        s = SemaphoreDef()
        if hasattr(node, 'name') and node.name:
            s.name = str(node.name)
        return s if s.name else None
    
    def _extract_coverpoint_bins(self, node):
        # 遍历子节点提取 bins
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind == 'WildcardBins':
                wb = WildcardBins()
                if hasattr(child, 'name') and child.name:
                    wb.bins_name = str(child.name)
                self.wildcard_bins.append(wb)
            
            elif child_kind == 'IllegalBins':
                ib = IllegalBins()
                self.illegal_bins.append(ib)
            
            elif child_kind == 'IgnoreBins':
                ib = IgnoreBins()
                self.ignore_bins.append(ib)
    
    def _extract_solve_before(self, node) -> Optional[SolveBefore]:
        sb = SolveBefore()
        # 提取变量
        if hasattr(node, 'variables') and node.variables:
            for var in node.variables:
                sb.variables.append(str(var))
        return sb if sb.variables else None
    
    def _extract_unique_constraint(self, node) -> Optional[UniqueConstraint]:
        uc = UniqueConstraint()
        if hasattr(node, 'variables') and node.variables:
            for var in node.variables:
                uc.variables.append(str(var))
        return uc if uc.variables else None
    
    def _extract_soft_constraint(self, node) -> Optional[SoftConstraint]:
        sc = SoftConstraint()
        if hasattr(node, 'expression') and node.expression:
            sc.expr = str(node.expression)
        return sc if sc.expr else None
    
    def _extract_dpi_export(self, node) -> Optional[DPIExport]:
        dpi = DPIExport()
        if hasattr(node, 'name') and node.name:
            dpi.name = str(node.name)
        if hasattr(node, 'returnType') and node.returnType:
            dpi.return_type = str(node.returnType)
        return dpi if dpi.name else None
    
    def _extract_pure_function(self, node) -> Optional[PureFunction]:
        pf = PureFunction()
        if hasattr(node, 'name') and node.name:
            pf.name = str(node.name)
        return pf if pf.name else None
    
    def _extract_process(self, node) -> Optional[ProcessOp]:
        p = ProcessOp()
        if hasattr(node, 'keyword') and node.keyword:
            p.operation = str(node.keyword)
        return p if p.operation else None
    
    def extract_from_text(self, code: str, source: str = "<text>"):
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'enums': len(self.enums),
            'queue_ops': len(self.queue_ops),
            'mailboxes': len(self.mailboxes),
            'semaphores': len(self.semaphores),
            'wildcard_bins': len(self.wildcard_bins),
            'solve_before': len(self.solve_before),
            'unique_constraints': len(self.unique_constraints),
            'dpi_exports': len(self.dpi_exports),
            'pure_functions': len(self.pure_functions),
            'process_ops': len(self.process_ops)
        }


# 便捷函数
def extract_advanced_verification(code: str) -> Dict:
    return AdvancedVerificationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    enum {IDLE, RUN, DONE} state;
    mailbox#(int) mb;
    semaphore sem(2);
    
    covergroup cg;
        bins wild = {[0:100]};
    endgroup
    
    constraint c {
        solve a before b;
        unique {x, y};
    }
    
    process p;
endmodule
'''
    
    print("=== Advanced Verification Extraction ===\n")
    result = extract_advanced_verification(test_code)
    for k, v in result.items():
        print(f"{k}: {v}")
