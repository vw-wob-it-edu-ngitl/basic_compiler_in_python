class Number:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"Number({self.value})"
    
class Var:
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"Var({self.name})"
    
class BinOp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    
    def __repr__(self):
        return f"BinOp({self.left}, {self.op}, {self.right})"
    
class Assignment:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"Assign({self.name}, {self.value})"
    
class Print:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Print({self.value})"

class Return:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Return({self.value})"
    
class String:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"String({self.value})"
    
class Function:
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

    def __repr__(self):
        return f"Function({self.name}, {self.params}, {self.body})" 
    
class FunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args
    
    def __repr__(self):
        return f"Call({self.name}, {self.args})"
    
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def eat(self):
        token = self.current()
        self.pos += 1
        return token
    
    def factor(self):
        token = self.current()

        #number
        if token.type.name == "NUMBER":
            self.eat()
            return Number(int(token.value))
        
        #variable
        elif token.type.name == "IDENTIFIER":
            name = token.value
            self.eat()

            #function call
            if self.current() and self.current().value == "(":
                self.eat() # (

                args = []
                if self.current().value != ")":
                    args.append(self.expression())

                    while self.current().value == ",":
                        self.eat()
                        args.append(self.expression())
                
                self.eat() # )
                return FunctionCall(name, args)
            return Var(name)
        
        #string
        elif token.type.name == "STRING":
            self.eat()
            return String(token.value)
        
        #parantheses
        elif token.value == "(":
            self.eat()
            node = self.expression()
            self.eat() # )
            return node
        
        else:
            raise Exception("Invalid syntax")

    def term(self):
        node = self.factor()

        while self.current() and self.current().value in ("*", "/"):
            op = self.eat()
            right = self.factor()
            node = BinOp(node, op.value, right)
        
        return node
    
    def expression(self):
        node = self.term()

        while self.current() and self.current().value in ("+", "-"):
            op = self.eat()
            right = self.term()
            node = BinOp(node, op.value, right)
        return node
    
    def return_statement(self):
        self.eat()
        if self.current() and self.current().value == "(":
            self.eat()
        value = self.expression()
        if self.current().value == ")":
            self.eat()
        return Return(value)

    def print_statement(self):
        self.eat()
        if self.current() and self.current().value == "(":
            self.eat()
        value = self.expression()
        if self.current().value == ")":
            self.eat()
        return Print(value)

    def statement(self):
        token = self.current()
        if token is None:
            return None

        if token.type.name == "KEYWORD":
            if token.value == "def":
                return self.function()
            elif token.value == "print":
                return self.print_statement()
            elif token.value == "return":
                return self.return_statement()

        elif token.type.name == "IDENTIFIER":
            return self.assignment()

        else:
            raise Exception(f"Unexpected token: {token}")
     
    def assignment(self):
        name = self.current().value
        self.eat()
        if self.current().value != "=":
            raise Exception("Expected =")
        self.eat()
        value = self.expression()
        return Assignment(name, value)
    
    def parse(self):
        statements = []
        while self.current() is not None:
            statements.append(self.statement())
        return statements
    
    def function(self):
        self.eat() #def
        name = self.current().value
        self.eat() #function name
        self.eat() #(
        params = []
        if self.current().value != ")":
            params.append(self.current().value)
            self.eat() #parameter token

            while self.current().value == ",":
                self.eat() #,
                params.append(self.current().value)
                self.eat()
        
        self.eat() #)
        self.eat() #{

        body = []
        while self.current() and self.current().value != "}":
            body.append(self.statement())
        self.eat()

        return Function(name, params, body)