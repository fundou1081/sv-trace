import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

# Test While Loop
TEST1 = '''module t;
    logic [31:0] cnt, max_val;
    logic valid;
    always_comb begin
        cnt = 0;
        while (cnt < max_val && valid) begin
            cnt = cnt + 1;
        end
    end
endmodule'''

# Test Do-While
TEST2 = '''module t;
    logic [31:0] cnt;
    always_comb begin
        do begin
            cnt = cnt - 1;
        end while (cnt > 0);
    end
endmodule'''

# Test Foreach
TEST3 = '''module t;
    logic [31:0] arr [0:3], sum;
    always_comb begin
        sum = 0;
        foreach (arr[i]) begin
            sum = sum + arr[i];
        end
    end
endmodule'''

for name, test in [("While", TEST1), ("Do-While", TEST2), ("Foreach", TEST3)]:
    print(f"=== {name} ===")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(test)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        
        for path, tree in parser.trees.items():
            root = tree.root
            
            if hasattr(root, 'members') and root.members:
                for i in range(len(root.members)):
                    member = root.members[i]
                    
                    if hasattr(member, 'members') and member.members:
                        for j in range(len(member.members)):
                            m = member.members[j]
                            
                            if 'ProceduralBlock' in str(type(m)):
                                stmt = m.statement
                                if hasattr(stmt, 'items') and stmt.items:
                                    for k in range(len(stmt.items)):
                                        item = stmt.items[k]
                                        type_name = str(type(item))
                                        if 'Loop' in type_name or 'While' in type_name or 'For' in type_name:
                                            print(f"  Found: {type_name}")
                                            attrs = [a for a in dir(item) if not a.startswith('_') and 'Statement' in a or a in ['body', 'statement', 'loopBody']]
                                            print(f"  attrs: {[a for a in dir(item) if not a.startswith('_')]}")
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        os.unlink(tmp)
    print()
