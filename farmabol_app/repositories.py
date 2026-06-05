from typing import Optional

from .db import get_connection, hash_password


class UserRepository:
    def find_by_credentials(self, username: str, password: str) -> Optional[dict]:
        with get_connection() as conn:
            row = conn.execute(
                '''
                SELECT id, username, role, full_name
                FROM users
                WHERE username = ? AND password_hash = ?
                ''',
                (username.strip(), hash_password(password))
            ).fetchone()
        return dict(row) if row else None


class ProductRepository:
    def list_all(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT id, code, name, price, stock, laboratory
                FROM products
                WHERE active = 1
                ORDER BY name
                '''
            ).fetchall()
        return [dict(row) for row in rows]

    def low_stock(self, limit: int = 5) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT id, code, name, price, stock, laboratory
                FROM products
                WHERE active = 1 AND stock < ?
                ORDER BY stock ASC, name ASC
                ''',
                (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def find_by_id(self, product_id: int) -> Optional[dict]:
        with get_connection() as conn:
            row = conn.execute(
                '''
                SELECT id, code, name, price, stock, laboratory
                FROM products
                WHERE id = ? AND active = 1
                ''',
                (product_id,)
            ).fetchone()
        return dict(row) if row else None

    def code_exists(self, code: str, ignore_id: Optional[int] = None) -> bool:
        sql = 'SELECT id FROM products WHERE code = ? AND active = 1'
        params: tuple = (code,)
        if ignore_id is not None:
            sql += ' AND id <> ?'
            params = (code, ignore_id)
        with get_connection() as conn:
            row = conn.execute(sql, params).fetchone()
        return row is not None

    def create(self, data: dict) -> None:
        with get_connection() as conn:
            conn.execute(
                '''
                INSERT INTO products(code, name, price, stock, laboratory)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (data['code'], data['name'], data['price'], data['stock'], data['laboratory'])
            )

    def update(self, product_id: int, data: dict) -> None:
        with get_connection() as conn:
            conn.execute(
                '''
                UPDATE products
                SET code = ?, name = ?, price = ?, stock = ?, laboratory = ?
                WHERE id = ?
                ''',
                (data['code'], data['name'], data['price'], data['stock'], data['laboratory'], product_id)
            )

    def deactivate(self, product_id: int) -> None:
        with get_connection() as conn:
            conn.execute('UPDATE products SET active = 0 WHERE id = ?', (product_id,))


class SaleRepository:
    def list_recent(self, limit: int = 20) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                '''
                SELECT s.id, p.code, p.name AS product_name, u.full_name AS seller,
                       s.quantity, s.total, s.created_at
                FROM sales s
                INNER JOIN products p ON p.id = s.product_id
                INNER JOIN users u ON u.id = s.user_id
                ORDER BY s.created_at DESC
                LIMIT ?
                ''',
                (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def total_today(self) -> float:
        with get_connection() as conn:
            row = conn.execute(
                '''
                SELECT COALESCE(SUM(total), 0) AS total
                FROM sales
                WHERE date(created_at) = date('now', 'localtime')
                '''
            ).fetchone()
        return float(row['total'])
