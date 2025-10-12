from rest_framework.permissions import BasePermission

class IsParticipant(BasePermission):
    """
    Permite acceso si el request.user es participante de la conversación.
    Para la creación, se permite a cualquier autenticado.
    """

    def has_permission(self, request, view):
        if view.action in ('create', ):
            return request.user and request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        # obj es una Conversation
        return obj.miembros.filter(user=request.user).exists()
