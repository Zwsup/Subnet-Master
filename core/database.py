import sqlite3
import json
from datetime import datetime

class ProjectDatabase:
    def __init__(self, db_name: str = "subnet_projects.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Veritabanı ve projeler tablosu yoksa otomatik oluşturur."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    base_network TEXT NOT NULL,
                    vlsm_data_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_project(self, name: str, base_network: str, vlsm_data: dict) -> bool:
        """Yeni bir VLSM planlama projesini veritabanına kaydeder veya varsa günceller."""
        try:
            json_data = json.dumps(vlsm_data, ensure_ascii=False)
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO projects (name, base_network, vlsm_data_json, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        base_network=excluded.base_network,
                        vlsm_data_json=excluded.vlsm_data_json,
                        created_at=excluded.created_at
                """, (name, base_network, json_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
            return True
        except Exception as e:
            raise e

    def get_all_projects(self) -> list[dict]:
        """Kayıtlı tüm projelerin özet listesini getirir."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, base_network, created_at FROM projects ORDER BY id DESC")
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "base_network": row[2],
                    "created_at": row[3]
                }
                for row in rows
            ]

    def get_project_by_name(self, name: str) -> dict | None:
        """İsme göre projenin detaylı JSON verisini çeker."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, base_network, vlsm_data_json, created_at FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "base_network": row[1],
                    "vlsm_data": json.loads(row[2]),
                    "created_at": row[3]
                }
            return None

    def delete_project(self, name: str) -> bool:
        """Bir projeyi veritabanından siler."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0