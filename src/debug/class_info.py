"""ClassInfo - SystemVerilog 类相关数据结构。

提供 Class、Property、Constraint、Method 等数据类的定义。

Example:
    >>> from debug.class_info import ClassInfo, PropertyInfo
    >>> prop = PropertyInfo(name="data", data_type="bit", width=8)
    >>> cls = ClassInfo(name="Packet", properties=[prop])
    >>> print(cls.name)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict


@dataclass
class TypeParameterInfo:
    """类型参数信息。
    
    Attributes:
        name: 参数名
        default_type: 默认类型
    """
    name: str
    default_type: Optional[str] = None
    
    def __repr__(self):
        if self.default_type:
            return f"type {self.name} = {self.default_type}"
        return f"type {self.name}"


@dataclass
class ValueParameterInfo:
    """值参数信息。
    
    Attributes:
        name: 参数名
        data_type: 数据类型 (int, bit, logic 等)
        width: 位宽
        default_value: 默认值
    """
    name: str
    data_type: str                    # int, bit, logic, etc.
    width: Optional[int] = None       # Bit width if applicable
    default_value: Optional[str] = None
    
    def __repr__(self):
        if self.default_value:
            return f"{self.name} = {self.default_value}"
        return f"{self.name}"


@dataclass
class PropertyInfo:
    """类属性信息。
    
    Attributes:
        name: 属性名
        data_type: 数据类型 (bit, logic, int 等)
        width: 位宽
        dimensions: 数组维度
        qualifiers: 限定符 (rand, randc, local, protected, static, const)
        rand_mode: 随机模式 (rand/randc/none)
        default_value: 默认值
    """
    name: str
    data_type: str                    # Base type: bit, logic, int, etc.
    width: Optional[int] = None       # Bit width for scalar types
    dimensions: List[str] = field(default_factory=list)  # Array dimensions
    qualifiers: List[str] = field(default_factory=list)   # rand, randc, local, protected, static, const
    rand_mode: str = "none"            # rand, randc, or none
    default_value: Optional[str] = None
    
    def is_random(self) -> bool:
        """检查属性是否为随机的。
        
        Returns:
            bool: 是否为 rand 或 randc
        """
        return self.rand_mode in ("rand", "randc")
    
    def is_dynamic_array(self) -> bool:
        """检查是否为动态数组。
        
        Returns:
            bool: 是否为动态数组
        """
        return any('[]' in d for d in self.dimensions)
    
    def is_queue(self) -> bool:
        """检查是否为队列。
        
        Returns:
            bool: 是否为队列
        """
        return any('$' in d for d in self.dimensions)
    
    def is_assoc_array(self) -> bool:
        """检查是否为关联数组。
        
        Returns:
            bool: 是否为关联数组
        """
        return any('*' in d for d in self.dimensions)


@dataclass
class ConstraintInfo:
    """约束块信息。
    
    Attributes:
        name: 约束名
        constraint_type: 约束类型 (simple/implication/conditional/loop/soft/dist/solve_before)
        expression: 表达式
        raw_text: 原始文本
        is_soft: 是否为软约束
        dist_items: dist 约束项列表
    """
    name: str
    constraint_type: str = "simple"  # simple, implication, conditional, loop, soft, dist, solve_before
    expression: str = ""
    raw_text: str = ""
    is_soft: bool = False
    dist_items: List[str] = field(default_factory=list)  # For dist constraints
    
    def is_dist_constraint(self) -> bool:
        """检查是否为分布约束。
        
        Returns:
            bool: 是否为 dist 约束
        """
        return self.constraint_type == "dist" or 'dist' in self.expression
    
    def is_soft_constraint(self) -> bool:
        """检查是否为软约束。
        
        Returns:
            bool: 是否为软约束
        """
        return self.is_soft or self.constraint_type == "soft"


@dataclass
class MethodInfo:
    """类方法信息。
    
    Attributes:
        name: 方法名
        prototype: 原型
        qualifiers: 限定符列表
        return_type: 返回类型
    """
    name: str
    prototype: str
    qualifiers: List[str] = field(default_factory=list)
    return_type: str = ""
    
    def is_virtual(self) -> bool:
        """检查是否为虚方法。
        
        Returns:
            bool: 是否为虚方法
        """
        return 'virtual' in self.qualifiers
    
    def is_pure(self) -> bool:
        """检查是否为纯虚方法。
        
        Returns:
            bool: 是否为纯虚方法
        """
        return 'pure' in self.qualifiers
    
    def is_randomization_hook(self) -> bool:
        """检查是否为随机化钩子方法。
        
        Returns:
            bool: 是否为随机化钩子
        """
        return self.name in ('pre_randomize', 'post_randomize', 
                            'pre_solve', 'post_solve', 'randomize')
    
    def is_constraint_mode_method(self) -> bool:
        """检查是否为 constraint_mode() 方法。
        
        Returns:
            bool: 是否为 constraint_mode 方法
        """
        return 'constraint_mode' in self.name


@dataclass  
class ConstraintModeInfo:
    """约束模式信息。
    
    Attributes:
        constraint_name: 约束名
        enabled: 是否启用
    """
    constraint_name: str
    enabled: bool = True


@dataclass
class ClassInfo:
    """SystemVerilog 类完整信息。
    
    Attributes:
        name: 类名
        extends: 父类名
        properties: 属性列表
        constraints: 约束列表
        methods: 方法列表
        constraint_modes: 约束模式列表
        is_virtual: 是否为虚类
        is_abstract: 是否为抽象类
        line_number: 行号
        type_parameters: 类型参数列表
        value_parameters: 值参数列表
    """
    name: str
    extends: Optional[str] = None
    properties: List[PropertyInfo] = field(default_factory=list)
    constraints: List[ConstraintInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    constraint_modes: List[ConstraintModeInfo] = field(default_factory=list)
    is_virtual: bool = False
    is_abstract: bool = False
    line_number: int = 0
    # Parameterized class support
    type_parameters: List[TypeParameterInfo] = field(default_factory=list)
    value_parameters: List[ValueParameterInfo] = field(default_factory=list)
    
    @property
    def is_parameterized(self) -> bool:
        """检查是否为参数化类。
        
        Returns:
            bool: 是否有类型或值参数
        """
        return len(self.type_parameters) > 0 or len(self.value_parameters) > 0
    
    def get_parameters_summary(self) -> str:
        """获取参数摘要字符串。
        
        Returns:
            str: 参数化类的参数字符串
        """
        parts = []
        for p in self.value_parameters:
            parts.append(str(p))
        for p in self.type_parameters:
            parts.append(str(p))
        if parts:
            return "#(" + ", ".join(parts) + ")"
        return ""

    def get_rand_properties(self) -> List[PropertyInfo]:
        """获取所有随机属性。
        
        Returns:
            List[PropertyInfo]: rand/randc 属性列表
        """
        return [p for p in self.properties if p.is_random()]

    def get_constraint_by_name(self, name: str) -> Optional[ConstraintInfo]:
        """按名称查找约束。
        
        Args:
            name: 约束名
        
        Returns:
            ConstraintInfo: 找到则返回约束对象，否则返回 None
        """
        for c in self.constraints:
            if c.name == name:
                return c
        return None
    
    def get_randomization_hooks(self) -> List[MethodInfo]:
        """获取所有随机化钩子方法。
        
        Returns:
            List[MethodInfo]: 钩子方法列表
        """
        return [m for m in self.methods if m.is_randomization_hook()]
    
    def get_enabled_constraints(self) -> List[ConstraintInfo]:
        """获取所有启用的约束。
        
        Returns:
            List[ConstraintInfo]: 启用的约束列表
        """
        enabled_names = {cm.constraint_name for cm in self.constraint_modes if cm.enabled}
        if not enabled_names:
            return self.constraints  # All constraints enabled by default
        return [c for c in self.constraints if c.name in enabled_names]
    
    def get_dist_constraints(self) -> List[ConstraintInfo]:
        """获取所有分布约束。
        
        Returns:
            List[ConstraintInfo]: dist 约束列表
        """
        return [c for c in self.constraints if c.is_dist_constraint()]
