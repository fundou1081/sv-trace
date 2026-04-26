"""
ConstraintGenerator - 约束自动生成
基于Spec自动生成随机约束
"""
import re
from typing import List, Dict

class ConstraintGenerator:
    """约束生成器"""
    
    # 常见参数范围
    KNOWN_RANGES = {
        'baud': [9600, 19200, 38400, 57600, 115200],
        'data_bits': [5, 6, 7, 8],
        'stop_bits': [1, 2],
        'parity': ['none', 'odd', 'even'],
    }
    
    def parse_spec_for_constraints(self, spec_text: str) -> Dict[str, List]:
        """从Spec中解析约束范围"""
        constraints = {}
        
        # 波特率
        baud_match = re.search(r'波特率.*?(\d+).*?(\d+)', spec_text)
        if baud_match:
            constraints['baud_rate'] = list(range(int(baud_match.group(1)), 
                                                  int(baud_match.group(2)) + 1))
        
        # 数据位
        bits_match = re.search(r'数据位.*?(\d).*?(\d)', spec_text)
        if bits_match:
            constraints['data_bits'] = list(range(int(bits_match.group(1)), 
                                                int(bits_match.group(2)) + 1))
        
        # 其他参数
        for key, values in self.KNOWN_RANGES.items():
            if key in spec_text.lower():
                constraints[key] = values
        
        return constraints
    
    def generate_systemverilog_constraint(self, constraints: Dict) -> str:
        """生成SystemVerilog约束"""
        lines = []
        lines.append("// 自动生成的约束")
        lines.append("")
        
        for name, values in constraints.items():
            lines.append(f"class {name}_constraint;")
            lines.append(f"    rand {self._get_type(name)} {name};")
            lines.append("")
            lines.append(f"    constraint {name}_c {{")
            
            if isinstance(values, list) and len(values) > 0:
                if all(isinstance(v, int) for v in values):
                    lines.append(f"        {name} inside {{ {', '.join(str(v) for v in values)} }};")
                else:
                    lines.append(f"        {name} inside {{ {', '.join(repr(v) for v in values)} }};")
            
            lines.append("    }")
            lines.append("endclass")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _get_type(self, name: str) -> str:
        """获取类型"""
        if 'bits' in name or 'count' in name or 'num' in name:
            return 'bit[7:0]'
        elif 'baud' in name:
            return 'bit[31:0]'
        else:
            return 'int'
    
    def generate_python_model(self, constraints: Dict) -> str:
        """生成Python参考模型"""
        lines = []
        lines.append("# 自动生成的参考模型")
        lines.append("")
        lines.append("class ReferenceModel:")
        lines.append("")
        lines.append("    def __init__(self):")
        for name, values in constraints.items():
            if values:
                lines.append(f"        self.{name} = {values[0]}")
        lines.append("")
        lines.append("    def drive_transaction(self, data):")
        lines.append("        # 参考模型实现")
        lines.append("        pass")
        
        return '\n'.join(lines)
