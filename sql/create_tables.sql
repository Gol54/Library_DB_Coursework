-- 1. Таблица Тематики
CREATE TABLE topics (
    topic_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE -- Ограничение UNIQUE
);

-- 2. Таблица Издательства
CREATE TABLE publishers (
    publisher_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    city VARCHAR(100) DEFAULT 'Москва' -- Ограничение DEFAULT
);

-- 3. Таблица Библиотеки
CREATE TABLE libraries (
    library_id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address TEXT
);

-- 4. Таблица Книги
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    library_id INT REFERENCES libraries(library_id), -- FOREIGN KEY
    topic_id INT REFERENCES topics(topic_id),
    publisher_id INT REFERENCES publishers(publisher_id),
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150),
    release_year INT CHECK (release_year > 0 AND release_year <= 2026), -- CHECK
    quantity INT DEFAULT 1 CHECK (quantity >= 0)
);

-- 5. Таблица Читатели
CREATE TABLE readers (
    reader_id SERIAL PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,    -- Фамилия
    first_name VARCHAR(50) NOT NULL,   -- Имя
    patronymic VARCHAR(50),            -- Отчество (может быть пустым)
    address TEXT,
    phone VARCHAR(20) UNIQUE,          -- Ограничение UNIQUE 
    birth_date DATE CHECK (birth_date > '1900-01-01') -- Ограничение CHECK 
);

-- 6. Таблица Абонемент (Связь 1:М к Книгам и Читателям)
CREATE TABLE subscriptions (
    sub_id SERIAL PRIMARY KEY,
    library_id INT REFERENCES libraries(library_id),
    book_id INT REFERENCES books(book_id),
    reader_id INT REFERENCES readers(reader_id),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    return_date DATE,
    deposit DECIMAL(10, 2) DEFAULT 0 CHECK (deposit >= 0),
    CONSTRAINT check_dates CHECK (return_date >= issue_date) -- Составной CHECK
);