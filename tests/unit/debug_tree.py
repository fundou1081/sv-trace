"""Debug connections"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
import pyslang

CODE = """
module top;
    logic [7:0] data;
    cpu u_cpu (.clk(clk), .data_in(data));
endmodule
"""

parser = SVParser()
tree = parser.parse_text(CODE, "test.sv")
root = tree.root

# 找到 HierarchyInstantiation
for i in range(len(root.members)):
    item = root.members[i]
    if item.kind == pyslang.SyntaxKind.HierarchyInstantiation:
        inst_node = item.instances
        inst = inst_node[0]  # u_cpu
        
        print(f"Instance: {inst.decl.name.value}")
        
        # connections
        conn_node = inst.connections
        print(f"\nconnections type: {type(conn_node).__name__}")
        
        for j in range(len(conn_node)):
            conn = conn_node[j]
            print(f"\n  [{j}] {type(conn).__name__}")
            
            # 打印属性
            for attr in dir(conn):
                if attr.startswith('_') or attr == 'parent':
                    continue
                try:
                    val = getattr(conn, attr)
                    if not callable(val):
                        print(f"    {attr}: {type(val).__name__}")
                        if hasattr(val, 'value'):
                            print(f"        value: {val.value}")
                except:
                    pass
