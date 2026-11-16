"""Simulated role A: database persistence, query safety, and atomicity."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from library import DuplicateISBNError, SqliteBookRepository, ValidationError


class RoleADatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "books.sqlite3"
        self.repo = SqliteBookRepository(self.database)
        self.addCleanup(self.repo.close)
        self.repo.initialize()

    def test_persistence_after_reopen(self):
        # Arrange
        expected = self.repo.add("Dune", "Frank Herbert", "9780441172719")
        self.repo.close()
        reopened = SqliteBookRepository(self.database)
        self.addCleanup(reopened.close)
        # Act
        reopened.initialize()
        actual = reopened.list_all()
        # Assert
        self.assertEqual(actual, [expected])
        self.assertGreater(expected.id, 0)

    def test_sql_injection_title_is_stored_as_data(self):
        # Arrange
        title = "'); DROP TABLE books; --"
        # Act
        book = self.repo.add(title, "Author", "9780441172719")
        second = self.repo.add("Other", "Author", "9780140328721")
        # Assert
        self.assertEqual(self.repo.list_all(), [book, second])
        self.assertEqual(book.title, title)

    def test_normalized_lookup_and_unique_insert(self):
        # Arrange
        first = self.repo.add("Dune", "Frank Herbert", "978-0-441-17271-9")
        # Act
        exists = self.repo.exists_by_isbn("978 0 441 17271 9")
        # Assert
        self.assertTrue(exists)
        self.assertFalse(self.repo.exists_by_isbn("9780140328721"))
        with self.assertRaises(DuplicateISBNError):
            self.repo.add("Duplicate", "Author", "9780441172719")
        self.assertEqual(self.repo.list_all(), [first])

    def test_unique_constraint_is_present_in_database(self):
        # Arrange
        self.repo.add("Dune", "Frank Herbert", "9780441172719")
        # Act / Assert: bypass repository to exercise the database constraint.
        with closing(sqlite3.connect(self.database)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO books (title, author, isbn) VALUES (?, ?, ?)",
                    ("Duplicate", "Author", "9780441172719"),
                )

    def test_concurrent_duplicate_add_is_atomic(self):
        # Arrange
        barrier = threading.Barrier(2)

        def insert(isbn):
            repo = SqliteBookRepository(self.database)
            try:
                barrier.wait(timeout=5)
                try:
                    repo.add("Dune", "Frank Herbert", isbn)
                    return "added"
                except DuplicateISBNError:
                    return "duplicate"
            finally:
                repo.close()

        # Act
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(insert, ["9780441172719", "978-0-441-17271-9"]))
        # Assert
        self.assertCountEqual(outcomes, ["added", "duplicate"])
        self.assertEqual(len(self.repo.list_all()), 1)

    def test_failed_insert_rolls_back_and_connection_remains_usable(self):
        # Arrange
        self.repo.add("Dune", "Frank Herbert", "9780441172719")
        # Act
        with self.assertRaises(DuplicateISBNError):
            self.repo.add("Duplicate", "Author", "9780441172719")
        second = self.repo.add("Matilda", "Roald Dahl", "9780140328721")
        # Assert
        self.assertEqual(len(self.repo.list_all()), 2)
        self.assertEqual(self.repo.list_all()[-1], second)

    def test_invalid_isbn_is_rejected_without_writing(self):
        # Arrange
        invalid = "9780441172710"
        # Act / Assert
        with self.assertRaises(ValidationError):
            self.repo.add("Title", "Author", invalid)
        self.assertEqual(self.repo.list_all(), [])


class RoleARepositoryEnhancementTests(unittest.TestCase):
    """UT1 (KAN-25): Bổ sung unit test kiểm thử SqliteBookRepository bởi Phan Văn Hào."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "books.sqlite3"
        self.repo = SqliteBookRepository(self.database)
        self.addCleanup(self.repo.close)
        self.repo.initialize()

    def test_empty_repository_returns_empty_list(self):
        # 1. Arrange: repository đã khởi tạo nhưng chưa có sách
        # 2. Act: lấy toàn bộ danh mục sách
        books = self.repo.list_all()
        # 3. Assert: kết quả là danh sách rỗng
        self.assertEqual(books, [])

    def test_add_book_with_max_length_fields_and_retrieve(self):
        # 1. Arrange: sách có độ dài tiêu đề 255 ký tự và tác giả 150 ký tự
        max_title = "A" * 255
        max_author = "B" * 150
        isbn = "9780132350884"
        # 2. Act: lưu sách vào database và kiểm tra tồn tại
        saved_book = self.repo.add(max_title, max_author, isbn)
        exists = self.repo.exists_by_isbn(isbn)
        all_books = self.repo.list_all()
        # 3. Assert: sách được lưu chính xác và tìm thấy bằng exists_by_isbn
        self.assertTrue(exists)
        self.assertEqual(len(all_books), 1)
        self.assertEqual(all_books[0].title, max_title)
        self.assertEqual(all_books[0].author, max_author)
        self.assertEqual(all_books[0].isbn, isbn)

    def test_multiple_books_preserve_incremental_ids(self):
        # 1. Arrange: chuẩn bị 3 cuốn sách khác nhau
        books_data = [
            ("Lập trình Python", "Tác giả 1", "9780441172719"),
            ("Clean Code", "Robert C. Martin", "9780132350884"),
            ("Design Patterns", "GoF", "9780201633610"),
        ]
        # 2. Act: thêm lần lượt vào database
        added = [self.repo.add(t, a, i) for t, a, i in books_data]
        all_books = self.repo.list_all()
        # 3. Assert: ID tự tăng tuần tự và danh sách đầy đủ
        self.assertEqual(len(all_books), 3)
        self.assertTrue(added[0].id < added[1].id < added[2].id)
        self.assertEqual([b.isbn for b in all_books], ["9780441172719", "9780132350884", "9780201633610"])

