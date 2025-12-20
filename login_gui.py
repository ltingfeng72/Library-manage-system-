import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from library_system import LibrarySystem


APP_TITLE = "图书管理系统 - 登录"


class LoginApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title(APP_TITLE)
        master.geometry("500x400")
        master.resizable(False, False)

        self.system = self._init_system()

        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.master, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="用户名").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var, width=30).grid(
            row=0, column=1, sticky=tk.W
        )

        ttk.Label(frame, text="密码").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password_var, show="*", width=30).grid(
            row=1, column=1, sticky=tk.W
        )

        ttk.Button(frame, text="登录", command=self.handle_login).grid(
            row=2, column=1, sticky=tk.W, pady=8
        )

        self.status_var = tk.StringVar(value="请登录")
        ttk.Label(frame, textvariable=self.status_var, foreground="blue").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=4
        )

        ttk.Label(frame, text="图书与借阅信息").grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(12, 4)
        )
        self.text = tk.Text(frame, height=12, width=60, state=tk.DISABLED)
        self.text.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)

        frame.rowconfigure(5, weight=1)
        frame.columnconfigure(1, weight=1)

    def _set_text(self, content: str) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, content)
        self.text.configure(state=tk.DISABLED)

    def handle_login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码")
            return

        user = self.system.authenticate(username, password)
        if not user:
            self.status_var.set("登录失败：用户名或密码错误")
            messagebox.showerror("错误", "用户名或密码错误")
            return

        role = user["role"]
        self.status_var.set(f"登录成功，当前角色：{role}")
        self._load_data(user)

    def _load_data(self, user: sqlite3.Row) -> None:
        try:
            books = self.system.list_books()
            lines = ["【库存列表】"]
            for b in books:
                lines.append(
                    f"- {b['id']}: {b['title']} (库存 {b['available_copies']}/{b['total_copies']})"
                )

            lines.append("")
            lines.append("【借阅记录】")
            borrows = self.system.list_borrows(user)
            if not borrows:
                lines.append("- 无借阅记录")
            else:
                for r in borrows:
                    status = "已归还" if r["returned_at"] else "借出中"
                    lines.append(
                        f"- {r['borrow_id']}: {r['title']} / {r['reader_name']} / {status}"
                    )

            self._set_text("\n".join(lines))
        except (ValueError, PermissionError, sqlite3.DatabaseError) as exc:
            if isinstance(exc, PermissionError):
                msg = f"权限不足：{exc}"
            elif isinstance(exc, sqlite3.DatabaseError):
                msg = f"数据库错误：{exc}"
            else:
                msg = str(exc)
            messagebox.showerror("错误", msg)

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
