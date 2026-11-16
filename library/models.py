"""Shared book model, domain errors, and canonical ISBN validation."""
from dataclasses import dataclass
import re


class ValidationError(ValueError):
    """A supplied book field is invalid."""


class DuplicateISBNError(ValueError):
    """A book already has this normalized ISBN."""


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str
    isbn: str


def normalize_isbn(isbn: str) -> str:
    """Remove whitespace/hyphens and validate an ISBN-10 or ISBN-13 checksum.

    ISBN-10 and its ISBN-13 equivalent remain distinct identifiers.
    """
    if not isinstance(isbn, str) or not isbn.strip():
        raise ValidationError("ISBN must be a nonempty string.")
    if len(isbn) > 64:
        raise ValidationError("ISBN input must be at most 64 characters.")
    normalized = re.sub(r"[\s-]", "", isbn).upper()
    if re.fullmatch(r"[0-9]{9}[0-9X]", normalized):
        digits = [int(c) if c != "X" else 10 for c in normalized]
        valid = sum((10 - i) * digit for i, digit in enumerate(digits)) % 11 == 0
    elif re.fullmatch(r"97[89][0-9]{10}", normalized):
        valid = sum(int(c) * (1 if i % 2 == 0 else 3)
                    for i, c in enumerate(normalized)) % 10 == 0
    else:
        valid = False
    if not valid:
        raise ValidationError("ISBN must be a valid ISBN-10 or ISBN-13 with a correct checksum.")
    return normalized
