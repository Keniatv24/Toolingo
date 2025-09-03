from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, UserRegisterSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        return UserSerializer

    def get_permissions(self):
        # Cualquiera puede registrarse
        if self.action == "create":
            return [permissions.AllowAny()]
        # Los demás endpoints requieren estar logueado
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Devuelve los datos del usuario autenticado"""
        return Response(UserSerializer(request.user).data)
