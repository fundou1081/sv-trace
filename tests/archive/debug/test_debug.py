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
        print(f"=== Tree: {path} ===")
        root = tree.root
        
        def find_always(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ProceduralBlock' in type_name:
                print(f"{'  '*depth}Found ProceduralBlock: {type_name}")
                if hasattr(node, 'statement'):
                    stmt = node.statement
                    print(f"{'  '*depth}  statement type: {type(stmt)}")
                    if hasattr(stmt, 'items') and stmt.items:
                        print(f"{'  '*depth}  items count: {len(stmt.items)}")
                        for i, item in enumerate(stmt.items):
                            print(f"{'  '*depth}    item[{i}] type: {type(item)}")
                            if hasattr(item, 'ifBody'):
                                print(f"{'  '*depth}      has ifBody: True")
                            if hasattr(item, 'elseBody'):
                                print(f"{'  '*depth}      has elseBody: True")
            for attr in ['members', 'body', 'statements', 'items']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                find_always(c, depth+1)
                        elif hasattr(child, "__len__") and hasattr(child, "__getitem__"):
                            for idx in range(len(child)):
                                find_always(child[idx], depth+1)
        
        find_always(root)
finally:
    os.unlink(tmp)
