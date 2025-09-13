from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from rest_framework import viewsets, permissions, status, mixins, filters
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from .models import Categoria, Articulo, Imagen
from .serializers import CategoriaSerializer, ArticuloSerializer
from .filters import ArticuloFilter


# ---------- Categorías (solo lectura) ----------
class CategoriaViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    """
    Listado/detalle de categorías (público).
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.AllowAny]


# ---------- Permiso de propietario ----------
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Lectura para todos; escritura solo para el propietario.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, "propietario_id", None) == getattr(request.user, "id", None)


# ---------- Artículos ----------
class ArticuloViewSet(ModelViewSet):
    """
    CRUD de artículos. Lectura abierta, escritura autenticada y limitada al owner.
    Soporta búsqueda (?search=), filtros (ArticuloFilter) y orden (?ordering=).
    """
    serializer_class = ArticuloSerializer
    filterset_class = ArticuloFilter
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "descripcion", "ubicacion"]
    ordering_fields = ["creado", "precio_por_dia"]
    ordering = ["-creado"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # Optimiza consultas y permite filtrar por slug y por categoria (slug)
    def get_queryset(self):
        qs = (
            Articulo.objects
            .select_related("categoria", "propietario")
            .prefetch_related(Prefetch("imagenes", queryset=Imagen.objects.order_by("id")))
            .all()
        )

        # /api/articulos/?slug=mi-slug
        slug = self.request.query_params.get("slug")
        if slug:
            qs = qs.filter(slug=slug)

        # /api/articulos/?categoria=slug-de-categoria
        cat_slug = self.request.query_params.get("categoria")
        if cat_slug:
            qs = qs.filter(categoria__slug=cat_slug)

        return qs

    # Permisos por método
    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    # Asigna propietario
    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)

    # Crear con imágenes (requiere al menos una). Acepta 'portada' opcional.
    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("imagenes")
        portada = request.FILES.get("portada")
        if len(files) == 0 and not portada:
            return Response(
                {"detail": "Debes adjuntar al menos una foto (campo 'imagenes' o 'portada')."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Normaliza campos
        data = {
            "titulo": request.data.get("titulo"),
            "descripcion": request.data.get("descripcion"),
            "categoria": request.data.get("categoria"),
            "estado": request.data.get("estado") or "USADO",
            "precio_por_dia": request.data.get("precio_por_dia") or 0,
            "deposito": request.data.get("deposito") or 0,
            "disponibilidad_global": request.data.get("disponibilidad_global", True) in (True, "true", "True", "1", 1, "on"),
            "ubicacion": request.data.get("ubicacion"),
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        articulo = serializer.instance

        # Portada primero (si viene), luego el resto
        if portada:
            Imagen.objects.create(articulo=articulo, imagen=portada, es_portada=True)

        for f in files:
            Imagen.objects.create(articulo=articulo, imagen=f)

        headers = self.get_success_headers(serializer.data)
        return Response(
            self.get_serializer(articulo).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    # Asegura permiso de owner en update/partial_update/destroy
    def update(self, request, *args, **kwargs):
        instance = self.get_object()  # dispara IsOwnerOrReadOnly
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        return super().destroy(request, *args, **kwargs)

    # --------- Acciones auxiliares ---------

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """
        /api/articulos/recent/?limit=6
        Devuelve los últimos N artículos.
        """
        limit = int(request.query_params.get("limit", 6))
        qs = self.get_queryset().order_by("-creado")[:limit]
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        """
        /api/articulos/mine/
        Devuelve los artículos del usuario autenticado.
        """
        qs = self.get_queryset().filter(propietario=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)
    
    def articulo_detalle(request, id):
        return render(request, "catalog/detalle.html", {"articulo_id": str(id)})
