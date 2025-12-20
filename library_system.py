import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class LibrarySystem:
    """
    A tiny library management helper backed by SQLite.
    It supports simple role-based access control and uses SQL views to expose
    curated data sets for read-only users.
    """

    def __init__(self, db_path: str = "library.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, timeout=5)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------------ setup
    def initialize(self, with_sample_data: bool = True) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'operator', 'borrower'))
            );

            CREATE TABLE IF NOT EXISTS shelves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                location TEXT
            );

            CREATE TABLE IF NOT EXISTS readers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                address TEXT,
                user_id INTEGER UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT,
                title TEXT NOT NULL,
                author TEXT,
                publisher TEXT,
                publication_date TEXT,
                shelf_id INTEGER,
                total_copies INTEGER NOT NULL DEFAULT 1 CHECK (total_copies > 0),
                available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
                FOREIGN KEY (shelf_id) REFERENCES shelves (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS borrows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                reader_id INTEGER NOT NULL,
                borrowed_at TEXT NOT NULL,
                returned_at TEXT,
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
                FOREIGN KEY (reader_id) REFERENCES readers (id) ON DELETE CASCADE
            );

            DROP VIEW IF EXISTS v_book_inventory;
            CREATE VIEW v_book_inventory AS
                SELECT
                    books.id,
                    books.title,
                    books.author,
                    books.isbn,
                    books.publisher,
                    books.publication_date,
                    shelves.code AS shelf_code,
                    books.available_copies,
                    books.total_copies
                FROM books
                LEFT JOIN shelves ON shelves.id = books.shelf_id;

            DROP VIEW IF EXISTS v_borrow_history;
            CREATE VIEW v_borrow_history AS
                SELECT
                    borrows.id AS borrow_id,
                    books.id AS book_id,
                    books.title AS book_title,
                    books.author AS book_author,
                    readers.name AS reader_name,
                    readers.id AS reader_id,
                    borrows.borrowed_at,
                    borrows.returned_at
                FROM borrows
                JOIN books ON books.id = borrows.book_id
                JOIN readers ON readers.id = borrows.reader_id;
            """
        )
        self.conn.commit()
        if with_sample_data:
            self._ensure_sample_data()

    def _ensure_sample_data(self) -> None:
        cur = self.conn.cursor()
        # Create default users
        _ = self._insert_user_if_missing("admin", "Admin!2345", "admin")
        _ = self._insert_user_if_missing("operator", "Operator!2345", "operator")
        borrower_id = self._insert_user_if_missing("reader", "Reader!2345", "borrower")
        
        # Create additional user accounts for readers
        user_zhangsan = self._insert_user_if_missing("zhangsan", "Zhang!2345", "borrower")
        user_lisi = self._insert_user_if_missing("lisi", "Lisi!2345", "borrower")
        user_wangwu = self._insert_user_if_missing("wangwu", "Wang!2345", "borrower")

        # Create shelves
        shelf_a1 = self._get_or_create_shelf("A1", "综合区")
        shelf_b1 = self._get_or_create_shelf("B1", "外文区")
        shelf_c1 = self._get_or_create_shelf("C1", "计算机区")
        shelf_d1 = self._get_or_create_shelf("D1", "文学区")
        shelf_e1 = self._get_or_create_shelf("E1", "科学区")

        # Create readers
        cur.execute(
            "INSERT OR IGNORE INTO readers (name, age, gender, address, user_id) VALUES (?, ?, ?, ?, ?)",
            ("示例读者", 25, "男", "北京市朝阳区示例街道1号", borrower_id),
        )
        
        # Get or create reader IDs
        reader1_id = cur.execute(
            "SELECT id FROM readers WHERE name = ?", ("示例读者",)
        ).fetchone()[0]
        
        # Add more readers with user accounts
        cur.execute(
            "INSERT OR IGNORE INTO readers (name, age, gender, address, user_id) VALUES (?, ?, ?, ?, ?)",
            ("张三", 28, "男", "上海市浦东新区世纪大道100号", user_zhangsan),
        )
        cur.execute(
            "INSERT OR IGNORE INTO readers (name, age, gender, address, user_id) VALUES (?, ?, ?, ?, ?)",
            ("李四", 32, "女", "广州市天河区珠江新城88号", user_lisi),
        )
        cur.execute(
            "INSERT OR IGNORE INTO readers (name, age, gender, address, user_id) VALUES (?, ?, ?, ?, ?)",
            ("王五", 22, "男", "深圳市南山区科技园南路99号", user_wangwu),
        )
        
        # Add reader without user account
        cur.execute(
            "INSERT OR IGNORE INTO readers (name, age, gender, address, user_id) VALUES (?, ?, ?, ?, ?)",
            ("赵六", 30, "女", "杭州市西湖区文一路66号", None),
        )

        # Add rich book collection if database is empty
        if not cur.execute("SELECT 1 FROM books LIMIT 1").fetchone():
            books_data = [
                # (ISBN, 书名, 作者, 出版社, 出版日期, shelf_id, 总数, 可用数)
                ("9787020002207", "红楼梦", "曹雪芹", "人民文学出版社", "1996-12-01", shelf_d1, 5, 5),
                ("9787020008735", "三国演义", "罗贯中", "人民文学出版社", "1998-05-01", shelf_d1, 4, 4),
                ("9787020015016", "西游记", "吴承恩", "人民文学出版社", "1999-01-01", shelf_d1, 4, 4),
                ("9787020015498", "水浒传", "施耐庵", "人民文学出版社", "1997-01-01", shelf_d1, 3, 3),
                ("9787115428028", "Python编程：从入门到实践", "Eric Matthes", "人民邮电出版社", "2016-07-01", shelf_c1, 8, 8),
                ("9787111544937", "深入理解计算机系统", "Randal E. Bryant", "机械工业出版社", "2016-11-01", shelf_c1, 6, 6),
                ("9787115547996", "算法导论", "Thomas H. Cormen", "人民邮电出版社", "2012-12-01", shelf_c1, 5, 5),
                ("9787111558422", "Java核心技术", "Cay S. Horstmann", "机械工业出版社", "2017-01-01", shelf_c1, 7, 7),
                ("9787115533623", "数据结构与算法分析", "Mark Allen Weiss", "人民邮电出版社", "2020-08-01", shelf_c1, 6, 6),
                ("9787115293800", "JavaScript高级程序设计", "Nicholas C. Zakas", "人民邮电出版社", "2012-03-01", shelf_c1, 5, 5),
                ("9780131103627", "The C Programming Language", "Brian W. Kernighan", "Prentice Hall", "1988-04-01", shelf_b1, 4, 4),
                ("9780596517748", "JavaScript: The Good Parts", "Douglas Crockford", "O'Reilly Media", "2008-05-01", shelf_b1, 3, 3),
                ("9787506365437", "平凡的世界", "路遥", "北京十月文艺出版社", "2012-03-01", shelf_d1, 6, 6),
                ("9787020125777", "活着", "余华", "人民文学出版社", "2017-04-01", shelf_d1, 5, 5),
                ("9787544270878", "追风筝的人", "卡勒德·胡赛尼", "上海人民出版社", "2006-05-01", shelf_d1, 4, 4),
                ("9787544291170", "解忧杂货店", "东野圭吾", "南海出版公司", "2014-05-01", shelf_d1, 5, 5),
                ("9787115476210", "人工智能：一种现代方法", "Stuart Russell", "人民邮电出版社", "2018-05-01", shelf_c1, 4, 4),
                ("9787302511359", "机器学习", "周志华", "清华大学出版社", "2019-01-01", shelf_c1, 6, 6),
                ("9787111641933", "深度学习", "Ian Goodfellow", "机械工业出版社", "2019-11-01", shelf_c1, 5, 5),
                ("9787115385376", "统计学习方法", "李航", "人民邮电出版社", "2015-03-01", shelf_c1, 5, 5),
                ("9787030396051", "量子力学导论", "曾谨言", "科学出版社", "2013-05-01", shelf_e1, 3, 3),
                ("9787040396744", "普通物理学", "程守洙", "高等教育出版社", "2013-06-01", shelf_e1, 5, 5),
                ("9787040453638", "概率论与数理统计", "盛骤", "高等教育出版社", "2016-06-01", shelf_e1, 6, 6),
                ("9787040472233", "线性代数", "同济大学", "高等教育出版社", "2017-03-01", shelf_e1, 7, 7),
                ("9787111213826", "数据库系统概念", "Abraham Silberschatz", "机械工业出版社", "2007-03-01", shelf_c1, 5, 5),
            ]
            
            for book_data in books_data:
                cur.execute(
                    """
                    INSERT INTO books (isbn, title, author, publisher, publication_date, shelf_id, total_copies, available_copies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    book_data,
                )
        
        # Add sample borrowing records if none exist
        if not cur.execute("SELECT 1 FROM borrows LIMIT 1").fetchone():
            # Get book and reader IDs
            books = cur.execute("SELECT id FROM books ORDER BY id LIMIT 10").fetchall()
            readers = cur.execute("SELECT id FROM readers ORDER BY id").fetchall()
            
            if books and readers:
                # Add some borrowing records with different statuses
                from datetime import datetime, timezone, timedelta
                
                now = datetime.now(timezone.utc)
                
                # Borrow record 1: Returned (borrowed 30 days ago, returned 25 days ago)
                if len(books) > 0 and len(readers) > 0:
                    borrowed_time = (now - timedelta(days=30)).isoformat()
                    returned_time = (now - timedelta(days=25)).isoformat()
                    cur.execute(
                        "INSERT INTO borrows (book_id, reader_id, borrowed_at, returned_at) VALUES (?, ?, ?, ?)",
                        (books[0][0], readers[0][0], borrowed_time, returned_time)
                    )
                
                # Borrow record 2: Currently borrowed (borrowed 15 days ago)
                if len(books) > 1 and len(readers) > 1:
                    borrowed_time = (now - timedelta(days=15)).isoformat()
                    cur.execute(
                        "INSERT INTO borrows (book_id, reader_id, borrowed_at, returned_at) VALUES (?, ?, ?, ?)",
                        (books[1][0], readers[1][0], borrowed_time, None)
                    )
                    # Update book availability
                    cur.execute(
                        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
                        (books[1][0],)
                    )
                
                # Borrow record 3: Returned (borrowed 20 days ago, returned 10 days ago)
                if len(books) > 2 and len(readers) > 2:
                    borrowed_time = (now - timedelta(days=20)).isoformat()
                    returned_time = (now - timedelta(days=10)).isoformat()
                    cur.execute(
                        "INSERT INTO borrows (book_id, reader_id, borrowed_at, returned_at) VALUES (?, ?, ?, ?)",
                        (books[2][0], readers[2][0], borrowed_time, returned_time)
                    )
                
                # Borrow record 4: Currently borrowed (borrowed 7 days ago)
                if len(books) > 3 and len(readers) > 3:
                    borrowed_time = (now - timedelta(days=7)).isoformat()
                    cur.execute(
                        "INSERT INTO borrows (book_id, reader_id, borrowed_at, returned_at) VALUES (?, ?, ?, ?)",
                        (books[3][0], readers[3][0], borrowed_time, None)
                    )
                    # Update book availability
                    cur.execute(
                        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
                        (books[3][0],)
                    )
                
                # Borrow record 5: Currently borrowed (borrowed 3 days ago)
                if len(books) > 4 and len(readers) > 0:
                    borrowed_time = (now - timedelta(days=3)).isoformat()
                    cur.execute(
                        "INSERT INTO borrows (book_id, reader_id, borrowed_at, returned_at) VALUES (?, ?, ?, ?)",
                        (books[4][0], readers[0][0], borrowed_time, None)
                    )
                    # Update book availability
                    cur.execute(
                        "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
                        (books[4][0],)
                    )
                
                # Borrow record 6: Returned (borrowed 60 days ago, returned 55 days ago)
                if len(books) > 5 and len(readers) > 1:
                    borrowed_time = (now - timedelta(days=60)).isoformat()
                    returned_time = (now - timedelta(days=55)).isoformat()
                    cur.execute(
                        "INSERT INTO borrows (book_id, reader_id, borrowed_at, returned_at) VALUES (?, ?, ?, ?)",
                        (books[5][0], readers[1][0], borrowed_time, returned_time)
                    )
        
        self.conn.commit()

    # ---------------------------------------------------------------- auth
    @staticmethod
    def _build_password_hash(password: str, salt: Optional[str] = None) -> str:
        salt = salt or secrets.token_hex(16)
        derived = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
        )
        return f"{salt}${derived.hex()}"

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        has_letter = any(ch.isalpha() for ch in password)
        has_digit = any(ch.isdigit() for ch in password)
        has_special = any(not ch.isalnum() for ch in password)
        if len(password) < 8 or not (has_letter and has_digit and has_special):
            raise ValueError("密码需至少 8 位，并包含字母、数字和特殊字符")

    @staticmethod
    def _verify_password(stored: str, candidate: str) -> bool:
        if "$" not in stored:
            return False
        salt, hashed = stored.split("$", 1)
        check = hashlib.pbkdf2_hmac(
            "sha256", candidate.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return secrets.compare_digest(hashed, check)

    def _insert_user_if_missing(self, username: str, password: str, role: str) -> int:
        cur = self.conn.cursor()
        self._validate_password_strength(password)
        row = cur.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row:
            return int(row["id"])
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, self._build_password_hash(password), role),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def authenticate(self, username: str, password: str) -> Optional[sqlite3.Row]:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row and self._verify_password(row["password"], password):
            return row
        return None

    def _require_role(self, user: sqlite3.Row, allowed_roles: Iterable[str]) -> None:
        if user["role"] not in allowed_roles:
            raise PermissionError(f"当前角色 {user['role']} 无法执行该操作")

    # --------------------------------------------------------- helper lookups
    def _get_or_create_shelf(self, code: str, location: Optional[str] = None) -> int:
        cur = self.conn.cursor()
        row = cur.execute("SELECT id FROM shelves WHERE code = ?", (code,)).fetchone()
        if row:
            return int(row["id"])
        cur.execute(
            "INSERT INTO shelves (code, location) VALUES (?, ?)", (code, location)
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def _get_reader_id_for_user(self, user_id: int) -> Optional[int]:
        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT id FROM readers WHERE user_id = ?", (user_id,)
        ).fetchone()
        return int(row["id"]) if row else None

    # -------------------------------------------------------------- book ops
    def list_books(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT * FROM v_book_inventory ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    def add_book(
        self,
        user: sqlite3.Row,
        *,
        title: str,
        author: Optional[str],
        isbn: Optional[str],
        publisher: Optional[str] = None,
        publication_date: Optional[str] = None,
        shelf_code: Optional[str],
        total_copies: int,
        shelf_location: Optional[str] = None,
    ) -> int:
        self._require_role(user, ("admin",))
        shelf_id = (
            self._get_or_create_shelf(shelf_code, shelf_location)
            if shelf_code
            else None
        )
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO books (isbn, title, author, publisher, publication_date, shelf_id, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (isbn, title, author, publisher, publication_date, shelf_id, total_copies, total_copies),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_book(
        self,
        user: sqlite3.Row,
        book_id: int,
        *,
        title: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        publisher: Optional[str] = None,
        publication_date: Optional[str] = None,
        shelf_code: Optional[str] = None,
        shelf_location: Optional[str] = None,
        total_copies: Optional[int] = None,
    ) -> None:
        self._require_role(user, ("admin",))
        fields = []
        params: List[Any] = []
        cur = self.conn.cursor()
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if author is not None:
            fields.append("author = ?")
            params.append(author)
        if isbn is not None:
            fields.append("isbn = ?")
            params.append(isbn)
        if publisher is not None:
            fields.append("publisher = ?")
            params.append(publisher)
        if publication_date is not None:
            fields.append("publication_date = ?")
            params.append(publication_date)
        if shelf_code is not None:
            shelf_id = self._get_or_create_shelf(shelf_code, shelf_location)
            fields.append("shelf_id = ?")
            params.append(shelf_id)
        if total_copies is not None:
            open_loans_row = cur.execute(
                "SELECT COUNT(1) FROM borrows WHERE book_id = ? AND returned_at IS NULL",
                (book_id,),
            ).fetchone()
            open_loans = open_loans_row[0] if open_loans_row else 0
            if total_copies < open_loans:
                raise ValueError("总册数不能小于当前未归还数量")
            fields.append("total_copies = ?")
            params.append(total_copies)
            adjusted_available = max(0, total_copies - open_loans)
            fields.append("available_copies = ?")
            params.append(adjusted_available)
        if not fields:
            return
        params.append(book_id)
        query = "UPDATE books SET " + ", ".join(fields) + " WHERE id = ?"
        cur.execute(query, params)
        self.conn.commit()

    def delete_book(self, user: sqlite3.Row, book_id: int) -> None:
        self._require_role(user, ("admin",))
        cur = self.conn.cursor()
        open_borrow = cur.execute(
            "SELECT 1 FROM borrows WHERE book_id = ? AND returned_at IS NULL",
            (book_id,),
        ).fetchone()
        if open_borrow:
            raise ValueError("存在未归还记录，无法删除该图书")
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

    # ------------------------------------------------------------ reader ops
    def list_readers(self, user: sqlite3.Row) -> List[Dict[str, Any]]:
        self._require_role(user, ("admin", "operator"))
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT readers.id, readers.name, readers.age, readers.gender, readers.address, users.username, users.role
            FROM readers
            LEFT JOIN users ON users.id = readers.user_id
            ORDER BY readers.id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def add_reader(
        self,
        user: sqlite3.Row,
        *,
        name: str,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> int:
        self._require_role(user, ("admin",))
        cur = self.conn.cursor()
        user_id = None
        if username:
            if not password:
                raise ValueError("创建账户需要同时提供密码")
            self._validate_password_strength(password)
            existing = cur.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                raise ValueError("该用户名已存在")
            user_id = self._insert_user_if_missing(username, password, "borrower")
        cur.execute(
            "INSERT INTO readers (name, age, gender, address, user_id) VALUES (?, ?, ?, ?, ?)", 
            (name, age, gender, address, user_id)
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_reader(
        self,
        user: sqlite3.Row,
        reader_id: int,
        *,
        name: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
    ) -> None:
        self._require_role(user, ("admin",))
        fields = []
        params: List[Any] = []
        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if age is not None:
            fields.append("age = ?")
            params.append(age)
        if gender is not None:
            fields.append("gender = ?")
            params.append(gender)
        if address is not None:
            fields.append("address = ?")
            params.append(address)
        if not fields:
            return
        params.append(reader_id)
        cur = self.conn.cursor()
        query = "UPDATE readers SET " + ", ".join(fields) + " WHERE id = ?"
        cur.execute(query, params)
        self.conn.commit()

    def delete_reader(self, user: sqlite3.Row, reader_id: int) -> None:
        self._require_role(user, ("admin",))
        cur = self.conn.cursor()
        open_borrow = cur.execute(
            "SELECT 1 FROM borrows WHERE reader_id = ? AND returned_at IS NULL",
            (reader_id,),
        ).fetchone()
        if open_borrow:
            raise ValueError("该读者存在未归还记录，暂不能删除")
        cur.execute("DELETE FROM readers WHERE id = ?", (reader_id,))
        self.conn.commit()

    # ----------------------------------------------------------- borrow ops
    def list_borrows(self, user: sqlite3.Row) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if user["role"] == "borrower":
            reader_id = self._get_reader_id_for_user(user["id"])
            if reader_id is None:
                return []
            rows = cur.execute(
                """
                SELECT borrow_id, book_id, book_title, book_author, reader_name, reader_id, borrowed_at, returned_at
                FROM v_borrow_history
                WHERE reader_id = ?
                ORDER BY borrow_id DESC
                """,
                (reader_id,),
            ).fetchall()
        else:
            rows = cur.execute(
                """
                SELECT borrow_id, book_id, book_title, book_author, reader_name, reader_id, borrowed_at, returned_at
                FROM v_borrow_history
                ORDER BY borrow_id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def borrow_book(
        self,
        user: sqlite3.Row,
        *,
        book_id: int,
        reader_id: int,
    ) -> int:
        self._require_role(user, ("admin", "operator"))
        cur = self.conn.cursor()
        book = cur.execute(
            "SELECT available_copies FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        reader = cur.execute(
            "SELECT 1 FROM readers WHERE id = ?", (reader_id,)
        ).fetchone()
        if not book:
            raise ValueError("图书不存在")
        if not reader:
            raise ValueError("读者不存在")
        if int(book["available_copies"]) <= 0:
            raise ValueError("该图书当前无库存")
        cur.execute(
            """
            INSERT INTO borrows (book_id, reader_id, borrowed_at)
            VALUES (?, ?, ?)
            """,
            (book_id, reader_id, datetime.now(timezone.utc).isoformat()),
        )
        cur.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id = ?",
            (book_id,),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def return_book(self, user: sqlite3.Row, borrow_id: int) -> None:
        self._require_role(user, ("admin", "operator"))
        cur = self.conn.cursor()
        borrow = cur.execute(
            "SELECT book_id, returned_at FROM borrows WHERE id = ?", (borrow_id,)
        ).fetchone()
        if not borrow:
            raise ValueError("借阅记录不存在")
        if borrow["returned_at"] is not None:
            raise ValueError("该记录已经归还")
        cur.execute(
            "UPDATE borrows SET returned_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), borrow_id),
        )
        cur.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (borrow["book_id"],),
        )
        self.conn.commit()
