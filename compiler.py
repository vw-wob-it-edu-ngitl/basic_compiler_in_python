from lexer import lex
from parser import Parser
from codegen import CodeGenerator

file = "code.txt"

tokens = lex(file)
parser = Parser(tokens)
ast = parser.parse()

gen = CodeGenerator()

for stmt in ast:
    gen.generate(stmt)

print("\n".join(gen.code))