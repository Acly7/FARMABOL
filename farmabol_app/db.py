import hashlib
import os
import sqlite3
from typing import Iterable

from .config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: str = 'farmabol') -> str:
    value = f'{salt}:{password}'.encode('utf-8')
    return hashlib.sha256(value).hexdigest()


def init_database() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('ADMIN', 'VENDEDOR')),
                full_name TEXT NOT NULL
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0),
                laboratory TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                total REAL NOT NULL CHECK(total >= 0),
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            '''
        )
        seed_users(conn)
        seed_products(conn)


def seed_users(conn: sqlite3.Connection) -> None:
    total = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if total > 0:
        return
    users = [
        ('admin', hash_password('admin123'), 'ADMIN', 'Administrador General'),
        ('vendedor', hash_password('vendedor123'), 'VENDEDOR', 'Vendedor de Sucursal')
    ]
    conn.executemany(
        'INSERT INTO users(username, password_hash, role, full_name) VALUES (?, ?, ?, ?)',
        users
    )


def seed_products(conn: sqlite3.Connection) -> None:
    total = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if total > 0:
        return
    products: Iterable[tuple[str, str, float, int, str]] = [
        ('MED001', 'Paracetamol 500mg', 4.50, 22, 'Laboratorios Bago'),
        ('MED002', 'Ibuprofeno 400mg', 6.00, 4, 'Laboratorios Inti'),
        ('MED003', 'Amoxicilina 500mg', 18.50, 15, 'COFAR'),
        ('MED004', 'Omeprazol 20mg', 12.00, 3, 'Drogueria Bolivia'),
        ('MED005', 'Alcohol medicinal 70%', 9.50, 30, 'FARMABOL'),
        ('MED006', 'Vitamina C 1g', 8.00, 5, 'Lafarmed')
    ]
    conn.executemany(
        'INSERT INTO products(code, name, price, stock, laboratory) VALUES (?, ?, ?, ?, ?)',
        products
    )
