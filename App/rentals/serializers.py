from rest_framework import serializers
from django.db.models import Q

from .models import Alquiler, Pago, Calificacion


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

        # No permitir reservar el propio artículo
        if articulo and user and articulo.propietario_id == getattr(user, "id", None):
            raise serializers.ValidationError("No puedes reservar tu propio artículo.")

        # Chequeo de solape con estados que bloquean
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
        """
        Completa arrendatario (ya viene de perform_create),
        propietario desde el artículo y calcula precio_total simple: días * precio_por_dia.
        """
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
