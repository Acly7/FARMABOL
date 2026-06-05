from .db import get_connection
from .repositories import ProductRepository, SaleRepository


class ProductService:
    def __init__(self) -> None:
        self.products = ProductRepository()

    def validate(self, form: dict, product_id: int | None = None) -> tuple[bool, str, dict]:
        code = form.get('code', '').strip().upper()
        name = form.get('name', '').strip()
        laboratory = form.get('laboratory', '').strip()

        if not code or not name or not laboratory:
            return False, 'Completa todos los campos del producto.', {}
        if len(code) < 3:
            return False, 'El codigo debe tener al menos 3 caracteres.', {}

        try:
            price = float(form.get('price', '0'))
            stock = int(form.get('stock', '0'))
        except ValueError:
            return False, 'El precio y el stock deben ser valores numericos.', {}

        if price <= 0:
            return False, 'El precio debe ser mayor a cero.', {}
        if stock < 0:
            return False, 'El stock no puede ser negativo.', {}
        if self.products.code_exists(code, ignore_id=product_id):
            return False, 'Ya existe un producto con ese codigo.', {}

        clean_data = {
            'code': code,
            'name': name,
            'price': price,
            'stock': stock,
            'laboratory': laboratory
        }
        return True, 'Producto validado correctamente.', clean_data

    def save_new(self, form: dict) -> tuple[bool, str]:
        valid, message, data = self.validate(form)
        if not valid:
            return False, message
        self.products.create(data)
        return True, 'Producto registrado correctamente.'

    def save_edit(self, product_id: int, form: dict) -> tuple[bool, str]:
        valid, message, data = self.validate(form, product_id=product_id)
        if not valid:
            return False, message
        self.products.update(product_id, data)
        return True, 'Producto actualizado correctamente.'


class SaleService:
    def __init__(self) -> None:
        self.products = ProductRepository()
        self.sales = SaleRepository()

    def register_sale(self, product_id: int, quantity: int, user_id: int) -> tuple[bool, str]:
        if quantity <= 0:
            return False, 'La cantidad debe ser mayor a cero.'

        product = self.products.find_by_id(product_id)
        if not product:
            return False, 'El producto seleccionado no existe.'
        if product['stock'] < quantity:
            return False, 'No hay suficiente stock para completar la venta.'
        if product['stock'] - quantity < 5:
            # Se permite vender, pero queda registrado como alerta visual en el dashboard.
            pass

        total = round(product['price'] * quantity, 2)
        with get_connection() as conn:
            conn.execute(
                'UPDATE products SET stock = stock - ? WHERE id = ?',
                (quantity, product_id)
            )
            conn.execute(
                '''
                INSERT INTO sales(product_id, user_id, quantity, total)
                VALUES (?, ?, ?, ?)
                ''',
                (product_id, user_id, quantity, total)
            )
        return True, f'Venta registrada. Total: Bs {total:.2f}'
