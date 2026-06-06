# Guia rapida para subir FARMABOL a Render

1. Sube este proyecto a un repositorio de GitHub.
2. En Render, elige **New Web Service**.
3. Conecta tu repositorio.
4. Configura:
   - Build Command: dejar vacio
   - Start Command: `python app.py`
5. Agrega variables de entorno si te las pide:
   - `SECRET_KEY`: cualquier texto largo
   - `PORT`: Render normalmente lo asigna automaticamente, pero el `render.yaml` ya deja una base.
6. Espera el despliegue y abre la URL publica.

Usuarios de prueba:
- admin / admin123
- vendedor / vendedor123
