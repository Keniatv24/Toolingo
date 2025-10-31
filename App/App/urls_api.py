
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from App.views import NotificacionesList
from catalog.views import ArticuloViewSet
from rentals.views import AlquilerViewSet
from catalog.views import CategoriaViewSet  #
router = DefaultRouter()
router.register(r'articulos', ArticuloViewSet, basename='articulo')
router.register(r'alquileres', AlquilerViewSet, basename='alquiler')
# viewset de categorías:
try:
    router.register(r'categorias', CategoriaViewSet, basename='categoria')
except NameError:
    pass

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("notificaciones/", NotificacionesList.as_view(), name="notificaciones-list")
]
