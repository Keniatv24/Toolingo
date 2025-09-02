from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet

from .models import Categoria, Articulo, Imagen
from .serializers import CategoriaSerializer, ArticuloSerializer
from .filters import ArticuloFilter


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, "propietario_id", None) == getattr(request.user, "id", None)


class ArticuloViewSet(ModelViewSet):
    queryset = Articulo.objects.select_related("categoria", "propietario").all()
    serializer_class = ArticuloSerializer
    filterset_class = ArticuloFilter
    ordering_fields = ["creado", "precio_por_dia"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)

    def create(self, request, *args, **kwargs):
        # Requiere al menos 1 imagen
        files = request.FILES.getlist("imagenes")
        if len(files) == 0:
            return Response(
                {"detail": "Debes adjuntar al menos una foto (campo 'imagenes')."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {
            "titulo": request.data.get("titulo"),
            "descripcion": request.data.get("descripcion"),
            "categoria": request.data.get("categoria"),
            "estado": request.data.get("estado") or "USADO",
            "precio_por_dia": request.data.get("precio_por_dia") or 0,
            "deposito": request.data.get("deposito") or 0,
            "disponibilidad_global": request.data.get("disponibilidad_global", True)
            in (True, "true", "True", "1"),
            "ubicacion": request.data.get("ubicacion"),
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        articulo = serializer.instance

        # Guardar imágenes
        for f in files:
            Imagen.objects.create(articulo=articulo, imagen=f)

        headers = self.get_success_headers(serializer.data)
        return Response(
            self.get_serializer(articulo).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
