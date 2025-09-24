"""
URL configuration for App project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# App/App/urls.py
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from users.views import ProfileViewSet
from catalog import views as catalog_views
from django.shortcuts import render




from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# ViewSets del proyecto
from users.views import UserViewSet
from catalog.views import CategoriaViewSet, ArticuloViewSet
from rentals.views import AlquilerViewSet, PagoViewSet, CalificacionViewSet, CartItemViewSet




def articulo_detalle(request, id):
    # id puede ser UUID o int; pásalo como string al template
    return render(request, "catalog/detalle.html", {"articulo_id": str(id)})

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"categorias", CategoriaViewSet, basename="categorias")
router.register(r"articulos", ArticuloViewSet, basename="articulos")
router.register(r"alquileres", AlquilerViewSet, basename="alquileres")
router.register(r"pagos", PagoViewSet, basename="pagos")
router.register(r"calificaciones", CalificacionViewSet, basename="calificaciones")
router.register("perfiles", ProfileViewSet, basename="perfiles")
router.register(r"carrito", CartItemViewSet, basename="carrito") 



urlpatterns = [
    # Páginas HTML
    path("", TemplateView.as_view(template_name="landing/index.html"), name="landing"),
    path("catalogo/", TemplateView.as_view(template_name="catalogo/index.html"), name="catalogo"),
    path("publicar/", TemplateView.as_view(template_name="catalog/publicar.html"), name="publicar"),
    path("login/", TemplateView.as_view(template_name="auth/login.html"), name="login"),
    path("registro/", TemplateView.as_view(template_name="users/registro.html"), name="registro"),

    # API REST
    path("api/", include(router.urls)),

    # Admin
    path("admin/", admin.site.urls),

    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("perfil/", TemplateView.as_view(template_name="users/perfil.html"), name="perfil"),
    path("perfil/editar/", TemplateView.as_view(template_name="users/perfil_editar.html"), name="perfil_editar"),
    path("articulo/<uuid:id>/", articulo_detalle, name="articulo_detalle"),
    path("carrito/", TemplateView.as_view(template_name="cart/index.html"), name="carrito"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)