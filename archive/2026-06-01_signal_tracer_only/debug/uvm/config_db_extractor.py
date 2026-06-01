"""
ConfigDBExtractor - UVM Config DB 提取器
追踪 uvm_config_db 的 set/get 操作
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ConfigDBEntry:
    """单个 uvm_config_db 条目"""
    operation: str = "set"
    type_param: str = ""
    instance_path: str = ""
    field_name: str = ""
    value: str = ""
    is_virtual: bool = False
    is_sequence: bool = False
    line_number: int = 0
    file_name: str = ""
    
    def visualize(self) -> str:
        v = self.value.rstrip(')')
        return f"[{self.line_number}] {self.instance_path}.{self.field_name} = {v[:50]}"


@dataclass
class ConfigDBStats:
    """配置统计"""
    total_sets: int = 0
    virtual_interfaces: int = 0
    sequences: int = 0
    int_configs: int = 0
    by_component: Dict[str, int] = field(default_factory=dict)


@dataclass 
class ConfigDBResult:
    """完整结果"""
    entries: List[ConfigDBEntry] = field(default_factory=list)
    stats: ConfigDBStats = field(default_factory=ConfigDBStats)
    config_trace: Dict[str, List[str]] = field(default_factory=dict)
    
    def visualize(self) -> str:
        lines = ["=" * 60, "UVM CONFIG DB ANALYSIS", "=" * 60]
        
        lines.append(f"\n📊 Summary:")
        lines.append(f"  Total Sets: {self.stats.total_sets}")
        lines.append(f"  Virtual Interfaces: {self.stats.virtual_interfaces}")
        lines.append(f"  Sequences: {self.stats.sequences}")
        lines.append(f"  Int Configs: {self.stats.int_configs}")
        
        if self.stats.by_component:
            lines.append(f"\n📦 By Component:")
            for comp, count in sorted(self.stats.by_component.items()):
                lines.append(f"  {comp}: {count}")
        
        if self.entries:
            lines.append(f"\n📝 Config Entries ({len(self.entries)}):")
            for e in self.entries:
                lines.append(f"  {e.visualize()}")
                lines.append(f"      type: {e.type_param}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ConfigDBExtractor:
    """uvm_config_db 提取器"""
    
    def __init__(self, parser):
        self.parser = parser
    
    def extract_from_file(self, file_path: str) -> ConfigDBResult:
        """从文件提取"""
        try:
            with open(file_path) as f:
                lines = f.readlines()
        except:
            return ConfigDBResult()
        
        return self._extract_lines(lines, file_path)
    
    def extract_from_parser(self) -> ConfigDBResult:
        """从 parser 提取"""
        all_lines = []
        for fname, tree in self.parser.trees.items():
            try:
                code = tree.source if hasattr(tree, 'source') and tree.source else ""
            except:
                code = ""
            
            if code:
                all_lines.extend([(i+1, fname, line) for i, line in enumerate(code.split('\n'))])
            else:
                try:
                    with open(fname) as f:
                        all_lines.extend([(i+1, fname, line) for i, line in enumerate(f.readlines())])
                except:
                    continue
        
        return self._extract_raw(all_lines)
    
    def _extract_lines(self, lines: List[str], file_path: str) -> ConfigDBResult:
        numbered_lines = [(i+1, file_path, line) for i, line in enumerate(lines)]
        return self._extract_raw(numbered_lines)
    
    def _extract_raw(self, lines: List[tuple]) -> ConfigDBResult:
        result = ConfigDBResult()
        
        for line_num, fname, line in lines:
            entry = self._parse_line(line.strip(), line_num, fname)
            if entry:
                result.entries.append(entry)
                self._update_stats(result, entry)
        
        return result
    
    def _parse_line(self, line: str, line_num: int, file_path: str) -> Optional[ConfigDBEntry]:
        if 'uvm_config_db' not in line or '::set' not in line:
            return None
        
        type_match = line.find('#(')
        type_end = line.find(')::set')
        
        if type_match < 0 or type_end < 0:
            return None
        
        type_param = line[type_match+2:type_end].strip()
        
        set_start = line.find('::set(')
        if set_start < 0:
            return None
        
        param_str = line[set_start + 5:]
        if param_str.rstrip().endswith(';'):
            param_str = param_str[:-1].strip()
        
        parts = self._split_params(param_str)
        
        if len(parts) < 4:
            return None
        
        instance_path = parts[1].strip().strip('"')
        field_name = parts[2].strip().strip('"')
        value = parts[3].strip()
        
        is_virtual = 'virtual' in type_param.lower()
        is_sequence = 'wrapper' in type_param.lower()
        
        return ConfigDBEntry(
            operation="set",
            type_param=type_param,
            instance_path=instance_path,
            field_name=field_name,
            value=value,
            is_virtual=is_virtual,
            is_sequence=is_sequence,
            line_number=line_num,
            file_name=file_path
        )
    
    def _split_params(self, s: str) -> List[str]:
        parts = []
        current = ""
        in_quotes = 0
        
        for char in s:
            if char == '"':
                in_quotes = 1 - in_quotes
            elif char == ',' and in_quotes == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            parts.append(current.strip())
        
        return parts
    
    def _update_stats(self, result: ConfigDBResult, entry: ConfigDBEntry):
        result.stats.total_sets += 1
        
        if entry.is_virtual:
            result.stats.virtual_interfaces += 1
        elif entry.is_sequence:
            result.stats.sequences += 1
        elif 'int' in entry.type_param.lower():
            result.stats.int_configs += 1
        
        if '.' in entry.instance_path:
            comp = entry.instance_path.split('.')[0]
            result.stats.by_component[comp] = result.stats.by_component.get(comp, 0) + 1
        
        key = f"{entry.instance_path}.{entry.field_name}"
        if key not in result.config_trace:
            result.config_trace[key] = []
        result.config_trace[key].append(entry.value)
    
    def find_interface_configs(self) -> List[ConfigDBEntry]:
        return [e for e in self.entries if e.is_virtual]
    
    def find_sequence_configs(self) -> List[ConfigDBEntry]:
        return [e for e in self.entries if e.is_sequence]


def extract_config_db(parser) -> ConfigDBResult:
    extractor = ConfigDBExtractor(parser)
    return extractor.extract_from_parser()
