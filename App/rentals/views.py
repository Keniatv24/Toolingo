from django.db import models
from rest_framework import viewsets, permissions
from .models import Alquiler, Pago, Calificacion
from .serializers import AlquilerSerializer, PagoSerializer, CalificacionSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response


class AlquilerViewSet(viewsets.ModelViewSet):
    serializer_class = AlquilerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        return Alquiler.objects.filter(models.Q(arrendatario=u) | models.Q(propietario=u)).select_related("articulo")

class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Pago.objects.filter(alquiler__arrendatario=self.request.user)

class CalificacionViewSet(viewsets.ModelViewSet):
    serializer_class = CalificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        u = self.request.user
        return Calificacion.objects.filter(models.Q(autor=u) | models.Q(destinatario=u))
    
class AlquilerViewSet(ModelViewSet):
    queryset = Alquiler.objects.all()
    serializer_class = AlquilerSerializer

    def get_permissions(self):
        # POST requiere login. Lectura puede ser pública.
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(arrendatario=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def mios(self, request):
        qs = self.get_queryset().filter(arrendatario=request.user)
        return Response(self.get_serializer(qs, many=True).data)