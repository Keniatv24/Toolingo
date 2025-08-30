from rest_framework import viewsets, permissions
from .models import Categoria, Articulo
from .serializers import CategoriaSerializer, ArticuloSerializer
from .filters import ArticuloFilter
from rest_framework.viewsets import ModelViewSet

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]

class ArticuloViewSet(viewsets.ModelViewSet):
    queryset = Articulo.objects.select_related("categoria","propietario").all()
    serializer_class = ArticuloSerializer
    filterset_class = ArticuloFilter
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, "propietario_id", None) == getattr(request.user, "id", None)

class ArticuloViewSet(ModelViewSet):
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    filterset_class = ArticuloFilter
    ordering_fields = ["creado", "precio_por_dia"]

    def get_permissions(self):
        # Lectura pública, escritura autenticada + dueño
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        # POST requiere login, PUT/PATCH/DELETE requiere login + ser dueño
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)