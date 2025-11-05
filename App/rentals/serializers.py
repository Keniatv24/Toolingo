from datetime import date, datetime
from rest_framework import serializers
from django.db.models import Q
from django.utils.timezone import now
from .models import Alquiler, Pago, Calificacion, CartItem


def _as_date(v):
    """Soporta date o datetime sin romper."""
    if isinstance(v, datetime):
        return v.date()
    return v  # ya es date o None


class AlquilerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alquiler
        fields = (
            "id",
            "articulo",
            "arrendatario",
            "propietario",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "precio_total",
            "creado",
        )
        read_only_fields = ("arrendatario", "propietario", "precio_total")

    def validate(self, data):
        inicio = data.get("fecha_inicio")
        fin = data.get("fecha_fin")
        articulo = data.get("articulo")

        if not inicio or not fin or inicio > fin:
            raise serializers.ValidationError("Rango de fechas inválido.")

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if articulo and user and articulo.propietario_id == getattr(user, "id", None):
            raise serializers.ValidationError("No puedes reservar tu propio artículo.")

        bloqueantes = ["SOLICITADO", "APROBADO", "EN_CURSO"]
        solapes = Alquiler.objects.filter(
            articulo=articulo,
            estado__in=bloqueantes,
            fecha_inicio__lte=fin,
            fecha_fin__gte=inicio,
        )
        if self.instance:
            solapes = solapes.exclude(pk=self.instance.pk)
        if solapes.exists():
            raise serializers.ValidationError("Las fechas seleccionadas no están disponibles.")

        return data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        art = validated_data["articulo"]
        validated_data["arrendatario"] = user
        validated_data["propietario"] = art.propietario

        dias = (validated_data["fecha_fin"] - validated_data["fecha_inicio"]).days + 1
        if dias < 1:
            dias = 1

        precio_dia = art.precio_por_dia or 0
        validated_data["precio_total"] = dias * precio_dia

        obj = Alquiler(**validated_data)
        obj.full_clean()
        obj.save()
        return obj


class CartItemSerializer(serializers.ModelSerializer):
    articulo_titulo = serializers.CharField(source="articulo.titulo", read_only=True)
    articulo_portada = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id",
            "articulo",
            "articulo_titulo",
            "articulo_portada",
            "fecha_inicio",
            "fecha_fin",
            "dias",
            "precio_por_dia",
            "total_estimado",
            "creado",
        )
        read_only_fields = ("dias", "precio_por_dia", "total_estimado", "creado")

    def get_articulo_portada(self, obj):
        try:
            return obj.articulo.imagenes.first().imagen.url if obj.articulo.imagenes.exists() else obj.articulo.portada
        except Exception:
            return None

    def validate(self, data):
        inicio = data.get("fecha_inicio")
        fin = data.get("fecha_fin")
        art = data.get("articulo")

        if not inicio or not fin or inicio > fin:
            raise serializers.ValidationError("Rango de fechas inválido.")

        # Evitar pasado (soporta date y datetime)
        if _as_date(inicio) < date.today():
            raise serializers.ValidationError("La fecha inicio no puede ser en el pasado.")

        user = self.context["request"].user
        if art and art.propietario_id == user.id:
            raise serializers.ValidationError("No puedes agregar tu propio artículo al carrito.")

        # Solapes con alquileres existentes
        bloqueantes = ["SOLICITADO", "APROBADO", "EN_CURSO"]
        if Alquiler.objects.filter(
            articulo=art,
            estado__in=bloqueantes,
            fecha_inicio__lte=fin,
            fecha_fin__gte=inicio,
        ).exists():
            raise serializers.ValidationError("Las fechas seleccionadas no están disponibles.")

        # Solapes dentro del mismo carrito del usuario
        if CartItem.objects.filter(
            user=user,
            articulo=art,
            fecha_inicio__lte=fin,
            fecha_fin__gte=inicio,
        ).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Ya tienes este artículo en el carrito para un rango que se cruza.")

        # Calcular totales
        dias = (fin - inicio).days + 1
        if dias < 1:
            dias = 1
        data["dias"] = dias
        data["precio_por_dia"] = art.precio_por_dia or 0
        data["total_estimado"] = dias * (art.precio_por_dia or 0)
        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = ("id", "alquiler", "monto", "metodo", "estado", "fecha")
        read_only_fields = ("estado", "fecha")


class CalificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = ("id", "alquiler", "autor", "destinatario", "puntaje", "comentario", "fecha")
        read_only_fields = ("autor", "fecha")

    def create(self, validated_data):
        validated_data["autor"] = self.context["request"].user
        cal = Calificacion(**validated_data)
        cal.full_clean()
        cal.save()
        return cal
