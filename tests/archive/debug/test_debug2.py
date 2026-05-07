import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

TEST = '''module t;
    logic [31:0] a, b, r;
    logic cond;
    always_comb begin
        if (cond)
            r = a;
        else
            r = b;
    end
endmodule'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    for path, tree in parser.trees.items():
        root = tree.root
        
        def find_and_check(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ProceduralBlock' in type_name:
                stmt = node.statement
                if hasattr(stmt, 'items') and stmt.items:
                    for idx in range(len(stmt.items)):
                        item = stmt.items[idx]
                        print(f"Block item[{idx}]: {type(item)}")
                        # Check what attributes it has
                        print(f"  attr ifBody: {hasattr(item, 'ifBody')}")
                        print(f"  attr elseBody: {hasattr(item, 'elseBody')}")
                        print(f"  attr condition: {hasattr(item, 'condition')}")
                        if hasattr(item, 'ifBody') and item.ifBody:
                            print(f"    ifBody type: {type(item.ifBody)}")
                        if hasattr(item, 'elseBody') and item.elseBody:
                            print(f"    elseBody type: {type(item.elseBody)}")
            for attr in ['members', 'body', 'statements', 'items']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                find_and_check(c, depth+1)
                        elif hasattr(child, "__len__") and hasattr(child, "__getitem__"):
                            for idx in range(len(child)):
                                find_and_check(child[idx], depth+1)
        
        find_and_check(root)
finally:
    os.unlink(tmp)
