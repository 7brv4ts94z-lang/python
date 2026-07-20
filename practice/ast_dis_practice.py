import ast
import dis

# AST 분석
tree = ast.parse("x = a + b")
print("=== AST 분석 결과 ===")
print(ast.dump(tree, indent=2))


# 바이트코드 분석
def add(x, y):
    return x + y


print("\n=== 바이트코드 분석 결과 ===")
dis.dis(add)