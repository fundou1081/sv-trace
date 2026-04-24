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
        print(f"Root type: {type(root)}")
        
        # Walk through CompilationUnit to find modules
        def find_procedural(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ProceduralBlock' in type_name:
                print(f"{'  '*depth}Found ProceduralBlock")
                # Get the statement
                stmt = node.statement
                print(f"{'  '*depth}  statement type: {type(stmt)}")
                if hasattr(stmt, 'items') and stmt.items:
                    for i in range(len(stmt.items)):
                        item = stmt.items[i]
                        print(f"{'  '*depth}    item[{i}]: {type(item)}")
                        if 'ConditionalStatement' in str(type(item)):
                            print(f"{'  '*depth}      -> ConditionalStatement!")
                            # Print the elseClause
                            ec = item.elseClause
                            print(f"{'  '*depth}      elseClause: {type(ec)}")
                            if ec and hasattr(ec, 'statement'):
                                es = ec.statement
                                print(f"{'  '*depth}        else statement: {type(es)}")
                                if es:
                                    # Check if it's a Block or another Conditional
                                    print(f"{'  '*depth}        is Conditional? {'ConditionalStatement' in str(type(es))}")
            
            # Continue traversal
            if hasattr(node, 'members') and node.members:
                for m in node.members:
                    find_procedural(m, depth+1)
            if hasattr(node, 'body') and node.body:
                for b in node.body:
                    find_procedural(b, depth+1)
        
        find_procedural(root)
finally:
    os.unlink(tmp)
