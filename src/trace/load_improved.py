"""
Load Tracer Improved - 改进版信号负载追踪器
"""
import re
from typing import List, Dict, Set
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load


class LoadTracerImproved:
    """改进版信号负载追踪器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._code_cache: Dict[str, str] = {}
    
    def _load_code(self, filepath: str) -> str:
        if filepath in self._code_cache:
            return self._code_cache[filepath]
        
        if hasattr(self.parser, 'sources') and filepath in self.parser.sources:
            code = self.parser.sources[filepath]
            self._code_cache[filepath] = code
            return code
        
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            self._code_cache[filepath] = code
            return code
        except:
            return ""
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        loads = []
        
        for filepath in self.parser.trees.keys():
            code = self._load_code(filepath)
            if not code:
                continue
            
            lines = code.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                
                if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                    continue
                
                # 时钟/复位事件
                if re.search(rf'@\s*\([^)]*\b{signal_name}\b', stripped):
                    loads.append(Load(
                        signal_name=signal_name,
                        context=stripped[:100],
                        line=line_num,
                        condition="clock_event"
                    ))
                
                # 条件判断
                if re.search(rf'\b(?:if|else\s+if)\s*\([^)]*\b{signal_name}\b[^)]*\)', stripped):
                    loads.append(Load(
                        signal_name=signal_name,
                        context=stripped[:100],
                        line=line_num,
                        condition=signal_name
                    ))
                
                # case语句
                if re.search(rf'\bcase\s*\([^)]*\b{signal_name}\b[^)]*\)', stripped):
                    loads.append(Load(
                        signal_name=signal_name,
                        context=stripped[:100],
                        line=line_num,
                        condition=signal_name
                    ))
                
                # 赋值右侧
                if re.search(rf'\b{signal_name}\b\s*=', stripped):
                    if not re.search(r'\b(?:logic|wire|reg|bit)\s+[^{]*\b(?:=|\Z)', stripped):
                        loads.append(Load(
                            signal_name=signal_name,
                            context=stripped[:100],
                            line=line_num
                        ))
                
                # 三元表达式
                if re.search(rf'\b{signal_name}\s*\?', stripped):
                    loads.append(Load(
                        signal_name=signal_name,
                        context=stripped[:100],
                        line=line_num
                    ))
            
        return loads
    
    def get_fanout(self, signal_name: str) -> int:
        return len(self.find_load(signal_name))


class FanoutAnalyzerImproved:
    """改进版扇出分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self.load_tracer = LoadTracerImproved(parser)
        self._all_signals: Set[str] = set()
        self._collect_all_signals()
    
    def _collect_all_signals(self):
        """收集所有信号"""
        # 从源码中提取所有信号
        for filepath in self.parser.trees.keys():
            code = self.load_tracer._load_code(filepath)
            if not code:
                continue
            
            # 提取信号名
            patterns = [
                r'\blogic\s*(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\bwire\s*(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\breg\s*(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\binput\s+(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
                r'\boutput\s+(?:\[[^\]]+\])?\s+([a-zA-Z_]\w*)',
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    self._all_signals.add(match.group(1))
    
    def analyze_signal(self, signal_name: str) -> Dict:
        loads = self.load_tracer.find_load(signal_name)
        return {
            'signal': signal_name,
            'direct_fanout': len(loads),
            'loads': loads
        }
    
    def find_high_fanout_signals(self, threshold: int = 10):
        """查找高扇出信号 - 分析所有信号"""
        results = []
        
        for sig in self._all_signals:
            if sig.startswith('_'):
                continue  # 跳过内部信号
            fanout = self.load_tracer.get_fanout(sig)
            if fanout >= threshold:
                results.append({
                    'signal': sig,
                    'direct_fanout': fanout,
                    'loads': self.load_tracer.find_load(sig)
                })
        
        return sorted(results, key=lambda x: -x['direct_fanout'])


def get_signal_fanout_improved(parser, signal_name: str) -> int:
    tracer = LoadTracerImproved(parser)
    return tracer.get_fanout(signal_name)


__all__ = ['LoadTracerImproved', 'FanoutAnalyzerImproved', 'get_signal_fanout_improved']
