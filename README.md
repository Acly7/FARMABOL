# FARMABOL - Control de Inventarios y Ventas

Sistema web pequeño para la evaluación del Hito 4 de Ingeniería de Software II.
Fue armado para el caso de Farmacias Bolivianas Unidas (FARMABOL), con 12 sucursales.

## Tecnologías usadas

- Python 3
- SQLite
- HTML, CSS y JavaScript básico
- Servidor HTTP de la librería estándar de Python

No necesita instalar Flask ni otros paquetes externos para funcionar.

## Usuarios de prueba

| Rol | Usuario | Contraseña |
| --- | --- | --- |
| ADMIN | admin | admin123 |
| VENDEDOR | vendedor | vendedor123 |

## Cómo ejecutar

```bash
python app.py
```

Luego abrir:

```text
http://localhost:8000
```

## Funciones principales

- Login con roles ADMIN y VENDEDOR.
- CRUD de productos para ADMIN.
- Registro de ventas para ADMIN y VENDEDOR.
- Descuento automático de stock al vender.
- Dashboard con stock bajo y ventas del día.
- Base de datos SQLite con tablas de usuarios, productos y ventas.
