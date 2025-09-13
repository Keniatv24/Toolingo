from django.db import models

# Create your models here.
import uuid
from django.contrib.auth.models import AbstractUser
from common.enums import TipoUsuario
from django.conf import settings
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=120, blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    tipo_usuario = models.CharField(max_length=20, choices=TipoUsuario.choices, default=TipoUsuario.AMBOS)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # para admin

    def __str__(self):
        return self.email

class Profile(models.Model):
    class TipoDocumento(models.TextChoices):
        CC = "CC", "Cédula de ciudadanía"
        PASAPORTE = "Pasaporte", "Pasaporte"
    @property
    def nombre(self):
        return self.nombre_completo
    
    class Status(models.TextChoices):
        INCOMPLETE = "INCOMPLETE", "Incompleto"
        VERIFIED = "VERIFIED", "Verificado"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )

    nombre_completo = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    tipo_documento = models.CharField(
        max_length=20, choices=TipoDocumento.choices, default=TipoDocumento.CC
    )
    numero_documento = models.CharField(max_length=50)

    telefono = models.CharField(max_length=30, blank=True)

    pais = models.CharField(max_length=80)
    ciudad = models.CharField(max_length=80)  # pública

    # PRIVADA: solo dueño o staff
    direccion_exacta = models.CharField(max_length=255, blank=True)  # privada

    foto_perfil = models.ImageField(upload_to="profiles/", null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INCOMPLETE
    )
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil({self.user.email if hasattr(self.user,'email') else self.user.username})"

    # helper: marcar aceptación de términos
    def accept_terms(self):
        self.terms_accepted_at = timezone.now()
        self.save(update_fields=["terms_accepted_at"])
    