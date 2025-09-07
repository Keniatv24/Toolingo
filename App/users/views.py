# App/users/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Profile
from .permissions import IsOwnerOrReadOnly
from .serializers import UserSerializer, UserRegisterSerializer, ProfilePublicSerializer, ProfileOwnerSerializer    
from rest_framework.exceptions import MethodNotAllowed

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        return UserRegisterSerializer if self.action == "create" else UserSerializer

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


class ProfileViewSet(viewsets.ModelViewSet):
    """
    GET list/retrieve -> público (sin 'direccion_exacta' salvo dueño/admin)
    me -> devuelve MI perfil completo
    PUT/PATCH -> permitimos actualizaciones parciales
    """
    queryset = Profile.objects.select_related("user").all()
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        # Dueño en update/partial_update/destroy o en /me
        if self.action in ("update", "partial_update", "destroy", "me"):
            return ProfileOwnerSerializer

        # En retrieve, si es dueño o staff, ve campos privados
        if self.action == "retrieve":
            try:
                obj = self.get_object()
            except Exception:
                obj = None
            req = getattr(self, "request", None)
            if obj and req and req.user.is_authenticated and (obj.user_id == req.user.id or req.user.is_staff):
                return ProfileOwnerSerializer

        # Por defecto, vista pública
        return ProfilePublicSerializer

    def update(self, request, *args, **kwargs):
        # Trata PUT como parcial para no exigir todos los campos
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        # Garantiza que exista un perfil para el usuario
        profile, _ = Profile.objects.get_or_create(user=request.user)
        ser = ProfileOwnerSerializer(profile, context={"request": request})
        return Response(ser.data)
