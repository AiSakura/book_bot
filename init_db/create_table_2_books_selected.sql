CREATE TABLE IF NOT EXISTS books_selected (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    selection_time TIMESTAMP NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books (id)
);