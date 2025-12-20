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
python main.py --username reader --password 'Reader!2345' list-books

# 管理员新增图书
python main.py --username admin --password 'Admin!2345' add-book --title "数据库原理" --author "教学组" --copies 2 --shelf-code A2

# 管理员查看读者列表
python main.py --username admin --password 'Admin!2345' list-readers

# 管理员新增读者（带登录账户）
python main.py --username admin --password 'Admin!2345' add-reader --name "新读者" --reader-username "new_user" --reader-password "NewUser!2345"

# 操作员为读者借书（reader_id 可从 list-readers 获取）
python main.py --username operator --password 'Operator!2345' borrow --book-id 1 --reader-id 1

# 操作员归还图书
python main.py --username operator --password 'Operator!2345' return --borrow-id 1

# 查看借阅历史（操作员可查看所有记录，读者仅能查看自己的记录）
python main.py --username operator --password 'Operator!2345' list-borrows

# 读者查看自己的借阅历史（基于视图）
python main.py --username reader --password 'Reader!2345' list-borrows
```

> 📖 **详细使用指南**: 查看 [USAGE_GUIDE.md](USAGE_GUIDE.md) 了解登录后如何进行各种操作，包括完整的命令示例和操作流程。

## 图形登录界面（可选）
需要本机支持图形环境（Windows/macOS 默认可用）。提供两个版本：

### 1. 完整功能版（推荐）
```bash
python login_gui_enhanced.py
```

**功能特性：**
- ✅ **完整的CRUD操作** - 支持图书和读者的增删改查
- ✅ **借还书操作** - 直接在界面上进行借书和还书
- ✅ **分标签页管理** - 查看、图书管理、读者管理、借还书四个独立页面
- ✅ **角色权限控制** - 根据用户角色自动启用/禁用相应功能
- ✅ **双击填充表单** - 双击列表项自动填充到表单，方便修改
- ✅ **实时数据刷新** - 操作后自动更新相关列表

**权限说明：**
- **管理员** - 可访问所有功能页面
- **操作员** - 可访问查看和借还书页面
- **读者** - 仅可访问查看页面

### 2. 简洁查看版
```bash
python login_gui.py
```

登录后可查看：
- 📚 **图书库存列表** - 显示所有图书的详细信息（ID、书名、作者、ISBN、书架位置、库存状态）
- 📋 **借阅记录** - 显示借阅历史（包括图书名称、作者、读者姓名、借阅时间、归还状态）
- 支持登录后刷新数据
- 支持退出登录切换账户

**界面特性：**
- 优化的用户体验，支持Enter键快速登录
- 彩色状态显示（可用/借出/已归还）
- 详细的错误提示和状态信息
- 可调整窗口大小，支持滚动查看

> 💡 **提示**: 推荐使用完整功能版（login_gui_enhanced.py）进行日常管理操作。

账户默认同上（admin/operator/reader）。

## 数据结构概览
- `users`：登录账户（字段：username、password、role）
- `readers`：读者信息，可与 `users` 关联（user_id）
- `shelves`：书架信息（code、location）
- `books`：图书信息与库存数量（total/available）
- `borrows`：借阅记录（借出、归还时间）
- 视图：
  - `v_book_inventory`：图书库存总览
  - `v_borrow_history`：借阅历史（含 book_id、book_title、book_author、reader_id、reader_name，供权限过滤）

> 所有操作均使用参数化 SQL，且启用 `PRAGMA foreign_keys=ON` 以保证引用完整性。

## 功能完善情况

### ✅ 已实现功能
1. **登录界面优化**
   - 改进的图形界面，支持Enter键登录
   - 更好的错误提示和状态显示
   - 登录/退出/刷新功能
   - 彩色状态标识和格式化输出

2. **图书CRUD操作**
   - ✅ 新增图书（支持书名、作者、ISBN、书架、库存数量）
   - ✅ 修改图书信息
   - ✅ 删除图书（需确保无未归还记录）
   - ✅ 查询图书列表

3. **读者CRUD操作**
   - ✅ 新增读者（可选择是否创建登录账户）
   - ✅ 修改读者信息
   - ✅ 删除读者（需确保无未归还记录）
   - ✅ 查询读者列表

4. **借阅管理**
   - ✅ 借书操作（自动扣减库存）
   - ✅ 还书操作（自动增加库存）
   - ✅ 借阅记录查询（包含图书名称、作者信息）
   - ✅ 按权限过滤记录（读者只能查看自己的记录）

5. **数据增强**
   - ✅ 借阅记录包含完整图书信息（ID、书名、作者）
   - ✅ 借阅记录包含读者信息
   - ✅ 支持时间戳记录借阅和归还时间
