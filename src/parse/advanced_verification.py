"""
高级验证语法解析器 - 使用 pyslang AST (P2-P6)
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind, TokenKind


# ========== P2: 高级数据类型 ==========

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


@dataclass
class MailboxDef:
    name: str = ""


@dataclass
class SemaphoreDef:
    name: str = ""
    count: int = 1


# ========== P3: 高级覆盖 ==========

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


# ========== P4: 高级约束 ==========

@dataclass
class SolveBefore:
    variables: List[str] = field(default_factory=list)


@dataclass
class UniqueConstraint:
    variables: List[str] = field(default_factory=list)


@dataclass
class SoftConstraint:
    expr: str = ""


# ========== P5: DPI ==========

@dataclass
class DPIExport:
    name: str = ""


@dataclass
class PureFunction:
    name: str = ""


# ========== P6: Process ==========

@dataclass
class ProcessOp:
    operation: str = ""


class AdvancedVerificationExtractor:
    def __init__(self, parser=None):
        self.enums = []
        self.string_ops = []
        self.queues = []
        self.mailboxes = []
        self.semaphores = []
        self.wildcard_bins = []
        self.illegal_bins = []
        self.ignore_bins = []
        self.solve_before = []
        self.unique_constraints = []
        self.soft_constraints = []
        self.dpi_exports = []
        self.pure_functions = []
        self.process_ops = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree.root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            self._process_node(node)
            return pyslang.VisitAction.Advancee
        
        root.visit(collect)
    
    def _process_node(self, node):
        kn = node.kind.name
        
        # P2: EnumDefinition (typedef enum)
        if kn == 'EnumDeclaration' or (kn == 'TypedefDeclaration' and 'enum' in str(node).lower()):
            enum = EnumDef()
            
            # 获取 enum 名称
            if hasattr(node, 'name'):
                enum.name = str(node.name).strip()
            
            # 提取值
            str_repr = str(node)
            # enum { IDLE, RUN, DONE }
            match = re.finditer(r'(\w+)\s*,?', str_repr)
            for m in match:
                val = m.group(1)
                if val not in ['enum', 'typedef', '{', '}']:
                    enum.values.append(val)
            
            if enum.values:
                self.enums.append(enum)
        
        # P2: StringType 或 StringKeyword
        elif 'String' in kn:
            self.string_ops.append(StringOp(operation='string_type'))
        
        # P2: Queue - QueueDimensionSpecifier
        elif 'Queue' in kn:
            self.queues.append(QueueOp(name='queue'))
        
        # P2: MailboxDeclaration
        elif kn == 'MailboxDeclaration':
            mb = MailboxDef()
            if hasattr(node, 'name'):
                mb.name = str(node.name).strip()
            if not mb.name:
                s = str(node)
                m = re.search(r'mailbox\s+(\w+)', s)
                if m:
                    mb.name = m.group(1)
            if mb.name:
                self.mailboxes.append(mb)
        
        # P2: SemaphoreDeclaration
        elif kn == 'SemaphoreDeclaration':
            sm = SemaphoreDef()
            if hasattr(node, 'name'):
                sm.name = str(node.name).strip()
            if not sm.name:
                s = str(node)
                m = re.search(r'semaphore\s+(\w+)', s)
                if m:
                    sm.name = m.group(1)
            if sm.name:
                self.semaphores.append(sm)
        
        # P3: WildcardCoverBin
        elif 'Wildcard' in kn:
            wc = WildcardBins()
            s = str(node)
            # wildcard bins NAME = {...}
            m = re.search(r'wildcard\s+bins\s+(\w+)\s*=\s*\{([^}]+)\}', s)
            if m:
                wc.bins_name = m.group(1)
                for v in m.group(2).split(','):
                    wc.values.append(v.strip())
            self.wildcard_bins.append(wc)
        
        # P3: IllegalCoverBin
        elif 'Illegal' in kn:
            ib = IllegalBins()
            s = str(node)
            m = re.finditer(r'illegal\s+bins\s*\{([^}]+)\}', s)
            for m2 in m:
                ib.values.append(m2.group(1).strip())
            self.illegal_bins.append(ib)
        
        # P3: IgnoreCoverBin
        elif 'Ignore' in kn:
            igb = IgnoreBins()
            s = str(node)
            m = re.finditer(r'ignore\s+bins\s*\{([^}]+)\}', s)
            for m2 in m:
                igb.values.append(m2.group(1).strip())
            self.ignore_bins.append(igb)
        
        # P4: SolveBefore/SolveOrderingConstraint
        elif 'Solve' in kn:
            sv = SolveBefore()
            s = str(node)
            # solve a before b
            match = re.search(r'solve\s+(\w+)\s+before\s+(\w+)', s)
            if match:
                sv.variables = [match.group(1), match.group(2)]
            self.solve_before.append(sv)
        
        # P4: UniqueConstraint
        elif 'Unique' in kn:
            uc = UniqueConstraint()
            s = str(node)
            # unique { a, b }
            match = re.search(r'unique\s+\{([^}]+)\}', s)
            if match:
                for v in match.group(1).split(','):
                    uc.variables.append(v.strip())
            self.unique_constraints.append(uc)
        
        # P4: SoftConstraint
        elif 'Soft' in kn:
            sc = SoftConstraint()
            sc.expr = str(node).strip()
            self.soft_constraints.append(sc)
        
        # P5: DPIExport
        elif kn == 'DPIExport':
            dpi = DPIExport()
            s = str(node)
            m = re.search(r'DPI["\s]+(\w*)\s+(\w+)', s)
            if m:
                dpi.name = m.group(2)
            self.dpi_exports.append(dpi)
        
        # P5: Pure function
        elif 'Pure' in kn:
            s = str(node)
            m = re.search(r'pure\s+function\s+(\w+)\s+(\w+)', s)
            if m:
                pf = PureFunction()
                pf.name = m.group(2)
                self.pure_functions.append(pf)
        
        # P6: Process operations (process::self, wait fork, disable fork)
        else:
            s = str(node)
            if 'process::self' in s:
                self.process_ops.append(ProcessOp(operation='process_self'))
            elif 'wait fork' in s:
                self.process_ops.append(ProcessOp(operation='wait_fork'))
            elif 'disable fork' in s:
                self.process_ops.append(ProcessOp(operation='disable_fork'))
    
    def get_results(self):
        return {
            'enums': self.enums,
            'string_ops': self.string_ops,
            'queues': self.queues,
            'mailboxes': self.mailboxes,
            'semaphores': self.semaphores,
            'wildcard_bins': self.wildcard_bins,
            'illegal_bins': self.illegal_bins,
            'ignore_bins': self.ignore_bins,
            'solve_before': self.solve_before,
            'unique_constraints': self.unique_constraints,
            'soft_constraints': self.soft_constraints,
            'dpi_exports': self.dpi_exports,
            'pure_functions': self.pure_functions,
            'process_ops': self.process_ops,
        }


def extract_advanced_verification(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = AdvancedVerificationExtractor(None)
    extractor._extract_from_tree(tree.root)
    return extractor.get_results()


if __name__ == "__main__":
    test_code = '''module m;
    // P2: 高级数据类型
    typedef enum {IDLE, RUN, DONE} state_e;
    string s;
    int q[$];
    mailbox mb;
    semaphore sem;
    
    // P3: 高级覆盖
    covergroup cg;
        coverpoint data {
            wildcard bins wb[] = {[0:255]};
            illegal bins ib = {255};
            ignore bins ign = {[32:63]};
        }
    endgroup
    
    // P4: 高级约束
    constraint data_c {
        solve data before addr;
        unique {field_a, field_b};
        soft data < 100;
    }
    
    // P5: DPI
    export "DPI" void test_export();
    export "DPI" pure function int get_id();
    
    // P6: Process
    process p;
    initial begin
        process::self();
        wait fork;
        disable fork;
    end
endmodule'''
    
    result = extract_advanced_verification(test_code)
    
    print("=== 高级验证语法 (P2-P6) ===")
    
    print(f"\n【P2 Advanced Data】")
    print(f"  Enums: {len(result['enums'])}")
    for e in result['enums']:
        print(f"    {e.name}: {e.values}")
    print(f"  String: {len(result['string_ops'])}")
    print(f"  Queues: {len(result['queues'])}")
    print(f"  Mailboxes: {len(result['mailboxes'])}")
    for m in result['mailboxes']:
        print(f"    {m.name}")
    print(f"  Semaphores: {len(result['semaphores'])}")
    for s in result['semaphores']:
        print(f"    {s.name}")
    
    print(f"\n【P3 Coverage】")
    print(f"  Wildcard bins: {len(result['wildcard_bins'])}")
    for wb in result['wildcard_bins']:
        print(f"    {wb.bins_name}: {wb.values}")
    print(f"  Illegal bins: {len(result['illegal_bins'])}")
    print(f"  Ignore bins: {len(result['ignore_bins'])}")
    
    print(f"\n【P4 Constraints】")
    print(f"  Solve before: {len(result['solve_before'])}")
    for sc in result['solve_before']:
        print(f"    {sc.variables}")
    print(f"  Unique: {len(result['unique_constraints'])}")
    print(f"  Soft: {len(result['soft_constraints'])}")
    
    print(f"\n【P5 DPI】")
    print(f"  Exports: {len(result['dpi_exports'])}")
    for d in result['dpi_exports']:
        print(f"    {d.name}")
    print(f"  Pure functions: {len(result['pure_functions'])}")
    
    print(f"\n【P6 Process】")
    print(f"  Ops: {len(result['process_ops'])}")
    for p in result['process_ops']:
        print(f"    {p.operation}")
