# database.py
import psycopg2
from psycopg2 import OperationalError, IntegrityError
from config import DB_CONFIG
from datetime import datetime


class Database:

    def get_all_artists_for_select(self):
        """Получить список артистов для выпадающего списка"""
        query = "SELECT artist_id, name FROM artists ORDER BY name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_all_genres_for_select(self):
        """Получить список жанров для выпадающего списка"""
        query = "SELECT genre_id, genre_name FROM genres ORDER BY genre_name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def add_release_with_artists_and_genres(self, release_data, artist_ids, genre_ids):
        """Добавить релиз с артистами и жанрами"""
        cursor = self.connection.cursor()

        try:
            # Добавляем релиз
            query = """
            INSERT INTO releases (
                title, release_year, original_year, label, 
                country, catalog_code, total_duration, total_tracks
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING release_id
            """
            cursor.execute(query, release_data)
            release_id = cursor.fetchone()[0]

            # Добавляем артистов
            for artist_id in artist_ids:
                cursor.execute(
                    "INSERT INTO release_artists (release_id, artist_id) VALUES (%s, %s)",
                    (release_id, artist_id)
                )

            # Добавляем жанры
            for genre_id in genre_ids:
                cursor.execute(
                    "INSERT INTO release_genres (release_id, genre_id) VALUES (%s, %s)",
                    (release_id, genre_id)
                )

            self.connection.commit()
            return release_id

        except Exception as e:
            self.connection.rollback()
            raise e
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            return True
        except OperationalError as e:
            print(f"Ошибка подключения: {e}")
            return False

    # ===== CRUD для Физических носителей =====
    def get_all_media_items(self, search=None):
        query = """
        SELECT 
            mi.media_item_id,
            mi.catalog_number,
            r.title as album_title,
            a.name as artist_name,
            mt.type_name as format,
            mi.condition,
            mi.purchase_price,
            TO_CHAR(mi.purchase_date, 'DD.MM.YYYY') as purchase_date,
            mi.storage_location
        FROM media_items mi
        LEFT JOIN releases r ON mi.release_id = r.release_id
        LEFT JOIN media_types mt ON mi.media_type_id = mt.media_type_id
        LEFT JOIN release_artists ra ON r.release_id = ra.release_id
        LEFT JOIN artists a ON ra.artist_id = a.artist_id
        WHERE 1=1
        """
        params = []

        if search:
            query += """
                AND (mi.catalog_number ILIKE %s 
                OR r.title ILIKE %s 
                OR a.name ILIKE %s
                OR mt.type_name ILIKE %s)
            """
            search_term = f"%{search}%"
            params = [search_term, search_term, search_term, search_term]

        query += " ORDER BY r.title"

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def add_media_item(self, data):
        query = """
        INSERT INTO media_items (
            catalog_number, media_type_id, release_id, 
            condition, purchase_price, purchase_date, 
            storage_location, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING media_item_id
        """
        cursor = self.connection.cursor()
        cursor.execute(query, data)
        self.connection.commit()
        return cursor.fetchone()[0]

    def update_media_item(self, item_id, data):
        query = """
        UPDATE media_items SET
            catalog_number = %s,
            media_type_id = %s,
            release_id = %s,
            condition = %s,
            purchase_price = %s,
            purchase_date = %s,
            storage_location = %s,
            notes = %s
        WHERE media_item_id = %s
        """
        cursor = self.connection.cursor()
        cursor.execute(query, data + (item_id,))
        self.connection.commit()

    def delete_media_item(self, item_id):
        query = "DELETE FROM media_items WHERE media_item_id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (item_id,))
        self.connection.commit()

    # ===== CRUD для Артистов =====
    def get_all_artists(self, search=None):
        query = "SELECT artist_id, name, artist_type, country FROM artists"
        params = []

        if search:
            query += " WHERE name ILIKE %s"
            params = [f"%{search}%"]

        query += " ORDER BY name"

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def add_artist(self, name, artist_type, country):
        query = "INSERT INTO artists (name, artist_type, country) VALUES (%s, %s, %s) RETURNING artist_id"
        cursor = self.connection.cursor()
        cursor.execute(query, (name, artist_type, country))
        self.connection.commit()
        return cursor.fetchone()[0]

    def update_artist(self, artist_id, name, artist_type, country):
        query = "UPDATE artists SET name = %s, artist_type = %s, country = %s WHERE artist_id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (name, artist_type, country, artist_id))
        self.connection.commit()

    def delete_artist(self, artist_id):
        query = "DELETE FROM artists WHERE artist_id = %s"
        cursor = self.connection.cursor()
        cursor.execute(query, (artist_id,))
        self.connection.commit()

    # ===== CRUD для Релизов =====
    def get_all_releases(self, search=None):
        query = """
        SELECT r.release_id, r.title, r.release_year, r.label, 
               r.country, a.name as artist_name
        FROM releases r
        LEFT JOIN release_artists ra ON r.release_id = ra.release_id
        LEFT JOIN artists a ON ra.artist_id = a.artist_id
        """
        params = []

        if search:
            query += " WHERE r.title ILIKE %s OR a.name ILIKE %s"
            params = [f"%{search}%", f"%{search}%"]

        query += " ORDER BY r.title"

        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def add_release(self, data):
        query = """
        INSERT INTO releases (
            title, release_year, original_year, label, 
            country, catalog_code, total_duration, total_tracks
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING release_id
        """
        cursor = self.connection.cursor()
        cursor.execute(query, data)
        self.connection.commit()
        return cursor.fetchone()[0]

    # ===== CRUD для Жанров =====
    def get_all_genres(self):
        query = "SELECT genre_id, genre_name FROM genres ORDER BY genre_name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    # ===== CRUD для Типов носителей =====
    def get_all_media_types(self):
        query = "SELECT media_type_id, type_name, description FROM media_types ORDER BY type_name"
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    # ===== Отчеты =====
    def get_collection_statistics(self):
        cursor = self.connection.cursor()

        # Общая статистика
        stats = {}

        # Количество по форматам
        cursor.execute("""
            SELECT mt.type_name, COUNT(*)
            FROM media_items mi
            JOIN media_types mt ON mi.media_type_id = mt.media_type_id
            GROUP BY mt.type_name
            ORDER BY COUNT(*) DESC
        """)
        stats['by_format'] = cursor.fetchall()

        # Количество по состоянию
        cursor.execute("""
            SELECT condition, COUNT(*)
            FROM media_items
            GROUP BY condition
            ORDER BY COUNT(*) DESC
        """)
        stats['by_condition'] = cursor.fetchall()

        # Общая стоимость
        cursor.execute("SELECT SUM(purchase_price) FROM media_items")
        stats['total_value'] = cursor.fetchone()[0] or 0

        # Количество релизов
        cursor.execute("SELECT COUNT(DISTINCT release_id) FROM media_items")
        stats['releases_count'] = cursor.fetchone()[0]

        # Количество артистов
        cursor.execute(
            "SELECT COUNT(DISTINCT a.artist_id) FROM artists a JOIN release_artists ra ON a.artist_id = ra.artist_id")
        stats['artists_count'] = cursor.fetchone()[0]

        # По годам покупки
        cursor.execute("""
            SELECT EXTRACT(YEAR FROM purchase_date) as year, 
                   COUNT(*), 
                   SUM(purchase_price)
            FROM media_items
            WHERE purchase_date IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM purchase_date)
            ORDER BY year DESC
        """)
        stats['by_year'] = cursor.fetchall()

        return stats

    def get_artist_report(self, artist_id=None):
        cursor = self.connection.cursor()

        if artist_id:
            query = """
            SELECT 
                r.title,
                mt.type_name,
                mi.condition,
                mi.purchase_price,
                TO_CHAR(mi.purchase_date, 'DD.MM.YYYY')
            FROM media_items mi
            JOIN releases r ON mi.release_id = r.release_id
            JOIN media_types mt ON mi.media_type_id = mt.media_type_id
            JOIN release_artists ra ON r.release_id = ra.release_id
            WHERE ra.artist_id = %s
            ORDER BY r.title
            """
            cursor.execute(query, (artist_id,))
        else:
            query = """
            SELECT 
                a.name,
                COUNT(DISTINCT r.release_id) as releases_count,
                COUNT(mi.media_item_id) as items_count,
                SUM(mi.purchase_price) as total_value
            FROM artists a
            LEFT JOIN release_artists ra ON a.artist_id = ra.artist_id
            LEFT JOIN releases r ON ra.release_id = r.release_id
            LEFT JOIN media_items mi ON r.release_id = mi.release_id
            GROUP BY a.artist_id, a.name
            ORDER BY a.name
            """
            cursor.execute(query)

        return cursor.fetchall()

    def get_format_report(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT 
                mt.type_name,
                COUNT(mi.media_item_id) as count,
                AVG(mi.purchase_price) as avg_price,
                SUM(mi.purchase_price) as total_value,
                MIN(mi.purchase_date) as first_purchase,
                MAX(mi.purchase_date) as last_purchase
            FROM media_types mt
            LEFT JOIN media_items mi ON mt.media_type_id = mi.media_type_id
            GROUP BY mt.media_type_id, mt.type_name
            ORDER BY COUNT(mi.media_item_id) DESC
        """)
        return cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()
