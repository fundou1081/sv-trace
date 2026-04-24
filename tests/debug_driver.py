"""Debug: BlockStatement 结构"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parse import SVParser

TEST_CODE = """
module top;
    logic [7:0] result;
    always_comb begin result = 8'h1; end
endmodule
"""

parser = SVParser()
tree = parser.parse_text(TEST_CODE)
root = tree.root

for i in range(len(root.members)):
    item = root.members[i]
    if 'Always' in type(item).__name__:
        stmt = item.statement
        
        print("BlockStatementSyntax attributes:")
        for attr in dir(stmt):
            if not attr.startswith('_') and not callable(getattr(stmt, attr, None)):
                try:
                    val = getattr(stmt, attr)
                    print(f"  {attr}: {type(val).__name__} = {str(val)[:30]}")
                except:
                    pass
