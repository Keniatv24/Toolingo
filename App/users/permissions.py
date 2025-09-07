from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Lectura pública (GET/HEAD/OPTIONS).
    Escritura solo si es el dueño del perfil.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(obj, "user_id", None) == request.user.id or request.user.is_staff
