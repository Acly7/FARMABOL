from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8000

class App(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'<h1>FARMABOL</h1><p>Sistema base del proyecto.</p>')
            return
        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    print(f'Servidor iniciado en http://localhost:{PORT}')
    HTTPServer(('0.0.0.0', PORT), App).serve_forever()
