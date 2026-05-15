"""
Constraint extraction stub (铁律8)

This module provides stub implementations for constraint extraction
that were part of the old architecture but not yet migrated.
"""
from typing import List, Any


class ConstraintExtractor:
    """Constraint extractor (stub)
    
    Note: 完整实现需要解析 class 中的 rand 和 constraint 声明
    """
    def __init__(self):
        pass
    
    def extract(self, tree) -> List[Any]:
        """Extract constraints from syntax tree"""
        return []
    
    def extract_from_text(self, code: str) -> List[Any]:
        """Extract constraints from code text"""
        return []