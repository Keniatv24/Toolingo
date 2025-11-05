# 🔧 Toolingo

**Toolingo** es un marketplace web para el alquiler de herramientas y equipos.  
Permite a propietarios publicar sus artículos y a arrendatarios explorar, reservar y contactar de forma sencilla.  

## Autores
-  Kenia Margarita Toscano Vasquez


## Características principales

- Catálogo navegable con buscador por título / descripción / ciudad.
- Detalle de artículos con carrusel de imágenes.
- Creación de artículos con geocodificación automática (`ubicación → lat/lng`).
- Carrito de alquiler.
- Pagos simulados (wallet + cheque PDF).
- Chat entre arrendatario ↔ propietario.
- Sistema de reseñas con elegibilidad.
- Paginación, ordenación y filtros en DRF.
- **Servicio JSON público** para ser consumido por otro equipo.
- **Consumo del servicio JSON del equipo anterior**.
- Multilenguaje (ES/EN) vía `{% trans %}` y mensajes en `.po`.

---

## Tecnologías y Arquitectura

| Capa | Tecnología |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Autenticación | JWT (Simple JWT) |
| Proyecto API | DRF Router + ViewSets + Serializers |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| Frontend | HTML + TailwindCSS + Vanilla JS |
| Arquitectura | MVC + Services + **DI (Interfaz + 2 Implementaciones)** |
| Servicios externos | Nominatim (OpenStreetMap) – geocodificación |
| API Aliado | Consumo servicio JSON de otro equipo |
| Documentación API | drf-spectacular → `/api/docs/` |
| Internacionalización | **2 idiomas: ES / EN** (sin textos quemados) |

---

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
├── App/                                 # Proyecto Django principal
│   ├── App/                             # settings / urls / wsgi / asgi
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── common/                          # Servicios / Interfaces / Utils
│   │   ├── interfaces/
│   │   │   └── payments.py              # INTERFAZ PaymentProcessor  ← DIP
│   │   ├── services/
│   │   │   ├── geocoding.py             # consumo API externa Nominatim
│   │   │   ├── wallet_processor.py      # implementación 1
│   │   │   └── cheque_pdf_processor.py  # implementación 2 (PDF cheque)
│   │   ├── payment_factory.py           # fabrica (elige implementaciones)
│   │   └── utils.py
│   │
│   ├── catalog/                         # artículos
│   │   ├── migrations/
│   │   ├── templates/catalog/
│   │   │   ├── index.html
│   │   │   ├── detalle.html
│   │   │   ├── publicar.html
│   │   │   ├── productos_aliados.html    # muestra consumo API equipo previo
│   │   │   └── ...
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py                     # incluye endpoint “cerca”
│   │   ├── pages.py                     # consumo servicio equipo previo
│   │   ├── utils.py                     # Haversine
│   │   └── tests.py
│   │
│   ├── rentals/                         # Alquiler + Wallet + Pagos
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py                     # usa PaymentProcessor vía factory
│   │   └── tests.py
│   │
│   ├── chat/                            # Mensajería
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── tests.py
│   │
│   ├── users/                           # usuarios y perfiles
│   │   ├── migrations/
│   │   ├── templates/users/
│   │   │   ├── login.html
│   │   │   ├── registro.html
│   │   │   ├── perfil.html
│   │   │   └── perfil_editar.html
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── tests.py
│   │
│   ├── templates/                       # Template globales (i18n)
│   │   ├── base.html
│   │   ├── landing/
│   │   │   └── index.html
│   │   └── _partials/
│   │       ├── header.html
│   │       └── footer.html
│   │
│   ├── locale/
│   │   ├── es/LC_MESSAGES/django.po
│   │   └── en/LC_MESSAGES/django.po
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   └── favicon.ico
│   │
│   └── manage.py
│
├── media/                                # archivos subidos
│   ├── articulos/
│   └── profiles/
│
├── requirements.txt
├── README.md
└── .gitignore

```
## API

La API está construida con Django REST Framework.
Endpoints principales:

-  /api/articulos/ → Listado y creación de artículos

-  /api/articulos/<id>/ → Detalle de artículo

-  /api/categorias/ → Categorías en árbol

-  /api/users/ → Gestión de usuarios

-  /api/perfiles/ → Perfiles de usuario

La documentación interactiva (Swagger/ReDoc) está disponible en:
```bash
/api/docs/
```


