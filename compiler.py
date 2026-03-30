from lexer import lex
from parser import Parser


file = "code.txt"

tokens = lex(file)
parser = Parser(tokens)
ast = parser.parse()

print("AST:")
for stmt in ast:
    print(stmt)