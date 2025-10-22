from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, logout
from .forms import (RegistroClienteForm, RegistroFarmaciaForm, RegistroRepartidorForm)
from .models import Cliente, Farmacia, Repartidor


class CustomLoginView(LoginView):
    success_url = None
    template_name = "login.html" 
    #redirect_authenticated_user = True 

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'cliente'):
            return redirect("cliente_panel").url
        
        elif hasattr(user, 'farmacia'):
            farmacia = user.farmacia  
            if farmacia.valido:
                return redirect("farmacia_panel").url
            else:
                logout(self.request) 
                messages.error(self.request, "¡Acceso denegado! Tu perfil de Farmacia aún no ha sido validado por el administrador.")
                return redirect("login").url 
        
        
        elif hasattr(user, 'repartidor'):
            repartidor = user.repartidor 
            if repartidor.valido:
                return redirect("repartidor_panel").url
            else:
                logout(self.request) 
                messages.error(self.request, "¡Acceso denegado! Tu perfil de Repartidor aún no ha sido validado por el administrador.")
                return redirect("login").url
        
        # 4. DEFAULT
        return super().get_success_url()
   
login_view = CustomLoginView.as_view()
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
