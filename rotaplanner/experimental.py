import ast

source = "a==b or (len(c)>5)+(6*9) and 1 in [9]"

tree = ast.parse(source, mode="eval")
code = compile(tree, filename="<ast>", mode="eval")
print(ast.dump(tree, indent=4))
print(ast.unparse(tree))
print(eval(code, locals={"a": 1, "b": 1, "c": "hello world"}))
