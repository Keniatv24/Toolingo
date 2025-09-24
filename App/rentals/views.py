from datetime import timedelta
from django.db import models
from django.utils.dateparse import parse_date

from rest_framework import viewsets, permissions, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Alquiler, Pago, Calificacion, CartItem
from .serializers import (
    AlquilerSerializer,
    PagoSerializer,
    CalificacionSerializer,
    CartItemSerializer,
)


def daterange(d1, d2):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)


class AlquilerViewSet(ModelViewSet):
    serializer_class = AlquilerSerializer

    def get_queryset(self):
        qs = Alquiler.objects.select_related("articulo", "arrendatario", "propietario")
        u = getattr(self.request, "user", None)
        if u and u.is_authenticated:
            if u.is_staff:
                return qs
            return qs.filter(models.Q(arrendatario=u) | models.Q(propietario=u))
        return qs.none()

    def get_permissions(self):
        if getattr(self, "action", None) == "disponibilidad":
            return [permissions.AllowAny()]
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(arrendatario=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mios(self, request):
        qs = self.get_queryset().filter(arrendatario=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="disponibilidad", permission_classes=[permissions.AllowAny])
    def disponibilidad(self, request):
        art = request.query_params.get("articulo")
        s = parse_date(request.query_params.get("from") or "")
        e = parse_date(request.query_params.get("to") or "")

        if not art or not s or not e or s > e:
            return Response({"detail": "Parámetros inválidos"}, status=400)

        bloqueantes = ["SOLICITADO", "APROBADO", "EN_CURSO"]
        qs = Alquiler.objects.filter(
            articulo_id=art,
            estado__in=bloqueantes,
            fecha_inicio__lte=e,
            fecha_fin__gte=s,
        ).order_by("fecha_inicio")

        rangos = []
        dias_ocupados = set()
        for a in qs:
            rangos.append({
                "inicio": a.fecha_inicio.isoformat(),
                "fin": a.fecha_fin.isoformat(),
                "estado": a.estado,
            })
            for d in daterange(max(a.fecha_inicio, s), min(a.fecha_fin, e)):
                dias_ocupados.add(d.isoformat())

        return Response({
            "articulo": art,
            "from": s.isoformat(),
            "to": e.isoformat(),
            "rangos": rangos,
            "dias_ocupados": sorted(list(dias_ocupados)),
        })


class CartItemViewSet(ModelViewSet):
    """
    /api/carrito/  (lista, crea, elimina)
    /api/carrito/checkout/  (POST) -> crea Alquileres a partir del carrito y lo vacía
    """
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.select_related("articulo").filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        items = list(self.get_queryset())
        if not items:
            return Response({"detail": "El carrito está vacío."}, status=400)

        creados = []
        errores = []
        for it in items:
            data = {
                "articulo": it.articulo_id,
                "fecha_inicio": it.fecha_inicio,
                "fecha_fin": it.fecha_fin,
            }
            ser = AlquilerSerializer(data=data, context={"request": request})
            if ser.is_valid():
                try:
                    obj = ser.save()
                    creados.append(obj.id)
                except Exception as e:
                    errores.append(str(e))
            else:
                errores.append(ser.errors)

        # si al menos 1 se creó, vaciamos los correspondientes
        if creados:
            CartItem.objects.filter(id__in=[i.id for i in items]).delete()

        return Response({"creados": creados, "errores": errores}, status=201 if creados else 400)


class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Pago.objects.select_related("alquiler").filter(
            models.Q(alquiler__arrendatario=u) | models.Q(alquiler__propietario=u)
        )


class CalificacionViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Calificacion.objects.filter(models.Q(autor=u) | models.Q(destinatario=u))
