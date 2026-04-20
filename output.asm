section .data
fmt db "%ld", 10, 0
str0 db "hello", 0

section .text
global _main
extern _printf
extern _exit

_main:
call test
mov rsi, rax
lea rdi, [rel fmt]
xor rax, rax
call _printf
mov rdi, 0
call _exit

test:
push rbp
mov rbp, rsp
sub rsp, 8
lea rax, [rel str0]
mov [rbp - 8], rax
mov rax, 5
mov rsp, rbp
pop rbp
ret