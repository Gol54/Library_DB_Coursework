-- Индекс для быстрого поиска книг по названию
CREATE INDEX idx_book_title ON books(title);

-- Индекс для поиска читателей по фамилии
CREATE INDEX idx_reader_last_name ON readers(last_name);

--представления
CREATE VIEW v_available_books AS
SELECT title, author, quantity
FROM books
WHERE quantity > 0;

--Объединяет данные о книге, её жанре (тематике) и издательстве.

CREATE VIEW v_full_book_info AS
SELECT b.title, b.author, t.name AS topic, p.name AS publisher, l.name AS library
FROM books b
JOIN topics t ON b.topic_id = t.topic_id
JOIN publishers p ON b.publisher_id = p.publisher_id
JOIN libraries l ON b.library_id = l.library_id;


--Считает количество книг в каждой тематике, но показывает только те жанры, где больше 5 книг.
CREATE VIEW v_popular_topics AS
SELECT t.name AS topic_name, SUM(b.quantity) AS total_books
FROM topics t
JOIN books b ON t.topic_id = b.topic_id
GROUP BY t.name
HAVING SUM(b.quantity) > 5;




--триогер 

CREATE OR REPLACE FUNCTION update_book_quantity()
RETURNS TRIGGER AS $$
BEGIN
    -- При выдаче книги (INSERT в subscriptions) уменьшаем остаток в books
    UPDATE books 
    SET quantity = quantity - 1 
    WHERE book_id = NEW.book_id;
    
    -- Проверка: если книг не осталось, выдаем ошибку
    IF (SELECT quantity FROM books WHERE book_id = NEW.book_id) < 0 THEN
        RAISE EXCEPTION 'Этой книги нет в наличии!';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_after_subscription
AFTER INSERT ON subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_book_quantity();
