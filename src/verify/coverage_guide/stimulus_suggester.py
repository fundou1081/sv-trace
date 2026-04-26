"""
CoverageStimulusSuggester - Coverage激励建议器
使用sv-trace已有的解析器进行路径分析

⚠️ 当前状态: 框架完成 (40%)
TODO:
- [x] 使用SVParser解析 ✅
- [x] 使用DriverCollector获取驱动 ✅
- [ ] 路径约束提取 (需要更深的AST分析)
- [ ] Z3约束求解集成
"""
import re
import sys
import os
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from parse import SVParser
from trace.driver import DriverCollector

class CoverageType(Enum):
    LINE = "line"
    BRANCH = "branch"
    FSM = "fsm"
    CONDITION = "condition"
    TOGGLE = "toggle"

@dataclass
class CoverageTarget:
    """Coverage目标"""
    coverage_type: CoverageType
    file: str
    line: int
    module: str = ""
    condition: Optional[str] = None

@dataclass
class StimulusSuggestion:
    """激励建议"""
    description: str
    input_signals: List[str]
    expected_values: Dict[str, str]
    priority: str  # high/medium/low
    confidence: float  # 0-1
    reasoning: str = ""

class CoverageStimulusSuggester:
    """Coverage激励建议器
    
    使用sv-trace的解析器进行路径分析
    """
    
    def __init__(self):
        self.parser = None
        self.driver_collector = None
        self.signal_info = {}
    
    def load_design(self, filepaths: List[str]) -> bool:
        """加载设计文件"""
        try:
            self.parser = SVParser()
            for fp in filepaths:
                self.parser.parse_file(fp)
            
            # 使用DriverCollector获取驱动信息
            self.driver_collector = DriverCollector(self.parser)
            
            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False
    
    def analyze_target(self, target: CoverageTarget) -> List[StimulusSuggestion]:
        """分析Coverage目标，生成激励建议"""
        suggestions = []
        
        if not self.parser:
            return suggestions
        
        # 根据coverage类型生成建议
        if target.coverage_type == CoverageType.LINE:
            suggestions = self._analyze_line_coverage(target)
        elif target.coverage_type == CoverageType.BRANCH:
            suggestions = self._analyze_branch_coverage(target)
        elif target.coverage_type == CoverageType.CONDITION:
            suggestions = self._analyze_condition_coverage(target)
        
        return suggestions
    
    def _get_signal_drivers(self, signal: str) -> List[Dict]:
        """获取信号的驱动信息"""
        if not self.driver_collector:
            return []
        
        drivers = self.driver_collector.drivers.get(signal, [])
        return [{'kind': str(d.kind), 'sources': d.sources} for d in drivers]
    
    def _extract_condition_from_ast(self, file: str, line: int) -> Optional[str]:
        """从AST中提取指定行的条件表达式
        
        使用sv-trace的parser
        """
        if not self.parser:
            return None
        
        # TODO: 使用pyslang AST深度遍历
        # 这个需要完整的AST分析
        
        return None
    
    def _analyze_line_coverage(self, target: CoverageTarget) -> List[StimulusSuggestion]:
        """分析行覆盖"""
        suggestions = []
        
        # 1. 尝试从源码提取条件
        source = self.parser.get_source(target.file) if self.parser else ""
        lines = source.split('\n') if source else []
        
        if target.line <= len(lines):
            line_content = lines[target.line - 1]
            
            # 分析该行的内容
            suggestions = self._generate_suggestions_from_code(line_content)
        
        return suggestions
    
    def _analyze_branch_coverage(self, target: CoverageTarget) -> List[StimulusSuggestion]:
        """分析分支覆盖"""
        suggestions = []
        
        # 分支: if/case/三元运算符
        suggestions.append(StimulusSuggestion(
            description="触发True分支",
            input_signals=[],
            expected_values={"condition": "1"},
            priority="high",
            confidence=0.5,
            reasoning="需要满足分支条件"
        ))
        
        suggestions.append(StimulusSuggestion(
            description="触发False分支",
            input_signals=[],
            expected_values={"condition": "0"},
            priority="high",
            confidence=0.5,
            reasoning="需要不满足分支条件"
        ))
        
        return suggestions
    
    def _analyze_condition_coverage(self, target: CoverageTarget) -> List[StimulusSuggestion]:
        """分析条件覆盖"""
        return self._analyze_branch_coverage(target)
    
    def _generate_suggestions_from_code(self, code: str) -> List[StimulusSuggestion]:
        """根据代码内容生成建议"""
        suggestions = []
        
        # 1. if语句
        if 'if' in code:
            match = re.search(r'if\s*\((.+?)\)', code)
            if match:
                condition = match.group(1)
                signals = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', condition)
                
                suggestions.append(StimulusSuggestion(
                    description=f"让条件为真: {condition}",
                    input_signals=signals,
                    expected_values={s: "1" for s in signals},
                    priority="high",
                    confidence=0.6,
                    reasoning="执行if内部代码"
                ))
        
        # 2. case语句
        if 'case' in code:
            match = re.search(r'(\w+)\s*==', code)
            if match:
                signal = match.group(1)
                suggestions.append(StimulusSuggestion(
                    description=f"设置 {signal} 的值",
                    input_signals=[signal],
                    expected_values={signal: "<value>"},
                    priority="high",
                    confidence=0.5,
                    reasoning="触发对应case分支"
                ))
        
        # 3. 比较运算符
        for op in ['==', '!=', '>', '<', '>= '<=']:
            if op in code:
                suggestions.append(StimulusSuggestion(
                    description=f"满足比较: {op}",
                    input_signals=[],
                    expected_values={},
                    priority="medium",
                    confidence=0.4,
                    reasoning="满足比较条件"
                ))
        
        if not suggestions:
            suggestions.append(StimulusSuggestion(
                description="覆盖该行",
                input_signals=[],
                expected_values={},
                priority="medium",
                confidence=0.3,
                reasoning="直接覆盖该代码行"
            ))
        
        return suggestions
    
    def suggest_stimulus(self, target: CoverageTarget) -> str:
        """生成激励建议文本"""
        suggestions = self.analyze_target(target)
        
        lines = []
        lines.append(f"# Coverage激励建议")
        lines.append(f"## 目标: {target.coverage_type.value} - {target.file}:{target.line}")
        lines.append("")
        
        # 信号驱动信息
        if self.driver_collector:
            lines.append("### 相关驱动信号")
            for sig, drivers in self.driver_collector.drivers.items()[:10]:
                if drivers:
                    lines.append(f"- {sig}: {[str(d.kind) for d in drivers]}")
            lines.append("")
        
        for i, s in enumerate(suggestions, 1):
            lines.append(f"### 建议 {i}: {s.description}")
            lines.append(f"- 优先级: {s.priority}")
            lines.append(f"- 置信度: {s.confidence:.0%}")
            lines.append(f"- 推理: {s.reasoning}")
            
            if s.input_signals:
                lines.append(f"- 需要信号: {', '.join(s.input_signals)}")
            
            if s.expected_values:
                lines.append(f"- 设置值:")
                for sig, val in s.expected_values.items():
                    lines.append(f"  - {sig} = {val}")
            
            lines.append("")
        
        return '\n'.join(lines)

# 使用示例
if __name__ == "__main__":
    import glob
    
    # 查找SV文件
    sv_files = glob.glob("../../../test/**/*.sv", recursive=True)
    
    if sv_files:
        suggester = CoverageStimulusSuggester()
        suggester.load_design(sv_files[:3])
        
        target = CoverageTarget(
            coverage_type=CoverageType.LINE,
            file=sv_files[0],
            line=50,
        )
        
        result = suggester.suggest_stimulus(target)
        print(result)
