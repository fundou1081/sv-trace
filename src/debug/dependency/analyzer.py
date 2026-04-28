"""模块依赖分析器"""
import pyslang


class ModuleDependencyAnalyzer:
    def __init__(self, parser):
        self.parser = parser
        self.modules = {}
        self.instances = {}
        self._extract()
    
    def _extract(self):
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._find_modules(tree.root)
    
    def _find_modules(self, root):
        def callback(node):
            if node.kind == pyslang.SyntaxKind.ModuleDeclaration:
                name = str(node.header.name) if hasattr(node, 'header') and hasattr(node.header, 'name') else 'unknown'
                self.modules[name] = {'name': name, 'instances': []}
            return pyslang.VisitAction.Advance
        root.visit(callback)
    
    def get_all_modules(self):
        return list(self.modules.keys())


__all__ = ['ModuleDependencyAnalyzer']
