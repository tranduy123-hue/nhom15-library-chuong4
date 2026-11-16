-- Canonical ISBN values are validated and normalized by the repository.
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 255),
    author TEXT NOT NULL CHECK (length(trim(author)) BETWEEN 1 AND 150),
    isbn TEXT NOT NULL UNIQUE CHECK (
        length(isbn) IN (10, 13)
        AND isbn NOT GLOB '*[^0-9X]*'
        AND instr(isbn, '-') = 0
    )
);
