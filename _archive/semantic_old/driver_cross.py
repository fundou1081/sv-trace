"""跨模块驱动提取"""

def find_all_instantiations(tree) -> list:
    """从 AST 提取所有模块实例 - 简化版"""
    results = []
    
    # 遍历顶层节点找 HierarchyInstantiation
    for node in tree.root:
        if node.kind.name != 'SyntaxList':
            continue
            
        for sub in node:
            if sub.kind.name == 'HierarchyInstantiation':
                result = {'instance': '', 'module': '', 'ports': {}}
                
                # 遍历 HierarchyInstantiation 的子节点
                for item in sub:
                    # Identifier = 模块名
                    if item.kind.name == 'Identifier':
                        result['module'] = str(getattr(item, 'value', item))
                    
                    # SeparatedList = 端口参数
                    elif item.kind.name == 'SeparatedList':
                        # 这里可能包含 HierarchicalInstance
                        for port_item in item:
                            if port_item.kind.name == 'HierarchicalInstance':
                                for hi_child in port_item:
                                    # InstanceName = 实例名
                                    if hi_child.kind.name == 'InstanceName':
                                        for ic in hi_child:
                                            if ic.kind.name == 'Identifier':
                                                result['instance'] = str(getattr(ic, 'value', ic))
                                    
                    # 也可能有直接的 NamedPortConnection
                    # 这里需要更完整的解析
                
                if result['module']:
                    results.append(result)
    
    return results
