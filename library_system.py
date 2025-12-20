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
                user_id INTEGER UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT,
                title TEXT NOT NULL,
                author TEXT,
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
                    shelves.code AS shelf_code,
                    books.available_copies,
                    books.total_copies
                FROM books
                LEFT JOIN shelves ON shelves.id = books.shelf_id;

            DROP VIEW IF EXISTS v_borrow_history;
            CREATE VIEW v_borrow_history AS
                SELECT
                    borrows.id AS borrow_id,
                    books.title,
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
        _ = self._insert_user_if_missing("admin", "Admin!2345", "admin")
        _ = self._insert_user_if_missing("operator", "Operator!2345", "operator")
        borrower_id = self._insert_user_if_missing("reader", "Reader!2345", "borrower")

        main_shelf = self._get_or_create_shelf("A1", "综合区")
        _ = self._get_or_create_shelf("B1", "外文区")

        cur.execute(
            "INSERT OR IGNORE INTO readers (name, user_id) VALUES (?, ?)",
            ("示例读者", borrower_id),
        )

        if not cur.execute("SELECT 1 FROM books LIMIT 1").fetchone():
            cur.execute(
                """
                INSERT INTO books (isbn, title, author, shelf_id, total_copies, available_copies)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "9787020000000",
                    "示例图书",
                    "佚名",
                    main_shelf,
                    3,
                    3,
                ),
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
            INSERT INTO books (isbn, title, author, shelf_id, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (isbn, title, author, shelf_id, total_copies, total_copies),
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
            SELECT readers.id, readers.name, users.username, users.role
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
            "INSERT INTO readers (name, user_id) VALUES (?, ?)", (name, user_id)
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_reader(
        self,
        user: sqlite3.Row,
        reader_id: int,
        *,
        name: Optional[str] = None,
    ) -> None:
        self._require_role(user, ("admin",))
        if name is None:
            return
        cur = self.conn.cursor()
        cur.execute("UPDATE readers SET name = ? WHERE id = ?", (name, reader_id))
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
                SELECT borrow_id, title, reader_name, borrowed_at, returned_at
                FROM v_borrow_history
                WHERE reader_id = ?
                ORDER BY borrow_id DESC
                """,
                (reader_id,),
            ).fetchall()
        else:
            rows = cur.execute(
                "SELECT * FROM v_borrow_history ORDER BY borrow_id DESC"
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
