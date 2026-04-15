class CodeGenerator:
    def __init__(self):
        self.code = [] # list of instructions

    def emit(self, instruction):
        self.code.append(instruction)
    
    def generate(self, node):
        method_name = f"gen_{type(node).__name__}"
        method = getattr(self, method_name, self.no_gen)
        return method(node)
    
    def no_gen(self, node):
        raise Exception(f"No generator for {type(node).__name__}")
    
    def gen_Number(self, node):
        self.emit(f"mov rax, {node.value}")
    
    def gen_Var(self, node):
        name = node.name

        if hasattr(self, "current_params") and node.name in self.current_locals:
            offset = self.current_params[node.name]
            self.emit(f"mov rax, [rsp + {offset}]") 
        elif hasattr(self, "current_params") and name in self.current_params:
            offset = self.current_params[name]
            self.emit(f"mov rax, [rsp + {offset}]")
        else:
            self.emit(f"mov rax, [{name}]")

    def gen_Assignment(self, node):
        self.generate(node.value)
        name = node.name

        if hasattr(self, "current_locals") and name in self.current_locals:
            offset = self.current_locals[name]
            self.emit(f"mov [rsp + {offset}], rax")
        elif hasattr(self, "current_params") and name in self.current_params:
            offset = self.current_params[name]
            self.emit(f"mov [rsp + {offset}], rax")
        else:
            self.emit(f"mov [{name}], rax")

    def gen_Print(self, node):
        self.generate(node.value)
        self.emit("print rax")
    
    def gen_Return(self, node):
        self.generate(node.value)
        self.emit("RET rax")


    def gen_BinOp(self, node):
        self.generate(node.left)
        self.emit("push rax")

        self.generate(node.right)
        self.emit("pop rbx")

        if node.op == "+":
            self.emit("add rax, rbx")
        elif node.op == "-":
            self.emit("sub rbx, rax")
            self.emit("mov rax, rbx")
        elif node.op == "*":
            self.emit("mul rax, rbx")
        elif node.op == "/":
            self.emit("div rax, rbx")


    def gen_Function(self, node):
        self.emit(f"FUNC {node.name}")

        self.current_params = {}
        self.current_locals = {}

        for i, param in enumerate(node.params):
            offset = i * 8
            self.current_params[param] = offset
            self.emit(f"; {param} at [rsp + {offset}]")

        local_index = len(node.params)
        
        for stmt in node.body:
            if type(stmt) in node.body:
                var_name = stmt.name
                if var_name not in self.current_params:
                    offset = local_index * 8
                    self.current_locals[local_index] = offset
                    local_index += 1
                    self.emit(f"; local {var_name} at [rsp + {offset}]")
        
        for stmt in node.body:
            self.generate(stmt)

        self.emit("END_FUNC\n")
        self.current_params = {}
        self.current_locals = {}

    def gen_FunctionCall(self, node):
        for arg in reversed(node.args):
            self.generate(arg)
            self.emit("push rax")
        
        self.emit(f"Call {node.name}")

        if node.args:
            self.emit(f"add rsp, {len(node.args) * 8}")

    def gen_String(self, node):
        self.emit(f'mov rax, "{node.value}"')