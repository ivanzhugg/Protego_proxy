import sqlite3

class ExcelDatabase:
    def __init__(self):
        self.file_path = "/protego_vpn/ui_bot/Bd/slon.db"
        self._create_table()

    def _connect(self):
        """Создаёт новое соединение с базой данных."""
        return sqlite3.connect(self.file_path)

    def _create_table(self):
        """Создает таблицу, если её нет."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                tg_id INTEGER UNIQUE,
                rate INTEGER,
                ref TEXT,
                status INTEGER CHECK(status BETWEEN 0 AND 2)
            )
        ''')
        conn.commit()
        conn.close()

    def save(self):
        """Метод-заглушка (не нужен в SQLite, так как commit вызывается в каждом методе)."""
        pass

    def find_row_index(self, tg_id):
        """Ищет id строки по tg_id."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM data WHERE tg_id = ?", (tg_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def add_row(self, username, tg_id, rate, ref, status):
        """Добавляет новую строку в таблицу."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO data (username, tg_id, rate, ref, status)
            VALUES (?, ?, ?, ?, ?)
        """, (username, tg_id, rate, ref, status))
        conn.commit()
        conn.close()

    def get_row(self, tg_id):
        """Получает элементы строки по tg_id."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data WHERE tg_id = ?", (tg_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def delete_row(self, tg_id):
        """Удаляет строку по tg_id."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM data WHERE tg_id = ?", (tg_id,))
        conn.commit()
        row_deleted = cursor.rowcount > 0
        conn.close()
        return row_deleted

    def update_cell(self, tg_id, column_index, new_value):
        """Обновляет значение в указанной ячейке по tg_id и номеру столбца."""
        columns = ['id', 'username', 'tg_id', 'rate', 'ref', 'status']  # Список колонок в таблице
        
        if column_index < 1 or column_index >= len(columns):
            raise ValueError("Некорректый индекс столбца")
        
        column_name = columns[column_index]
        
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE data SET {column_name} = ? WHERE tg_id = ?
        """, (new_value, tg_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def get_all_tg_ids(self) -> list[int]:
        """
        Возвращает список всех tg_id из таблицы data.
        """
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT tg_id FROM data")
        rows = cursor.fetchall()
        conn.close()
        # превращаем [(tg1,), (tg2,), ...] в [tg1, tg2, ...]
        return [row[0] for row in rows]