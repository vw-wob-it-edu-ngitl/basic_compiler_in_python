class CodeGenerator:
    def __init__(self):
        self.code = [] # list of instructions
        self.data = []
        self.functions_code = []
        self.variables = set()
        self.string_count = 0
        self.string_vars = set()
            
    def emit(self, instruction):
        if hasattr(self, "in_function") and self.in_function:
            self.functions_code.append(instruction)
        else:
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

        if hasattr(self, "current_locals") and name in self.current_locals:
            offset = self.current_locals[name]
            self.emit(f"mov rax, [rbp - {offset}]")
        elif hasattr(self, "current_params") and name in self.current_params:
            offset = self.current_params[name]        
            self.emit(f"mov rax, [rbp + {offset}]")
        else:
            self.emit(f"mov rax, [rel {name}]")

    def gen_Assignment(self, node):
        self.generate(node.value)
        name = node.name

        # track string variables
        if type(node.value).__name__ == "String":
            self.string_vars.add(name)

        if hasattr(self, "current_locals") and name in self.current_locals:
            offset = self.current_locals[name]
            self.emit(f"mov [rbp - {offset}], rax")
        elif hasattr(self, "current_params") and name in self.current_params:
            offset = self.current_params[name]
            self.emit(f"mov [rbp + {offset}], rax")
        else:
            self.variables.add(name)
            self.emit(f"mov [rel {name}], rax")

    def gen_Print(self, node):
        self.generate(node.value)

        is_string = (
            type(node.value).__name__ == "String" or
            (type(node.value).__name__ == "Var" and node.value.name in self.string_vars)
        )

        if is_string:
            self.emit("mov rdi, rax")           # rdi = pointer to string (1st arg)
            self.emit("xor rax, rax")
            self.emit("and rsp, -16")           # align stack (Bug 4 fix)
            self.emit("call _printf")
        else:
            self.emit("mov rsi, rax")           # rsi = number value (2nd arg)
            self.emit("lea rdi, [rel fmt]")     # rdi = format string (1st arg)
            self.emit("xor rax, rax")
            self.emit("and rsp, -16")           # align stack (Bug 4 fix)
            self.emit("call _printf")
    
    def gen_Return(self, node):
        self.generate(node.value)

        self.emit("mov rsp, rbp")
        self.emit("pop rbp")
        self.emit("ret")


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
            self.emit("imul rax, rbx")
        elif node.op == "/":
            self.emit("xchg rax, rbx")
            self.emit("cqo")
            self.emit("idiv rbx")


    def gen_Function(self, node):
        self.in_function = True

        self.emit(f"{node.name}:")
        self.emit("push rbp")
        self.emit("mov rbp, rsp")

        self.current_params = {}
        for i, param in enumerate(node.params):
            self.current_params[param] = 16 + (i * 8)

        self.current_locals = {}
        local_offset = 0

        for stmt in node.body:
            if type(stmt).__name__ == "Assignment":
                name = stmt.name

                if name not in self.current_params:
                    if name not in self.current_locals:
                        local_offset += 8
                        self.current_locals[name] = local_offset

        if local_offset > 0:
            self.emit(f"sub rsp, {local_offset}")
        
        has_return = False

        for stmt in node.body:
            self.generate(stmt)

            if type(stmt).__name__ == "Return":
                has_return = True
                break
        
        if not has_return:
            self.emit("mov rax, 0")
            self.emit("mov rsp, rbp")
            self.emit("pop rbp")
            self.emit("ret")

        self.in_function = False

    def gen_FunctionCall(self, node):
        for arg in reversed(node.args):
            self.generate(arg)
            self.emit("push rax")
        
        self.emit(f"call {node.name}")

        if node.args:
            self.emit(f"add rsp, {len(node.args) * 8}")

    def gen_String(self, node):
        label = f"str{self.string_count}"
        self.string_count += 1

        #store string in data section
        self.data.append(f'{label} db "{node.value}", 0')

        self.emit(f"lea rax, [rel {label}]")

    def get_program(self):
        data_section = ["section .data"]

        # number format
        data_section.append('fmt db "%ld", 10, 0')

        # generated strings (like str0, str1, …)
        data_section.extend(self.data)

        # global variables
        for var in self.variables:
            data_section.append(f"{var} dq 0")

        # text section
        text_section = [
            "section .text",
            "global _main",
            "extern _printf",
            "extern _exit",
            "",
            "_main:"
        ]

        # combine everything
        program = []
        program.extend(data_section)
        program.append("")
        program.extend(text_section)
        program.extend(self.code)

        # exit
        program.append("and rsp, -16")
        program.append("mov rdi, 0")
        program.append("call _exit")

        program.append("")
        program.extend(self.functions_code)

        return "\n".join(program)
    

