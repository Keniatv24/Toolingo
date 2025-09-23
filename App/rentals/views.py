from datetime import timedelta
from django.db import models
from django.utils.dateparse import parse_date
from rest_framework import viewsets, permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Alquiler, Pago, Calificacion
from .serializers import AlquilerSerializer, PagoSerializer, CalificacionSerializer


def daterange(d1, d2):
    cur = d1
    while cur <= d2:
        yield cur
        cur += timedelta(days=1)


class AlquilerViewSet(ModelViewSet):
    """
    CRUD de alquileres.
    - Acciones:
        * GET disponibilidad/?articulo=<id>&from=YYYY-MM-DD&to=YYYY-MM-DD  (pública)
        * GET mios/   (autenticado)  -> alquileres donde soy arrendatario
    """
    serializer_class = AlquilerSerializer

    # Por privacidad: solo staff ve todos; usuarios ven solo los suyos.
    def get_queryset(self):
        qs = Alquiler.objects.select_related("articulo", "arrendatario", "propietario")
        u = getattr(self.request, "user", None)
        if u and u.is_authenticated:
            if u.is_staff:
                return qs
            return qs.filter(models.Q(arrendatario=u) | models.Q(propietario=u))
        # No autenticado: no listamos nada (para /list), la disponibilidad es otra acción pública
        return qs.none()

    def get_permissions(self):
        # La acción 'disponibilidad' es pública.
        if getattr(self, "action", None) == "disponibilidad":
            return [permissions.AllowAny()]
        # Crear/editar/borrar requieren login
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            return [permissions.IsAuthenticated()]
        # Lecturas normales: autenticado (para no exponer datos privados)
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # arrendatario = request.user; propietario = dueño del artículo (lo completa el serializer)
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
        """
        GET /api/alquileres/disponibilidad/?articulo=<uuid>&from=YYYY-MM-DD&to=YYYY-MM-DD
        Devuelve rangos y días ocupados para el artículo en el intervalo consultado.
        """
        art = request.query_params.get("articulo")
        s = parse_date(request.query_params.get("from") or "")
        e = parse_date(request.query_params.get("to") or "")

        if not art or not s or not e or s > e:
            return Response({"detail": "Parámetros inválidos"}, status=400)

        bloqueantes = ["SOLICITADO", "APROBADO", "EN_CURSO"]
        qs = Alquiler.objects.filter(
            articulo_id=art,
            estado__in=bloqueantes,
            # solape: start <= e and end >= s
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


class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        # puede ver pagos donde es arrendatario o propietario del alquiler
        return Pago.objects.select_related("alquiler").filter(
            models.Q(alquiler__arrendatario=u) | models.Q(alquiler__propietario=u)
        )


class CalificacionViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Calificacion.objects.filter(models.Q(autor=u) | models.Q(destinatario=u))
