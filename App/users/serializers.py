from rest_framework import serializers
from .models import User, Profile

# ===USERSS 
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "nombre", "direccion", "telefono", "tipo_usuario")


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password", "nombre", "direccion", "telefono", "tipo_usuario")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return value

    def create(self, validated_data):
        # Asignar username = email para cumplir unicidad si el modelo hereda de AbstractUser
        password = validated_data.pop("password")
        email = validated_data.get("email")
        user = User(username=email, **validated_data)
        user.set_password(password)  # guardar hash de contraseña
        user.is_active = True
        user.save()
        return user


# PROFILES
# =======================
PUBLIC_FIELDS = (
    "id",
    "user",
    "nombre_completo",
    "fecha_nacimiento",
    "tipo_documento",
    "numero_documento",
    "telefono",
    "pais",
    "ciudad",           # pública
    "foto_perfil",
    "status",
    "terms_accepted_at",
    "created_at",
    "updated_at",
)


class ProfilePublicSerializer(serializers.ModelSerializer):
    """
    Versión pública del perfil (no expone direccion_exacta).
    """
    class Meta:
        model = Profile
        fields = PUBLIC_FIELDS
        read_only_fields = fields


class ProfileOwnerSerializer(serializers.ModelSerializer):
    """
    Versión para el dueño o staff (incluye direccion_exacta) y
    marca como VERIFIED si todos los campos requeridos están completos.
    """
    class Meta:
        model = Profile
        fields = PUBLIC_FIELDS + ("direccion_exacta",)  # incluye privada
        read_only_fields = ("status", "terms_accepted_at", "created_at", "updated_at")

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # Solo dueño o staff debe ver direccion_exacta
        request = self.context.get("request")
        if not request:
            rep.pop("direccion_exacta", None)
            return rep
        is_owner = request.user.is_authenticated and instance.user_id == request.user.id
        if not (is_owner or request.user.is_staff):
            rep.pop("direccion_exacta", None)
        return rep

    def update(self, instance, validated_data):
        # aplicar cambios
        for k, v in validated_data.items():
            setattr(instance, k, v)

        # si está completo, marcar VERIFIED
        required = ["nombre_completo", "tipo_documento", "numero_documento", "telefono", "pais", "ciudad"]
        if all(getattr(instance, f) for f in required):
            instance.status = "VERIFIED"

        instance.save()
        return instance
