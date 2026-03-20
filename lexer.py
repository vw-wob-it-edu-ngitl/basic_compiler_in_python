from enum import Enum 
class Token:
    def __init__(self, type: TokenType, value: str):
        self.type = type
        self.value = value

    def __repr__ (self):
        return f"{self.type.name}, {self.value}"

class TokenType(Enum):
    SEPARATOR = "separator"
    KEYWORD = "keyword"
    OPERATOR = "operator"
    LITERAL = "literal"

SEPARATORS = ["(",")","{","}",";"]
KEYWORDS = ["int", "return", "main"]
OPERATORS = ["+","-","*","/", "="]
tokens = []

def readfile(file):
    with open(file) as f:
        return f.read().replace("\r", "").replace("\n", "").replace(" ", "")
    
def checkkey(s):
    if s in SEPARATORS:
        tokens.append(Token(TokenType.SEPARATOR, s))
        return True
    if s in KEYWORDS:
        tokens.append(Token(TokenType.KEYWORD, s))
        return True
    if s in OPERATORS:
        tokens.append(Token(TokenType.OPERATOR, s))
        return True
    else:
        return False
    
def lex(file):
    code = readfile(file)
    substr = ""
    for c in code:
        substr += c
        if c in SEPARATORS and len(substr)>1:
            tokens.append(Token(TokenType.LITERAL, substr[0:-1]))
            substr = ""
            checkkey(c)
        if checkkey(substr):
            substr = ""
            continue
        

    
    for token in tokens:
        print(token)