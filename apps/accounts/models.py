from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError


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
            return f"Usuario: {self.email}"
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
        return f"Usuario: {self.email}"

# Modelo para obras sociales
class ObraSocial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Obra social: {self.nombre}"

# Perfiles
class Cliente(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    documento = models.IntegerField(unique=True)
    edad = models.IntegerField()
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    terms_cond = models.BooleanField(default=False)

    def __str__(self):
        return f"Cliente: {self.user.email}"

class Farmacia(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)

    latitud = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    longitud = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )

    cuit = models.CharField(max_length=13, unique=True, default='00-00000000-0')
    cbu = models.CharField(max_length=22, default='000000000000000000000') 
    obras_sociales = models.ManyToManyField(ObraSocial, blank=True, related_name="farmacias")
    documentacion = models.FileField(upload_to='documentacion_farmacias/', null=True, blank=False)
    acepta_tyc = models.BooleanField(default=False)
    valido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre}"

class Repartidor(models.Model):
    VEHICULO_AUTO = 'auto'
    VEHICULO_MOTO = 'moto'
    VEHICULO_BICI = 'bicicleta'
    VEHICULO_CHOICES = [
        (VEHICULO_AUTO, 'Auto'),
        (VEHICULO_MOTO, 'Moto'),
        (VEHICULO_BICI, 'Bicicleta'),
    ]

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    cuit = models.CharField(max_length=13, unique=True, default='00-00000000-0')
    cbu = models.CharField(max_length=22, default='000000000000000000000')
    vehiculo = models.CharField(max_length=20, choices=VEHICULO_CHOICES)
    patente = models.CharField(max_length=7, null=True, blank=True)
    antecedentes = models.FileField(
        upload_to='antecedentes_repartidores/',
        null=False,
        blank=False,
        help_text='Documento de antecedentes (JPG, PNG o PDF).'
    )
    disponible = models.BooleanField(default=True)
    valido = models.BooleanField(default=False)

    # Validación hecha por la ia, no se bien que hace.
    def clean(self):
        """
        Validación: exigir `patente` para auto o moto; limpiar `patente` para bicicleta.
        Lanza ValidationError (dict por campo) si falta patente cuando corresponde.
        """
        if self.vehiculo in (self.VEHICULO_AUTO, self.VEHICULO_MOTO) and not self.patente:
            raise ValidationError({'patente': 'La patente es requerida para auto o moto.'})

        if self.vehiculo == self.VEHICULO_BICI:
            self.patente = None

    def save(self, *args, **kwargs):
        # Forzar validación de modelo antes de guardar (admin y forms respetan esto)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Repartidor: {self.user.email}"
        

