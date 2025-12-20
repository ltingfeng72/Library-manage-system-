import argparse
import getpass
import json
import os
import sqlite3
from typing import Any, Dict, List

from library_system import LibrarySystem


def _print_rows(rows: List[Dict[str, Any]]) -> None:
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def _require_user(system: LibrarySystem, args: argparse.Namespace) -> sqlite3.Row:
    if not args.username:
        raise SystemExit("Username is required (--username)")
    password = args.password or os.getenv("LIBSYS_PASSWORD")
    if not password:
        password = getpass.getpass("Password: ")
    user = system.authenticate(args.username, password)
    if not user:
        raise SystemExit("Invalid username or password")
    return user


def main() -> None:
    parser = argparse.ArgumentParser(
        description="简易图书管理系统（包含权限与视图）"
    )
    parser.add_argument(
        "--db", default="library.db", help="SQLite 数据库文件路径（默认 library.db）"
    )
    parser.add_argument("--username", help="登录用户名")
    parser.add_argument(
        "--password", help="登录密码（可用环境变量 LIBSYS_PASSWORD 或交互输入）"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="初始化数据库结构并插入示例数据")
    sub.add_parser("list-books", help="查看图书库存（所有角色可用）")

    add_book = sub.add_parser("add-book", help="新增图书（管理员）")
    add_book.add_argument("--title", required=True)
    add_book.add_argument("--author")
    add_book.add_argument("--isbn")
    add_book.add_argument("--publisher")
    add_book.add_argument("--publication-date")
    add_book.add_argument("--shelf-code")
    add_book.add_argument("--shelf-location")
    add_book.add_argument("--copies", type=int, default=1)

    update_book = sub.add_parser("update-book", help="更新图书（管理员）")
    update_book.add_argument("--book-id", type=int, required=True)
    update_book.add_argument("--title")
    update_book.add_argument("--author")
    update_book.add_argument("--isbn")
    update_book.add_argument("--publisher")
    update_book.add_argument("--publication-date")
    update_book.add_argument("--shelf-code")
    update_book.add_argument("--shelf-location")
    update_book.add_argument("--copies", type=int)

    delete_book = sub.add_parser("delete-book", help="删除图书（管理员）")
    delete_book.add_argument("--book-id", type=int, required=True)

    sub.add_parser("list-readers", help="查看读者（管理员）")

    add_reader = sub.add_parser("add-reader", help="新增读者（管理员）")
    add_reader.add_argument("--name", required=True)
    add_reader.add_argument("--age", type=int)
    add_reader.add_argument("--gender")
    add_reader.add_argument("--address")
    add_reader.add_argument("--reader-username", dest="reader_username")
    add_reader.add_argument("--reader-password", dest="reader_password")

    update_reader = sub.add_parser("update-reader", help="修改读者（管理员）")
    update_reader.add_argument("--reader-id", type=int, required=True)
    update_reader.add_argument("--name")
    update_reader.add_argument("--age", type=int)
    update_reader.add_argument("--gender")
    update_reader.add_argument("--address")

    delete_reader = sub.add_parser("delete-reader", help="删除读者（管理员）")
    delete_reader.add_argument("--reader-id", type=int, required=True)

    borrow_cmd = sub.add_parser("borrow", help="借书（管理员/操作员）")
    borrow_cmd.add_argument("--book-id", type=int, required=True)
    borrow_cmd.add_argument("--reader-id", type=int, required=True)

    return_cmd = sub.add_parser("return", help="还书（管理员/操作员）")
    return_cmd.add_argument("--borrow-id", type=int, required=True)

    sub.add_parser("list-borrows", help="查看借阅记录（按权限筛选）")

    args = parser.parse_args()
    system = LibrarySystem(args.db)
    system.initialize()

    try:
        if args.command == "init-db":
            print("数据库初始化完成，内置账户：admin/operator/reader。默认密码见 README。")
            return

        # commands that require authentication
        user = _require_user(system, args)

        if args.command == "list-books":
            _print_rows(system.list_books())
        elif args.command == "add-book":
            book_id = system.add_book(
                user,
                title=args.title,
                author=args.author,
                isbn=args.isbn,
                publisher=getattr(args, 'publisher', None),
                publication_date=getattr(args, 'publication_date', None),
                shelf_code=args.shelf_code,
                shelf_location=args.shelf_location,
                total_copies=args.copies,
            )
            print(f"新增图书成功，ID={book_id}")
        elif args.command == "update-book":
            system.update_book(
                user,
                args.book_id,
                title=args.title,
                author=args.author,
                isbn=args.isbn,
                publisher=getattr(args, 'publisher', None),
                publication_date=getattr(args, 'publication_date', None),
                shelf_code=args.shelf_code,
                shelf_location=args.shelf_location,
                total_copies=args.copies,
            )
            print("图书信息已更新")
        elif args.command == "delete-book":
            system.delete_book(user, args.book_id)
            print("图书已删除")
        elif args.command == "list-readers":
            _print_rows(system.list_readers(user))
        elif args.command == "add-reader":
            password = args.reader_password
            if args.reader_username and not password:
                password = getpass.getpass("New user password: ")
            reader_id = system.add_reader(
                user,
                name=args.name,
                age=getattr(args, 'age', None),
                gender=getattr(args, 'gender', None),
                address=getattr(args, 'address', None),
                username=args.reader_username,
                password=password,
            )
            print(f"新增读者成功，ID={reader_id}")
        elif args.command == "update-reader":
            system.update_reader(
                user, 
                args.reader_id, 
                name=args.name,
                age=getattr(args, 'age', None),
                gender=getattr(args, 'gender', None),
                address=getattr(args, 'address', None)
            )
            print("读者信息已更新")
        elif args.command == "delete-reader":
            system.delete_reader(user, args.reader_id)
            print("读者已删除")
        elif args.command == "borrow":
            borrow_id = system.borrow_book(
                user, book_id=args.book_id, reader_id=args.reader_id
            )
            print(f"借阅成功，借阅记录ID={borrow_id}")
        elif args.command == "return":
            system.return_book(user, args.borrow_id)
            print("归还成功")
        elif args.command == "list-borrows":
            _print_rows(system.list_borrows(user))
        else:
            parser.error("未知命令")
    except Exception as exc:  # pragma: no cover - defensive user feedback
        print(f"Error: {exc}")
        raise SystemExit(1)
    finally:
        system.close()


if __name__ == "__main__":
    main()
