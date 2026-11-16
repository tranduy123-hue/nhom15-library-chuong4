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
