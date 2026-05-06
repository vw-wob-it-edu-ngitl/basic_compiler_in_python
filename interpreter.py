class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Interpreter:
    def __init__(self):
        self.env = {} # stores variables
        self.functions = {}

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit)
        return method(node)
    
    def no_visit(self, node):
        raise Exception(f"No visit Method for {type(node).__name__}")
    
    def visit_Number(self, node):
        return node.value
    
    def visit_Var(self, node):
        if node.name not in self.env:
            raise Exception(f"Undefined variable: {node.name}")
        return self.env[node.name]
    
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)

        if node.op == "+":
            return left + right
        elif node.op == "-":
            return left - right
        elif node.op == "*":
            return left * right
        elif node.op == "/":
            return left / right
    
    def visit_Assignment(self, node):
        value = self.visit(node.value)
        self.env[node.name] = value

    def visit_Print(self, node):
        value = self.visit(node.value)
        print(value)

    def visit_String(self, node):
        return node.value
    
    def visit_Return(self, node):
        value = self.visit(node.value)
        raise ReturnException(value)
    
    def visit_Function(self, node):
        self.functions[node.name] = node

    def visit_FunctionCall(self, node):
        if node.name not in self.functions:
            raise Exception(f"Undefined function {node.name}")
        
        func = self.functions[node.name]

        args = [self.visit(arg) for arg in node.args]

        local_env = {}

        for i in range(len(func.params)):
            param_name = func.params[i]
            local_env[param_name] = args[i]

        old_env = self.env
        self.env = local_env

        result = None
        try:
            for stmt in func.body:
                self.visit(stmt)
        except ReturnException as r:
            result = r.value
        
        self.env = old_env
        return result