"""ConstraintParser - SystemVerilog 约束 AST 解析器。

解析约束表达式，提取：
- 引用的变量
- 变量关系 (>, <, ==, 等)
- 约束类型 (simple, implication, soft, dist)
- 跨变量约束

Example:
    >>> from debug.class_const_parser import ConstraintParser
    >>> from debug.class_extractor import ClassExtractor
    >>> ce = ClassExtractor(parser)
    >>> cp = ConstraintParser(ce)
    >>> print(cp.get_report())
"""
import sys
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field

from .class_info import ConstraintInfo as ClassConstraintInfo
from .class_extractor import ClassExtractor


@dataclass
class ConstraintVariable:
    """约束变量引用数据类。
    
    Attributes:
        name: 变量名
        data_type: 数据类型
        is_rand: 是否为随机变量
    """
    name: str
    data_type: str = ""
    is_rand: bool = False


@dataclass
class ConstraintExpression:
    """约束表达式数据类。
    
    Attributes:
        left_var: 左侧变量
        operator: 运算符
        right_value: 右侧值
        expression_str: 完整表达式字符串
    """
    left_var: str
    operator: str
    right_value: str
    expression_str: str = ""


@dataclass
class ConstraintDetail:
    """详细约束信息数据类。
    
    Attributes:
        name: 约束名
        class_name: 所属类名
        constraint_type: 约束类型
        variables: 涉及的变量列表
        expressions: 表达式列表
        line_number: 行号
        is_overridden: 是否被覆盖
        parent_class: 父类名
    """
    name: str
    class_name: str
    constraint_type: str  # "simple", "implication", "soft", "dist"
    variables: List[ConstraintVariable] = field(default_factory=list)
    expressions: List[ConstraintExpression] = field(default_factory=list)
    line_number: int = 0
    is_overridden: bool = False
    parent_class: Optional[str] = None


class ConstraintParser:
    """约束 AST 解析器。
    
    解析类约束的抽象语法树，提取变量和表达式信息。

    Attributes:
        class_extractor: 类提取器
        classes: 类信息字典
        constraints: 约束详情字典
    
    Example:
        >>> cp = ConstraintParser(ce)
        >>> print(cp.get_report())
    """
    
    def __init__(self, class_extractor: ClassExtractor):
        """初始化解析器。
        
        Args:
            class_extractor: ClassExtractor 实例
        """
        self.class_extractor = class_extractor
        self.classes = class_extractor.classes
        self.constraints: Dict[str, ConstraintDetail] = {}  # class.constraint -> detail
        
        self._parse_all_constraints()
    
    def _parse_all_constraints(self):
        """解析所有类的约束。"""
        for class_name, cls in self.classes.items():
            if cls.constraints:
                for const in cls.constraints:
                    self._parse_constraint(class_name, const)
    
    def _parse_constraint(self, class_name: str, const: ClassConstraintInfo):
        """解析单个约束。
        
        Args:
            class_name: 类名
            const: 约束信息对象
        """
        detail = ConstraintDetail(
            name=const.name,
            class_name=class_name,
            constraint_type=const.constraint_type,
            line_number=0,
            is_overridden=False
        )
        
        # Get variables from class properties
        if class_name in self.classes:
            cls = self.classes[class_name]
            
            # Find variables used in constraint expression
            const_expr = const.expression
            
            # Extract variable references
            var_pattern = r'\b(\w+)\b'
            matches = re.findall(var_pattern, const_expr)
            
            for var_name in matches:
                # Skip keywords
                if var_name.lower() in {'inside', 'dist', 'weight', 'true', 'false', 
                                        'and', 'or', 'not', 'if', 'else', 'soft'}:
                    continue
                
                # Check if it's a class property
                is_property = any(p.name == var_name for p in cls.properties)
                is_rand = any(p.name == var_name and p.rand_mode in ('rand', 'randc') 
                            for p in cls.properties)
                
                detail.variables.append(ConstraintVariable(
                    name=var_name,
                    is_rand=is_rand
                ))
            
            # Parse expressions
            self._parse_expressions(const_expr, detail)
        
        key = f"{class_name}.{const.name}"
        self.constraints[key] = detail
    
    def _parse_expressions(self, expr_str: str, detail: ConstraintDetail):
        """解析约束表达式。
        
        Args:
            expr_str: 表达式字符串
            detail: 约束详情对象
        """
        # Remove constraint keywords for cleaner parsing
        expr = re.sub(r'\binside\b.*?\{.*?\}', '', expr_str)  # Remove inside {...}
        expr = re.sub(r'\bdist\b.*?\{.*?\}', '', expr)      # Remove dist {...}
        
        # Find comparisons: var > value, var < value, etc.
        comp_pattern = r'(\w+)\s*(==|!=|>=|<=|>|<|->|<->)\s*(\w+|[\'"][\w]+[\'"])'
        matches = re.findall(comp_pattern, expr)
        
        for left, op, right in matches:
            if left.lower() not in {'inside', 'dist', 'if', 'else', 'soft'}:
                detail.expressions.append(ConstraintExpression(
                    left_var=left,
                    operator=op,
                    right_value=right,
                    expression_str=f"{left} {op} {right}"
                ))
    
    def get_constraint_variables(self, class_name: str, constraint_name: str) -> List[ConstraintVariable]:
        """获取约束中使用的所有变量。
        
        Args:
            class_name: 类名
            constraint_name: 约束名
        
        Returns:
            List[ConstraintVariable]: 变量列表
        """
        key = f"{class_name}.{constraint_name}"
        return self.constraints.get(key, ConstraintDetail("", "", "")).variables
    
    def get_cross_variable_constraints(self, class_name: str) -> Set[Tuple[str, str]]:
        """查找涉及多个类属性的约束。
        
        Args:
            class_name: 类名
        
        Returns:
            Set[Tuple[str, str]]: 变量对集合
        """
        results = set()
        
        if class_name not in self.classes:
            return results
        
        cls = self.classes[class_name]
        property_names = {p.name for p in cls.properties}
        
        for const in cls.constraints:
            key = f"{class_name}.{const.name}"
            detail = self.constraints.get(key)
            
            if not detail:
                continue
            
            # Only keep class properties
            vars_used = [v.name for v in detail.variables if v.name in property_names]
            
            if len(vars_used) > 1:
                # Unique pairs
                for i in range(len(vars_used)):
                    for j in range(i+1, len(vars_used)):
                        results.add((vars_used[i], vars_used[j]))
        
        return results
    
    def get_constraint_type_summary(self) -> Dict[str, int]:
        """获取约束类型统计。
        
        Returns:
            Dict[str, int]: 类型到数量的映射
        """
        summary = {}
        
        for key, detail in self.constraints.items():
            ctype = detail.constraint_type
            summary[ctype] = summary.get(ctype, 0) + 1
        
        return summary
    
    def find_overridden_constraints(self) -> List[ConstraintDetail]:
        """查找被子类覆盖的约束。
        
        Returns:
            List[ConstraintDetail]: 被覆盖的约束列表
        """
        overridden = []
        
        for class_name, cls in self.classes.items():
            for const in cls.constraints:
                key = f"{class_name}.{const.name}"
                # Check parent classes
                while hasattr(cls, 'extends') and cls.extends:
                    parent = cls.extends
                    parent_key = f"{parent}.{const.name}"
                    if parent_key in self.constraints:
                        detail = self.constraints[key]
                        detail.is_overridden = True
                        detail.parent_class = parent
                        overridden.append(detail)
                        break
        
        return overridden
    
    def get_report(self) -> str:
        """获取约束分析报告。
        
        Returns:
            str: 格式化的报告字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CONSTRAINT ANALYSIS")
        lines.append("=" * 60)
        
        # Summary by type
        lines.append("\n[Constraint Types]")
        for ctype, count in sorted(self.get_constraint_type_summary().items()):
            lines.append(f"  {ctype}: {count}")
        
        # Cross-variable constraints
        lines.append("\n[Cross-Variable Constraints]")
        for class_name in self.classes:
            cross = self.get_cross_variable_constraints(class_name)
            if cross:
                lines.append(f"  {class_name}:")
                for v1, v2 in cross:
                    lines.append(f"    {v1} <-> {v2}")
        
        # Overridden constraints  
        lines.append("\n[Overridden Constraints]")
        overridden = self.find_overridden_constraints()
        for detail in overridden:
            if detail.is_overridden:
                lines.append(f"  {detail.name}: {detail.parent_class} -> {detail.class_name}")
        
        return "\n".join(lines)
