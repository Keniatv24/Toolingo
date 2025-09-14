# 🔧 Toolingo

**Toolingo** es un marketplace web para el alquiler de herramientas y equipos.  
Permite a propietarios publicar sus artículos y a arrendatarios explorar, reservar y contactar de forma sencilla.  

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

  ## Estructura del proyecto

- Toolingo/
  
├── App/                                # Proyecto Django principal
│   ├── App/                            # Configuración Django (settings, urls, wsgi, asgi)
│   │   ├── __init__.py
│   │   ├── settings.py                 # Configuración principal
│   │   ├── urls.py                     # URLs globales
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── catalog/                        # Aplicación Catálogo (artículos, categorías, imágenes)
│   │   ├── migrations/                 # Migraciones de base de datos
│   │   ├── templates/catalog/          
│   │   │   ├── detalle.html            # Vista detalle artículo
│   │   │   ├── listado.html            # Catálogo general
│   │   │   └── ...                     
│   │   ├── admin.py                    # Configuración del admin
│   │   ├── apps.py
│   │   ├── models.py                   # Modelos: Categoria, Articulo, Imagen
│   │   ├── serializers.py              # Serializadores DRF
│   │   ├── urls.py                     # Rutas de la app
│   │   ├── views.py                    # Vistas API y vistas HTML
│   │   └── tests.py
│   │
│   ├── users/                          # App de Usuarios y Perfiles
│   │   ├── migrations/
│   │   ├── templates/users/            # Templates de perfil
│   │   │   ├── perfil.html
│   │   │   ├── perfil_editar.html
│   │   │   └── ...
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py                   # Modelos de UserProfile, etc.
│   │   ├── serializers.py              # Serializadores User/Profile
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── tests.py
│   │
│   ├── templates/                      # Templates compartidos
│   │   ├── base.html                    # Layout general
│   │   ├── landing/index.html           # Landing principal
│   │   └── ...
│   │
│   ├── static/                         # Archivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   └── favicon.ico
│   │
│   └── manage.py                       # Comando principal Django
│
├── Frontend/                           # (Opcional) Cliente en React + Vite
│   ├── src/
│   │   ├── components/                 # Componentes UI
│   │   │   ├── home.jsx
│   │   │   ├── methods/                # Métodos numéricos (ejemplo Fractal)
│   │   │   └── ...
│   │   ├── pages/                      # Páginas
│   │   │   ├── CatalogPage.jsx
│   │   │   ├── DetailPage.jsx
│   │   │   └── ...
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── vite.config.js
│
├── media/                              # Archivos subidos (imagenes de artículos y perfiles)
│   ├── articulos/
│   └── profiles/
│
├── requirements.txt                    # Dependencias Python
├── README.md                           # Documentación del proyecto
└── .gitignore
