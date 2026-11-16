"""Simulated role B: service; simulated role C: form-field validation."""
import unittest
from unittest.mock import Mock

from library import BookService, DuplicateISBNError, SqliteBookRepository, ValidationError
from library.services import DuplicateISBNError as ServiceDuplicateISBNError
from library.services import ValidationError as ServiceValidationError


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = SqliteBookRepository(":memory:")
        self.addCleanup(self.repo.close)
        self.repo.initialize()
        self.service = BookService(self.repo)


class RoleBServiceTests(ServiceTestCase):
    def test_add_trims_fields_and_lists_book(self):
        # Arrange
        title, author, isbn = "  Dune  ", "  Frank Herbert  ", "978-0-441-17271-9"
        # Act
        book = self.service.add_book(title, author, isbn)
        # Assert
        self.assertEqual((book.title, book.author, book.isbn),
                         ("Dune", "Frank Herbert", "9780441172719"))
        self.assertEqual(self.service.list_books(), [book])

    def test_duplicate_isbn_including_normalization(self):
        # Arrange
        first = self.service.add_book("Dune", "Frank Herbert", "9780441172719")
        # Act / Assert
        for isbn in ("9780441172719", "978-0-441-17271-9", " 978 0 441 17271 9 "):
            with self.subTest(isbn=isbn), self.assertRaises(DuplicateISBNError):
                self.service.add_book("Another title", "Another author", isbn)
        self.assertEqual(self.service.list_books(), [first])

    def test_isbn10_with_lowercase_x_is_supported_and_unique(self):
        # Arrange
        isbn = "0-8044-2957-x"
        # Act
        book = self.service.add_book("Title", "Author", isbn)
        # Assert
        self.assertEqual(book.isbn, "080442957X")
        with self.assertRaises(DuplicateISBNError):
            self.service.add_book("Title", "Author", "080442957X")

    def test_exception_exports_are_the_same_value_errors(self):
        # Arrange
        errors = (ValidationError, DuplicateISBNError)
        # Act
        aliases = (ServiceValidationError, ServiceDuplicateISBNError)
        # Assert
        self.assertEqual(errors, aliases)
        self.assertTrue(all(issubclass(error, ValueError) for error in errors))

    def test_list_books_delegates_to_repository(self):
        # Arrange
        repo = Mock()
        repo.list_all.return_value = []
        service = BookService(repo)
        # Act
        books = service.list_books()
        # Assert
        self.assertEqual(books, [])
        repo.list_all.assert_called_once_with()


class RoleCFormValidationTests(ServiceTestCase):
    def test_blank_and_non_string_fields_are_rejected(self):
        # Arrange
        defaults = ["Title", "Author", "9780441172719"]
        # Act / Assert
        for field in range(3):
            for invalid in ("", " \t\n", None, 123):
                values = defaults.copy()
                values[field] = invalid
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValidationError):
                    self.service.add_book(*values)
        self.assertEqual(self.service.list_books(), [])

    def test_maximum_lengths_are_accepted(self):
        # Arrange
        title, author = "T" * 255, "A" * 150
        # Act
        book = self.service.add_book(title, author, "9780441172719")
        # Assert
        self.assertEqual(book.title, title)
        self.assertEqual(book.author, author)

    def test_overlong_fields_are_rejected(self):
        # Arrange
        cases = [("T" * 256, "Author", "9780441172719"),
                 ("Title", "A" * 151, "9780441172719"),
                 ("Title", "Author", " " * 52 + "9780441172719")]
        # Act / Assert
        for fields in cases:
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                self.service.add_book(*fields)
        self.assertEqual(self.service.list_books(), [])

    def test_bad_isbn_shapes_and_checksums_are_rejected(self):
        # Arrange
        invalids = ("9780441172710", "0804429570", "123", "abcdefghij",
                    "978044117271X", "X804429570", "９７８０４４１１７２７１９",
                    "978/0/441/17271/9", "0000000000000")
        # Act / Assert
        for isbn in invalids:
            with self.subTest(isbn=isbn), self.assertRaises(ValidationError):
                self.service.add_book("Title", "Author", isbn)
        self.assertEqual(self.service.list_books(), [])

    def test_invalid_input_never_calls_repository(self):
        # Arrange
        repo = Mock()
        service = BookService(repo)
        # Act / Assert
        with self.assertRaises(ValidationError):
            service.add_book(" ", "Author", "9780441172719")
        repo.add.assert_not_called()
