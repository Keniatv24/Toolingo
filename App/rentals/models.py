import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from catalog.models import Articulo
from common.enums import EstadoAlquiler, MetodoPago, EstadoPago

class Alquiler(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT, related_name="alquileres")
    arrendatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="alquileres_realizados")
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="alquileres_recibidos")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20, choices=EstadoAlquiler.choices, default=EstadoAlquiler.SOLICITADO)
    precio_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.fecha_inicio > self.fecha_fin:
            raise ValidationError("La fecha de inicio debe ser <= fecha fin.")
        traslape = Alquiler.objects.filter(
            articulo=self.articulo,
            estado__in=[EstadoAlquiler.APROBADO, EstadoAlquiler.EN_CURSO],
            fecha_inicio__lte=self.fecha_fin,
            fecha_fin__gte=self.fecha_inicio,
        )
        if self.pk: traslape = traslape.exclude(pk=self.pk)
        if traslape.exists():
            raise ValidationError("El artículo no está disponible en ese rango.")

    def calcular_precio(self):
        dias = (self.fecha_fin - self.fecha_inicio).days + 1
        return dias * self.articulo.precio_por_dia + self.articulo.deposito

    def save(self, *args, **kwargs):
        self.precio_total = self.calcular_precio()
        if not self.propietario_id:
            self.propietario = self.articulo.propietario
        super().save(*args, **kwargs)

class Pago(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alquiler = models.OneToOneField(Alquiler, on_delete=models.CASCADE, related_name="pago")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices)
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    fecha = models.DateTimeField(auto_now_add=True)

class Calificacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alquiler = models.ForeignKey(Alquiler, on_delete=models.CASCADE, related_name="calificaciones")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="calificaciones_emitidas")
    destinatario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="calificaciones_recibidas")
    puntaje = models.IntegerField()
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("alquiler","autor")]

    def clean(self):
        if not (1 <= self.puntaje <= 5):
            raise ValidationError("El puntaje debe estar entre 1 y 5.")
        
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    articulo = models.ForeignKey("catalog.Articulo", on_delete=models.PROTECT, related_name="cart_items")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveIntegerField()
    precio_por_dia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_estimado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"CartItem({self.user_id}, {self.articulo_id}, {self.fecha_inicio}→{self.fecha_fin})"