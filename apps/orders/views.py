from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Pedido
from apps.orders.utils import es_cliente, es_farmacia, es_repartidor
from .forms import PedidoForm


# ---------- CLIENTE ----------
@login_required
def cliente_panel(request):
    if not es_cliente(request.user): return HttpResponseForbidden("Solo clientes")
    pedidos = Pedido.objects.filter(cliente=request.user).order_by("-creado")
    return render(request, "cliente/panel.html", {"pedidos": pedidos})

@login_required
def crear_pedido(request):
    if not es_cliente(request.user): return HttpResponseForbidden("Solo clientes")
    if request.method == "POST":
        detalles = request.POST.get("detalles","")
        Pedido.objects.create(cliente=request.user, detalles=detalles)
        return redirect("cliente_panel")
    return render(request, "cliente/crear.html")

# ---------- FARMACIA ----------
@login_required
def farmacia_panel(request):
    if not es_farmacia(request.user): return HttpResponseForbidden("Solo farmacias")
    pendientes = Pedido.objects.filter(estado="PENDIENTE").order_by("creado")
    return render(request, "farmacia/panel.html", {"pedidos": pendientes})

@login_required
def farmacia_aceptar(request, pedido_id):
    if not es_farmacia(request.user): return HttpResponseForbidden("Solo farmacias")
    p = get_object_or_404(Pedido, id=pedido_id, estado="PENDIENTE")
    p.farmacia = request.user
    p.estado = "ACEPTADO"
    p.save()
    return redirect("farmacia_panel")

@login_required
def farmacia_rechazar(request, pedido_id):
    if not es_farmacia(request.user): return HttpResponseForbidden("Solo farmacias")
    p = get_object_or_404(Pedido, id=pedido_id, estado="PENDIENTE")
    p.farmacia = request.user
    p.estado = "RECHAZADO"
    p.save()
    return redirect("farmacia_panel")

# ---------- REPARTIDOR ----------
@login_required
def repartidor_panel(request):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    disponibles = Pedido.objects.filter(estado="ACEPTADO", repartidor__isnull=True)
    mis = Pedido.objects.filter(repartidor=request.user).exclude(estado__in=["ENTREGADO","RECHAZADO"])
    return render(request, "repartidor/panel.html", {"disponibles": disponibles, "mis": mis})

@login_required
def repartidor_tomar(request, pedido_id):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    p = get_object_or_404(Pedido, id=pedido_id, estado="ACEPTADO", repartidor__isnull=True)
    p.repartidor = request.user
    p.estado = "EN_CAMINO"
    p.save()
    return redirect("repartidor_panel")

@login_required
def repartidor_entregado(request, pedido_id):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    p = get_object_or_404(Pedido, id=pedido_id, repartidor=request.user, estado="EN_CAMINO")
    p.estado = "ENTREGADO"
    p.save()
    return redirect("repartidor_panel")


#---------------------pedido----------------


@login_required
def crear_pedido(request):
    form = PedidoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.cliente = request.user
        p.save()
        return redirect("cliente_panel")
    return render(request, "cliente/crearPedido.html", {"form": form})

