# 图书管理系统使用指南

## 登录后操作说明

本系统提供两种使用方式：**图形界面（GUI）** 和 **命令行界面（CLI）**

---

## 一、图形界面使用方法

系统提供两个图形界面版本：

### 版本1: 完整功能版（推荐）

#### 1. 启动完整功能版
```bash
python login_gui_enhanced.py
```

#### 2. 登录系统
使用以下账户登录：
- **管理员**: `admin` / `Admin!2345`
- **操作员**: `operator` / `Operator!2345`
- **读者**: `reader` / `Reader!2345`

#### 3. 完整功能版特性

登录后可使用以下功能（根据角色权限）：

##### 📊 查看页面（所有角色）
- 查看图书库存列表（带库存状态）
- 查看借阅记录（读者只能看自己的记录）
- 刷新图书列表和借阅记录

##### 📚 图书管理页面（仅管理员）
- ➕ **新增图书** - 填写书名、作者、ISBN、书架、库存数量后点击"新增图书"
- ✏️ **修改图书** - 双击图书列表选择图书，修改信息后点击"修改图书"
- 🗑️ **删除图书** - 输入图书ID或双击选择，点击"删除图书"（需确认）
- 🔍 **查询图书** - 点击"查询图书"刷新列表
- 🧹 **清空表单** - 清空所有输入框

##### 👥 读者管理页面（仅管理员）
- ➕ **新增读者** - 填写姓名（必填），可选填用户名和密码创建登录账户
- ✏️ **修改读者** - 双击读者列表选择读者，修改姓名后点击"修改读者"
- 🗑️ **删除读者** - 输入读者ID或双击选择，点击"删除读者"（需确认）
- 🔍 **查询读者** - 点击"查询读者"刷新列表
- 🧹 **清空表单** - 清空所有输入框

##### 📖 借还书页面（管理员和操作员）
- 📚 **借书操作** - 输入图书ID和读者ID，点击"借书"按钮
- 📥 **还书操作** - 输入借阅ID或双击借阅记录，点击"还书"按钮
- 🔄 **查看借阅记录** - 显示所有借阅记录

#### 4. 使用技巧
- **双击填充**: 双击列表中的任意行，相关信息会自动填充到表单中
- **Enter快速登录**: 在密码框按Enter键可快速登录
- **标签页切换**: 根据角色自动启用/禁用标签页
- **实时刷新**: 完成操作后自动刷新相关列表

---

### 版本2: 简洁查看版

#### 1. 启动简洁版
```bash
python login_gui.py
```

#### 2. 登录系统
使用以下账户登录：
- **管理员**: `admin` / `Admin!2345`
- **操作员**: `operator` / `Operator!2345`
- **读者**: `reader` / `Reader!2345`

#### 3. 登录后功能

图形界面登录后可以：

#### 📚 查看图书库存列表
- 显示所有图书的详细信息（ID、书名、作者、ISBN、书架位置）
- 显示实时库存状态（可用数量/总数量）
- 彩色标识：✅ 充足 | ⚠️ 部分借出 | ❌ 无库存

#### 📋 查看借阅记录
- 显示借阅历史（图书名称、作者、读者姓名、借阅时间）
- 显示归还状态（📖 借阅中 | ✅ 已归还）
- 根据角色显示不同内容：
  - 管理员/操作员：查看所有借阅记录
  - 读者：仅查看自己的借阅记录

#### 🔄 其他操作
- **刷新数据**: 点击"刷新数据"按钮更新显示内容
- **退出登录**: 点击"退出登录"按钮切换账户

### 💡 图形界面版本对比

| 功能 | 完整功能版 | 简洁查看版 |
|------|-----------|-----------|
| 查看图书和借阅记录 | ✅ | ✅ |
| 图书增删改 | ✅ | ❌ |
| 读者增删改 | ✅ | ❌ |
| 借还书操作 | ✅ | ❌ |
| 标签页界面 | ✅ | ❌ |
| 双击填充表单 | ✅ | ❌ |

**推荐**: 日常管理使用完整功能版（`login_gui_enhanced.py`），快速查看使用简洁版（`login_gui.py`）。

---

## 二、命令行界面使用方法（支持完整功能）

命令行界面支持所有管理操作，根据不同角色有不同权限。

### 1. 初始化数据库（首次使用）
```bash
python main.py init-db
```

### 2. 按角色进行的操作

#### 👨‍💼 管理员 (admin) - 完整权限

**图书管理**
```bash
# 新增图书
python main.py --username admin --password 'Admin!2345' add-book \
  --title "数据库原理" --author "教学组" --copies 5 --shelf-code A2

# 修改图书信息
python main.py --username admin --password 'Admin!2345' update-book \
  --book-id 1 --title "数据库原理(第2版)" --copies 10

# 删除图书（需确保无未归还记录）
python main.py --username admin --password 'Admin!2345' delete-book --book-id 2

# 查看图书列表
python main.py --username admin --password 'Admin!2345' list-books
```

**读者管理**
```bash
# 新增读者（仅姓名）
python main.py --username admin --password 'Admin!2345' add-reader \
  --name "张三"

# 新增读者（带登录账户）
python main.py --username admin --password 'Admin!2345' add-reader \
  --name "李四" --reader-username "lisi" --reader-password "Lisi!2345"

# 修改读者信息
python main.py --username admin --password 'Admin!2345' update-reader \
  --reader-id 2 --name "李四(VIP)"

# 删除读者（需确保无未归还记录）
python main.py --username admin --password 'Admin!2345' delete-reader --reader-id 3

# 查看读者列表
python main.py --username admin --password 'Admin!2345' list-readers
```

**借阅管理**
```bash
# 为读者借书
python main.py --username admin --password 'Admin!2345' borrow \
  --book-id 1 --reader-id 1

# 归还图书
python main.py --username admin --password 'Admin!2345' return --borrow-id 1

# 查看所有借阅记录
python main.py --username admin --password 'Admin!2345' list-borrows
```

#### 👨‍💻 操作员 (operator) - 借阅管理权限

**借阅管理**
```bash
# 为读者借书
python main.py --username operator --password 'Operator!2345' borrow \
  --book-id 1 --reader-id 1

# 归还图书
python main.py --username operator --password 'Operator!2345' return --borrow-id 1

# 查看所有借阅记录
python main.py --username operator --password 'Operator!2345' list-borrows

# 查看图书列表
python main.py --username operator --password 'Operator!2345' list-books

# 查看读者列表
python main.py --username operator --password 'Operator!2345' list-readers
```

#### 👤 读者 (reader) - 查看权限

```bash
# 查看图书列表
python main.py --username reader --password 'Reader!2345' list-books

# 查看自己的借阅记录
python main.py --username reader --password 'Reader!2345' list-borrows
```

### 3. 常用操作流程示例

#### 场景1: 新书入库并借出
```bash
# 1. 管理员添加新书
python main.py --username admin --password 'Admin!2345' add-book \
  --title "Python编程" --author "作者A" --copies 3 --shelf-code B1

# 2. 查看图书列表，获取book-id（假设是2）
python main.py --username admin --password 'Admin!2345' list-books

# 3. 操作员为读者借书（reader-id从list-readers获取，假设是1）
python main.py --username operator --password 'Operator!2345' borrow \
  --book-id 2 --reader-id 1

# 4. 查看借阅记录
python main.py --username operator --password 'Operator!2345' list-borrows
```

#### 场景2: 新增读者并为其借书
```bash
# 1. 管理员添加新读者（带账户）
python main.py --username admin --password 'Admin!2345' add-reader \
  --name "王五" --reader-username "wangwu" --reader-password "Wangwu!2345"

# 2. 查看读者列表，获取reader-id（假设是3）
python main.py --username admin --password 'Admin!2345' list-readers

# 3. 操作员为新读者借书
python main.py --username operator --password 'Operator!2345' borrow \
  --book-id 1 --reader-id 3

# 4. 新读者登录查看自己的借阅记录
python main.py --username wangwu --password 'Wangwu!2345' list-borrows
```

#### 场景3: 还书操作
```bash
# 1. 查看借阅记录，获取borrow-id（假设是1）
python main.py --username operator --password 'Operator!2345' list-borrows

# 2. 归还图书
python main.py --username operator --password 'Operator!2345' return --borrow-id 1

# 3. 再次查看借阅记录，确认已归还
python main.py --username operator --password 'Operator!2345' list-borrows
```

---

## 三、权限对照表

| 功能 | 管理员 | 操作员 | 读者 |
|------|--------|--------|------|
| 查看图书列表 | ✅ | ✅ | ✅ |
| 新增图书 | ✅ | ❌ | ❌ |
| 修改图书 | ✅ | ❌ | ❌ |
| 删除图书 | ✅ | ❌ | ❌ |
| 查看读者列表 | ✅ | ✅ | ❌ |
| 新增读者 | ✅ | ❌ | ❌ |
| 修改读者 | ✅ | ❌ | ❌ |
| 删除读者 | ✅ | ❌ | ❌ |
| 借书操作 | ✅ | ✅ | ❌ |
| 还书操作 | ✅ | ✅ | ❌ |
| 查看所有借阅记录 | ✅ | ✅ | ❌ |
| 查看自己的借阅记录 | ✅ | ✅ | ✅ |

---

## 四、常见问题

### Q1: 如何获取book-id或reader-id？
**A**: 使用`list-books`或`list-readers`命令查看列表，ID显示在返回的JSON数据中。

### Q2: 忘记密码怎么办？
**A**: 管理员可以删除旧账户后重新创建，或直接修改数据库中的密码哈希值（需要技术知识）。

### Q3: 为什么图形界面不能进行增删改操作？
**A**: 当前版本的图形界面设计为只读视图，主要用于快速查看数据。完整的管理功能请使用命令行界面。

### Q4: 可以同时借多本书吗？
**A**: 可以，多次执行借书命令即可。每次借书会创建一条独立的借阅记录。

### Q5: 删除图书或读者时提示有未归还记录怎么办？
**A**: 系统为保护数据完整性，不允许删除有未归还记录的图书或读者。请先归还所有相关图书，然后再执行删除操作。

---

## 五、提示和技巧

### 💡 使用环境变量保护密码
```bash
# 设置环境变量
export LIBSYS_PASSWORD='Admin!2345'

# 使用时可省略--password参数
python main.py --username admin list-books
```

### 💡 批量导入数据
可以编写Python脚本调用LibrarySystem类的方法进行批量操作，参考`library_system.py`中的API。

### 💡 备份数据库
```bash
# 数据库文件为library.db，定期备份
cp library.db library_backup_$(date +%Y%m%d).db
```

---

## 六、技术支持

如有问题或建议，请在GitHub仓库提交Issue。
