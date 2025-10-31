from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions


def pagos_view(request):
    
    return render(request, "checkout/pagos.html")

class NotificacionesList(APIView):
    """
    Stub de notificaciones para no romper el detalle.
    Retorna una lista vacía (ajústalo luego a tu lógica real).
    """
    permission_classes = [permissions.IsAuthenticated]  # o AllowAny si quieres verlo sin login

    def get(self, request):
        return Response([])