"""Book creation validation and the public service interface."""
from typing import Protocol

from .models import Book, DuplicateISBNError, ValidationError, normalize_isbn

__all__ = ["BookService", "ValidationError", "DuplicateISBNError"]


class BookRepository(Protocol):
    def add(self, title: str, author: str, isbn: str) -> Book: ...
    def exists_by_isbn(self, isbn: str) -> bool: ...
    def list_all(self) -> list[Book]: ...


class BookService:
    def __init__(self, repo: BookRepository):
        self._repo = repo

    @staticmethod
    def _text(value: str, name: str, limit: int) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{name} must be a nonempty string.")
        value = value.strip()
        if len(value) > limit:
            raise ValidationError(f"{name} must be at most {limit} characters.")
        return value

    def add_book(self, title: str, author: str, isbn: str) -> Book:
        title = self._text(title, "Title", 255)
        author = self._text(author, "Author", 150)
        canonical = normalize_isbn(isbn)
        # Repository UNIQUE enforcement also covers concurrent service calls.
        return self._repo.add(title, author, canonical)

    def list_books(self) -> list[Book]:
        return self._repo.list_all()
