import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, font

from library_system import LibrarySystem


APP_TITLE = "图书管理系统 - 完整版"


class EnhancedLoginApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title(APP_TITLE)
        master.geometry("900x700")
        master.resizable(True, True)
        
        # Set minimum window size
        master.minsize(800, 600)

        self.system = self._init_system()
        self.current_user = None

        self._build_widgets()

    def _build_widgets(self) -> None:
        # Main container
        main_frame = ttk.Frame(self.master, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        title_label = ttk.Label(main_frame, text="📚 图书管理系统 - 完整版", font=title_font)
        title_label.pack(pady=(0, 10))

        # Login section
        login_frame = ttk.LabelFrame(main_frame, text="用户登录", padding=10)
        login_frame.pack(fill=tk.X, pady=(0, 10))

        # Login fields in a grid
        ttk.Label(login_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(login_frame, textvariable=self.username_var, width=20)
        username_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        username_entry.bind('<Return>', lambda e: self.handle_login())

        ttk.Label(login_frame, text="密码:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(login_frame, textvariable=self.password_var, show="●", width=20)
        password_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        password_entry.bind('<Return>', lambda e: self.handle_login())

        # Buttons
        self.login_button = ttk.Button(login_frame, text="登录", command=self.handle_login, width=10)
        self.login_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.logout_button = ttk.Button(login_frame, text="退出", command=self.handle_logout, width=10, state=tk.DISABLED)
        self.logout_button.grid(row=0, column=5, padx=5, pady=5)

        # Status label
        self.status_var = tk.StringVar(value="请输入用户名和密码登录系统")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.pack(pady=(0, 5))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Initially disable notebook
        self.notebook.state(['disabled'])

        # Create tabs
        self._create_view_tab()
        self._create_book_tab()
        self._create_reader_tab()
        self._create_borrow_tab()

        # Help text
        help_text = "💡 默认账户: admin/Admin!2345 | operator/Operator!2345 | reader/Reader!2345"
        ttk.Label(main_frame, text=help_text, foreground="gray", font=("Helvetica", 8)).pack(pady=(5, 0))

    def _create_view_tab(self) -> None:
        """Create the view/query tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 查看")

        # Buttons frame
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="刷新图书列表", command=self.refresh_books).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新借阅记录", command=self.refresh_borrows).pack(side=tk.LEFT, padx=5)

        # Create text widget with scrollbar
        text_frame = ttk.Frame(tab)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.view_text = tk.Text(text_frame, height=20, wrap=tk.WORD, 
                                 yscrollcommand=scrollbar.set, font=("Courier New", 9))
        self.view_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.view_text.yview)

        # Configure tags
        self.view_text.tag_configure("header", foreground="navy", font=("Helvetica", 10, "bold"))
        self.view_text.tag_configure("success", foreground="green")
        self.view_text.tag_configure("warning", foreground="orange")
        self.view_text.tag_configure("error", foreground="red")

    def _create_book_tab(self) -> None:
        """Create the book management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📚 图书管理")

        # Input frame
        input_frame = ttk.LabelFrame(tab, text="图书信息", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Book ID (for update/delete)
        ttk.Label(input_frame, text="图书ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.book_id_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.book_id_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        # Title
        ttk.Label(input_frame, text="*书名:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)
        self.book_title_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.book_title_var, width=25).grid(row=0, column=3, sticky=tk.W, padx=5, pady=3)

        # Author
        ttk.Label(input_frame, text="作者:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        self.book_author_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.book_author_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)

        # ISBN
        ttk.Label(input_frame, text="ISBN:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=3)
        self.book_isbn_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.book_isbn_var, width=20).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)

        # Shelf code
        ttk.Label(input_frame, text="书架编号:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        self.book_shelf_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.book_shelf_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)

        # Copies
        ttk.Label(input_frame, text="库存数量:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=3)
        self.book_copies_var = tk.StringVar(value="1")
        ttk.Entry(input_frame, textvariable=self.book_copies_var, width=10).grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)

        # Buttons frame
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="➕ 新增图书", command=self.add_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ 修改图书", command=self.update_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除图书", command=self.delete_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 查询图书", command=self.query_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 清空表单", command=self.clear_book_form).pack(side=tk.LEFT, padx=5)

        # List frame
        list_frame = ttk.LabelFrame(tab, text="图书列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview
        columns = ("ID", "书名", "作者", "ISBN", "书架", "库存")
        self.book_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.book_tree.heading(col, text=col)
            if col == "书名":
                self.book_tree.column(col, width=200)
            elif col == "作者":
                self.book_tree.column(col, width=120)
            elif col == "ISBN":
                self.book_tree.column(col, width=120)
            else:
                self.book_tree.column(col, width=80)

        self.book_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.book_tree.bind('<Double-Button-1>', self.on_book_select)

        # Scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.book_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.book_tree.configure(yscrollcommand=tree_scroll.set)

    def _create_reader_tab(self) -> None:
        """Create the reader management tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="👥 读者管理")

        # Input frame
        input_frame = ttk.LabelFrame(tab, text="读者信息", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Reader ID
        ttk.Label(input_frame, text="读者ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.reader_id_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.reader_id_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        # Name
        ttk.Label(input_frame, text="*姓名:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)
        self.reader_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.reader_name_var, width=20).grid(row=0, column=3, sticky=tk.W, padx=5, pady=3)

        # Username (optional)
        ttk.Label(input_frame, text="用户名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        self.reader_username_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.reader_username_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)

        # Password (optional)
        ttk.Label(input_frame, text="密码:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=3)
        self.reader_password_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.reader_password_var, show="●", width=20).grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="➕ 新增读者", command=self.add_reader).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ 修改读者", command=self.update_reader).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除读者", command=self.delete_reader).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔍 查询读者", command=self.query_reader).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🧹 清空表单", command=self.clear_reader_form).pack(side=tk.LEFT, padx=5)

        # List frame
        list_frame = ttk.LabelFrame(tab, text="读者列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview
        columns = ("ID", "姓名", "用户名", "角色")
        self.reader_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.reader_tree.heading(col, text=col)
            if col == "姓名":
                self.reader_tree.column(col, width=150)
            elif col == "用户名":
                self.reader_tree.column(col, width=150)
            else:
                self.reader_tree.column(col, width=100)

        self.reader_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.reader_tree.bind('<Double-Button-1>', self.on_reader_select)

        # Scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.reader_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_tree.configure(yscrollcommand=tree_scroll.set)

    def _create_borrow_tab(self) -> None:
        """Create the borrow/return tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📖 借还书")

        # Borrow frame
        borrow_frame = ttk.LabelFrame(tab, text="借书", padding=10)
        borrow_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(borrow_frame, text="*图书ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.borrow_book_id_var = tk.StringVar()
        ttk.Entry(borrow_frame, textvariable=self.borrow_book_id_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        ttk.Label(borrow_frame, text="*读者ID:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)
        self.borrow_reader_id_var = tk.StringVar()
        ttk.Entry(borrow_frame, textvariable=self.borrow_reader_id_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5, pady=3)

        ttk.Button(borrow_frame, text="📚 借书", command=self.borrow_book).grid(row=0, column=4, padx=10, pady=3)

        # Return frame
        return_frame = ttk.LabelFrame(tab, text="还书", padding=10)
        return_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(return_frame, text="*借阅ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.return_borrow_id_var = tk.StringVar()
        ttk.Entry(return_frame, textvariable=self.return_borrow_id_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        ttk.Button(return_frame, text="📥 还书", command=self.return_book).grid(row=0, column=2, padx=10, pady=3)

        # Borrow records list
        list_frame = ttk.LabelFrame(tab, text="借阅记录", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Refresh button
        ttk.Button(list_frame, text="🔄 刷新", command=self.refresh_borrow_list).pack(anchor=tk.W, padx=5, pady=3)

        # Create treeview
        columns = ("借阅ID", "图书ID", "书名", "读者", "借出时间", "归还时间", "状态")
        self.borrow_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.borrow_tree.heading(col, text=col)
            if col == "书名":
                self.borrow_tree.column(col, width=180)
            elif col == "读者":
                self.borrow_tree.column(col, width=100)
            elif col in ["借出时间", "归还时间"]:
                self.borrow_tree.column(col, width=100)
            else:
                self.borrow_tree.column(col, width=80)

        self.borrow_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.borrow_tree.bind('<Double-Button-1>', self.on_borrow_select)

        # Scrollbar
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.borrow_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.borrow_tree.configure(yscrollcommand=tree_scroll.set)

    def handle_login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            self.status_var.set("❌ 请输入用户名和密码")
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        try:
            user = self.system.authenticate(username, password)
            if not user:
                self.status_var.set("❌ 登录失败：用户名或密码错误")
                messagebox.showerror("登录失败", "用户名或密码错误，请重试")
                return

            self.current_user = user
            role_name = {"admin": "管理员", "operator": "操作员", "borrower": "读者"}.get(user["role"], user["role"])
            self.status_var.set(f"✅ 登录成功！当前用户: {username} ({role_name})")
            
            # Update button states
            self.login_button.config(state=tk.DISABLED)
            self.logout_button.config(state=tk.NORMAL)
            
            # Enable notebook
            self.notebook.state(['!disabled'])
            
            # Configure tabs based on role
            self._configure_tabs_by_role(user["role"])
            
            # Load initial data
            self.refresh_books()
            self.refresh_borrows()
            
        except Exception as e:
            self.status_var.set(f"❌ 登录出错: {str(e)}")
            messagebox.showerror("错误", f"登录过程中出现错误:\n{str(e)}")

    def _configure_tabs_by_role(self, role: str) -> None:
        """Configure which tabs are accessible based on user role"""
        # Clear all tabs first
        for i in range(self.notebook.index("end")):
            self.notebook.tab(i, state="normal")
        
        if role == "borrower":
            # Readers can only view
            self.notebook.tab(1, state="disabled")  # Book management
            self.notebook.tab(2, state="disabled")  # Reader management
            self.notebook.tab(3, state="disabled")  # Borrow/return
        elif role == "operator":
            # Operators cannot manage books/readers
            self.notebook.tab(1, state="disabled")  # Book management
            self.notebook.tab(2, state="disabled")  # Reader management
        # Admin has access to all tabs

    def handle_logout(self) -> None:
        """Handle user logout"""
        self.current_user = None
        self.username_var.set("")
        self.password_var.set("")
        self.status_var.set("已退出登录，请重新登录")
        
        # Update button states
        self.login_button.config(state=tk.NORMAL)
        self.logout_button.config(state=tk.DISABLED)
        
        # Disable notebook
        self.notebook.state(['disabled'])
        
        # Clear all data
        self.view_text.delete("1.0", tk.END)
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)
        for item in self.reader_tree.get_children():
            self.reader_tree.delete(item)
        for item in self.borrow_tree.get_children():
            self.borrow_tree.delete(item)

    # Book operations
    def add_book(self) -> None:
        if not self._check_permission(['admin']):
            return
        
        title = self.book_title_var.get().strip()
        if not title:
            messagebox.showwarning("提示", "请输入书名")
            return
        
        try:
            book_id = self.system.add_book(
                self.current_user,
                title=title,
                author=self.book_author_var.get().strip() or None,
                isbn=self.book_isbn_var.get().strip() or None,
                shelf_code=self.book_shelf_var.get().strip() or None,
                total_copies=int(self.book_copies_var.get() or 1)
            )
            messagebox.showinfo("成功", f"图书添加成功！ID: {book_id}")
            self.clear_book_form()
            self.refresh_books()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"添加图书失败: {str(e)}")

    def update_book(self) -> None:
        if not self._check_permission(['admin']):
            return
        
        book_id = self.book_id_var.get().strip()
        if not book_id:
            messagebox.showwarning("提示", "请输入图书ID")
            return
        
        try:
            self.system.update_book(
                self.current_user,
                int(book_id),
                title=self.book_title_var.get().strip() or None,
                author=self.book_author_var.get().strip() or None,
                isbn=self.book_isbn_var.get().strip() or None,
                shelf_code=self.book_shelf_var.get().strip() or None,
                total_copies=int(self.book_copies_var.get()) if self.book_copies_var.get() else None
            )
            messagebox.showinfo("成功", "图书信息已更新！")
            self.clear_book_form()
            self.refresh_books()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"更新图书失败: {str(e)}")

    def delete_book(self) -> None:
        if not self._check_permission(['admin']):
            return
        
        book_id = self.book_id_var.get().strip()
        if not book_id:
            messagebox.showwarning("提示", "请输入图书ID")
            return
        
        if not messagebox.askyesno("确认", f"确定要删除ID为 {book_id} 的图书吗？"):
            return
        
        try:
            self.system.delete_book(self.current_user, int(book_id))
            messagebox.showinfo("成功", "图书已删除！")
            self.clear_book_form()
            self.refresh_books()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"删除图书失败: {str(e)}")

    def query_book(self) -> None:
        self.refresh_books()

    def clear_book_form(self) -> None:
        self.book_id_var.set("")
        self.book_title_var.set("")
        self.book_author_var.set("")
        self.book_isbn_var.set("")
        self.book_shelf_var.set("")
        self.book_copies_var.set("1")

    def on_book_select(self, event) -> None:
        """Handle book selection from tree"""
        selection = self.book_tree.selection()
        if selection:
            item = self.book_tree.item(selection[0])
            values = item['values']
            self.book_id_var.set(values[0])
            self.book_title_var.set(values[1])
            self.book_author_var.set(values[2] if values[2] != 'N/A' else '')
            self.book_isbn_var.set(values[3] if values[3] != 'N/A' else '')
            self.book_shelf_var.set(values[4] if values[4] != 'N/A' else '')
            # Parse stock info (e.g., "3/5")
            stock_str = str(values[5])
            if '/' in stock_str:
                stock = stock_str.split('/')[1]
            else:
                stock = stock_str
            self.book_copies_var.set(stock)

    # Reader operations
    def add_reader(self) -> None:
        if not self._check_permission(['admin']):
            return
        
        name = self.reader_name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入姓名")
            return
        
        try:
            reader_id = self.system.add_reader(
                self.current_user,
                name=name,
                username=self.reader_username_var.get().strip() or None,
                password=self.reader_password_var.get() or None
            )
            messagebox.showinfo("成功", f"读者添加成功！ID: {reader_id}")
            self.clear_reader_form()
            self.refresh_readers()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"添加读者失败: {str(e)}")

    def update_reader(self) -> None:
        if not self._check_permission(['admin']):
            return
        
        reader_id = self.reader_id_var.get().strip()
        if not reader_id:
            messagebox.showwarning("提示", "请输入读者ID")
            return
        
        try:
            self.system.update_reader(
                self.current_user,
                int(reader_id),
                name=self.reader_name_var.get().strip() or None
            )
            messagebox.showinfo("成功", "读者信息已更新！")
            self.clear_reader_form()
            self.refresh_readers()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"更新读者失败: {str(e)}")

    def delete_reader(self) -> None:
        if not self._check_permission(['admin']):
            return
        
        reader_id = self.reader_id_var.get().strip()
        if not reader_id:
            messagebox.showwarning("提示", "请输入读者ID")
            return
        
        if not messagebox.askyesno("确认", f"确定要删除ID为 {reader_id} 的读者吗？"):
            return
        
        try:
            self.system.delete_reader(self.current_user, int(reader_id))
            messagebox.showinfo("成功", "读者已删除！")
            self.clear_reader_form()
            self.refresh_readers()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"删除读者失败: {str(e)}")

    def query_reader(self) -> None:
        self.refresh_readers()

    def clear_reader_form(self) -> None:
        self.reader_id_var.set("")
        self.reader_name_var.set("")
        self.reader_username_var.set("")
        self.reader_password_var.set("")

    def on_reader_select(self, event) -> None:
        """Handle reader selection from tree"""
        selection = self.reader_tree.selection()
        if selection:
            item = self.reader_tree.item(selection[0])
            values = item['values']
            self.reader_id_var.set(values[0])
            self.reader_name_var.set(values[1])
            self.reader_username_var.set(values[2] if values[2] != 'N/A' else '')

    # Borrow/Return operations
    def borrow_book(self) -> None:
        if not self._check_permission(['admin', 'operator']):
            return
        
        book_id = self.borrow_book_id_var.get().strip()
        reader_id = self.borrow_reader_id_var.get().strip()
        
        if not book_id or not reader_id:
            messagebox.showwarning("提示", "请输入图书ID和读者ID")
            return
        
        try:
            borrow_id = self.system.borrow_book(
                self.current_user,
                book_id=int(book_id),
                reader_id=int(reader_id)
            )
            messagebox.showinfo("成功", f"借书成功！借阅ID: {borrow_id}")
            self.borrow_book_id_var.set("")
            self.borrow_reader_id_var.set("")
            self.refresh_borrow_list()
            self.refresh_books()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"借书失败: {str(e)}")

    def return_book(self) -> None:
        if not self._check_permission(['admin', 'operator']):
            return
        
        borrow_id = self.return_borrow_id_var.get().strip()
        
        if not borrow_id:
            messagebox.showwarning("提示", "请输入借阅ID")
            return
        
        try:
            self.system.return_book(self.current_user, int(borrow_id))
            messagebox.showinfo("成功", "还书成功！")
            self.return_borrow_id_var.set("")
            self.refresh_borrow_list()
            self.refresh_books()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"还书失败: {str(e)}")

    def on_borrow_select(self, event) -> None:
        """Handle borrow record selection"""
        selection = self.borrow_tree.selection()
        if selection:
            item = self.borrow_tree.item(selection[0])
            values = item['values']
            self.return_borrow_id_var.set(values[0])

    # Refresh operations
    def refresh_books(self) -> None:
        """Refresh book list"""
        try:
            # Clear current items
            for item in self.book_tree.get_children():
                self.book_tree.delete(item)
            
            # Load books
            books = self.system.list_books()
            for book in books:
                stock = f"{book['available_copies']}/{book['total_copies']}"
                self.book_tree.insert("", tk.END, values=(
                    book['id'],
                    book['title'],
                    book.get('author') or 'N/A',
                    book.get('isbn') or 'N/A',
                    book.get('shelf_code') or 'N/A',
                    stock
                ))
            
            # Update view text
            self._update_view_text()
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新图书列表失败: {str(e)}")

    def refresh_readers(self) -> None:
        """Refresh reader list"""
        if not self._check_permission(['admin', 'operator'], show_error=False):
            return
        
        try:
            # Clear current items
            for item in self.reader_tree.get_children():
                self.reader_tree.delete(item)
            
            # Load readers
            readers = self.system.list_readers(self.current_user)
            for reader in readers:
                self.reader_tree.insert("", tk.END, values=(
                    reader['id'],
                    reader['name'],
                    reader.get('username') or 'N/A',
                    reader.get('role') or 'N/A'
                ))
        except Exception as e:
            messagebox.showerror("错误", f"刷新读者列表失败: {str(e)}")

    def refresh_borrows(self) -> None:
        """Refresh borrow records in view tab"""
        self._update_view_text()

    def refresh_borrow_list(self) -> None:
        """Refresh borrow list in borrow tab"""
        try:
            # Clear current items
            for item in self.borrow_tree.get_children():
                self.borrow_tree.delete(item)
            
            # Load borrows
            borrows = self.system.list_borrows(self.current_user)
            for borrow in borrows:
                book_title = borrow.get('book_title') or borrow.get('title') or 'N/A'
                borrowed_at = self._format_date(borrow['borrowed_at'])
                returned_at = self._format_date(borrow['returned_at']) if borrow['returned_at'] else 'N/A'
                status = "已归还" if borrow['returned_at'] else "借阅中"
                
                self.borrow_tree.insert("", tk.END, values=(
                    borrow['borrow_id'],
                    borrow.get('book_id', 'N/A'),
                    book_title,
                    borrow['reader_name'],
                    borrowed_at,
                    returned_at,
                    status
                ))
        except Exception as e:
            messagebox.showerror("错误", f"刷新借阅记录失败: {str(e)}")

    def _update_view_text(self) -> None:
        """Update the view tab text widget"""
        if not self.current_user:
            return
        
        try:
            books = self.system.list_books()
            borrows = self.system.list_borrows(self.current_user)
            
            self.view_text.delete("1.0", tk.END)
            
            # Books section
            self.view_text.insert(tk.END, "=" * 80 + "\n")
            self.view_text.insert(tk.END, "📚 图书库存列表\n", "header")
            self.view_text.insert(tk.END, "=" * 80 + "\n\n")
            
            if books:
                for b in books:
                    book_info = (
                        f"ID: {b['id']:3d} | "
                        f"书名: {b['title']:<25s} | "
                        f"作者: {(b['author'] or '未知'):<15s} | "
                        f"书架: {(b['shelf_code'] or 'N/A'):<5s}\n"
                    )
                    self.view_text.insert(tk.END, book_info)
                    
                    available = b['available_copies']
                    total = b['total_copies']
                    stock_info = f"       库存: {available}/{total} "
                    
                    if available == 0:
                        stock_info += "❌ 无库存\n"
                        tag = "error"
                    elif available == total:
                        stock_info += "✅ 充足\n"
                        tag = "success"
                    else:
                        stock_info += "⚠️  部分借出\n"
                        tag = "warning"
                    
                    self.view_text.insert(tk.END, stock_info, tag)
                    if b.get('isbn'):
                        self.view_text.insert(tk.END, f"       ISBN: {b['isbn']}\n")
                    self.view_text.insert(tk.END, "\n")
            else:
                self.view_text.insert(tk.END, "  暂无图书记录\n\n")

            # Borrows section
            self.view_text.insert(tk.END, "=" * 80 + "\n")
            self.view_text.insert(tk.END, "📋 借阅记录\n", "header")
            self.view_text.insert(tk.END, "=" * 80 + "\n\n")
            
            if borrows:
                for r in borrows:
                    book_title = r.get('book_title') or r.get('title') or '未知书名'
                    book_author = r.get('book_author') or r.get('author') or '未知作者'
                    
                    borrow_info = f"记录ID: {r['borrow_id']:3d} | 图书: {book_title:<25s} "
                    if book_author != '未知作者':
                        borrow_info += f"({book_author}) "
                    borrow_info += f"| 读者: {r['reader_name']:<15s}\n"
                    self.view_text.insert(tk.END, borrow_info)
                    
                    borrowed_time = self._format_date(r['borrowed_at'])
                    
                    if r["returned_at"]:
                        returned_time = self._format_date(r['returned_at'])
                        status_info = f"       借出: {borrowed_time} | 归还: {returned_time} | 状态: ✅ 已归还\n"
                        tag = "success"
                    else:
                        status_info = f"       借出: {borrowed_time} | 状态: 📖 借阅中\n"
                        tag = "warning"
                    
                    self.view_text.insert(tk.END, status_info, tag)
                    self.view_text.insert(tk.END, "\n")
            else:
                self.view_text.insert(tk.END, "  暂无借阅记录\n")
                
        except Exception as e:
            self.view_text.insert(tk.END, f"加载数据出错: {str(e)}\n", "error")

    def _format_date(self, datetime_str: str) -> str:
        """Format ISO datetime string to display date only"""
        if not datetime_str:
            return "N/A"
        
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return datetime_str.split('T')[0] if 'T' in datetime_str else datetime_str

    def _check_permission(self, allowed_roles: list, show_error: bool = True) -> bool:
        """Check if current user has permission"""
        if not self.current_user:
            if show_error:
                messagebox.showerror("错误", "请先登录")
            return False
        
        if self.current_user["role"] not in allowed_roles:
            if show_error:
                messagebox.showerror("权限不足", f"当前角色 {self.current_user['role']} 无权执行此操作")
            return False
        
        return True

    def on_close(self) -> None:
        try:
            self.system.close()
        finally:
            self.master.destroy()

    def _init_system(self) -> LibrarySystem:
        system = LibrarySystem()
        with_sample = not system.db_path.exists()
        system.initialize(with_sample_data=with_sample)
        return system


def main() -> None:
    root = tk.Tk()
    app = EnhancedLoginApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
