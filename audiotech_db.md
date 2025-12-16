```sql
-- База данных для домашней аудиотеки
CREATE TABLE media_types (
    media_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Жанры
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(50) NOT NULL UNIQUE
);

-- Музыкальные релизы
CREATE TABLE releases (
    release_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INTEGER,
    original_year INTEGER,
    label VARCHAR(100),
    country VARCHAR(50),
    catalog_code VARCHAR(50),
    total_duration INTEGER,
    total_tracks INTEGER,
    
    CONSTRAINT check_years 
        CHECK (release_year IS NULL OR (release_year >= 1900 AND release_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1)),
    CONSTRAINT check_original_year 
        CHECK (original_year IS NULL OR (original_year >= 1900 AND original_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1))
);

-- Артисты
CREATE TABLE artists (
    artist_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    artist_type VARCHAR(20),
    country VARCHAR(50)
);

-- Треки
CREATE TABLE tracks (
    track_id SERIAL PRIMARY KEY,
    release_id INTEGER NOT NULL,
    track_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration INTEGER,
    side VARCHAR(10),
    
    CONSTRAINT check_track_number 
        CHECK (track_number > 0),
    
    FOREIGN KEY (release_id) 
        REFERENCES releases(release_id) 
        ON DELETE CASCADE,
    
    CONSTRAINT unique_track_in_release 
        UNIQUE (release_id, track_number)
);

-- Физические экземпляры
CREATE TABLE media_items (
    media_item_id SERIAL PRIMARY KEY,
    catalog_number VARCHAR(100) UNIQUE,
    media_type_id INTEGER NOT NULL,
    release_id INTEGER NOT NULL,
    condition VARCHAR(30),
    purchase_price NUMERIC(10, 2),
    purchase_date DATE,
    storage_location VARCHAR(255),
    notes TEXT,
    
    FOREIGN KEY (media_type_id) 
        REFERENCES media_types(media_type_id) 
        ON DELETE RESTRICT,
    
    FOREIGN KEY (release_id) 
        REFERENCES releases(release_id) 
        ON DELETE CASCADE
);

-- Атрибуты винила
CREATE TABLE vinyl_attributes (
    vinyl_id SERIAL PRIMARY KEY,
    media_item_id INTEGER NOT NULL,
    size VARCHAR(10),
    sides_count INTEGER,
    rpm INTEGER,
    
    FOREIGN KEY (media_item_id) 
        REFERENCES media_items(media_item_id) 
        ON DELETE CASCADE,
    
    CONSTRAINT unique_vinyl_item 
        UNIQUE (media_item_id)
);

-- Связь релизов и артистов
CREATE TABLE release_artists (
    release_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    
    PRIMARY KEY (release_id, artist_id),
    
    FOREIGN KEY (release_id) 
        REFERENCES releases(release_id) 
        ON DELETE CASCADE,
    
    FOREIGN KEY (artist_id) 
        REFERENCES artists(artist_id) 
        ON DELETE CASCADE
);

-- Связь треков и артистов
CREATE TABLE track_artists (
    track_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    
    PRIMARY KEY (track_id, artist_id),
    
    FOREIGN KEY (track_id) 
        REFERENCES tracks(track_id) 
        ON DELETE CASCADE,
    
    FOREIGN KEY (artist_id) 
        REFERENCES artists(artist_id) 
        ON DELETE CASCADE
);

-- Связь релизов и жанров
CREATE TABLE release_genres (
    release_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    
    PRIMARY KEY (release_id, genre_id),
    
    FOREIGN KEY (release_id) 
        REFERENCES releases(release_id) 
        ON DELETE CASCADE,
    
    FOREIGN KEY (genre_id) 
        REFERENCES genres(genre_id) 
        ON DELETE CASCADE
);

-- 3. Вставка тестовых данных

-- Типы носителей
INSERT INTO media_types (type_name, description) VALUES
('Виниловая пластинка', 'Винил'),
('Компакт-диск (CD)', 'CD'),
('Компакт-кассета', 'Кассета');

-- Жанры
INSERT INTO genres (genre_name) VALUES
('Рок'),
('Поп'),
('Джаз'),
('Альтернатива'),
('Прогрессивный рок');

-- Артисты
INSERT INTO artists (name, artist_type, country) VALUES
('Кино', 'Band', 'СССР'),
('Pink Floyd', 'Band', 'Великобритания'),
('Queen', 'Band', 'Великобритания');

-- Релизы
INSERT INTO releases (title, release_year, original_year, label, country, catalog_code) VALUES
('Группа крови', 1988, 1988, 'Мелодия', 'СССР', 'С60 28371 003'),
('The Dark Side of the Moon', 1973, 1973, 'Harvest', 'Великобритания', 'SHVL 804'),
('A Night at the Opera', 1975, 1975, 'EMI', 'Великобритания', 'EMA 767');

-- Треки для Группа крови
INSERT INTO tracks (release_id, track_number, title) VALUES
(1, 1, 'Группа крови'),
(1, 2, 'Война'),
(1, 3, 'Спокойная ночь');

-- Треки для Pink Floyd
INSERT INTO tracks (release_id, track_number, title) VALUES
(2, 1, 'Speak to Me'),
(2, 2, 'Breathe'),
(2, 3, 'On the Run');

-- Треки для Queen
INSERT INTO tracks (release_id, track_number, title) VALUES
(3, 1, 'Death on Two Legs'),
(3, 2, 'Lazing on a Sunday Afternoon'),
(3, 3, 'Bohemian Rhapsody');

-- Физические экземпляры
INSERT INTO media_items (catalog_number, media_type_id, release_id, condition, purchase_price, purchase_date, storage_location) VALUES
('VINYL-001', 1, 1, 'Хорошее', 3500.00, '2022-10-15', 'Полка 1'),
('VINYL-002', 1, 2, 'Коллекционное', 8500.50, '2023-05-20', 'Полка 2'),
('CD-001', 2, 1, 'Новое', 1200.00, '2024-01-10', 'Полка 3');

-- Атрибуты винила
INSERT INTO vinyl_attributes (media_item_id, size, sides_count, rpm) VALUES
(1, '12"', 2, 33),
(2, '12"', 2, 33);

-- Связь релизов и артистов
INSERT INTO release_artists (release_id, artist_id) VALUES
(1, 1), -- Кино - Группа крови
(2, 2), -- Pink Floyd - Dark Side
(3, 3); -- Queen - Night at Opera

-- Связь релизов и жанров
INSERT INTO release_genres (release_id, genre_id) VALUES
(1, 1), -- Группа крови - Рок
(1, 4), -- Группа крови - Альтернатива
(2, 1), -- Dark Side - Рок
(2, 5), -- Dark Side - Прогрессивный рок
(3, 1); -- Queen - Рок

-- 4. Проверочный запрос
SELECT 
    r.title AS "Альбом",
    a.name AS "Исполнитель",
    mt.type_name AS "Формат",
    mi.purchase_price || ' ₽' AS "Цена",
    mi.condition AS "Состояние"
FROM media_items mi
JOIN releases r ON mi.release_id = r.release_id
JOIN media_types mt ON mi.media_type_id = mt.media_type_id
JOIN release_artists ra ON r.release_id = ra.release_id
JOIN artists a ON ra.artist_id = a.artist_id
ORDER BY r.title;
```
