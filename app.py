from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import sqlite3

PORT = 8000
DB = 'farmabol.db'

PRODUCTS = [
    ('MED001', 'Paracetamol 500mg', 4.50, 20, 'Bago'),
    ('MED002', 'Ibuprofeno 400mg', 6.00, 4, 'Inti')
]

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, name TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, code TEXT, name TEXT, price REAL, stock INTEGER, laboratory TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY, product_id INTEGER, quantity INTEGER, total REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    cur.execute('SELECT COUNT(*) FROM users')
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users(username,password,role,name) VALUES('admin','admin123','ADMIN','Administrador')")
        cur.execute("INSERT INTO users(username,password,role,name) VALUES('vendedor','vendedor123','VENDEDOR','Vendedor')")
    cur.execute('SELECT COUNT(*) FROM products')
    if cur.fetchone()[0] == 0:
        cur.executemany('INSERT INTO products(code,name,price,stock,laboratory) VALUES(?,?,?,?,?)', PRODUCTS)
    conn.commit()
    conn.close()

class App(BaseHTTPRequestHandler):
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_GET(self):
        init_db()
        if self.path == '/':
            self.send_html('<h1>FARMABOL</h1><p>Login y módulo base.</p>')
        elif self.path == '/productos':
            conn = sqlite3.connect(DB)
            rows = conn.execute('SELECT code,name,price,stock,laboratory FROM products').fetchall()
            conn.close()
            html = '<h1>Productos</h1><ul>'
            for row in rows:
                html += f'<li>{row[0]} - {row[1]} - Bs {row[2]} - Stock {row[3]} - {row[4]}</li>'
            html += '</ul>'
            self.send_html(html)
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    init_db()
    print(f'Servidor iniciado en http://localhost:{PORT}')
    HTTPServer(('0.0.0.0', PORT), App).serve_forever()
