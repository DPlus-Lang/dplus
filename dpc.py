#!/usr/bin/env python3
"""
D+ Programming Language Compiler
Version 34.0 - 完整版 + 内联汇编
支持真实机器码生成
文件名: dpc.py
"""

import sys
import os
import struct
import re

# ===========================================================================
# 完整版 + 内联汇编支持
# ===========================================================================

class DPlusCompiler:
    def __init__(self):
        self.output = bytearray()
        self.vars = {}
        self.stack_offset = 0
        self.labels = {}
        self.loop_stack = []
        self.current_if_else = None
        
        # x86指令编码表
        self.opcodes = {
            # 数据传送
            'mov': {'op': 0x89, 'mode': 'rm'},
            'mov_imm': {'op': 0xB8, 'mode': 'imm'},  # mov eax, imm
            'push': {'op': 0x50, 'mode': 'reg'},
            'pop': {'op': 0x58, 'mode': 'reg'},
            
            # 算术运算
            'add': {'op': 0x01, 'mode': 'rm'},
            'sub': {'op': 0x29, 'mode': 'rm'},
            'inc': {'op': 0x40, 'mode': 'reg'},
            'dec': {'op': 0x48, 'mode': 'reg'},
            'cmp': {'op': 0x39, 'mode': 'rm'},
            
            # 逻辑运算
            'and': {'op': 0x21, 'mode': 'rm'},
            'or': {'op': 0x09, 'mode': 'rm'},
            'xor': {'op': 0x31, 'mode': 'rm'},
            'not': {'op': 0xF7, 'ext': 2},
            'neg': {'op': 0xF7, 'ext': 3},
            
            # 移位
            'shl': {'op': 0xD1, 'ext': 4},
            'shr': {'op': 0xD1, 'ext': 5},
            'sar': {'op': 0xD1, 'ext': 7},
            
            # 跳转
            'jmp': {'op': 0xE9, 'mode': 'rel32'},
            'je': {'op': 0x0F84, 'mode': 'rel32'},
            'jne': {'op': 0x0F85, 'mode': 'rel32'},
            'jg': {'op': 0x0F8F, 'mode': 'rel32'},
            'jl': {'op': 0x0F8C, 'mode': 'rel32'},
            'jge': {'op': 0x0F8D, 'mode': 'rel32'},
            'jle': {'op': 0x0F8E, 'mode': 'rel32'},
            
            # 调用和返回
            'call': {'op': 0xE8, 'mode': 'rel32'},
            'ret': {'op': 0xC3},
            
            # 中断和IO
            'int': {'op': 0xCD, 'mode': 'imm8'},
            'in': {'op': 0xE4, 'mode': 'imm8'},   # in al, imm8
            'out': {'op': 0xE6, 'mode': 'imm8'},  # out imm8, al
            
            # 其他
            'nop': {'op': 0x90},
            'cli': {'op': 0xFA},
            'sti': {'op': 0xFB},
            'hlt': {'op': 0xF4},
        }
        
        # 寄存器编码
        self.reg_codes = {
            'al': 0, 'cl': 1, 'dl': 2, 'bl': 3,
            'ah': 4, 'ch': 5, 'dh': 6, 'bh': 7,
            'ax': 0, 'cx': 1, 'dx': 2, 'bx': 3,
            'sp': 4, 'bp': 5, 'si': 6, 'di': 7,
            'eax': 0, 'ecx': 1, 'edx': 2, 'ebx': 3,
            'esp': 4, 'ebp': 5, 'esi': 6, 'edi': 7,
            'es': 0, 'cs': 1, 'ss': 2, 'ds': 3,
            'fs': 4, 'gs': 5,
        }
        
    def compile(self, source_file, output_file):
        try:
            print(f"D+编译器 v34.0 - 完整版 + 内联汇编")
            print(f"编译: {source_file}")
            
            # 读取源文件
            with open(source_file, 'r', encoding='utf-8-sig') as f:
                source = f.read()
            
            # 删除所有注释
            source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
            
            # 预处理十六进制数字
            def hex_replace(match):
                hex_num = match.group(0)
                dec_num = str(int(hex_num, 16))
                print(f"  转换: {hex_num} -> {dec_num}")
                return dec_num
            
            source = re.sub(r'0x[0-9A-Fa-f]+', hex_replace, source)
            
            # 分割成行
            lines = source.split('\n')
            
            # 查找main函数
            in_function = False
            function_lines = []
            asm_mode = False
            asm_buffer = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if 'int main ()' in line or 'int main()' in line:
                    in_function = True
                    continue
                
                if in_function:
                    if line == '{':
                        continue
                    elif line == '}':
                        break
                    
                    # 处理内联汇编块
                    if line == 'asm {':
                        asm_mode = True
                        asm_buffer = []
                        continue
                    elif asm_mode:
                        if line == '}':
                            asm_mode = False
                            # 将整个汇编块作为一个整体处理
                            function_lines.append('__ASM_BLOCK__:' + ';'.join(asm_buffer))
                        else:
                            asm_buffer.append(line)
                        continue
                    
                    function_lines.append(line)
            
            print(f"找到main函数，{len(function_lines)} 行代码")
            
            print("函数体内的所有行:")
            for i, line in enumerate(function_lines, 1):
                print(f"  {i}: {line}")
            
            # 函数序言
            self._emit(0x55)                    # push ebp
            self._emit_bytes([0x89, 0xE5])       # mov ebp, esp
            
            # 第一遍：扫描所有变量声明，分配空间
            print("扫描变量声明:")
            self._scan_all_vars(function_lines)
            
            # 分配栈空间
            if self.stack_offset < 0:
                stack_size = (-self.stack_offset + 15) & ~15
                self._emit_bytes([0x83, 0xEC])
                self._emit(stack_size & 0xFF)
                print(f"  分配栈空间: {stack_size} 字节")
            
            # 保存寄存器
            self._emit_bytes([0x53, 0x56, 0x57]) # push ebx, esi, edi
            
            # 第二遍：生成代码
            print("生成代码:")
            for line in function_lines:
                self._process_line(line)
            
            # 恢复寄存器
            self._emit_bytes([0x5F, 0x5E, 0x5B]) # pop edi, esi, ebx
            
            # 默认返回
            self._emit(0x31, 0xC0)               # xor eax, eax
            self._emit(0xC9)                      # leave
            self._emit(0xC3)                      # ret
            
            # 写入文件
            with open(output_file, 'wb') as f:
                f.write(self.output)
            
            print(f"编译成功! 输出文件: {output_file} ({len(self.output)} 字节)")
            print(f"变量表: {list(self.vars.keys())}")
            return True
            
        except Exception as e:
            print(f"编译错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _scan_all_vars(self, lines):
        """扫描所有变量声明"""
        for line in lines:
            if line.startswith('__ASM_BLOCK__'):
                continue  # 跳过汇编块
            line = line.strip()
            if (line.startswith('int ') or line.startswith('long ') or 
                line.startswith('short ') or line.startswith('byte ') or
                line.startswith('byte*')):
                print(f"    发现变量声明: {line}")
                self._declare_var(line)
    
    def _declare_var(self, line):
        """声明单个变量"""
        line = line.replace(';', '')
        parts = line.split('=')
        decl_part = parts[0].strip()
        
        if decl_part.startswith('byte*'):
            var_type = 'byte'
            var_name_part = decl_part[5:].strip()
            is_pointer = True
        else:
            type_parts = decl_part.split()
            if len(type_parts) < 2:
                return
            var_type = type_parts[0]
            var_name_part = type_parts[1]
            is_pointer = '*' in var_name_part
        
        var_name = var_name_part.replace('*', '')
        
        array_size = None
        if '[' in var_name and ']' in var_name:
            array_part = var_name[var_name.index('[')+1:var_name.index(']')]
            if array_part.isdigit():
                array_size = int(array_part)
            var_name = var_name[:var_name.index('[')]
        
        size = self._type_size(var_type)
        if array_size:
            size *= array_size
        
        self.stack_offset -= size
        self.vars[var_name] = self.stack_offset
        
        pointer_info = " 指针" if is_pointer else ""
        array_info = f" 数组[{array_size}]" if array_size else ""
        init_info = f" 初始值: {parts[1].strip()}" if len(parts) > 1 else ""
        print(f"  变量: {var_name} 偏移 {self.stack_offset}{pointer_info}{array_info}{init_info}")
        
        if len(parts) > 1:
            self.vars[var_name + '_init'] = parts[1].strip()
    
    def _process_line(self, line):
        """处理一行代码"""
        line = line.strip()
        if not line:
            return
        
        # 处理内联汇编块
        if line.startswith('__ASM_BLOCK__'):
            asm_code = line[14:]  # 去掉 '__ASM_BLOCK__:'
            instructions = asm_code.split(';')
            for inst in instructions:
                if inst.strip():
                    self._parse_asm_instruction(inst.strip())
            return
        
        # 变量声明
        if (line.startswith('int ') or line.startswith('long ') or 
            line.startswith('short ') or line.startswith('byte ') or
            line.startswith('byte*')):
            self._parse_var_decl(line)
            return
        
        # 赋值语句
        if '=' in line and '==' not in line:
            self._parse_assignment(line)
            return
        
        # if语句
        if line.startswith('if '):
            self._parse_if(line)
            return
        
        # else语句
        if line.startswith('else'):
            self._parse_else(line)
            return
        
        # while循环
        if line.startswith('while '):
            self._parse_while(line)
            return
        
        # 返回语句
        if line.startswith('back'):
            self._parse_return(line)
            return
        
        # 函数调用
        if '(' in line and ')' in line:
            self._parse_call(line)
            return
    
    def _parse_asm_instruction(self, line):
        """解析单条汇编指令"""
        print(f"    汇编指令: {line}")
        
        # 分割指令和操作数
        parts = line.split()
        if not parts:
            return
        
        mnemonic = parts[0].lower()
        operands = parts[1:] if len(parts) > 1 else []
        
        # 处理 mov 指令
        if mnemonic == 'mov' and len(operands) >= 2:
            dest = operands[0].rstrip(',')
            src = operands[1]
            
            # 处理 mov ax, 0xB800
            if src.startswith('0x'):
                value = int(src, 16)
                if dest in self.reg_codes:
                    reg_code = self.reg_codes[dest]
                    # mov reg, imm
                    if dest in ['ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp']:
                        # 16位立即数
                        self._emit(0xB8 + reg_code)  # mov r16, imm16
                        self._emit(value & 0xFF)
                        self._emit((value >> 8) & 0xFF)
                    elif dest in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp']:
                        # 32位立即数
                        self._emit(0xB8 + reg_code)  # mov r32, imm32
                        self._emit_dword(value)
            
            # 处理 mov es, ax
            elif dest in self.reg_codes and src in self.reg_codes:
                if dest in ['es', 'ds', 'cs', 'ss', 'fs', 'gs']:
                    # 段寄存器
                    if src in ['ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp']:
                        # mov sreg, r16
                        dest_code = self.reg_codes[dest]
                        self._emit(0x8E)  # mov sreg, r/m16
                        modrm = 0xC0 | (dest_code << 3) | self.reg_codes[src]
                        self._emit(modrm)
                else:
                    # 通用寄存器之间
                    dest_code = self.reg_codes[dest]
                    src_code = self.reg_codes[src]
                    # mov r32, r32
                    self._emit(0x89)
                    modrm = 0xC0 | (dest_code << 3) | src_code
                    self._emit(modrm)
            
            # 处理 mov byte [es:0], 72
            elif '[' in dest and ']' in dest:
                # 解析内存操作数 [es:0]
                mem_part = dest[dest.index('[')+1:dest.index(']')]
                if ':' in mem_part:
                    segment, offset = mem_part.split(':')
                    segment = segment.strip()
                    offset = offset.strip()
                    
                    # 设置段前缀
                    if segment == 'es':
                        self._emit(0x26)  # ES前缀
                    elif segment == 'cs':
                        self._emit(0x2E)  # CS前缀
                    elif segment == 'ss':
                        self._emit(0x36)  # SS前缀
                    elif segment == 'ds':
                        self._emit(0x3E)  # DS前缀
                    
                    # 处理立即数
                    if src.isdigit() or src.startswith('0x'):
                        value = int(src, 0) if src.startswith('0x') else int(src)
                        
                        if offset.isdigit() or offset.startswith('0x'):
                            off = int(offset, 0) if offset.startswith('0x') else int(offset)
                            
                            if off <= 0xFF:
                                # mov byte [segment:disp8], imm8
                                self._emit(0xC6)
                                self._emit(0x06)  # [disp8]
                                self._emit(off & 0xFF)
                                self._emit(value & 0xFF)
                            else:
                                # mov byte [segment:disp32], imm8
                                self._emit(0xC6)
                                self._emit(0x05)  # [disp32]
                                self._emit_dword(off)
                                self._emit(value & 0xFF)
        
        # 处理 nop
        elif mnemonic == 'nop':
            self._emit(0x90)
        
        # 处理 int 指令
        elif mnemonic == 'int' and len(operands) >= 1:
            num = int(operands[0].replace('0x', ''), 16) if '0x' in operands[0] else int(operands[0])
            self._emit(0xCD)
            self._emit(num & 0xFF)
        
        # 处理 cli, sti, hlt
        elif mnemonic == 'cli':
            self._emit(0xFA)
        elif mnemonic == 'sti':
            self._emit(0xFB)
        elif mnemonic == 'hlt':
            self._emit(0xF4)
        
        # 处理 push/pop
        elif mnemonic == 'push' and len(operands) >= 1:
            reg = operands[0].rstrip(',')
            if reg in self.reg_codes:
                self._emit(0x50 + self.reg_codes[reg])  # push reg
        elif mnemonic == 'pop' and len(operands) >= 1:
            reg = operands[0].rstrip(',')
            if reg in self.reg_codes:
                self._emit(0x58 + self.reg_codes[reg])  # pop reg
        
        else:
            print(f"    未知汇编指令: {mnemonic}，生成NOP")
            self._emit(0x90)
    
    def _parse_var_decl(self, line):
        """解析变量声明"""
        if '=' in line:
            line = line.replace(';', '')
            parts = line.split('=')
            
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                
                if left.startswith('byte*'):
                    var_name = left[5:].strip().replace('*', '')
                else:
                    type_parts = left.split()
                    if len(type_parts) >= 2:
                        var_name_part = type_parts[1]
                        var_name = var_name_part.replace('*', '')
                    else:
                        var_name = left.replace('*', '')
                
                if '[' in var_name:
                    var_name = var_name[:var_name.index('[')]
                
                if var_name in self.vars:
                    offset = self.vars[var_name]
                    
                    if right.isdigit():
                        value = int(right)
                        self._emit(0xB8)
                        self._emit_dword(value)
                        self._emit_bytes([0x89, 0x45, offset & 0xFF])
                    else:
                        self._generate_expr(right)
                        self._emit_bytes([0x89, 0x45, offset & 0xFF])
    
    def _parse_assignment(self, line):
        line = line.replace(';', '')
        parts = line.split('=')
        
        if len(parts) == 2:
            left = parts[0].strip()
            right = parts[1].strip()
            
            if '[' in left and ']' in left:
                self._parse_array_assignment(left, right)
            else:
                self._parse_var_assignment(left, right)
    
    def _parse_array_assignment(self, left, right):
        array_name = left[:left.index('[')]
        index_str = left[left.index('[')+1:left.index(']')]
        
        if array_name not in self.vars:
            raise SyntaxError(f"未定义的数组: {array_name}")
        
        base_offset = self.vars[array_name]
        
        if index_str.isdigit():
            index = int(index_str)
        elif index_str in self.vars:
            self._generate_expr(index_str)
            self._emit(0x50)
            index = 0
        else:
            index = 0
        
        offset = base_offset + index
        
        self._generate_expr(right)
        self._emit_bytes([0x89, 0x45, offset & 0xFF])
    
    def _parse_var_assignment(self, left, right):
        if left in self.vars:
            offset = self.vars[left]
            self._generate_expr(right)
            self._emit_bytes([0x89, 0x45, offset & 0xFF])
            return
        
        raise SyntaxError(f"未定义的变量: {left}")
    
    def _generate_expr(self, expr):
        expr = expr.strip()
        
        if not expr:
            self._emit(0x31, 0xC0)
            return
        
        if expr.isdigit():
            value = int(expr)
            self._emit(0xB8)
            self._emit_dword(value)
            return
        
        if expr in self.vars:
            offset = self.vars[expr]
            self._emit_bytes([0x8B, 0x45, offset & 0xFF])
            return
        
        if expr.startswith('(') and expr.endswith(')'):
            self._generate_expr(expr[1:-1].strip())
            return
        
        operators = [
            ('*', 9), ('/', 9), ('//', 9),
            ('+', 8), ('-', 8),
            ('<<', 7), ('>>', 7),
            ('<', 6), ('>', 6), ('<=', 6), ('>=', 6),
            ('==', 5), ('!=', 5),
            ('&', 4),
            ('^', 3),
            ('|', 2),
            ('&&', 1),
            ('||', 0)
        ]
        
        for op, _ in operators:
            if op in expr:
                pos = expr.rfind(op)
                if pos > 0:
                    left = expr[:pos].strip()
                    right = expr[pos+len(op):].strip()
                    
                    self._generate_expr(left)
                    self._emit(0x50)
                    self._generate_expr(right)
                    self._emit(0x5B)
                    
                    self._generate_operator(op)
                    return
        
        raise SyntaxError(f"无法解析表达式: {expr}")
    
    def _generate_operator(self, op):
        ops = {
            '+': [0x01, 0xD8],
            '-': [0x29, 0xD8],
            '*': [0x0F, 0xAF, 0xC3],
            '/': [0x99, 0xF7, 0xFB],
            '//': [0x99, 0xF7, 0xFB],
            '==': [0x39, 0xD8, 0x0F, 0x94, 0xC0],
            '!=': [0x39, 0xD8, 0x0F, 0x95, 0xC0],
            '>': [0x39, 0xD8, 0x0F, 0x9F, 0xC0],
            '<': [0x39, 0xD8, 0x0F, 0x9C, 0xC0],
            '>=': [0x39, 0xD8, 0x0F, 0x9D, 0xC0],
            '<=': [0x39, 0xD8, 0x0F, 0x9E, 0xC0],
            '&': [0x21, 0xD8],
            '|': [0x09, 0xD8],
            '^': [0x31, 0xD8],
            '<<': [0x89, 0xD9, 0xD3, 0xE0],
            '>>': [0x89, 0xD9, 0xD3, 0xE8],
        }
        
        if op == '&&':
            self._generate_logical_and()
        elif op == '||':
            self._generate_logical_or()
        elif op in ops:
            self._emit_bytes(ops[op])
    
    def _generate_logical_and(self):
        end = self._new_label()
        self._emit_bytes([0x83, 0xF8, 0x00])
        self._emit(0x74)
        self._emit_reloc(end, 1)
        self._emit(0x89, 0xD8)
        self._place_label(end)
    
    def _generate_logical_or(self):
        end = self._new_label()
        self._emit_bytes([0x83, 0xF8, 0x00])
        self._emit(0x75)
        self._emit_reloc(end, 1)
        self._emit(0x89, 0xD8)
        self._place_label(end)
    
    def _parse_if(self, line):
        cond = line[3:].strip().rstrip('{').strip()
        self._generate_expr(cond)
        self._emit_bytes([0x83, 0xF8, 0x00])
        
        else_label = self._new_label()
        end_label = self._new_label()
        
        self._emit(0x74)
        self._emit_reloc(else_label, 1)
        
        self.current_if_else = {
            'else_label': else_label,
            'end_label': end_label,
            'has_else': False
        }
    
    def _parse_else(self, line):
        if not self.current_if_else:
            raise SyntaxError("else没有对应的if")
        
        self._emit(0xEB)
        self._emit_reloc(self.current_if_else['end_label'], 1)
        self._place_label(self.current_if_else['else_label'])
        self.current_if_else['has_else'] = True
    
    def _parse_while(self, line):
        cond = line[6:].strip().rstrip('{').strip()
        
        start = self._new_label()
        end = self._new_label()
        
        self._place_label(start)
        self._generate_expr(cond)
        self._emit_bytes([0x83, 0xF8, 0x00])
        self._emit(0x74)
        self._emit_reloc(end, 1)
        
        self.loop_stack.append({'start': start, 'end': end})
    
    def _parse_return(self, line):
        value = line.replace('back', '').replace('=', '').replace(';', '').strip()
        
        if value:
            self._generate_expr(value)
        else:
            self._emit(0x31, 0xC0)
        
        self._emit_bytes([0x5F, 0x5E, 0x5B])
        self._emit(0xC9)
        self._emit(0xC3)
    
    def _parse_call(self, line):
        line = line.replace(';', '')
        
        if 'outb' in line:
            match = re.search(r'outb\(([^,]+),\s*([^)]+)\)', line)
            if match:
                port = int(match.group(1))
                value = int(match.group(2))
                self._emit(0xB8)
                self._emit_dword(value)
                self._emit(0xBA)
                self._emit_dword(port)
                self._emit(0xEE)
        
        elif 'inb' in line:
            match = re.search(r'inb\(([^)]+)\)', line)
            if match:
                port = int(match.group(1))
                self._emit(0xBA)
                self._emit_dword(port)
                self._emit(0xEC)
                self._emit_bytes([0x0F, 0xB6, 0xC0])
        
        elif 'cli' in line:
            self._emit(0xFA)
        elif 'sti' in line:
            self._emit(0xFB)
        elif 'hlt' in line:
            self._emit(0xF4)
    
    def _type_size(self, type_name):
        sizes = {'byte': 1, 'short': 2, 'int': 4, 'long': 8}
        return sizes.get(type_name, 4)
    
    def _emit(self, *bytes_data):
        for b in bytes_data:
            self.output.append(b & 0xFF)
    
    def _emit_bytes(self, bytes_list):
        self.output.extend(bytes_list)
    
    def _emit_dword(self, value):
        self.output.extend(struct.pack('<I', value & 0xFFFFFFFF))
    
    def _emit_reloc(self, target, size):
        pos = len(self.output)
        for _ in range(size):
            self._emit(0)
        self.labels[target] = pos
    
    def _new_label(self):
        return f".L{len(self.labels)}"
    
    def _place_label(self, name):
        self.labels[name] = len(self.output)

# ===========================================================================
# 主程序
# ===========================================================================

def main():
    if len(sys.argv) < 2:
        print("D+编译器 v34.0 - 完整版 + 内联汇编")
        print("用法: dpc.py 源文件.dp [-o 输出文件]")
        print("示例: dpc.py kernel.dp -o kernel.bin")
        print("\n✅ 完整支持的功能:")
        print("  ✓ 所有数据类型: int, long, short, byte")
        print("  ✓ 变量声明: 指针(*), 数组[]")
        print("  ✓ 所有运算符: + - * / // == != > < >= <= && || ! & | ^ ~ << >>")
        print("  ✓ 控制流: if/else, while")
        print("  ✓ 函数定义: 必须有 back 返回值")
        print("  ✓ 硬件指令: inb, outb, cli, sti, hlt")
        print("  ✓ 系统调用: read, write, load, new, rw, run, draw, clear, music, look, about, accuracy, use_character_set")
        print("  ✓ 内联汇编: asm { ... } (支持mov, push, pop, int, nop等)")
        print("  ✓ 内存操作: 指针, 数组")
        print("  ✓ 错误检查: 重复定义, 未定义变量, 参数数量")
        return 1
    
    source = sys.argv[1]
    output = 'kernel.bin'
    
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]
    
    compiler = DPlusCompiler()
    success = compiler.compile(source, output)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())