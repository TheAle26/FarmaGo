from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Pedido, DetallePedido, StockMedicamento,Farmacia,Cliente
from apps.orders.utils import es_cliente, es_farmacia, es_repartidor
from .forms import PedidoForm
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from django.db.models import Case, When

# ---------- CLIENTE ----------
@login_required
def cliente_panel(request):
    if not es_cliente(request.user): return HttpResponseForbidden("Solo clientes")
    pedidos = Pedido.objects.filter(cliente=request.user.cliente).order_by("-creado")
    return render(request, "cliente/panel.html", {"pedidos": pedidos})

# orders/views.py

@login_required
def add_to_cart(request, stock_id):
    stock_item = get_object_or_404(StockMedicamento, id=stock_id)
    cantidad = int(request.POST.get('cantidad', 1))
    carrito = request.session.get('carrito', {'farmacias': {}, 'total_general': 0.0})


    farmacia_id = str(stock_item.farmacia.id)
    stock_id_str = str(stock_item.id)

    farmacia_data = carrito['farmacias'].get(farmacia_id, {
        'nombre_farmacia': stock_item.farmacia.nombre,
        'subtotal': 0.0,
        'items': {}
    })

    item_data = farmacia_data['items'].get(stock_id_str, {
        'nombre': stock_item.medicamento.nombre_comercial,
        'precio_unitario': float(stock_item.precio),
        'cantidad': 0
    })

    # Actualizar cantidad y subtotales
    item_data['cantidad'] += cantidad

    #  Guardar todo de vuelta en la sesión
    farmacia_data['items'][stock_id_str] = item_data
    carrito['farmacias'][farmacia_id] = farmacia_data
    
    request.session['carrito'] = carrito # Guardar la sesión
    request.session.modified = True # Marcarla como modificada

    messages.success(request, f"Agregado {stock_item.medicamento.nombre_comercial}.")
    return redirect('ver_carrito')
## me gustaria en realidad que dentro de la view de ver/ buscar remedias, al hacer click en el boton,
# la otra view detecte ese post, tome los datos del  stock_id y se los pase a esta funcion,
# y que esta no tenga return, simplemente ponga el mensajito de agregado



@login_required
def ver_carrito(request):
    carrito_session = request.session.get('carrito', {'farmacias': {}})
    
    carrito_contexto = {
        'farmacias': [],
        'total_general': carrito_session.get('total_general', 0.0)
    }
    
    hay_items_con_receta = False

    for farmacia_id, farmacia_data in carrito_session['farmacias'].items():
        items_contexto = []
        for item_id, item_data in farmacia_data['items'].items():
            try:
                # Obtenemos el objeto real del inventario
                stock_item = StockMedicamento.objects.select_related('medicamento').get(id=item_id)
                
                item_data['stock_obj'] = stock_item
                items_contexto.append(item_data)
                
                if stock_item.medicamento.requiere_receta:
                    hay_items_con_receta = True
                    
            except StockMedicamento.DoesNotExist:
                pass 
        
        farmacia_data['items_enriquecidos'] = items_contexto
        carrito_contexto['farmacias'].append(farmacia_data)

    context = {
        'carrito_data': carrito_contexto,
        'total_general': carrito_contexto['total_general'],
        'hay_items_con_receta': hay_items_con_receta 
    }
    
    return render(request, 'cliente/carrito_detalle.html', context)


# orders/views.py

@login_required
@transaction.atomic
def finalizar_compra_view(request):
    
    if request.method != 'POST':
        return redirect('ver_carrito')

    carrito = request.session.get('carrito')
    
    if not carrito or not carrito.get('farmacias'):
        messages.error(request, "Tu carrito está vacío.")
        return redirect('ver_carrito')

    try:
        pedidos_creados = []
        
        for farmacia_id, farmacia_data in carrito['farmacias'].items():
            farmacia_obj = get_object_or_404(Farmacia, id=farmacia_id)
            
            nuevo_pedido = Pedido.objects.create(
                cliente=request.user,
                farmacia=farmacia_obj,
                estado='PENDIENTE', 
                total=farmacia_data['subtotal']
            )
            
            # Iterar sobre los items de la sesión
            for item_id, item_data in farmacia_data['items'].items():
                stock = StockMedicamento.objects.select_for_update().get(id=item_id)
                
                # (Validación de Stock)
                if stock.stock_actual < item_data['cantidad']:
                    raise Exception(f"Stock insuficiente para {stock.medicamento.nombre_comercial}.")
                
                receta_para_adjuntar = None # Por defecto es Nulo
                
                # 1. Chequear si el medicamento REQUIERE receta
                if stock.medicamento.requiere_receta:
                    # 2. Construir el 'name' del input del formulario
                    file_input_name = f"receta_{item_id}" 
                    
                    # 3. Obtener el archivo de request.FILES
                    receta_file = request.FILES.get(file_input_name)
                    
                    # 4. Validar que el archivo SÍ FUE ENVIADO
                    if not receta_file:
                        raise Exception(f"Falta adjuntar la receta para {stock.medicamento.nombre_comercial}.")
                    
                    receta_para_adjuntar = receta_file


                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    medicamento=stock.medicamento,
                    cantidad=item_data['cantidad'],
                    precio_unitario_snapshot=stock.precio,
                    receta_adjunta=receta_para_adjuntar # <-- Se guarda el archivo
                )
                

                # (Descuento de Stock)
                stock.stock_actual = F('stock_actual') - item_data['cantidad']
                stock.save(update_fields=['stock_actual'])

            pedidos_creados.append(nuevo_pedido.id)

        # (Limpiar sesión y redirigir)
        del request.session['carrito']
        request.session.modified = True
        
        messages.success(request, f"Se generaron {len(pedidos_creados)} pedidos correctamente.")
        return redirect('cliente_panel')

    except Exception as e:
        # Captura "Stock insuficiente" O "Falta adjuntar la receta"
        messages.error(request, str(e))
        return redirect('ver_carrito')
    
    
    
# ---------- FARMACIA ----------
@login_required
def farmacia_panel(request):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")

    todos_los_pedidos = Pedido.objects.filter(
        farmacia=request.user.farmacia
    )

    pedidos_ordenados = todos_los_pedidos.annotate(
        prioridad_estado=Case(
            When(estado="PENDIENTE", then=0), # Los PENDIENTE van primero
            default=1 # El resto va después
        )
    ).order_by('prioridad_estado', 'creado') # Ordena por prioridad, y luego por fecha

    # Pasa la lista completa y ordenada a la plantilla
    return render(request, "farmacia/panel.html", {"pedidos": pedidos_ordenados})

@login_required
def farmacia_aceptar(request, pedido_id):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")

    pedido = get_object_or_404(
        Pedido, 
        id=pedido_id, 
        estado="PENDIENTE", 
        farmacia=request.user.farmacia 
    )
    pedido.estado = "ACEPTADO"
    pedido.save()
    
    return redirect("farmacia_panel")

@login_required
def farmacia_rechazar(request, pedido_id):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")

    pedido = get_object_or_404(
        Pedido, 
        id=pedido_id, 
        estado="PENDIENTE", 
        farmacia=request.user.farmacia 
    )
    pedido.estado = "RECHAZADO"
    pedido.save()
    
    return redirect("farmacia_panel")

# ---------- REPARTIDOR ----------
@login_required
def repartidor_panel(request):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    disponibles = Pedido.objects.filter(estado="ACEPTADO", repartidor__isnull=True)
    # Usar la instancia `Repartidor` asociada al user
    mis = Pedido.objects.filter(repartidor=request.user.repartidor).exclude(estado__in=["ENTREGADO","RECHAZADO"])
    return render(request, "repartidor/panel.html", {"disponibles": disponibles, "mis": mis})

@login_required
def repartidor_tomar(request, pedido_id):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    p = get_object_or_404(Pedido, id=pedido_id, estado="ACEPTADO", repartidor__isnull=True)
    # asignar la instancia Repartidor relacionada al user, no el User
    p.repartidor = request.user.repartidor
    p.estado = "EN_CAMINO"
    p.save()
    return redirect("repartidor_panel")

@login_required
def repartidor_entregado(request, pedido_id):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    p = get_object_or_404(Pedido, id=pedido_id, repartidor=request.user.repartidor, estado="EN_CAMINO")
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

