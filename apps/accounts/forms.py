from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class BaseRegistroForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email"]  # User tiene email como USERNAME_FIELD


class RegistroClienteForm(BaseRegistroForm):
    direccion = forms.CharField(max_length=255)
    telefono = forms.CharField(max_length=20)

class RegistroFarmaciaForm(BaseRegistroForm):
    nombre_farmacia = forms.CharField(max_length=100)
    direccion_farmacia = forms.CharField(max_length=255)

class RegistroRepartidorForm(BaseRegistroForm):
    vehiculo = forms.CharField(max_length=50)