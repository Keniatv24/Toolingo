# 🔧 Toolingo

**Toolingo** es un marketplace web para el alquiler de herramientas y equipos.  
Permite a propietarios publicar sus artículos y a arrendatarios explorar, reservar y contactar de forma sencilla.  

## Autores
-  **Kenia Margarita Toscano Vasquez
-  **Leidy carolina Obando Figueroa

##  Características principales

-  **Publicación de artículos** con imágenes, precio por día y disponibilidad.  
-  **Catálogo navegable** con buscador rápido por título, descripción o ubicación.  
-  **Galería de imágenes** con portada y miniaturas.  
-  **Propietarios visibles**: muestra nombre, email, teléfono y ubicación de quien publicó el artículo.  
-  **Interacciones**: botones para reservar, contactar y compartir.  
-  **Frontend responsivo** en **TailwindCSS**, con animaciones suaves y diseño moderno.  
-  **Backend REST API** con **Django REST Framework**.

-  ##  Tecnologías

- **Backend**: Django + Django REST Framework  
- **Frontend**: HTML + TailwindCSS + Vanilla JS  
- **Base de datos**: SQLite (dev) / PostgreSQL (prod)  
- **Autenticación**: JWT  
- **Infraestructura**: Python 3.12+, Node.js

 ##  Instalación

### 1. Clonar el repositorio
  ```bash
  git clone https://github.com/tu-usuario/toolingo.git
  cd Toolingo
  ```

 ### 2. Configurar el entorno virtual
 ```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

```
 ### 3. Instalar dependencias
```bash
pip install -r requirements.txt

```

### 4. Migrar la base de datos
```bash
python manage.py migrate

```

### 5. Crear un superusuario

```bash
python manage.py createsuperuser

```

### 6. Levantar el servidor backend

```bash
cd App
python manage.py runserver

```
El backend estará disponible en http://localhost:8000 


##  Estructura del proyecto


```bash
Toolingo/
├── App/                                # Proyecto Django principal
│   ├── App/                            # Configuración Django (settings, urls, wsgi, asgi)
│   │   ├── __init__.py
│   │   ├── settings.py                  # Configuración principal
│   │   ├── urls.py                      # URLs globales
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── catalog/                         # App de Catálogo (artículos, categorías, imágenes)
│   │   ├── migrations/
│   │   ├── templates/catalog/
│   │   │   ├── detalle.html             # Vista detalle artículo
│   │   │   ├── listado.html             # Catálogo general
│   │   │   └── ...
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py               # Serializadores DRF
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── tests.py
│   │
│   ├── users/                           # App de Usuarios y Perfiles
│   │   ├── migrations/
│   │   ├── templates/users/
│   │   │   ├── perfil.html
│   │   │   ├── perfil_editar.html
│   │   │   └── ...
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── tests.py
│   │
│   ├── templates/                       # Templates compartidos
│   │   ├── base.html
│   │   ├── landing/index.html           # Landing principal
│   │   └── ...
│   │
│   ├── static/                          # Archivos estáticos (CSS, JS, imágenes)
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   └── favicon.ico
│   │
│   └── manage.py
│
├── Frontend/                            # Cliente React + Vite (opcional)
│   ├── src/
│   │   ├── components/
│   │   │   ├── home.jsx
│   │   │   ├── methods/
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── CatalogPage.jsx
│   │   │   ├── DetailPage.jsx
│   │   │   └── ...
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── public/index.html
│   ├── package.json
│   └── vite.config.js
│
├── media/                               # Archivos subidos (imágenes de artículos/perfiles)
│   ├── articulos/
│   └── profiles/
│
├── requirements.txt                     # Dependencias Python
├── README.md                            # Documentación del proyecto
└── .gitignore

```
## API

La API está construida con Django REST Framework.
Endpoints principales:

-  **/api/articulos/ → Listado y creación de artículos

-  **/api/articulos/<id>/ → Detalle de artículo

-  **/api/categorias/ → Categorías en árbol

-  **/api/users/ → Gestión de usuarios

-  **/api/perfiles/ → Perfiles de usuario

La documentación interactiva (Swagger/ReDoc) está disponible en:
```bash
/api/docs/
```


