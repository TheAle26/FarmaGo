from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from .forms import (RegistroClienteForm, RegistroFarmaciaForm, RegistroRepartidorForm)
from .models import Cliente, Farmacia, Repartidor

# si preferís las genéricas:
login_view = LoginView.as_view(template_name="login.html")
logout_view = LogoutView.as_view()

def registro_selector(request):
    return render(request, "registro_selector.html")

def registro_cliente(request):
    form = RegistroClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()  # crea User (email + pass)
        Cliente.objects.create(
            user=user,
            direccion=form.cleaned_data["direccion"],
            telefono=form.cleaned_data["telefono"],
        )
        messages.success(request, "Cuenta de cliente creada.")
        login(request, user)  # opcional: auto-login
        return redirect("cliente_panel")
    return render(request, "registro_form.html", {"form": form, "titulo": "Registro Cliente"})

def registro_farmacia(request):
    form = RegistroFarmaciaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Farmacia.objects.create(
            user=user,
            nombre_farmacia=form.cleaned_data["nombre_farmacia"],
            direccion_farmacia=form.cleaned_data["direccion_farmacia"],
        )
        messages.success(request, "Cuenta de farmacia creada.")
        login(request, user)
        return redirect("farmacia_panel")
    return render(request, "registro_form.html", {"form": form, "titulo": "Registro Farmacia"})

def registro_repartidor(request):
    form = RegistroRepartidorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Repartidor.objects.create(
            user=user,
            vehiculo=form.cleaned_data["vehiculo"],
        )
        messages.success(request, "Cuenta de repartidor creada.")
        login(request, user)
        return redirect("repartidor_panel")
    return render(request, "registro_form.html", {"form": form, "titulo": "Registro Repartidor"})
