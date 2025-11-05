# App/App/urls.py
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.conf.urls.i18n import i18n_patterns
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from App.views import NotificacionesList 
from App.views import WalletBalanceView, WalletRechargeView 

from App.views import SimularPagoView  
from users.views import ProfileViewSet, UserViewSet
from catalog.views import CategoriaViewSet, ArticuloViewSet, AliadosArticuloList
from rentals.views import AlquilerViewSet, PagoViewSet, CalificacionViewSet, CartItemViewSet
from chat.views import ConversationViewSet
from catalog.pages import productos_aliados 
from . import views  
from rentals.views import (
    ReviewsByArticuloList,
    ReviewsByArticuloSummary,
    ReviewsByArticuloEligibility,
    ReviewsByArticuloCreate,
)

@method_decorator(xframe_options_sameorigin, name="dispatch")
class ChatWidgetView(TemplateView):
    template_name = "chat/index.html"

def articulo_detalle(request, id):
    return render(request, "catalog/detalle.html", {"articulo_id": str(id)})

# -------- API router --------
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"categorias", CategoriaViewSet, basename="categorias")
router.register(r"articulos", ArticuloViewSet, basename="articulos")
router.register(r"alquileres", AlquilerViewSet, basename="alquileres")
router.register(r"pagos", PagoViewSet, basename="pagos")
router.register(r"calificaciones", CalificacionViewSet, basename="calificaciones")
router.register(r"perfiles", ProfileViewSet, basename="perfiles")
router.register(r"carrito", CartItemViewSet, basename="carrito")
router.register(r"chats", ConversationViewSet, basename="chat")


urlpatterns = [
    
    path("api/pagos/simular/", SimularPagoView.as_view(), name="pagos-simular"),
    path("api/notificaciones/", NotificacionesList.as_view(), name="notificaciones-list"),
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/aliados/productos/", AliadosArticuloList.as_view(), name="aliados-productos"),
    path("admin/", admin.site.urls),
    path("api/wallet/", WalletBalanceView.as_view(), name="wallet-balance"),
    path("api/wallet/recargar/", WalletRechargeView.as_view(), name="wallet-recharge"),
    path("api/articulos/<uuid:art_id>/reviews/", ReviewsByArticuloList.as_view(), name="art-reviews-list"),
    path("api/articulos/<uuid:art_id>/reviews/summary/", ReviewsByArticuloSummary.as_view(), name="art-reviews-summary"),
    path("api/articulos/<uuid:art_id>/reviews/eligibility/", ReviewsByArticuloEligibility.as_view(), name="art-reviews-eligibility"),
    path("api/articulos/<uuid:art_id>/reviews/create/", ReviewsByArticuloCreate.as_view(), name="art-reviews-create"),
]

# -------- Páginas HTML con prefijo /es/ o /en/ --------
urlpatterns += i18n_patterns(
    path("", TemplateView.as_view(template_name="landing/index.html"), name="landing"),
    path("catalogo/", TemplateView.as_view(template_name="catalogo/index.html"), name="catalogo"),
    path("publicar/", TemplateView.as_view(template_name="catalog/publicar.html"), name="publicar"),
    path("login/", TemplateView.as_view(template_name="auth/login.html"), name="login"),
    path("registro/", TemplateView.as_view(template_name="users/registro.html"), name="registro"),
    path("perfil/", TemplateView.as_view(template_name="users/perfil.html"), name="perfil"),
    path("perfil/editar/", TemplateView.as_view(template_name="users/perfil_editar.html"), name="perfil_editar"),
    path("carrito/", TemplateView.as_view(template_name="cart/index.html"), name="carrito"),
    path("checkout/", TemplateView.as_view(template_name="checkout/checkout.html"), name="checkout"),
    path("chat/", ChatWidgetView.as_view(), name="chat_ui"),
    path("pagos/", views.pagos_view, name="pagos"),
    path("articulo/<uuid:id>/", articulo_detalle, name="articulo_detalle"),
    path("productos-aliados/", productos_aliados, name="productos_aliados"),
    path("wallet/", TemplateView.as_view(template_name="wallet/index.html"), name="wallet"),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
