import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from common.enums import EstadoArticulo

class Categoria(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="hijas")
    slug = models.SlugField(max_length=120, blank=True)

    class Meta:
        unique_together = [("parent","nombre")]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.parent.slug}-{self.nombre}" if self.parent else self.nombre
            self.slug = slugify(base)
        super().save(*args, **kwargs)

    @property
    def es_hoja(self):
        return not self.hijas.exists()

    def __str__(self):
        return f"{self.parent} > {self.nombre}" if self.parent else self.nombre

class Articulo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    propietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="articulos")
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="articulos")
    estado = models.CharField(max_length=20, choices=EstadoArticulo.choices, default=EstadoArticulo.USADO)
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2)
    deposito = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    disponibilidad_global = models.BooleanField(default=True)
    ubicacion = models.CharField(max_length=140)
    creado = models.DateTimeField(auto_now_add=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitud en grados decimales")
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitud en grados decimales")

    @property
    def has_coords(self) -> bool:
        return self.lat is not None and self.lng is not None


    def clean(self):
        if not self.categoria.es_hoja:
            raise ValidationError("Selecciona una subcategoría (categoría hoja).")

    def __str__(self):
        return self.titulo

class Imagen(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name="imagenes")
    imagen = models.ImageField(upload_to="articulos/")
    descripcion = models.CharField(max_length=140, blank=True)
