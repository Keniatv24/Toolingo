from rest_framework import serializers
from .models import Categoria, Articulo, Imagen

class CategoriaSerializer(serializers.ModelSerializer):
    hijas = serializers.SerializerMethodField()
    class Meta:
        model = Categoria
        fields = ("id","nombre","slug","parent","hijas")
    def get_hijas(self, obj):
        return CategoriaSerializer(obj.hijas.all(), many=True).data

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

class ArticuloSerializer(serializers.ModelSerializer):
    imagenes = ImagenSerializer(many=True, read_only=True)
    portada = serializers.SerializerMethodField()

    class Meta:
        model = Articulo
        fields = (
            "id","propietario","titulo","descripcion","categoria","estado",
            "precio_por_dia","deposito","disponibilidad_global","ubicacion",
            "creado","portada","imagenes"
        )
        read_only_fields = ("propietario",)

    def get_portada(self, obj):
        img = obj.imagenes.first()
        if not img or not img.imagen:
            return None
        request = self.context.get("request")
        url = img.imagen.url
        return request.build_absolute_uri(url) if request else url
