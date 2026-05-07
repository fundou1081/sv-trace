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
        
        def find_procedural(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ProceduralBlock' in type_name:
                stmt = node.statement
                if hasattr(stmt, 'items') and stmt.items:
                    for i in range(len(stmt.items)):
                        item = stmt.items[i]
                        if 'ConditionalStatement' in str(type(item)):
                            analyze_conditional(item, depth+2)
            
            if hasattr(node, 'members') and node.members:
                for m in node.members:
                    find_procedural(m, depth+1)
            if hasattr(node, 'body') and node.body:
                for b in node.body:
                    find_procedural(b, depth+1)
        
        def analyze_conditional(cond, depth):
            print(f"{'  '*depth}ConditionalStatement:")
            print(f"{'  '*depth}  predicate: {cond.predicate}")
            print(f"{'  '*depth}  statement type: {type(cond.statement)}")
            
            if cond.elseClause:
                ec = cond.elseClause
                print(f"{'  '*depth}  elseClause.clause: {type(ec.clause)}")
                # Check if clause is another ConditionalStatement
                if ec.clause:
                    if 'ConditionalStatement' in str(type(ec.clause)):
                        print(f"{'  '*depth}    -> nested if/else-if!")
                        analyze_conditional(ec.clause, depth+2)
                    elif 'BlockStatement' in str(type(ec.clause)):
                        print(f"{'  '*depth}    -> else block")
                        if hasattr(ec.clause, 'items') and ec.clause.items:
                            for i in range(len(ec.clause.items)):
                                print(f"{'  '*depth}      block item: {type(ec.clause.items[i])}")
        
        find_procedural(root)
finally:
    os.unlink(tmp)
