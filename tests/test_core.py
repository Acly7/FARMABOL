import unittest

from farmabol_app.db import hash_password
from farmabol_app.services import ProductService


class CoreTest(unittest.TestCase):
    def test_hash_password_is_stable(self):
        self.assertEqual(hash_password('admin123'), hash_password('admin123'))
        self.assertNotEqual(hash_password('admin123'), hash_password('otra'))

    def test_product_validation_rejects_empty_values(self):
        service = ProductService()
        valid, message, _ = service.validate({'code': '', 'name': '', 'price': '0', 'stock': '0', 'laboratory': ''})
        self.assertFalse(valid)
        self.assertIn('Completa', message)


if __name__ == '__main__':
    unittest.main()
