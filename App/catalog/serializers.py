# App/catalog/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Categoria, Articulo, Imagen

User = get_user_model()


# Categorías

class CategoriaSerializer(serializers.ModelSerializer):
    hijas = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ("id", "nombre", "slug", "parent", "hijas")

    def get_hijas(self, obj):
        return CategoriaSerializer(obj.hijas.all(), many=True).data


# Imágenes

class ImagenSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Imagen
        fields = ("id", "url", "descripcion")

    def get_url(self, obj):
        if not obj.imagen:
            return None
        request = self.context.get("request")
        url = obj.imagen.url
        return request.build_absolute_uri(url) if request else url


# Propietario (usuario básico)

class UserBasicSerializer(serializers.ModelSerializer):
    """
    Devuelve datos básicos del usuario. Intenta tomarlos del propio User
    o de un perfil relacionado (perfil/profile) si existe.
    """
    nombre = serializers.SerializerMethodField()
    telefono = serializers.SerializerMethodField()
    ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Ajusta estos campos a tu modelo real.
        fields = ["id", "nombre", "email", "telefono", "ubicacion"]

    # Helpers para tomar desde user o su perfil
    def _from_user_or_profile(self, obj, *attrs):
        # Busca en user, luego en user.perfil, luego en user.profile
        for attr in attrs:
            val = getattr(obj, attr, None)
            if val:
                return val
        perfil = getattr(obj, "perfil", None) or getattr(obj, "profile", None)
        if perfil:
            for attr in attrs:
                val = getattr(perfil, attr, None)
                if val:
                    return val
        return None

    def get_nombre(self, obj):
        # Intenta nombre / first_name+last_name / username
        nombre = self._from_user_or_profile(obj, "nombre", "full_name")
        if not nombre:
            full = " ".join(filter(None, [getattr(obj, "first_name", ""), getattr(obj, "last_name", "")])).strip()
            nombre = full or getattr(obj, "username", None)
        return nombre or ""

    def get_telefono(self, obj):
        tel = self._from_user_or_profile(obj, "telefono", "phone", "celular", "mobile")
        return tel or ""

    def get_ubicacion(self, obj):
        ubi = self._from_user_or_profile(obj, "ubicacion", "ciudad", "city", "location")
        return ubi or ""


# Artículos

class ArticuloSerializer(serializers.ModelSerializer):
    imagenes = ImagenSerializer(many=True, read_only=True)
    portada = serializers.SerializerMethodField()
    # Datos anidados del propietario
    propietario_info = UserBasicSerializer(source="propietario", read_only=True)

    class Meta:
        model = Articulo
        fields = (
            "id",
            "propietario",         # PK del user 
            "propietario_info",    # Datos básicos del propietario
            "titulo",
            "descripcion",
            "categoria",
            "estado",
            "precio_por_dia",
            "deposito",
            "disponibilidad_global",
            "ubicacion",
            "creado",
            "portada",
            "imagenes",
            "lat",
             "lng",

        )
        read_only_fields = ("propietario",)

    def get_portada(self, obj):
        # Toma la primera imagen del artículo como portada
        img = obj.imagenes.first()
        if not img or not img.imagen:
            return None
        request = self.context.get("request")
        url = img.imagen.url
        return request.build_absolute_uri(url) if request else url
