CREATE TABLE books (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isbn VARCHAR(13) NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150) NOT NULL,
    publisher VARCHAR(150),
    published_year SMALLINT,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ràng buộc duy nhất cho ISBN
    CONSTRAINT uq_books_isbn UNIQUE (isbn),
    -- Ràng buộc kiểm tra định dạng ISBN chỉ gồm 10 hoặc 13 ký tự (tùy chọn nâng cao)
    CONSTRAINT chk_books_isbn_length CHECK (LENGTH(isbn) IN (10, 13))
);