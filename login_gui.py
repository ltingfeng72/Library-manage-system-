import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, font

from library_system import LibrarySystem


APP_TITLE = "图书管理系统"


class LoginApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title(APP_TITLE)
        master.geometry("700x550")
        master.resizable(True, True)
        
        # Set minimum window size
        master.minsize(600, 450)

        self.system = self._init_system()
        self.current_user = None

        self._build_widgets()

    def _build_widgets(self) -> None:
        # Main container
        main_frame = ttk.Frame(self.master, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_font = font.Font(family="Helvetica", size=16, weight="bold")
        title_label = ttk.Label(main_frame, text="📚 图书管理系统", font=title_font)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Login section
        login_frame = ttk.LabelFrame(main_frame, text="用户登录", padding=15)
        login_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 15))

        ttk.Label(login_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(login_frame, textvariable=self.username_var, width=25)
        username_entry.grid(row=0, column=1, sticky=tk.EW, pady=8)
        username_entry.bind('<Return>', lambda e: self.handle_login())

        ttk.Label(login_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(login_frame, textvariable=self.password_var, show="●", width=25)
        password_entry.grid(row=1, column=1, sticky=tk.EW, pady=8)
        password_entry.bind('<Return>', lambda e: self.handle_login())

        # Buttons frame
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.login_button = ttk.Button(button_frame, text="登录", command=self.handle_login, width=12)
        self.login_button.pack(side=tk.LEFT, padx=5)
        
        self.logout_button = ttk.Button(button_frame, text="退出登录", command=self.handle_logout, width=12, state=tk.DISABLED)
        self.logout_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(button_frame, text="刷新数据", command=self.refresh_data, width=12, state=tk.DISABLED)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        login_frame.columnconfigure(1, weight=1)

        # Status label
        self.status_var = tk.StringVar(value="请输入用户名和密码登录系统")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Info display section
        info_frame = ttk.LabelFrame(main_frame, text="系统信息", padding=10)
        info_frame.grid(row=3, column=0, columnspan=3, sticky=tk.NSEW)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(info_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(info_frame, height=15, width=70, state=tk.DISABLED, 
                           wrap=tk.WORD, yscrollcommand=scrollbar.set,
                           font=("Courier New", 10))
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text.yview)

        # Configure tags for colored text
        self.text.tag_configure("header", foreground="navy", font=("Helvetica", 11, "bold"))
        self.text.tag_configure("available", foreground="green")
        self.text.tag_configure("borrowed", foreground="orange")
        self.text.tag_configure("returned", foreground="gray")

        # Help text
        help_frame = ttk.Frame(main_frame)
        help_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        help_text = "💡 提示: 默认账户 - 管理员(admin/Admin!2345) | 操作员(operator/Operator!2345) | 读者(reader/Reader!2345)"
        ttk.Label(help_frame, text=help_text, foreground="gray", font=("Helvetica", 8)).pack()

        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def _set_text(self, content: str) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)
        self.text.configure(state=tk.DISABLED)

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
            self.refresh_button.config(state=tk.NORMAL)
            
            self._load_data(user)
        except Exception as e:
            self.status_var.set(f"❌ 登录出错: {str(e)}")
            messagebox.showerror("错误", f"登录过程中出现错误:\n{str(e)}")
    
    def handle_logout(self) -> None:
        """Handle user logout"""
        self.current_user = None
        self.username_var.set("")
        self.password_var.set("")
        self.status_var.set("已退出登录，请重新登录")
        
        # Update button states
        self.login_button.config(state=tk.NORMAL)
        self.logout_button.config(state=tk.DISABLED)
        self.refresh_button.config(state=tk.DISABLED)
        
        # Clear display
        self._set_text("请登录查看图书和借阅信息")
    
    def refresh_data(self) -> None:
        """Refresh the displayed data"""
        if self.current_user:
            self.status_var.set("正在刷新数据...")
            self._load_data(self.current_user)
            self.status_var.set(f"✅ 数据已刷新 ({self.current_user['username']})")

    def _format_date(self, datetime_str: str) -> str:
        """Format ISO datetime string to display date only
        
        Args:
            datetime_str: ISO format datetime string
            
        Returns:
            Date string in YYYY-MM-DD format
        """
        if not datetime_str:
            return "N/A"
        
        try:
            # Try to parse as ISO format and extract date
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            # Fallback: simple split for backward compatibility
            return datetime_str.split('T')[0] if 'T' in datetime_str else datetime_str

    def _load_data(self, user: sqlite3.Row) -> None:
        try:
            books = self.system.list_books()
            
            # Clear and prepare text widget
            self.text.configure(state=tk.NORMAL)
            self.text.delete("1.0", tk.END)
            
            # Books section
            self.text.insert(tk.END, "=" * 80 + "\n")
            self.text.insert(tk.END, "📚 图书库存列表\n", "header")
            self.text.insert(tk.END, "=" * 80 + "\n\n")
            
            if books:
                for b in books:
                    book_info = (
                        f"ID: {b['id']:3d} | "
                        f"书名: {b['title']:<25s} | "
                        f"作者: {(b['author'] or '未知'):<15s} | "
                        f"书架: {(b['shelf_code'] or 'N/A'):<5s}\n"
                    )
                    self.text.insert(tk.END, book_info)
                    
                    # Stock status with color
                    available = b['available_copies']
                    total = b['total_copies']
                    stock_info = f"       库存: {available}/{total} "
                    
                    if available == 0:
                        stock_info += "❌ 无库存\n"
                        tag = "borrowed"
                    elif available == total:
                        stock_info += "✅ 充足\n"
                        tag = "available"
                    else:
                        stock_info += "⚠️  部分借出\n"
                        tag = "borrowed"
                    
                    self.text.insert(tk.END, stock_info, tag)
                    
                    if b.get('isbn'):
                        self.text.insert(tk.END, f"       ISBN: {b['isbn']}\n")
                    self.text.insert(tk.END, "\n")
            else:
                self.text.insert(tk.END, "  暂无图书记录\n\n")

            # Borrow records section
            self.text.insert(tk.END, "=" * 80 + "\n")
            self.text.insert(tk.END, "📋 借阅记录\n", "header")
            self.text.insert(tk.END, "=" * 80 + "\n\n")
            
            borrows = self.system.list_borrows(user)
            if not borrows:
                self.text.insert(tk.END, "  暂无借阅记录\n")
            else:
                for r in borrows:
                    # Use book_title instead of title for consistency
                    book_title = r.get('book_title') or r.get('title') or '未知书名'
                    book_author = r.get('book_author') or r.get('author') or '未知作者'
                    
                    borrow_info = (
                        f"记录ID: {r['borrow_id']:3d} | "
                        f"图书: {book_title:<25s} "
                    )
                    
                    # Add author if available and not default value
                    if book_author != '未知作者':
                        borrow_info += f"({book_author}) "
                    
                    borrow_info += f"| 读者: {r['reader_name']:<15s}\n"
                    self.text.insert(tk.END, borrow_info)
                    
                    # Format datetime for display
                    borrowed_time = self._format_date(r['borrowed_at'])
                    
                    if r["returned_at"]:
                        returned_time = self._format_date(r['returned_at'])
                        status_info = f"       借出: {borrowed_time} | 归还: {returned_time} | 状态: ✅ 已归还\n"
                        tag = "returned"
                    else:
                        status_info = f"       借出: {borrowed_time} | 状态: 📖 借阅中\n"
                        tag = "borrowed"
                    
                    self.text.insert(tk.END, status_info, tag)
                    self.text.insert(tk.END, "\n")

            self.text.configure(state=tk.DISABLED)
            
        except (ValueError, PermissionError, sqlite3.DatabaseError) as exc:
            self.text.configure(state=tk.DISABLED)
            if isinstance(exc, PermissionError):
                msg = f"权限不足：{exc}"
            elif isinstance(exc, sqlite3.DatabaseError):
                msg = f"数据库错误：{exc}"
            else:
                msg = str(exc)
            messagebox.showerror("错误", msg)
            self.status_var.set(f"❌ 加载数据失败: {str(exc)}")

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
    app = LoginApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
