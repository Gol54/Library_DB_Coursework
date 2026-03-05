-- Библиотеки
INSERT INTO libraries (name, address) VALUES 
('Центральная библиотека', 'ул. Ленина, 10'),
('Городская библиотека №2', 'пр. Мира, 45'),
('Научный зал', 'ул. Университетская, 1');

-- Тематики (10 категорий)
INSERT INTO topics (name) VALUES 
('Классика'), ('Фантастика'), ('Детектив'), ('История'), 
('Программирование'), ('Психология'), ('Медицина'), 
('Фэнтези'), ('Научпоп'), ('Поэзия');

-- Издательства (10 компаний)
INSERT INTO publishers (name, city) VALUES 
('ЭКСМО', 'Москва'), ('АСТ', 'Москва'), ('Питер', 'Санкт-Петербург'),
('Манн, Иванов и Фербер', 'Москва'), ('Азбука', 'Санкт-Петербург'),
('Просвещение', 'Москва'), ('БХВ', 'Санкт-Петербург'),
('Альпина', 'Москва'), ('Центрполиграф', 'Москва'), ('Никея', 'Москва');



-- Генерируем 50 книг (с большим запасом quantity, чтобы триггер не ругался)
INSERT INTO books (library_id, topic_id, publisher_id, title, author, release_year, quantity)
SELECT (random()*2+1)::int, (random()*5+1)::int, (random()*2+1)::int, 'Книга №'||i, 'Автор '||i, 2020, 100
FROM generate_series(1, 50) s(i);

-- Генерация 50 читателей
INSERT INTO readers (last_name, first_name, patronymic, address, phone, birth_date)
SELECT 
    'Фамилия_' || i, 
    'Имя_' || i, 
    'Отчество_' || i, 
    'Улица Читателей, дом ' || i,
    '+7900' || LPAD(i::text, 7, '0'),
    '1980-01-01'::date + (i || ' days')::interval
FROM generate_series(1, 50) s(i);



INSERT INTO subscriptions (library_id, book_id, reader_id, issue_date, return_date, deposit)
SELECT
    floor(random() * 2 + 1)::int,
    (SELECT book_id FROM books ORDER BY random() LIMIT 1),
    (SELECT reader_id FROM readers ORDER BY random() LIMIT 1),
    CURRENT_DATE - (i || ' days')::interval,
    CURRENT_DATE + (i || ' days')::interval,
    (random() * 500)::decimal(10,2)
FROM generate_series(1, 50) s(i);