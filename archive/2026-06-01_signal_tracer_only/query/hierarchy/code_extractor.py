"""
代码片段提取器
从源文件中提取指定位置的代码片段
"""
import os
from typing import Optional, List, Dict, Any


class CodeSnippet:
    """代码片段"""
    def __init__(self, code: str, start_line: int, end_line: int, 
                 file: str = "", context: str = ""):
        self.code = code
        self.start_line = start_line
        self.end_line = end_line
        self.file = file
        self.context = context
        self.lines = code.split('\n')
    
    def __str__(self):
        return f"Lines {self.start_line}-{self.end_line}: {self.code[:50]}..."
    
    def format(self, context_lines: int = 2) -> str:
        """格式化输出，包含上下文"""
        lines = []
        
        # 标题
        if self.file:
            lines.append(f"// File: {self.file}")
        lines.append(f"// Lines: {self.start_line}-{self.end_line}")
        if self.context:
            lines.append(f"// Context: {self.context}")
        lines.append("")
        
        # 代码
        for i, line in enumerate(self.lines, self.start_line):
            prefix = ">>>" if i == self.start_line else "   "
            lines.append(f"{prefix} {i:4d} | {line}")
        
        return "\n".join(lines)


class CodeExtractor:
    """代码片段提取器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._file_cache: Dict[str, List[str]] = {}
    
    def get_snippet(self, file: str, start_line: int, end_line: int = None,
                    context: int = 2) -> Optional[CodeSnippet]:
        """获取代码片段"""
        if end_line is None:
            end_line = start_line
        
        lines = self._read_file_lines(file)
        if not lines:
            return None
        
        # 确保在有效范围内
        start = max(0, start_line - 1 - context)
        end = min(len(lines), end_line + context)
        
        snippet_lines = lines[start:end]
        code = "\n".join(snippet_lines)
        
        return CodeSnippet(
            code=code,
            start_line=start_line,
            end_line=end_line,
            file=file,
        )
    
    def get_snippet_by_offset(self, file: str, offset: int, 
                              context: int = 2) -> Optional[CodeSnippet]:
        """通过 offset 获取代码片段（pyslang 用 offset 而非 line）"""
        lines = self._read_file_lines(file)
        if not lines:
            return None
        
        # 简单实现：扫描 offset 找到行号
        line_num = 1
        char_count = 0
        for i, line in enumerate(lines):
            if char_count + len(line) >= offset:
                line_num = i + 1
                break
            char_count += len(line) + 1  # +1 for newline
        
        return self.get_snippet(file, line_num, line_num, context)
    
    def get_driver_snippet(self, signal_name: str, module_name: str = None) -> Optional[CodeSnippet]:
        """获取信号的驱动代码片段"""
        from trace import DriverTracer
        
        tracer = DriverTracer(self.parser)
        drivers = tracer.find_driver(signal_name, module_name)
        
        if not drivers:
            return None
        
        driver = drivers[0]
        
        # 使用 offset 获取文件
        filepath = ""
        for fp in self.parser.trees.keys():
            filepath = fp
            break
        
        if driver.file:
            filepath = driver.file
        
        if filepath and driver.line > 0:
            return self.get_snippet(filepath, driver.line)
        
        return None
    
    def get_load_snippet(self, signal_name: str, module_name: str = None) -> List[CodeSnippet]:
        """获取信号的负载代码片段列表"""
        from trace import LoadTracer
        
        tracer = LoadTracer(self.parser)
        loads = tracer.find_load(signal_name, module_name)
        
        snippets = []
        for load in loads:
            if load.file and load.line:
                snippet = self.get_snippet(load.file, load.line)
                if snippet:
                    snippet.context = load.context
                    snippets.append(snippet)
        
        return snippets
    
    def get_surrounding_lines(self, file: str, line: int, 
                              before: int = 5, after: int = 5) -> List[str]:
        """获取周围代码行"""
        lines = self._read_file_lines(file)
        if not lines:
            return []
        
        start = max(0, line - 1 - before)
        end = min(len(lines), line - 1 + after)
        
        return lines[start:end]
    
    def _read_file_lines(self, filepath: str) -> List[str]:
        """读取文件行缓存"""
        if not filepath:
            return []
        
        if filepath in self._file_cache:
            return self._file_cache[filepath]
        
        if not os.path.exists(filepath):
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            self._file_cache[filepath] = lines
            return lines
        except Exception:
            return []
    
    def search_keyword(self, keyword: str, file: str = None) -> List[Dict[str, Any]]:
        """搜索关键字"""
        results = []
        
        files = [file] if file else list(self.parser.trees.keys())
        
        for filepath in files:
            lines = self._read_file_lines(filepath)
            
            for i, line in enumerate(lines, 1):
                if keyword.lower() in line.lower():
                    results.append({
                        "file": filepath,
                        "line": i,
                        "content": line.rstrip(),
                        "snippet": self.get_snippet(filepath, i, i, context=1),
                    })
        
        return results


class SourceViewer:
    """源码查看器 - 高级封装"""
    
    def __init__(self, parser):
        self.parser = parser
        self.extractor = CodeExtractor(parser)
        self.resolver = HierarchicalResolver(parser)
    
    def show_signal(self, signal_path: str) -> str:
        """展示信号的完整信息"""
        # 解析路径
        signal_info = self.resolver.resolve_signal(signal_path)
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"Signal: {signal_path}")
        lines.append("=" * 60)
        
        if not signal_info:
            return "\n".join(lines) + "\n[ERROR] Signal not found"
        
        # 信号定义信息
        lines.append(f"\n[Definition]")
        lines.append(f"  Module: {signal_info.get('module', 'unknown')}")
        lines.append(f"  Type: {signal_info.get('type', 'unknown')}")
        lines.append(f"  Offset: {signal_info.get('offset', 0)}")
        
        # 获取代码片段
        signal_name = signal_path.split(".")[-1]
        
        # 驱动代码
        driver_snippet = self.extractor.get_driver_snippet(signal_name)
        if driver_snippet:
            lines.append(f"\n[Driver]")
            lines.append(driver_snippet.format(context_lines=2))
        
        # 负载代码
        load_snippets = self.extractor.get_load_snippet(signal_name)
        if load_snippets:
            lines.append(f"\n[Loads ({len(load_snippets)})]")
            for i, ls in enumerate(load_snippets[:3], 1):
                lines.append(f"  --- Load #{i} ---")
                lines.append(ls.format(context_lines=1))
        
        return "\n".join(lines)
    
    def show_dataflow(self, signal_path: str) -> str:
        """展示完整数据流"""
        from trace import DataFlowTracer
        
        signal_name = signal_path.split(".")[-1]
        
        tracer = DataFlowTracer(self.parser)
        flow = tracer.find_flow(signal_name)
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"DataFlow: {signal_name}")
        lines.append("=" * 60)
        
        # 驱动
        if flow.drivers:
            lines.append(f"\n[Drivers ({len(flow.drivers)})]")
            for d in flow.drivers:
                lines.append(f"  {d.driver_kind.name}: {d.source_expr}")
        
        # 负载
        if flow.loads:
            lines.append(f"\n[Loads ({len(flow.loads)})]")
            for l in flow.loads:
                lines.append(f"  {l.context}")
        
        return "\n".join(lines)


# 延迟导入避免循环依赖
from .resolver import HierarchicalResolver
