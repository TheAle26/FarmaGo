from django import forms
from django.contrib.auth.forms import UserCreationForm
# Importar para manejar errores de validación
from django.core.exceptions import ValidationError 
# Importar para validadores de rango
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import User, Cliente

class BaseRegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email"]  # User tiene email como USERNAME_FIELD


class RegistroClienteForm(BaseRegistroForm):
    nombre = forms.CharField(max_length=30)
    apellido = forms.CharField(max_length=30)
    documento = forms.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99999999)])
    edad = forms.IntegerField(validators=[MinValueValidator(18), MaxValueValidator(120)])
    direccion = forms.CharField(max_length=255)
    telefono = forms.CharField(max_length=20)
    terms_cond = forms.BooleanField(label="Acepto los términos y condiciones")
    
    class Meta(BaseRegistroForm.Meta):
        fields = BaseRegistroForm.Meta.fields + ["password1","password2","nombre","apellido","documento","edad","direccion", "telefono","terms_cond"]

    # Validación personalizada para el campo 'documento'
    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        
        # Verifica si ya existe un cliente con ese número de documento.
        # Esto asume que el modelo 'Cliente' ya existe y está importado.
        if Cliente.objects.filter(documento=documento).exists():
            raise ValidationError("Ya existe un cliente registrado con este número de documento.")
        
        return documento # Si es único, devuelve el valor.

class RegistroFarmaciaForm(BaseRegistroForm):
    nombre_farmacia = forms.CharField(max_length=100)
    direccion_farmacia = forms.CharField(max_length=255)

class RegistroRepartidorForm(BaseRegistroForm):
    vehiculo = forms.CharField(max_length=50)