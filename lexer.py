from enum import Enum 

class TokenType(Enum):
    IDENTIFIER = "identifier"
    STRING = "string"
    SEPARATOR = "separator"
    KEYWORD = "keyword"
    OPERATOR = "operator"
    NUMBER = "number"

class Token:
    def __init__(self, type: TokenType, value: str):
        self.type = type
        self.value = value

    def __repr__ (self):
        return f"{self.type.name}, {self.value}"


SEPARATORS = ["(",")","{","}", ","]
KEYWORDS = ["def", "return", "print"]
OPERATORS = ["+","-","*","/", "="]
    
def lex(file):
    with open(file) as f:
        code = f.read()
    
    tokens = []
    i = 0
    while i < len(code):
        c = code[i]

        # skip whitespace
        if c.isspace():
            i += 1
            continue

        # identifiers / keywords
        if c.isalpha():
            start = i
            while i < len(code) and code[i].isalnum():
                i +=1
            
            word = code[start:i]
            if word in KEYWORDS:
                tokens.append(Token(TokenType.KEYWORD, word))
            else:
                tokens.append(Token(TokenType.IDENTIFIER, word))
            continue
        
        # numbers
        if c.isdigit():
            start = i
            while i < len(code) and code[i].isdigit():
                i += 1
            
            number = code[start:i]
            tokens.append(Token(TokenType.NUMBER, number))
            continue

        # string
        if c == "'" or c == '"':
            i += 1
            start = i

            while i < len(code) and code[i] != "'" and code[i] != '"':
                i += 1
            
            string_value = code[start:i]
            tokens.append(Token(TokenType.STRING, string_value))
            i += 1
            continue

        # operators
        if c in OPERATORS:
            tokens.append(Token(TokenType.OPERATOR, c))
            i += 1
            continue

        # separators
        if c in SEPARATORS:
            tokens.append(Token(TokenType.SEPARATOR, c))
            i += 1
            continue
        
    return tokens