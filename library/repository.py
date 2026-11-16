"""Persistent SQLite book storage; initialize before calling data methods."""
from pathlib import Path
import sqlite3

from .models import Book, DuplicateISBNError, normalize_isbn


class SqliteBookRepository:
    """Own one SQLite connection; database may be a path or ':memory:'.

    Each add commits atomically. Separate instances may share a database;
    SQLite's unique constraint is the authority for duplicate detection.
    """

    def __init__(self, database):
        self._connection = sqlite3.connect(database)

    def initialize(self) -> None:
        schema = Path(__file__).resolve().parent.parent / "schema.sql"
        with self._connection:
            self._connection.executescript(schema.read_text(encoding="utf-8"))

    def add(self, title: str, author: str, isbn: str) -> Book:
        canonical = normalize_isbn(isbn)
        try:
            with self._connection:
                cursor = self._connection.execute(
                    "INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)",
                    (title, author, canonical),
                )
                book = Book(cursor.lastrowid, title, author, canonical)
        except sqlite3.IntegrityError as exc:
            if getattr(exc, "sqlite_errorname", "") == "SQLITE_CONSTRAINT_UNIQUE" or str(exc) == "UNIQUE constraint failed: books.isbn":
                raise DuplicateISBNError("A book with this ISBN already exists.") from exc
            raise
        return book

    def exists_by_isbn(self, isbn: str) -> bool:
        canonical = normalize_isbn(isbn)
        row = self._connection.execute(
            "SELECT 1 FROM books WHERE isbn = ?", (canonical,)
        ).fetchone()
        return row is not None

    def list_all(self) -> list[Book]:
        rows = self._connection.execute(
            "SELECT id, title, author, isbn FROM books ORDER BY id"
        ).fetchall()
        return [Book(*row) for row in rows]

    def close(self) -> None:
        self._connection.close()
