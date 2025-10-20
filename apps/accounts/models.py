from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    #username = None  # quitamos username
    email = models.EmailField(unique=True)  # login con email
    activo = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # antes estaba "username", lo sacamos

    def delete(self, *args, **kwargs):
        self.activo = False
        self.is_active = False
        self.save()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


# Perfiles
class Cliente(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"Cliente: {self.user.username}"

class Farmacia(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    nombre_farmacia = models.CharField(max_length=100)
    direccion_farmacia = models.CharField(max_length=255)

    def __str__(self):
        return f"Farmacia: {self.nombre_farmacia}"

class Repartidor(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    vehiculo = models.CharField(max_length=50)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Repartidor: {self.user.username}"
