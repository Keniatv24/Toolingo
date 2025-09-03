from rest_framework import serializers
from .models import User

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
