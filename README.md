# 图书管理系统（简易示例）

本仓库提供一个基于 SQLite 的最小化图书管理示例程序，覆盖文档中的功能需求：图书与读者的增删改查、借阅与归还操作，以及按角色划分的权限控制和视图管理。

## 核心特性
- **角色与权限**：管理员（admin）可维护图书与读者数据；操作员（operator）负责借书、还书；读者（reader，权限为 borrower）仅可查看图书与自己的借阅记录。
- **视图管理**：使用 SQL 视图 `v_book_inventory`（库存总览）与 `v_borrow_history`（借阅历史）供受限角色只读查询。
- **安全存储**：用户密码使用带盐的 PBKDF2（SHA-256）派生存储，避免明文及彩虹表攻击。
- **口令策略**：新增账户需至少 8 位，且包含字母、数字和特殊字符。
- **示例数据**：初始化时自动写入示例用户、读者与图书，便于快速体验。

## 快速开始
> 需要 Python 3（标准库即可，无额外依赖）。

1. 初始化数据库（建表并写入示例数据）：
   ```bash
   python main.py init-db
   ```
2. 以不同角色登录体验：
   - 管理员：admin / **Admin!2345**
   - 操作员：operator / **Operator!2345**
   - 读者（仅查看）：reader / **Reader!2345**

> 为避免密码出现在进程列表，可省略 `--password`，程序将优先读取环境变量 `LIBSYS_PASSWORD`，否则会交互式输入。

### 常用命令示例
```bash
# 查看库存（任何角色均可）
python main.py --username reader --password reader123 list-books

# 管理员新增图书
python main.py --username admin --password admin123 add-book --title "数据库原理" --author "教学组" --copies 2 --shelf-code A2

# 管理员查看读者列表
python main.py --username admin --password admin123 list-readers

# 操作员为读者借书（reader_id 可从 list-readers 获取）
python main.py --username operator --password operator123 borrow --book-id 1 --reader-id 1

# 操作员归还图书
python main.py --username operator --password operator123 return --borrow-id 1

# 读者查看自己的借阅历史（基于视图）
python main.py --username reader --password reader123 list-borrows
```

## 数据结构概览
- `users`：登录账户（字段：username、password、role）
- `readers`：读者信息，可与 `users` 关联（user_id）
- `shelves`：书架信息（code、location）
- `books`：图书信息与库存数量（total/available）
- `borrows`：借阅记录（借出、归还时间）
- 视图：
  - `v_book_inventory`：图书库存总览
  - `v_borrow_history`：借阅历史（含 reader_id，供权限过滤）

> 所有操作均使用参数化 SQL，且启用 `PRAGMA foreign_keys=ON` 以保证引用完整性。
