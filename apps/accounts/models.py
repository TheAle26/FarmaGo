from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Administrador de usuarios personalizado donde el email es el identificador único
    para autenticación en lugar del username.
    """
    
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El Email debe ser configurado")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        def __str__(self):
            # Usar el email en lugar del username
            return f"Usuario: {self.user.email}"
        return user

    def create_superuser(self, email, password, **extra_fields):
        # Asegúrate de que las banderas de permiso estén en True
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("activo", True) # Tu campo personalizado

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_superuser=True.")
            
        # Llamamos a create_user, que ya no requiere 'username'
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None 
    email = models.EmailField(unique=True)
    activo = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # AÑADE ESTO:
    objects = CustomUserManager() # Usar el manager personalizado

    def delete(self, *args, **kwargs):
        self.activo = False
        self.is_active = False
        self.save()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
    
    def __str__(self):
        # Usar el email en lugar del username
        return f"Usuario: {self.user.email}"


# Perfiles
class Cliente(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"Cliente: {self.user.email}"

class Farmacia(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    nombre_farmacia = models.CharField(max_length=100)
    direccion_farmacia = models.CharField(max_length=255)
    valido = models.BooleanField(default=False)

    def __str__(self):
        return f"Farmacia: {self.nombre_farmacia}"

class Repartidor(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    vehiculo = models.CharField(max_length=50)
    disponible = models.BooleanField(default=True)
    valido = models.BooleanField(default=False)

    def __str__(self):
        return f"Repartidor: {self.user.email}"
