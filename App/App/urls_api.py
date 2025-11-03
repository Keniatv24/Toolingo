# App/App/urls_api.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from App.views import NotificacionesList, SimularPagoView
from catalog.views import ArticuloViewSet, CategoriaViewSet
from rentals.views import AlquilerViewSet

router = DefaultRouter()
router.register(r'articulos', ArticuloViewSet, basename='articulo')
router.register(r'alquileres', AlquilerViewSet, basename='alquiler')
router.register(r'categorias', CategoriaViewSet, basename='categoria')

urlpatterns = [
    
    path("pagos/simular/", SimularPagoView.as_view(), name="pagos-simular"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("notificaciones/", NotificacionesList.as_view(), name="notificaciones-list"),l
    path('', include(router.urls)),
]
