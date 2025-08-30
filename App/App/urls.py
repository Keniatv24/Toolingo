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
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.views.generic import TemplateView
from users.views import UserViewSet
from catalog.views import CategoriaViewSet, ArticuloViewSet
from rentals.views import AlquilerViewSet, PagoViewSet, CalificacionViewSet
from django.views.generic import TemplateView

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("categorias", CategoriaViewSet)
router.register("articulos", ArticuloViewSet)
router.register("alquileres", AlquilerViewSet, basename="alquileres")
router.register("pagos", PagoViewSet, basename="pagos")
router.register("calificaciones", CalificacionViewSet, basename="calificaciones")

urlpatterns = [
    path("", TemplateView.as_view(template_name="landing/index.html")),
    path("", RedirectView.as_view(url="/api/docs/", permanent=False)),  # redirige la raíz  :) 
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include(router.urls)),
    path("catalogo/", TemplateView.as_view(template_name="catalogo/index.html")),
    path("login/", TemplateView.as_view(template_name="users/login.html")),
    path("registro/", TemplateView.as_view(template_name="users/registro.html")),
    path("publicar/", TemplateView.as_view(template_name="catalog/publicar.html")),
    path("api/", include("App.urls_api")),  # API
    path("api/docs/", include("App.urls_docs", namespace="docs")),  
    path("admin/", admin.site.urls),

]
