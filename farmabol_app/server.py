import hmac
import html
import json
import urllib.parse
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer

from .config import PORT, SECRET_KEY
from .db import init_database
from .repositories import ProductRepository, SaleRepository, UserRepository
from .services import ProductService, SaleService


def escape(value) -> str:
    return html.escape(str(value), quote=True)


def money(value: float) -> str:
    return f'Bs {float(value):,.2f}'


def make_signature(payload: str) -> str:
    return hmac.new(SECRET_KEY.encode(), payload.encode(), 'sha256').hexdigest()


def create_session_cookie(user: dict) -> str:
    payload = json.dumps({
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'full_name': user['full_name']
    }, separators=(',', ':'))
    encoded = urllib.parse.quote(payload)
    return f'{encoded}.{make_signature(encoded)}'


def read_session_cookie(cookie_value: str | None) -> dict | None:
    if not cookie_value or '.' not in cookie_value:
        return None
    encoded, signature = cookie_value.rsplit('.', 1)
    if not hmac.compare_digest(signature, make_signature(encoded)):
        return None
    try:
        return json.loads(urllib.parse.unquote(encoded))
    except json.JSONDecodeError:
        return None


def layout(title: str, body: str, user: dict | None = None, active: str = '', show_header: bool = True) -> str:
    menu = ''
    user_box = ''
    if user:
        initial = escape(user['full_name'][:1].upper())
        user_box = f'''
        <div class="user-box">
            <div class="avatar">{initial}</div>
            <div>
                <strong>{escape(user['full_name'])}</strong>
                <span>{escape(user['role'])}</span>
            </div>
        </div>
        '''
        product_link = '<a class="{0}" href="/products">Productos</a>'.format('active' if active == 'products' else '')
        menu = f'''
        <aside class="sidebar">
            <div class="brand">
                <span class="pill">FB</span>
                <div>
                    <strong>FARMABOL</strong>
                    <small>Inventarios y ventas</small>
                </div>
            </div>
            <nav>
                <a class="{'active' if active == 'dashboard' else ''}" href="/dashboard">Dashboard</a>
                {product_link}
                <a class="{'active' if active == 'sales' else ''}" href="/sales">Ventas</a>
                <a class="{'active' if active == 'new-sale' else ''}" href="/sales/new">Registrar venta</a>
                <a href="/logout">Cerrar sesion</a>
            </nav>
        </aside>
        '''

    header = ''
    if show_header:
        header = f'''
        <header class="topbar">
            <div>
                <h1>{escape(title)}</h1>
                <p>Farmacias Bolivianas Unidas - control rápido de stock y ventas.</p>
            </div>
            {user_box}
        </header>
        '''

    return f'''<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)} | FARMABOL</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    {menu}
    <main class="main {'with-sidebar' if user else 'login-main'}">
        {header}
        {body}
    </main>
</body>
</html>'''


def login_page(error: str = '') -> str:
    alert = f'<div class="alert error">{escape(error)}</div>' if error else ''
    body = f'''
    <section class="login-card">
        <div class="login-info">
            <span class="pill big">FB</span>
            <h2>FARMABOL</h2>
            <p>Sistema funcional para inventario, ventas y control de stock bajo.</p>
            <div class="mini-grid">
                <div><strong>12</strong><span>Sucursales</span></div>
                <div><strong>2</strong><span>Roles</span></div>
                <div><strong>24/7</strong><span>Control</span></div>
            </div>
        </div>
        <form class="form-panel" method="post" action="/login">
            <h2>Iniciar sesion</h2>
            <p class="muted">Usuarios de prueba: admin/admin123 o vendedor/vendedor123.</p>
            {alert}
            <label>Usuario</label>
            <input name="username" placeholder="admin" required>
            <label>Contraseña</label>
            <input name="password" type="password" placeholder="admin123" required>
            <button type="submit">Entrar al sistema</button>
        </form>
    </section>
    '''
    return layout('Login', body, show_header=False)


def dashboard_page(user: dict) -> str:
    products = ProductRepository().list_all()
    low_stock = ProductRepository().low_stock()
    sales_repo = SaleRepository()
    total_today = sales_repo.total_today()
    sales = sales_repo.list_recent(limit=5)

    low_rows = ''.join(
        f'<tr><td>{escape(p["code"])}</td><td>{escape(p["name"])}</td><td><span class="badge danger">{p["stock"]}</span></td></tr>'
        for p in low_stock
    ) or '<tr><td colspan="3">No hay productos con stock bajo por ahora.</td></tr>'

    sale_rows = ''.join(
        f'<tr><td>{escape(s["product_name"])}</td><td>{s["quantity"]}</td><td>{money(s["total"])}</td><td>{escape(s["created_at"])}</td></tr>'
        for s in sales
    ) or '<tr><td colspan="4">Todavia no hay ventas registradas.</td></tr>'

    body = f'''
    <section class="cards">
        <article class="card"><span>Productos activos</span><strong>{len(products)}</strong><small>Catalogo disponible</small></article>
        <article class="card"><span>Stock bajo</span><strong>{len(low_stock)}</strong><small>Menos de 5 unidades</small></article>
        <article class="card"><span>Ventas de hoy</span><strong>{money(total_today)}</strong><small>Total acumulado del dia</small></article>
    </section>
    <section class="grid-two">
        <article class="panel">
            <div class="panel-title"><h2>Productos con stock bajo</h2><a href="/products">Ver productos</a></div>
            <table><thead><tr><th>Codigo</th><th>Producto</th><th>Stock</th></tr></thead><tbody>{low_rows}</tbody></table>
        </article>
        <article class="panel">
            <div class="panel-title"><h2>Ultimas ventas</h2><a href="/sales/new">Nueva venta</a></div>
            <table><thead><tr><th>Producto</th><th>Cant.</th><th>Total</th><th>Fecha</th></tr></thead><tbody>{sale_rows}</tbody></table>
        </article>
    </section>
    '''
    return layout('Dashboard', body, user=user, active='dashboard')


def product_form(product: dict | None = None, error: str = '') -> str:
    is_edit = product is not None
    action = f'/products/edit?id={product["id"]}' if is_edit else '/products/new'
    title = 'Editar producto' if is_edit else 'Nuevo producto'
    alert = f'<div class="alert error">{escape(error)}</div>' if error else ''
    values = product or {'code': '', 'name': '', 'price': '', 'stock': '', 'laboratory': ''}
    return f'''
    <article class="panel narrow">
        <h2>{title}</h2>
        {alert}
        <form method="post" action="{action}" class="stack-form">
            <label>Codigo</label>
            <input name="code" value="{escape(values['code'])}" placeholder="MED001" required>
            <label>Nombre</label>
            <input name="name" value="{escape(values['name'])}" placeholder="Paracetamol 500mg" required>
            <label>Precio</label>
            <input name="price" type="number" step="0.01" min="0" value="{escape(values['price'])}" required>
            <label>Stock</label>
            <input name="stock" type="number" min="0" value="{escape(values['stock'])}" required>
            <label>Laboratorio</label>
            <input name="laboratory" value="{escape(values['laboratory'])}" placeholder="Laboratorio" required>
            <div class="actions">
                <button type="submit">Guardar</button>
                <a class="button secondary" href="/products">Cancelar</a>
            </div>
        </form>
    </article>
    '''


def products_page(user: dict, message: str = '') -> str:
    rows = ProductRepository().list_all()
    can_manage = user['role'] == 'ADMIN'
    create_button = '<a class="button" href="/products/new">Agregar producto</a>' if can_manage else ''
    alert = f'<div class="alert success">{escape(message)}</div>' if message else ''
    table_rows = ''
    for product in rows:
        actions = ''
        if can_manage:
            actions = f'''
            <td class="actions-cell">
                <a class="small-link" href="/products/edit?id={product['id']}">Editar</a>
                <form method="post" action="/products/delete?id={product['id']}" onsubmit="return confirm('Seguro que deseas eliminar este producto?')">
                    <button class="danger-btn" type="submit">Eliminar</button>
                </form>
            </td>
            '''
        else:
            actions = '<td><span class="muted">Solo consulta</span></td>'
        stock_class = 'danger' if product['stock'] < 5 else 'ok'
        table_rows += f'''
        <tr>
            <td>{escape(product['code'])}</td>
            <td>{escape(product['name'])}</td>
            <td>{money(product['price'])}</td>
            <td><span class="badge {stock_class}">{product['stock']}</span></td>
            <td>{escape(product['laboratory'])}</td>
            {actions}
        </tr>
        '''
    body = f'''
    <article class="panel">
        <div class="panel-title"><h2>Gestion de productos</h2>{create_button}</div>
        {alert}
        <table>
            <thead><tr><th>Codigo</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Laboratorio</th><th>Acciones</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
    </article>
    '''
    return layout('Productos', body, user=user, active='products')


def sale_form_page(user: dict, message: str = '', error: str = '') -> str:
    products = ProductRepository().list_all()
    options = ''.join(
        f'<option value="{p["id"]}">{escape(p["code"])} - {escape(p["name"])} (stock: {p["stock"]})</option>'
        for p in products
    )
    alert = ''
    if message:
        alert = f'<div class="alert success">{escape(message)}</div>'
    if error:
        alert = f'<div class="alert error">{escape(error)}</div>'
    body = f'''
    <article class="panel narrow">
        <h2>Registrar venta</h2>
        <p class="muted">Al guardar la venta, el stock se descuenta automaticamente.</p>
        {alert}
        <form method="post" action="/sales/new" class="stack-form">
            <label>Producto</label>
            <select name="product_id" required>{options}</select>
            <label>Cantidad</label>
            <input name="quantity" type="number" min="1" value="1" required>
            <button type="submit">Registrar venta</button>
        </form>
    </article>
    '''
    return layout('Registrar venta', body, user=user, active='new-sale')


def sales_page(user: dict) -> str:
    rows = SaleRepository().list_recent(limit=50)
    table_rows = ''.join(
        f'''<tr><td>{sale['id']}</td><td>{escape(sale['product_name'])}</td><td>{sale['quantity']}</td><td>{money(sale['total'])}</td><td>{escape(sale['seller'])}</td><td>{escape(sale['created_at'])}</td></tr>'''
        for sale in rows
    ) or '<tr><td colspan="6">Todavia no hay ventas registradas.</td></tr>'
    body = f'''
    <article class="panel">
        <div class="panel-title"><h2>Historial de ventas</h2><a class="button" href="/sales/new">Nueva venta</a></div>
        <table>
            <thead><tr><th>Nro.</th><th>Producto</th><th>Cantidad</th><th>Total</th><th>Vendedor</th><th>Fecha</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
    </article>
    '''
    return layout('Ventas', body, user=user, active='sales')


class FarmabolHandler(BaseHTTPRequestHandler):
    def current_user(self) -> dict | None:
        cookie = SimpleCookie(self.headers.get('Cookie'))
        session = cookie.get('farmabol_session')
        return read_session_cookie(session.value if session else None)

    def parse_form(self) -> dict:
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length).decode('utf-8')
        parsed = urllib.parse.parse_qs(raw)
        return {key: values[0] for key, values in parsed.items()}

    def parse_query(self) -> dict:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        return {key: values[0] for key, values in query.items()}

    def send_html(self, content: str, status: HTTPStatus = HTTPStatus.OK, headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def redirect(self, location: str, headers: dict | None = None) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header('Location', location)
        if headers:
            for name, value in headers.items():
                self.send_header(name, value)
        self.end_headers()

    def require_user(self, roles: tuple[str, ...] | None = None) -> dict | None:
        user = self.current_user()
        if not user:
            self.redirect('/login')
            return None
        if roles and user['role'] not in roles:
            self.send_html(layout('Acceso denegado', '<div class="alert error">No tienes permiso para entrar a esta seccion.</div>', user=user), HTTPStatus.FORBIDDEN)
            return None
        return user

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == '/static/styles.css':
            with open('static/styles.css', 'rb') as file:
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'text/css; charset=utf-8')
                self.end_headers()
                self.wfile.write(file.read())
            return
        if path in ('/', '/login'):
            if self.current_user():
                self.redirect('/dashboard')
            else:
                self.send_html(login_page())
            return
        if path == '/logout':
            self.redirect('/login', {'Set-Cookie': 'farmabol_session=; Path=/; Max-Age=0; HttpOnly'})
            return
        if path == '/dashboard':
            user = self.require_user()
            if user:
                self.send_html(dashboard_page(user))
            return
        if path == '/products':
            user = self.require_user()
            if user:
                query = self.parse_query()
                self.send_html(products_page(user, message=query.get('msg', '')))
            return
        if path == '/products/new':
            user = self.require_user(('ADMIN',))
            if user:
                self.send_html(layout('Nuevo producto', product_form(), user=user, active='products'))
            return
        if path == '/products/edit':
            user = self.require_user(('ADMIN',))
            if user:
                product_id = int(self.parse_query().get('id', '0'))
                product = ProductRepository().find_by_id(product_id)
                if not product:
                    self.send_html(layout('Producto no encontrado', '<div class="alert error">No se encontro el producto.</div>', user=user), HTTPStatus.NOT_FOUND)
                    return
                self.send_html(layout('Editar producto', product_form(product), user=user, active='products'))
            return
        if path == '/sales/new':
            user = self.require_user()
            if user:
                self.send_html(sale_form_page(user))
            return
        if path == '/sales':
            user = self.require_user()
            if user:
                self.send_html(sales_page(user))
            return
        self.send_html(layout('No encontrado', '<div class="alert error">La pagina solicitada no existe.</div>', user=self.current_user()), HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == '/login':
            form = self.parse_form()
            user = UserRepository().find_by_credentials(form.get('username', ''), form.get('password', ''))
            if not user:
                self.send_html(login_page('Usuario o contraseña incorrectos.'))
                return
            cookie = create_session_cookie(user)
            self.redirect('/dashboard', {'Set-Cookie': f'farmabol_session={cookie}; Path=/; HttpOnly; SameSite=Lax'})
            return
        if path == '/products/new':
            user = self.require_user(('ADMIN',))
            if not user:
                return
            ok, message = ProductService().save_new(self.parse_form())
            if ok:
                self.redirect('/products?msg=' + urllib.parse.quote(message))
            else:
                self.send_html(layout('Nuevo producto', product_form(error=message), user=user, active='products'))
            return
        if path == '/products/edit':
            user = self.require_user(('ADMIN',))
            if not user:
                return
            product_id = int(self.parse_query().get('id', '0'))
            ok, message = ProductService().save_edit(product_id, self.parse_form())
            if ok:
                self.redirect('/products?msg=' + urllib.parse.quote(message))
            else:
                product = ProductRepository().find_by_id(product_id)
                self.send_html(layout('Editar producto', product_form(product, error=message), user=user, active='products'))
            return
        if path == '/products/delete':
            user = self.require_user(('ADMIN',))
            if not user:
                return
            product_id = int(self.parse_query().get('id', '0'))
            ProductRepository().deactivate(product_id)
            self.redirect('/products?msg=Producto eliminado correctamente.')
            return
        if path == '/sales/new':
            user = self.require_user()
            if not user:
                return
            form = self.parse_form()
            try:
                product_id = int(form.get('product_id', '0'))
                quantity = int(form.get('quantity', '0'))
            except ValueError:
                self.send_html(sale_form_page(user, error='Selecciona un producto y una cantidad valida.'))
                return
            ok, message = SaleService().register_sale(product_id, quantity, user['id'])
            if ok:
                self.send_html(sale_form_page(user, message=message))
            else:
                self.send_html(sale_form_page(user, error=message))
            return
        self.send_html(layout('No encontrado', '<div class="alert error">Ruta no encontrada.</div>', user=self.current_user()), HTTPStatus.NOT_FOUND)


def create_app() -> HTTPServer:
    init_database()
    return HTTPServer(('0.0.0.0', PORT), FarmabolHandler)


def run() -> None:
    server = create_app()
    print(f'FARMABOL iniciado en http://localhost:{PORT}')
    server.serve_forever()
