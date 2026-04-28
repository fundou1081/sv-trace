import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

TEST = '''module t;
    logic [31:0] a, b, c, r;
    logic [1:0] sel;
    always_comb begin
        if (sel == 2'b00)
            r = a;
        else if (sel == 2'b01)
            r = b;
        else
            r = c;
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
        
        def find_if(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ConditionalStatement' in type_name:
                print(f"{'  '*depth}ConditionalStatement:")
                print(f"{'  '*depth}  predicate: {node.predicate if hasattr(node, 'predicate') else 'N/A'}")
                print(f"{'  '*depth}  statement type: {type(node.statement) if hasattr(node, 'statement') else 'N/A'}")
                print(f"{'  '*depth}  elseClause type: {type(node.elseClause) if hasattr(node, 'elseClause') and node.elseClause else 'None'}")
                if hasattr(node, 'elseClause') and node.elseClause:
                    ec = node.elseClause
                    print(f"{'  '*depth}    elseClause has statement: {hasattr(ec, 'statement')}")
                    if hasattr(ec, 'statement') and ec.statement:
                        print(f"{'  '*depth}      else statement type: {type(ec.statement)}")
                        # Check if it's another conditional
                        if 'ConditionalStatement' in str(type(ec.statement)):
                            print(f"{'  '*depth}      -> nested if!")
                            find_if(ec.statement, depth+3)
            for attr in ['members', 'body', 'statements', 'items']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                find_if(c, depth+1)
                        elif hasattr(child, "__len__") and hasattr(child, "__getitem__"):
                            for idx in range(len(child)):
                                find_if(child[idx], depth+1)
        
        find_if(root)
finally:
    os.unlink(tmp)
