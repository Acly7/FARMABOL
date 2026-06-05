from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

PORT = 8000

USERS = {
    'admin': {'password': 'admin123', 'role': 'ADMIN', 'name': 'Administrador'},
    'vendedor': {'password': 'vendedor123', 'role': 'VENDEDOR', 'name': 'Vendedor'}
}

class App(BaseHTTPRequestHandler):
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_GET(self):
        if self.path == '/':
            self.send_html('''
            <h1>FARMABOL</h1>
            <form method="post" action="/login">
                <input name="username" placeholder="Usuario">
                <input name="password" type="password" placeholder="Contraseña">
                <button>Entrar</button>
            </form>
            ''')
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == '/login':
            length = int(self.headers.get('Content-Length', '0'))
            data = parse_qs(self.rfile.read(length).decode())
            username = data.get('username', [''])[0]
            password = data.get('password', [''])[0]
            user = USERS.get(username)
            if user and user['password'] == password:
                self.send_html(f'<h1>Bienvenido {user["name"]}</h1><p>Rol: {user["role"]}</p>')
            else:
                self.send_html('<h1>Error</h1><p>Usuario o contraseña incorrectos.</p>')
            return
        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    print(f'Servidor iniciado en http://localhost:{PORT}')
    HTTPServer(('0.0.0.0', PORT), App).serve_forever()
