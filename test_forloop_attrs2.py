import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

TEST = '''module t;
    logic [31:0] i, sum, data [0:3];
    always_comb begin
        sum = 0;
        for (int i = 0; i < 4; i++) begin
            sum = sum + data[i];
        end
    end
endmodule'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    
    # Manual traversal to find the for loop
    for path, tree in parser.trees.items():
        root = tree.root
        
        # Get modules
        modules = []
        if 'ModuleDeclaration' in str(type(root)):
            modules = [root]
        elif hasattr(root, 'members') and root.members:
            for i in range(len(root.members)):
                if 'ModuleDeclaration' in str(type(root.members[i])):
                    modules.append(root.members[i])
        
        for module in modules:
            # Get body
            if hasattr(module, 'body') and module.body:
                for b in module.body:
                    if 'ProceduralBlock' in str(type(b)):
                        stmt = b.statement
                        if hasattr(stmt, 'items') and stmt.items:
                            for idx in range(len(stmt.items)):
                                item = stmt.items[idx]
                                print(f"Block item[{idx}]: {type(item).__name__}")
                                if 'ForLoop' in str(type(item)):
                                    print(f"  -> Found ForLoop!")
                                    print(f"     has body: {hasattr(item, 'body')}")
                                    print(f"     has statement: {hasattr(item, 'statement')}")
                                    print(f"     has loopBody: {hasattr(item, 'loopBody')}")
finally:
    os.unlink(tmp)
