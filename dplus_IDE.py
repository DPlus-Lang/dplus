#!/usr/bin/env python3
"""
D+ IDE - 专门为D+语言设计的轻量级集成开发环境
版本: 1.1
功能: 语法高亮、文件管理、代码编辑
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import os
import re
from datetime import datetime

class DPlusIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("D+ IDE - 面壁者编程环境 v1.1")
        self.root.geometry("1000x700")
        
        # 设置图标（如果有的话）
        # self.root.iconbitmap("dplus.ico")
        
        # 当前文件路径
        self.current_file = None
        self.file_modified = False
        
        # 配色方案 - 暗色主题（护眼）
        self.colors = {
            'bg': '#1e1e1e',           # 背景色
            'fg': '#d4d4d4',            # 前景色
            'linenumber': '#858585',     # 行号颜色
            'keyword': '#569cd6',        # 关键字
            'type': '#4ec9b0',           # 类型
            'number': '#b5cea8',         # 数字
            'comment': '#6a9955',        # 注释
            'string': '#ce9178',         # 字符串
            'function': '#dcdcaa',       # 函数
            'operator': '#d4d4d4',       # 运算符
        }
        
        # D+ 关键字
        self.keywords = [
            'int', 'long', 'short', 'byte',
            'if', 'else', 'while',
            'back', 'asm',
            'inb', 'outb', 'cli', 'sti', 'hlt',
            'read', 'write', 'load', 'new', 'rw',
            'run', 'draw', 'clear', 'music', 'look',
            'about', 'accuracy', 'use_character_set'
        ]
        
        # 类型关键字
        self.types = ['int', 'long', 'short', 'byte']
        
        # 内置函数
        self.builtins = [
            'inb', 'outb', 'cli', 'sti', 'hlt',
            'read', 'write', 'load', 'new', 'rw',
            'run', 'draw', 'clear', 'music', 'look',
            'about', 'accuracy', 'use_character_set'
        ]
        
        # 设置UI
        self.setup_ui()
        
        # 绑定事件
        self.setup_bindings()
        
        # 状态栏更新
        self.update_status()
        
    def setup_ui(self):
        """设置UI界面"""
        
        # 创建菜单栏
        self.create_menubar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧文件浏览器框架
        self.create_file_browser(main_frame)
        
        # 右侧编辑区框架
        self.create_editor(main_frame)
        
        # 底部状态栏
        self.create_statusbar()
        
    def create_menubar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建 (Ctrl+N)", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开 (Ctrl+O)", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存 (Ctrl+S)", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为 (Ctrl+Shift+S)", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", command=lambda: self.editor.edit_undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=lambda: self.editor.edit_redo(), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", command=lambda: self.root.focus_get().event_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label="复制", command=lambda: self.root.focus_get().event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="粘贴", command=lambda: self.root.focus_get().event_generate("<<Paste>>"), accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找 (Ctrl+F)", command=self.show_find_dialog, accelerator="Ctrl+F")
        edit_menu.add_command(label="替换 (Ctrl+H)", command=self.show_replace_dialog, accelerator="Ctrl+H")
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="放大字体 (Ctrl++)", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="缩小字体 (Ctrl+-)", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="重置字体 (Ctrl+0)", command=self.reset_font, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="显示行号", variable=tk.BooleanVar(value=True), command=self.toggle_line_numbers)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="D+语法手册", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # 新建按钮
        new_btn = ttk.Button(toolbar, text="新建", command=self.new_file, width=8)
        new_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 打开按钮
        open_btn = ttk.Button(toolbar, text="打开", command=self.open_file, width=8)
        open_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 保存按钮
        save_btn = ttk.Button(toolbar, text="保存", command=self.save_file, width=8)
        save_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 分隔线
        separator = ttk.Separator(toolbar, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, padx=5, pady=2, fill=tk.Y)
        
        # 语法手册按钮
        help_btn = ttk.Button(toolbar, text="语法手册", command=self.show_help, width=8)
        help_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 快速示例按钮
        example_btn = ttk.Button(toolbar, text="示例", command=self.insert_example, width=8)
        example_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 字体大小调节
        ttk.Label(toolbar, text="字体:").pack(side=tk.LEFT, padx=(20, 5))
        self.font_size_var = tk.StringVar(value="12")
        font_size_spin = ttk.Spinbox(toolbar, from_=8, to=30, width=5, textvariable=self.font_size_var, command=self.change_font_size)
        font_size_spin.pack(side=tk.LEFT)
        
    def create_file_browser(self, parent):
        """创建文件浏览器"""
        browser_frame = ttk.Frame(parent, width=200)
        browser_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        browser_frame.pack_propagate(False)
        
        # 标题
        title_frame = ttk.Frame(browser_frame)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="📁 项目文件", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT)
        
        # 刷新按钮
        refresh_btn = ttk.Button(title_frame, text="🔄", width=3, command=self.refresh_file_browser)
        refresh_btn.pack(side=tk.RIGHT)
        
        # 文件列表
        list_frame = ttk.Frame(browser_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, bg=self.colors['bg'], fg=self.colors['fg'],
                                        selectbackground='#264f78', selectforeground='white')
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.file_listbox.yview)
        
        # 绑定双击事件
        self.file_listbox.bind('<Double-Button-1>', self.open_selected_file)
        
        # 初始刷新
        self.refresh_file_browser()
        
    def create_editor(self, parent):
        """创建编辑器"""
        editor_frame = ttk.Frame(parent)
        editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 编辑器头部（显示当前文件）
        self.header_frame = ttk.Frame(editor_frame)
        self.header_frame.pack(fill=tk.X)
        
        self.file_label = ttk.Label(self.header_frame, text="无标题", font=('微软雅黑', 10, 'bold'))
        self.file_label.pack(side=tk.LEFT)
        
        self.modified_label = ttk.Label(self.header_frame, text="", font=('微软雅黑', 10))
        self.modified_label.pack(side=tk.LEFT, padx=5)
        
        # 创建行号和编辑区
        text_frame = ttk.Frame(editor_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 行号区域
        self.line_numbers = tk.Text(text_frame, width=5, padx=5, takefocus=0, border=0,
                                     background=self.colors['bg'], foreground=self.colors['linenumber'],
                                     state='disabled', font=('Consolas', 12), wrap='none')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 主编辑区
        self.editor = DPlusText(text_frame, self.colors, self.keywords, self.types, self.builtins,
                                 bg=self.colors['bg'], fg=self.colors['fg'],
                                 insertbackground='white', font=('Consolas', 12),
                                 wrap='none', undo=True)
        self.editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        y_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.sync_scroll)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.editor.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.editor.config(yscrollcommand=self.on_text_scroll, xscrollcommand=x_scrollbar.set)
        
    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 光标位置
        self.pos_label = ttk.Label(self.statusbar, text="行: 1, 列: 1", relief=tk.SUNKEN, anchor=tk.W)
        self.pos_label.pack(side=tk.LEFT, padx=5)
        
        # 文件状态
        self.status_label = ttk.Label(self.statusbar, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 编码
        encoding_label = ttk.Label(self.statusbar, text="UTF-8", relief=tk.SUNKEN, anchor=tk.CENTER, width=8)
        encoding_label.pack(side=tk.RIGHT, padx=5)
        
        # 语言
        lang_label = ttk.Label(self.statusbar, text="D+", relief=tk.SUNKEN, anchor=tk.CENTER, width=8)
        lang_label.pack(side=tk.RIGHT, padx=5)
        
    def setup_bindings(self):
        """设置事件绑定"""
        # 编辑器修改事件
        self.editor.bind('<<Modified>>', self.on_editor_modified)
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<Button-1>', self.update_cursor_position)
        
        # 快捷键
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_as_file())
        self.root.bind('<Control-f>', lambda e: self.show_find_dialog())
        self.root.bind('<Control-h>', lambda e: self.show_replace_dialog())
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.reset_font())
        
    def sync_scroll(self, *args):
        """同步滚动条和行号"""
        self.editor.yview(*args)
        self.line_numbers.yview(*args)
        
    def on_text_scroll(self, *args):
        """文本滚动时的处理"""
        self.editor.yview(*args)
        self.line_numbers.yview(*args)
        
    def update_line_numbers(self):
        """更新行号显示"""
        if not hasattr(self, 'line_numbers'):
            return
            
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        # 获取总行数
        try:
            line_count = int(self.editor.index('end-1c').split('.')[0])
            for i in range(1, line_count + 1):
                self.line_numbers.insert(tk.END, f"{i:4d}\n")
        except:
            pass
            
        self.line_numbers.config(state='disabled')
        
    def on_editor_modified(self, event):
        """编辑器内容修改事件"""
        self.update_line_numbers()
        self.file_modified = True
        self.modified_label.config(text="● 已修改")
        self.editor.edit_modified(False)
        
    def on_key_release(self, event):
        """按键释放事件"""
        self.update_cursor_position()
        
    def update_cursor_position(self, event=None):
        """更新光标位置显示"""
        try:
            cursor = self.editor.index(tk.INSERT)
            line, col = cursor.split('.')
            self.pos_label.config(text=f"行: {line}, 列: {col}")
        except:
            pass
        
    def new_file(self):
        """新建文件"""
        if self.file_modified:
            if not self.ask_save_changes():
                return
                
        self.editor.delete(1.0, tk.END)
        self.current_file = None
        self.file_modified = False
        self.file_label.config(text="无标题")
        self.modified_label.config(text="")
        self.status_label.config(text="新建文件")
        self.update_line_numbers()
        
    def open_file(self):
        """打开文件"""
        if self.file_modified:
            if not self.ask_save_changes():
                return
                
        filename = filedialog.askopenfilename(
            title="打开D+文件",
            filetypes=[("D+文件", "*.dp"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.editor.delete(1.0, tk.END)
                self.editor.insert(1.0, content)
                self.current_file = filename
                self.file_modified = False
                self.file_label.config(text=os.path.basename(filename))
                self.modified_label.config(text="")
                self.status_label.config(text=f"已打开: {filename}")
                self.update_line_numbers()
                self.refresh_file_browser()
                
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {e}")
                
    def save_file(self):
        """保存文件"""
        if self.current_file:
            try:
                content = self.editor.get(1.0, tk.END)
                # 去掉末尾可能多余的换行
                if content.endswith('\n'):
                    content = content[:-1]
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.file_modified = False
                self.modified_label.config(text="")
                self.status_label.config(text=f"已保存: {self.current_file}")
                
            except Exception as e:
                messagebox.showerror("错误", f"无法保存文件: {e}")
        else:
            self.save_as_file()
            
    def save_as_file(self):
        """另存为"""
        filename = filedialog.asksaveasfilename(
            title="保存D+文件",
            defaultextension=".dp",
            filetypes=[("D+文件", "*.dp"), ("所有文件", "*.*")]
        )
        
        if filename:
            self.current_file = filename
            self.save_file()
            self.file_label.config(text=os.path.basename(filename))
            self.refresh_file_browser()
            
    def ask_save_changes(self):
        """询问是否保存更改"""
        result = messagebox.askyesnocancel(
            "保存更改",
            f"文件 {self.file_label.cget('text')} 已修改，是否保存？"
        )
        
        if result is True:
            self.save_file()
            return True
        elif result is False:
            return True
        else:
            return False
            
    def refresh_file_browser(self):
        """刷新文件浏览器"""
        self.file_listbox.delete(0, tk.END)
        
        # 获取当前目录
        if self.current_file:
            current_dir = os.path.dirname(self.current_file)
        else:
            current_dir = os.getcwd()
        
        if os.path.exists(current_dir):
            try:
                for file in sorted(os.listdir(current_dir)):
                    if file.endswith('.dp'):
                        self.file_listbox.insert(tk.END, file)
            except:
                pass
                    
    def open_selected_file(self, event):
        """打开选中的文件"""
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            if self.current_file:
                filepath = os.path.join(os.path.dirname(self.current_file), filename)
            else:
                filepath = os.path.join(os.getcwd(), filename)
                
            if os.path.exists(filepath):
                self.open_file_by_path(filepath)
                
    def open_file_by_path(self, filepath):
        """通过路径打开文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.editor.delete(1.0, tk.END)
            self.editor.insert(1.0, content)
            self.current_file = filepath
            self.file_modified = False
            self.file_label.config(text=os.path.basename(filepath))
            self.modified_label.config(text="")
            self.status_label.config(text=f"已打开: {filepath}")
            self.update_line_numbers()
            
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {e}")
            
    def insert_example(self):
        """插入示例代码"""
        example = """/* D+ 内核示例 - MossMiNi-PDC */
int main ()
{
    /* 设置显存地址 */
    byte* video = 0xb8000;
    int i = 0;
    
    /* 清屏 */
    while i < 80 * 25 * 2 {
        video[i] = 0;
        i = i + 1;
    }
    
    /* 显示 "MMN-PDC" */
    video[0] = 77;    /* M */
    video[2] = 77;    /* M */
    video[4] = 78;    /* N */
    video[6] = 45;    /* - */
    video[8] = 80;    /* P */
    video[10] = 68;   /* D */
    video[12] = 67;   /* C */
    
    /* 设置颜色为绿色 */
    i = 1;
    while i < 26 {
        video[i] = 0x0A;
        i = i + 2;
    }
    
    /* 硬件测试 */
    outb(0x3F8, 65);  /* 串口输出 'A' */
    byte status = inb(0x1F7);  /* 读硬盘状态 */
    
    /* 无限循环 */
    while 1 {
        asm {
            hlt;  /* 省电 */
        }
    }
    
    back = 0;
}
"""
        self.editor.insert(tk.INSERT, example)
        self.update_line_numbers()
        
    def show_find_dialog(self):
        """显示查找对话框"""
        FindDialog(self.root, self.editor)
        
    def show_replace_dialog(self):
        """显示替换对话框"""
        ReplaceDialog(self.root, self.editor)
        
    def zoom_in(self):
        """放大字体"""
        try:
            current_font = font.nametofont(self.editor.cget('font'))
            size = current_font.cget('size')
            if size < 30:
                current_font.configure(size=size + 1)
                self.font_size_var.set(str(size + 1))
                # 更新行号字体
                line_font = font.nametofont(self.line_numbers.cget('font'))
                line_font.configure(size=size + 1)
        except:
            pass
            
    def zoom_out(self):
        """缩小字体"""
        try:
            current_font = font.nametofont(self.editor.cget('font'))
            size = current_font.cget('size')
            if size > 8:
                current_font.configure(size=size - 1)
                self.font_size_var.set(str(size - 1))
                # 更新行号字体
                line_font = font.nametofont(self.line_numbers.cget('font'))
                line_font.configure(size=size - 1)
        except:
            pass
            
    def reset_font(self):
        """重置字体"""
        try:
            current_font = font.nametofont(self.editor.cget('font'))
            current_font.configure(size=12)
            line_font = font.nametofont(self.line_numbers.cget('font'))
            line_font.configure(size=12)
            self.font_size_var.set("12")
        except:
            pass
            
    def change_font_size(self):
        """改变字体大小"""
        try:
            size = int(self.font_size_var.get())
            current_font = font.nametofont(self.editor.cget('font'))
            current_font.configure(size=size)
            line_font = font.nametofont(self.line_numbers.cget('font'))
            line_font.configure(size=size)
        except:
            pass
            
    def toggle_line_numbers(self):
        """切换行号显示"""
        # 简单处理，可扩展
        pass
        
    def show_help(self):
        """显示帮助"""
        help_text = """D+ 语言快速参考

数据类型:
  int    - 32位整数
  long   - 64位整数
  short  - 16位整数
  byte   - 8位整数

运算符:
  算术: + - * / //
  比较: == != > < >= <=
  逻辑: && || !
  位运算: & | ^ ~ << >>

控制流:
  if 条件 { ... } else { ... }
  while 条件 { ... }

硬件指令:
  inb(端口)    - 读端口
  outb(端口, 值) - 写端口
  cli()        - 关中断
  sti()        - 开中断
  hlt()        - 停机

系统调用:
  read(), write(), load(), new(), rw()
  run(), draw(), clear(), music()
  look(), about(), accuracy(), use_character_set()

内联汇编:
  asm {
    mov ax, 0xB800
    mov es, ax
  }

示例: 点击工具栏的"示例"按钮
"""
        messagebox.showinfo("D+语法手册", help_text)
        
    def show_about(self):
        """显示关于"""
        about_text = """D+ IDE v1.1
专门为 D+ 语言设计的轻量级IDE

D+ 语言特点:
  • 专门为内核开发设计
  • 语法简洁，直接生成机器码
  • 完全控制硬件
  • 致敬刘慈欣科幻宇宙

作者: 一个六年级的"面壁者"
        
“给岁月以文明，而不是给文明以岁月。”
"""
        messagebox.showinfo("关于 D+ IDE", about_text)
        
    def update_status(self):
        """更新状态"""
        try:
            # 每1秒更新一次状态
            self.root.after(1000, self.update_status)
        except:
            pass


class DPlusText(tk.Text):
    """支持语法高亮的D+编辑器"""
    
    def __init__(self, parent, colors, keywords, types, builtins, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.colors = colors
        self.keywords = keywords
        self.types = types
        self.builtins = builtins
        
        # 配置标签样式
        self.tag_config('keyword', foreground=colors['keyword'])
        self.tag_config('type', foreground=colors['type'])
        self.tag_config('number', foreground=colors['number'])
        self.tag_config('comment', foreground=colors['comment'])
        self.tag_config('string', foreground=colors['string'])
        self.tag_config('function', foreground=colors['function'])
        self.tag_config('operator', foreground=colors['operator'])
        
        # 绑定按键事件进行语法高亮
        self.bind('<KeyRelease>', self.on_key_release)
        self.bind('<Button-1>', self.on_click)
        
    def on_key_release(self, event):
        """按键释放时更新语法高亮"""
        self.after_idle(self.highlight_syntax)
        
    def on_click(self, event):
        """点击时更新语法高亮"""
        self.after_idle(self.highlight_syntax)
        
    def highlight_syntax(self):
        """语法高亮"""
        try:
            # 移除所有标签
            for tag in ['keyword', 'type', 'number', 'comment', 'string', 'function', 'operator']:
                self.tag_remove(tag, '1.0', tk.END)
                
            content = self.get('1.0', tk.END)
            
            # 高亮注释
            self.highlight_comments()
            
            # 高亮数字
            self.highlight_numbers()
            
            # 高亮关键字
            self.highlight_keywords()
            
            # 高亮类型
            self.highlight_types()
            
            # 高亮内置函数
            self.highlight_builtins()
            
            # 高亮运算符
            self.highlight_operators()
        except:
            pass
        
    def highlight_comments(self):
        """高亮注释"""
        try:
            start = '1.0'
            while True:
                pos = self.search('/*', start, tk.END)
                if not pos:
                    break
                end = self.search('*/', pos, tk.END)
                if end:
                    self.tag_add('comment', pos, f"{end}+2c")
                    start = f"{end}+2c"
                else:
                    self.tag_add('comment', pos, tk.END)
                    break
        except:
            pass
        
    def highlight_numbers(self):
        """高亮数字"""
        try:
            content = self.get('1.0', tk.END)
            lines = content.split('\n')
            
            line_num = 1
            for line in lines:
                # 匹配十进制数字
                for match in re.finditer(r'\b\d+\b', line):
                    start = f"{line_num}.{match.start()}"
                    end = f"{line_num}.{match.end()}"
                    # 检查是否在注释中
                    if not self.tag_ranges('comment') or not any(self._is_in_comment(start)):
                        self.tag_add('number', start, end)
                line_num += 1
        except:
            pass
            
    def _is_in_comment(self, pos):
        """检查位置是否在注释中"""
        try:
            ranges = self.tag_ranges('comment')
            if not ranges:
                return False
            for i in range(0, len(ranges), 2):
                if self.compare(ranges[i], '<=', pos) and self.compare(pos, '<=', ranges[i+1]):
                    return True
            return False
        except:
            return False
        
    def highlight_keywords(self):
        """高亮关键字"""
        try:
            for keyword in self.keywords:
                start = '1.0'
                while True:
                    pos = self.search(rf'\m{keyword}\M', start, tk.END, regexp=True)
                    if not pos:
                        break
                    end = f"{pos}+{len(keyword)}c"
                    if not self._is_in_comment(pos):
                        self.tag_add('keyword', pos, end)
                    start = end
        except:
            pass
                
    def highlight_types(self):
        """高亮类型"""
        try:
            for type_name in self.types:
                start = '1.0'
                while True:
                    pos = self.search(rf'\m{type_name}\M', start, tk.END, regexp=True)
                    if not pos:
                        break
                    end = f"{pos}+{len(type_name)}c"
                    if not self._is_in_comment(pos):
                        self.tag_add('type', pos, end)
                    start = end
        except:
            pass
                
    def highlight_builtins(self):
        """高亮内置函数"""
        try:
            for builtin in self.builtins:
                start = '1.0'
                while True:
                    pos = self.search(rf'\m{builtin}\M', start, tk.END, regexp=True)
                    if not pos:
                        break
                    end = f"{pos}+{len(builtin)}c"
                    if not self._is_in_comment(pos):
                        self.tag_add('function', pos, end)
                    start = end
        except:
            pass
                
    def highlight_operators(self):
        """高亮运算符"""
        try:
            operators = ['+', '-', '*', '/', '//', '=', '==', '!=', '>', '<', '>=', '<=',
                         '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', ';', ',', '(', ')',
                         '{', '}', '[', ']', ':']
            
            for op in operators:
                start = '1.0'
                while True:
                    pos = self.search(re.escape(op), start, tk.END)
                    if not pos:
                        break
                    end = f"{pos}+{len(op)}c"
                    if not self._is_in_comment(pos):
                        self.tag_add('operator', pos, end)
                    start = end
        except:
            pass


class FindDialog:
    """查找对话框"""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text = text_widget
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("查找")
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 查找内容
        ttk.Label(self.dialog, text="查找内容:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.find_entry = ttk.Entry(self.dialog, width=40)
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)
        self.find_entry.focus()
        
        # 选项
        self.case_var = tk.BooleanVar()
        ttk.Checkbutton(self.dialog, text="区分大小写", variable=self.case_var).grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky=tk.W)
        
        self.word_var = tk.BooleanVar()
        ttk.Checkbutton(self.dialog, text="全词匹配", variable=self.word_var).grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="查找下一个", command=self.find_next, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查找上一个", command=self.find_prev, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)
        
        # 绑定回车键
        self.find_entry.bind('<Return>', lambda e: self.find_next())
        
    def find_next(self):
        """查找下一个"""
        search_term = self.find_entry.get()
        if not search_term:
            return
            
        try:
            # 获取当前光标位置
            current_pos = self.text.index(tk.INSERT)
            
            # 搜索
            pos = self.text.search(search_term, current_pos, tk.END, nocase=not self.case_var.get(),
                                   regexp=False, exact=True)
            
            if pos:
                # 选中找到的文本
                end_pos = f"{pos}+{len(search_term)}c"
                self.text.tag_remove(tk.SEL, '1.0', tk.END)
                self.text.tag_add(tk.SEL, pos, end_pos)
                self.text.mark_set(tk.INSERT, end_pos)
                self.text.see(pos)
            else:
                # 从头开始搜索
                pos = self.text.search(search_term, '1.0', tk.END, nocase=not self.case_var.get(),
                                       regexp=False, exact=True)
                if pos:
                    end_pos = f"{pos}+{len(search_term)}c"
                    self.text.tag_remove(tk.SEL, '1.0', tk.END)
                    self.text.tag_add(tk.SEL, pos, end_pos)
                    self.text.mark_set(tk.INSERT, end_pos)
                    self.text.see(pos)
                else:
                    messagebox.showinfo("查找", f"未找到: {search_term}")
        except:
            pass
                
    def find_prev(self):
        """查找上一个"""
        search_term = self.find_entry.get()
        if not search_term:
            return
            
        try:
            # 获取当前光标位置
            current_pos = self.text.index(tk.INSERT)
            
            # 搜索
            pos = self.text.search(search_term, '1.0', current_pos, nocase=not self.case_var.get(),
                                   regexp=False, exact=True, backwards=True)
            
            if pos:
                end_pos = f"{pos}+{len(search_term)}c"
                self.text.tag_remove(tk.SEL, '1.0', tk.END)
                self.text.tag_add(tk.SEL, pos, end_pos)
                self.text.mark_set(tk.INSERT, end_pos)
                self.text.see(pos)
            else:
                messagebox.showinfo("查找", f"未找到: {search_term}")
        except:
            pass


class ReplaceDialog:
    """替换对话框"""
    
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text = text_widget
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("替换")
        self.dialog.geometry("450x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 查找内容
        ttk.Label(self.dialog, text="查找内容:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.find_entry = ttk.Entry(self.dialog, width=40)
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)
        self.find_entry.focus()
        
        # 替换为
        ttk.Label(self.dialog, text="替换为:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.replace_entry = ttk.Entry(self.dialog, width=40)
        self.replace_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 选项
        self.case_var = tk.BooleanVar()
        ttk.Checkbutton(self.dialog, text="区分大小写", variable=self.case_var).grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky=tk.W)
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="查找下一个", command=self.find_next, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="替换", command=self.replace, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全部替换", command=self.replace_all, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy, width=12).pack(side=tk.LEFT, padx=2)
        
    def find_next(self):
        """查找下一个"""
        search_term = self.find_entry.get()
        if not search_term:
            return
            
        try:
            current_pos = self.text.index(tk.INSERT)
            
            pos = self.text.search(search_term, current_pos, tk.END, nocase=not self.case_var.get())
            
            if pos:
                end_pos = f"{pos}+{len(search_term)}c"
                self.text.tag_remove(tk.SEL, '1.0', tk.END)
                self.text.tag_add(tk.SEL, pos, end_pos)
                self.text.mark_set(tk.INSERT, end_pos)
                self.text.see(pos)
            else:
                pos = self.text.search(search_term, '1.0', tk.END, nocase=not self.case_var.get())
                if pos:
                    end_pos = f"{pos}+{len(search_term)}c"
                    self.text.tag_remove(tk.SEL, '1.0', tk.END)
                    self.text.tag_add(tk.SEL, pos, end_pos)
                    self.text.mark_set(tk.INSERT, end_pos)
                    self.text.see(pos)
        except:
            pass
                
    def replace(self):
        """替换当前找到的"""
        if self.text.tag_ranges(tk.SEL):
            try:
                self.text.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.text.insert(tk.INSERT, self.replace_entry.get())
                self.find_next()
            except:
                pass
        else:
            self.find_next()
            
    def replace_all(self):
        """全部替换"""
        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()
        
        if not search_term:
            return
            
        try:
            content = self.text.get('1.0', tk.END)
            if not self.case_var.get():
                new_content = re.sub(search_term, replace_term, content, flags=re.IGNORECASE)
            else:
                new_content = content.replace(search_term, replace_term)
                
            self.text.delete('1.0', tk.END)
            self.text.insert('1.0', new_content)
            
            messagebox.showinfo("替换", f"已替换所有: {search_term} -> {replace_term}")
        except:
            pass


def main():
    root = tk.Tk()
    app = DPlusIDE(root)
    root.mainloop()


if __name__ == "__main__":
    main()